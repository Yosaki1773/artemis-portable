"""sao_player_changes

Revision ID: 680789dabab3
Revises: a616fd164e40
Create Date: 2024-06-26 23:19:16.863778

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '680789dabab3'
down_revision = 'a616fd164e40'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sao_equipment_data', sa.Column('is_shop_purchase', sa.BOOLEAN(), server_default='0', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('is_protect', sa.BOOLEAN(), server_default='0', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('property1_property_id', sa.BIGINT(), server_default='2', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('property1_value1', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('property1_value2', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('property2_property_id', sa.BIGINT(), server_default='2', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('property2_value1', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('property2_value2', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('property3_property_id', sa.BIGINT(), server_default='2', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('property3_value1', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('property3_value2', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('property4_property_id', sa.BIGINT(), server_default='2', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('property4_value1', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('property4_value2', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_equipment_data', sa.Column('converted_card_num', sa.INTEGER(), server_default='0', nullable=False))
    op.alter_column('sao_equipment_data', 'equipment_id',
               existing_type=mysql.INTEGER(),
               type_=sa.BIGINT(),
               existing_nullable=False)
    op.alter_column('sao_equipment_data', 'get_date',
               existing_type=mysql.TIMESTAMP(),
               server_default=sa.text('now()'),
               existing_nullable=False)
    op.create_foreign_key(None, 'sao_equipment_data', 'sao_static_property', ['property2_property_id'], ['PropertyId'], onupdate='cascade', ondelete='cascade')
    op.create_foreign_key(None, 'sao_equipment_data', 'sao_static_property', ['property4_property_id'], ['PropertyId'], onupdate='cascade', ondelete='cascade')
    op.create_foreign_key(None, 'sao_equipment_data', 'sao_static_property', ['property3_property_id'], ['PropertyId'], onupdate='cascade', ondelete='cascade')
    op.create_foreign_key(None, 'sao_equipment_data', 'sao_static_property', ['property1_property_id'], ['PropertyId'], onupdate='cascade', ondelete='cascade')
    op.create_foreign_key(None, 'sao_equipment_data', 'sao_static_equipment_list', ['equipment_id'], ['EquipmentId'], onupdate='cascade', ondelete='cascade')
    op.add_column('sao_hero_log_data', sa.Column('max_level_extend_num', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('is_awakenable', sa.BOOLEAN(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('awakening_stage', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('awakening_exp', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('is_shop_purchase', sa.BOOLEAN(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('is_protect', sa.BOOLEAN(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('property1_property_id', sa.BIGINT(), server_default='2', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('property1_value1', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('property1_value2', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('property2_property_id', sa.BIGINT(), server_default='2', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('property2_value1', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('property2_value2', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('property3_property_id', sa.BIGINT(), server_default='2', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('property3_value1', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('property3_value2', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('property4_property_id', sa.BIGINT(), server_default='2', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('property4_value1', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('property4_value2', sa.INTEGER(), server_default='0', nullable=False))
    op.add_column('sao_hero_log_data', sa.Column('converted_card_num', sa.INTEGER(), server_default='0', nullable=False))
    op.alter_column('sao_hero_log_data', 'main_weapon',
               existing_type=mysql.INTEGER(),
               nullable=True)
    op.alter_column('sao_hero_log_data', 'sub_equipment',
               existing_type=mysql.INTEGER(),
               nullable=True)
    op.alter_column('sao_hero_log_data', 'skill_slot1_skill_id',
               existing_type=mysql.INTEGER(),
               type_=sa.BIGINT(),
               nullable=True)
    op.alter_column('sao_hero_log_data', 'skill_slot2_skill_id',
               existing_type=mysql.INTEGER(),
               type_=sa.BIGINT(),
               nullable=True)
    op.alter_column('sao_hero_log_data', 'skill_slot3_skill_id',
               existing_type=mysql.INTEGER(),
               type_=sa.BIGINT(),
               nullable=True)
    op.alter_column('sao_hero_log_data', 'skill_slot4_skill_id',
               existing_type=mysql.INTEGER(),
               type_=sa.BIGINT(),
               nullable=True)
    op.alter_column('sao_hero_log_data', 'skill_slot5_skill_id',
               existing_type=mysql.INTEGER(),
               type_=sa.BIGINT(),
               nullable=True)
    op.alter_column('sao_hero_log_data', 'get_date',
               existing_type=mysql.TIMESTAMP(),
               server_default=sa.text('now()'),
               existing_nullable=False)
    op.alter_column("sao_hero_log_data", "user_hero_log_id",
                    existing_type=sa.Integer(),
                    new_column_name="hero_log_id",
                    type_=sa.BIGINT(),
                    nullable=False)
    op.execute(sa.text("UPDATE sao_hero_log_data SET skill_slot1_skill_id = NULL WHERE skill_slot1_skill_id = 0;"))
    op.execute(sa.text("UPDATE sao_hero_log_data SET skill_slot2_skill_id = NULL WHERE skill_slot2_skill_id = 0;"))
    op.execute(sa.text("UPDATE sao_hero_log_data SET skill_slot3_skill_id = NULL WHERE skill_slot3_skill_id = 0;"))
    op.execute(sa.text("UPDATE sao_hero_log_data SET skill_slot4_skill_id = NULL WHERE skill_slot4_skill_id = 0;"))
    op.execute(sa.text("UPDATE sao_hero_log_data SET skill_slot5_skill_id = NULL WHERE skill_slot5_skill_id = 0;"))
    op.execute(sa.text("UPDATE sao_hero_log_data SET main_weapon = NULL WHERE main_weapon = 0;"))
    op.execute(sa.text("UPDATE sao_hero_log_data SET sub_equipment = NULL WHERE sub_equipment = 0;"))
    op.execute(sa.text("UPDATE sao_hero_party SET user_hero_log_id_1 = NULL WHERE user_hero_log_id_1 = 0;"))
    op.execute(sa.text("UPDATE sao_hero_party SET user_hero_log_id_2 = NULL WHERE user_hero_log_id_2 = 0;"))
    op.execute(sa.text("UPDATE sao_hero_party SET user_hero_log_id_3 = NULL WHERE user_hero_log_id_3 = 0;"))
    
    op.execute(sa.text("UPDATE sao_hero_log_data INNER JOIN sao_equipment_data ON sao_hero_log_data.main_weapon = sao_equipment_data.equipment_id SET sao_hero_log_data.main_weapon = sao_equipment_data.id;"))
    op.execute(sa.text("UPDATE sao_hero_log_data INNER JOIN sao_equipment_data ON sao_hero_log_data.sub_equipment = sao_equipment_data.equipment_id SET sao_hero_log_data.sub_equipment = sao_equipment_data.id;"))
    
    op.execute(sa.text("UPDATE sao_hero_party INNER JOIN sao_hero_log_data ON sao_hero_party.user_hero_log_id_1 = sao_hero_log_data.hero_log_id SET sao_hero_party.user_hero_log_id_1 = sao_hero_log_data.id;"))
    op.execute(sa.text("UPDATE sao_hero_party INNER JOIN sao_hero_log_data ON sao_hero_party.user_hero_log_id_2 = sao_hero_log_data.hero_log_id SET sao_hero_party.user_hero_log_id_2 = sao_hero_log_data.id;"))
    op.execute(sa.text("UPDATE sao_hero_party INNER JOIN sao_hero_log_data ON sao_hero_party.user_hero_log_id_3 = sao_hero_log_data.hero_log_id SET sao_hero_party.user_hero_log_id_3 = sao_hero_log_data.id;"))
    
    op.create_foreign_key(None, 'sao_hero_log_data', 'sao_static_property', ['property4_property_id'], ['PropertyId'], onupdate='cascade', ondelete='cascade')
    op.create_foreign_key(None, 'sao_hero_log_data', 'sao_static_skill', ['skill_slot1_skill_id'], ['SkillId'], onupdate='set null', ondelete='set null')
    op.create_foreign_key(None, 'sao_hero_log_data', 'sao_static_skill', ['skill_slot5_skill_id'], ['SkillId'], onupdate='set null', ondelete='set null')
    op.create_foreign_key(None, 'sao_hero_log_data', 'sao_static_skill', ['skill_slot2_skill_id'], ['SkillId'], onupdate='set null', ondelete='set null')
    op.create_foreign_key(None, 'sao_hero_log_data', 'sao_static_skill', ['skill_slot3_skill_id'], ['SkillId'], onupdate='set null', ondelete='set null')
    op.create_foreign_key(None, 'sao_hero_log_data', 'sao_equipment_data', ['main_weapon'], ['id'], onupdate='set null', ondelete='set null')
    op.create_foreign_key(None, 'sao_hero_log_data', 'sao_static_property', ['property3_property_id'], ['PropertyId'], onupdate='cascade', ondelete='cascade')
    op.create_foreign_key(None, 'sao_hero_log_data', 'sao_static_skill', ['skill_slot4_skill_id'], ['SkillId'], onupdate='set null', ondelete='set null')
    op.create_foreign_key(None, 'sao_hero_log_data', 'sao_equipment_data', ['sub_equipment'], ['id'], onupdate='set null', ondelete='set null')
    op.create_foreign_key(None, 'sao_hero_log_data', 'sao_static_property', ['property1_property_id'], ['PropertyId'], onupdate='cascade', ondelete='cascade')
    op.create_foreign_key(None, 'sao_hero_log_data', 'sao_static_hero_list', ['hero_log_id'], ['HeroLogId'], onupdate='cascade', ondelete='cascade')
    op.create_foreign_key(None, 'sao_hero_log_data', 'sao_static_property', ['property2_property_id'], ['PropertyId'], onupdate='cascade', ondelete='cascade')
    op.create_foreign_key(None, 'sao_hero_party', 'sao_hero_log_data', ['user_hero_log_id_3'], ['id'], onupdate='cascade', ondelete='cascade')
    op.create_foreign_key(None, 'sao_hero_party', 'sao_hero_log_data', ['user_hero_log_id_1'], ['id'], onupdate='cascade', ondelete='cascade')
    op.create_foreign_key(None, 'sao_hero_party', 'sao_hero_log_data', ['user_hero_log_id_2'], ['id'], onupdate='cascade', ondelete='cascade')
    op.alter_column('sao_item_data', 'get_date',
               existing_type=mysql.TIMESTAMP(),
               server_default=sa.text('now()'),
               existing_nullable=False)
    op.alter_column('sao_play_sessions', 'play_date',
               existing_type=mysql.TIMESTAMP(),
               server_default=sa.text('now()'),
               existing_nullable=False)
    op.add_column('sao_player_quest', sa.Column('quest_type', sa.INTEGER(), server_default='1', nullable=False))
    op.alter_column('sao_player_quest', 'play_date',
               existing_type=mysql.TIMESTAMP(),
               server_default=sa.text('now()'),
               existing_nullable=False)
    op.alter_column('sao_player_quest', 'episode_id',
               existing_type=mysql.INTEGER(),
               new_column_name="quest_scene_id",
               type_=sa.BIGINT(),
               nullable=False)
    op.create_foreign_key(None, 'sao_player_quest', 'sao_static_quest', ['quest_scene_id'], ['QuestSceneId'], onupdate='cascade', ondelete='cascade')
    op.add_column('sao_profile', sa.Column('my_shop', sa.INTEGER(), nullable=True))
    op.add_column('sao_profile', sa.Column('fav_hero', sa.INTEGER(), nullable=True))
    op.add_column('sao_profile', sa.Column('when_register', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True))
    op.add_column('sao_profile', sa.Column('last_login_date', sa.TIMESTAMP(), nullable=True))
    op.add_column('sao_profile', sa.Column('last_yui_medal_date', sa.TIMESTAMP(), nullable=True))
    op.add_column('sao_profile', sa.Column('last_bonus_yui_medal_date', sa.TIMESTAMP(), nullable=True))
    op.add_column('sao_profile', sa.Column('last_comeback_date', sa.TIMESTAMP(), nullable=True))
    op.add_column('sao_profile', sa.Column('last_login_bonus_date', sa.TIMESTAMP(), nullable=True))
    op.add_column('sao_profile', sa.Column('ad_confirm_date', sa.TIMESTAMP(), nullable=True))
    op.add_column('sao_profile', sa.Column('login_ct', sa.INTEGER(), server_default='0', nullable=True))
    op.create_foreign_key(None, 'sao_profile', 'sao_hero_log_data', ['fav_hero'], ['id'], onupdate='cascade', ondelete='set null')


def downgrade():
    op.drop_constraint("sao_profile_ibfk_2", 'sao_profile', type_='foreignkey')
    op.drop_column('sao_profile', 'login_ct')
    op.drop_column('sao_profile', 'ad_confirm_date')
    op.drop_column('sao_profile', 'last_login_bonus_date')
    op.drop_column('sao_profile', 'last_comeback_date')
    op.drop_column('sao_profile', 'last_bonus_yui_medal_date')
    op.drop_column('sao_profile', 'last_yui_medal_date')
    op.drop_column('sao_profile', 'last_login_date')
    op.drop_column('sao_profile', 'when_register')
    op.drop_column('sao_profile', 'fav_hero')
    op.drop_column('sao_profile', 'my_shop')
    op.alter_column('sao_player_quest', 'quest_scene_id',
               existing_type=mysql.BIGINT(),
               new_column_name="episode_id",
               type_=sa.INTEGER(),
               nullable=False)
    op.drop_constraint("sao_player_quest_ibfk_2", 'sao_player_quest', type_='foreignkey')
    op.alter_column('sao_player_quest', 'play_date',
               existing_type=mysql.TIMESTAMP(),
               server_default=sa.text('CURRENT_TIMESTAMP'),
               existing_nullable=False)
    op.drop_column('sao_player_quest', 'quest_scene_id')
    op.drop_column('sao_player_quest', 'quest_type')
    op.alter_column('sao_play_sessions', 'play_date',
               existing_type=mysql.TIMESTAMP(),
               server_default=sa.text('CURRENT_TIMESTAMP'),
               existing_nullable=False)
    op.alter_column('sao_item_data', 'get_date',
               existing_type=mysql.TIMESTAMP(),
               server_default=sa.text('CURRENT_TIMESTAMP'),
               existing_nullable=False)
    op.drop_constraint("sao_hero_party_ibfk_2", 'sao_hero_party', type_='foreignkey')
    op.drop_constraint("sao_hero_party_ibfk_3", 'sao_hero_party', type_='foreignkey')
    op.drop_constraint("sao_hero_party_ibfk_4", 'sao_hero_party', type_='foreignkey')
    op.alter_column("sao_hero_log_data", "hero_log_id",
                    existing_type=sa.BIGINT(),
                    new_column_name="user_hero_log_id",
                    type_=sa.Integer(),
                    nullable=False)
    op.drop_constraint("sao_hero_log_data_ibfk_2", 'sao_hero_log_data', type_='foreignkey')
    op.drop_constraint("sao_hero_log_data_ibfk_3", 'sao_hero_log_data', type_='foreignkey')
    op.drop_constraint("sao_hero_log_data_ibfk_4", 'sao_hero_log_data', type_='foreignkey')
    op.drop_constraint("sao_hero_log_data_ibfk_5", 'sao_hero_log_data', type_='foreignkey')
    op.drop_constraint("sao_hero_log_data_ibfk_6", 'sao_hero_log_data', type_='foreignkey')
    op.drop_constraint("sao_hero_log_data_ibfk_7", 'sao_hero_log_data', type_='foreignkey')
    op.drop_constraint("sao_hero_log_data_ibfk_8", 'sao_hero_log_data', type_='foreignkey')
    op.drop_constraint("sao_hero_log_data_ibfk_9", 'sao_hero_log_data', type_='foreignkey')
    op.drop_constraint("sao_hero_log_data_ibfk_10", 'sao_hero_log_data', type_='foreignkey')
    op.drop_constraint("sao_hero_log_data_ibfk_11", 'sao_hero_log_data', type_='foreignkey')
    op.drop_constraint("sao_hero_log_data_ibfk_12", 'sao_hero_log_data', type_='foreignkey')
    op.drop_constraint("sao_hero_log_data_ibfk_13", 'sao_hero_log_data', type_='foreignkey')
    op.alter_column('sao_hero_log_data', 'get_date',
               existing_type=mysql.TIMESTAMP(),
               server_default=sa.text('CURRENT_TIMESTAMP'),
               existing_nullable=False)
    op.alter_column('sao_hero_log_data', 'skill_slot5_skill_id',
               existing_type=sa.BIGINT(),
               type_=mysql.INTEGER(),
               nullable=False)
    op.alter_column('sao_hero_log_data', 'skill_slot4_skill_id',
               existing_type=sa.BIGINT(),
               type_=mysql.INTEGER(),
               nullable=False)
    op.alter_column('sao_hero_log_data', 'skill_slot3_skill_id',
               existing_type=sa.BIGINT(),
               type_=mysql.INTEGER(),
               nullable=False)
    op.alter_column('sao_hero_log_data', 'skill_slot2_skill_id',
               existing_type=sa.BIGINT(),
               type_=mysql.INTEGER(),
               nullable=False)
    op.alter_column('sao_hero_log_data', 'skill_slot1_skill_id',
               existing_type=sa.BIGINT(),
               type_=mysql.INTEGER(),
               nullable=False)
    op.alter_column('sao_hero_log_data', 'sub_equipment',
               existing_type=mysql.INTEGER(),
               nullable=False)
    op.alter_column('sao_hero_log_data', 'main_weapon',
               existing_type=mysql.INTEGER(),
               nullable=False)
    op.drop_column('sao_hero_log_data', 'converted_card_num')
    op.drop_column('sao_hero_log_data', 'property4_value2')
    op.drop_column('sao_hero_log_data', 'property4_value1')
    op.drop_column('sao_hero_log_data', 'property4_property_id')
    op.drop_column('sao_hero_log_data', 'property3_value2')
    op.drop_column('sao_hero_log_data', 'property3_value1')
    op.drop_column('sao_hero_log_data', 'property3_property_id')
    op.drop_column('sao_hero_log_data', 'property2_value2')
    op.drop_column('sao_hero_log_data', 'property2_value1')
    op.drop_column('sao_hero_log_data', 'property2_property_id')
    op.drop_column('sao_hero_log_data', 'property1_value2')
    op.drop_column('sao_hero_log_data', 'property1_value1')
    op.drop_column('sao_hero_log_data', 'property1_property_id')
    op.drop_column('sao_hero_log_data', 'is_protect')
    op.drop_column('sao_hero_log_data', 'is_shop_purchase')
    op.drop_column('sao_hero_log_data', 'awakening_exp')
    op.drop_column('sao_hero_log_data', 'awakening_stage')
    op.drop_column('sao_hero_log_data', 'is_awakenable')
    op.drop_column('sao_hero_log_data', 'max_level_extend_num')
    op.drop_constraint("sao_equipment_data_ibfk_2", 'sao_equipment_data', type_='foreignkey')
    op.drop_constraint("sao_equipment_data_ibfk_3", 'sao_equipment_data', type_='foreignkey')
    op.drop_constraint("sao_equipment_data_ibfk_4", 'sao_equipment_data', type_='foreignkey')
    op.drop_constraint("sao_equipment_data_ibfk_5", 'sao_equipment_data', type_='foreignkey')
    op.drop_constraint("sao_equipment_data_ibfk_6", 'sao_equipment_data', type_='foreignkey')
    op.alter_column('sao_equipment_data', 'get_date',
               existing_type=mysql.TIMESTAMP(),
               server_default=sa.text('CURRENT_TIMESTAMP'),
               existing_nullable=False)
    op.alter_column('sao_equipment_data', 'equipment_id',
               existing_type=sa.BIGINT(),
               type_=mysql.INTEGER(),
               existing_nullable=False)
    op.drop_column('sao_equipment_data', 'converted_card_num')
    op.drop_column('sao_equipment_data', 'property4_value2')
    op.drop_column('sao_equipment_data', 'property4_value1')
    op.drop_column('sao_equipment_data', 'property4_property_id')
    op.drop_column('sao_equipment_data', 'property3_value2')
    op.drop_column('sao_equipment_data', 'property3_value1')
    op.drop_column('sao_equipment_data', 'property3_property_id')
    op.drop_column('sao_equipment_data', 'property2_value2')
    op.drop_column('sao_equipment_data', 'property2_value1')
    op.drop_column('sao_equipment_data', 'property2_property_id')
    op.drop_column('sao_equipment_data', 'property1_value2')
    op.drop_column('sao_equipment_data', 'property1_value1')
    op.drop_column('sao_equipment_data', 'property1_property_id')
    op.drop_column('sao_equipment_data', 'is_protect')
    op.drop_column('sao_equipment_data', 'is_shop_purchase')
