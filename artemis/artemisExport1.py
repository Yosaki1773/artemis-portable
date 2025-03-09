import json
import pymysql
from pymysql import cursors, connections
from typing import Literal
import argparse
import logging
from logging.handlers import TimedRotatingFileHandler
import coloredlogs
from datetime import datetime, timezone
import pytz

mysql: connections.Connection
cursor: cursors.Cursor

def connect_remote_mysql(args):
    global mysql, cursor
    mysql = pymysql.connect(host=args.host, port=args.port, user=args.user, password=args.password)
    cursor = mysql.cursor()
    
def recursor():
    global cursor
    cursor.close()
    cursor = mysql.cursor()
    
class ChuniData:
    userData: dict
    userActivityList: list
    userCharacterList: list
    userChargeList: list
    userCourseList: list
    userDuelList: list
    userGameOption: dict
    userItemList: list
    userMapList: list
    userMusicDetailList: list
    userPlaylogList: list
    
    def __init__(self, args) -> None:
        self.user = args.target_user
        self.version = args.target_version
        self.gameId = 'SDHD'
        
        logger = logging.getLogger('export')
        log_fmt_str = "[%(asctime)s] Exporter | %(levelname)s | %(message)s"
        log_fmt = logging.Formatter(log_fmt_str)
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(log_fmt)
        logger.addHandler(consoleHandler)
        log_lv = logging.INFO
        logger.setLevel(log_lv)
        coloredlogs.install(level=log_lv, logger=logger, fmt=log_fmt_str)
        self.logger = logger
        
        try:
            connect_remote_mysql(args)
        except Exception as ex:
            logger.error(ex)
            exit(1)
        
        logger.info('Starting exporter...')
        try:
            self.userData = self.collect(resultType='dict', database='chuni_profile_data', version=True, ignore = ('id', 'user', 'isWebJoin', 'version', 'isMaimai'), ac=True)
            self.userActivityList = self.collect(resultType='list', database='chuni_profile_activity', version=False, ignore = ('id', 'user'))
            self.userCharacterList = self.collect(resultType='list', database='chuni_item_character', version=False, ignore = ('id', 'user'))
            self.userChargeList = self.collect(resultType='list', database='chuni_profile_charge', version=False, ignore = ('id', 'user'))
            self.userCourseList = self.collect(resultType='list', database='chuni_score_course', version=False, ignore = ('id', 'user'))
            self.userDuelList = self.collect(resultType='list', database='chuni_item_duel', version=False, ignore = ('id', 'user'))
            self.userGameOption = self.collect(resultType='dict', database='chuni_profile_option', version=False, ignore = ('id', 'user'))
            self.userItemList = self.collect(resultType='list', database='chuni_item_item', version=False, ignore = ('id', 'user'))
            self.userMapList = self.collect(resultType='list', database='chuni_item_map_area', version=False, ignore = ('id', 'user'))
            self.userMusicDetailList = self.collect(resultType='list', database='chuni_score_best', version=False, ignore = ('id', 'user'))
            self.userPlaylogList = self.collect(resultType='list', database='chuni_score_playlog', version=False, ignore = ('id', 'user'))
        except Exception as ex:
            logger.error(ex)
            exit(1)
        logger.info('Successfully exported.')
    
    def dict_type(self, keys, values, dataTypes, ignore, addition: dict):
        result = {}
        for i in range(len(keys)):
            value = values[0][i]
            key = keys[i]
            if key in ignore:
                continue
            if dataTypes[i] == 'tinyint(1)':
                value = True if value else False
            if value == 'null':
                value = None
            if key == 'activityId':
                key = 'id'
            if 'date' in key.lower() and value != None:
                value = value.replace(' ','T')
            result[keys[i]] = value
        for key in addition:
            result[key] = addition[key]
        return result
        
    def list_type(self, keys, values, dataTypes, ignore):
        result = []
        for items in values:
            tmp = {}
            for i in range(len(items)):
                value = items[i]
                key = keys[i]
                if key in ignore:
                    continue
                if dataTypes[i] == 'tinyint(1)':
                    value = True if value else False
                if value == 'null':
                    value = None
                if 'date' in key.lower() and value != None:
                    value = value.replace(' ','T')
                tmp[keys[i]] = value
            result.append(tmp)
        return result
    
    def collect(self, resultType: Literal['dict', 'list'], database: str, version: bool, ac=False, ignore: tuple = ('id', 'user')):
        self.logger.info(f'Exporting {database}')
        if resultType not in ['dict', 'list']:
            self.logger.error('Unsuppoted type')
            exit(1)
        recursor()
        if version:
            cursor.execute("select * from aime.{} where user = {} and version = {};".format(database, self.user, self.version))
        else:
            cursor.execute("select * from aime.{} where user = {};".format(database, self.user))
        values = cursor.fetchall()
        keys = [info[0] for info in cursor.description]
        updated_rows = []
        local_tz = pytz.timezone('Asia/Shanghai')  # 设置时区为东八区

        for row in values:
            row_list = list(row)
            for i in range(len(keys)):
                column_name = keys[i]
                column_value = row[i]

                if column_value is not None and column_name.endswith('Date') and not isinstance(column_value, int) and 'T' not in column_value:
                    try:
                        strdate=float(column_value)
                        if column_value.endswith('000'):
                           strdate=float(column_value[:-3])
                           local_dt = datetime.fromtimestamp(strdate, tz=pytz.utc).astimezone(local_tz)
                        row_list[i] = local_dt.strftime('%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        pass
            updated_rows.append(tuple(row_list))
             
        recursor()
        cursor.execute("describe aime.{}".format(database))
        dataTypes = [dataType[1] for dataType in cursor.fetchall()]
        if resultType == 'list':
            result = self.list_type(keys, updated_rows, dataTypes, ignore)
        elif resultType == 'dict':
            if ac:
                recursor()
                cursor.execute("select access_code from aime.aime_card where user = %s;", (self.user))
                access_code = cursor.fetchone()[0]
                result = self.dict_type(keys, updated_rows, dataTypes, ignore, {"accessCode": access_code})
            else:
                result = self.dict_type(keys, updated_rows, dataTypes, ignore, {})
        return result
    
def main(args):
    a = ChuniData(args)
    data = a.__dict__
    data.pop('user')
    data.pop('logger')
    nowtime = datetime.now()
    with open(f'./export-{a.userData["userName"]}-{nowtime.strftime("%Y-%m-%d")}.json', 'w+', encoding='utf8') as file:
        json.dump(data, file, ensure_ascii=False)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export data from Artemis. !!!ONLY AVAILABLE FOR ARTEMIS SERVERS THAT YOU CAN REACH!!! (USING MYSQL!!!)')
    parser.add_argument('--host', '-H', type=str, help='the host of the target mysql')
    parser.add_argument('--port', '-P', type=int, help='the port of the target mysql')
    parser.add_argument('--user', '-u', type=str, help='the user of the target mysql')
    parser.add_argument('--password', '-p', type=str, help='the password of the mysql user')
    parser.add_argument('--target_user', '-tu', type=int, help='the uid of the user in artemis you want to export (necessary)')
    parser.add_argument('--target_version', '-tv', type=int, help='the version of data you want to export')
    args = parser.parse_args()
    if args.target_user is not None and args.target_version is not None:
        main(args)
    else:
        parser.print_help()