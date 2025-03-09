from datetime import timedelta
from typing import Dict

from core.config import CoreConfig
from titles.chuni.config import ChuniConfig
from titles.chuni.const import ChuniConstants, MapAreaConditionLogicalOperator, MapAreaConditionType
from titles.chuni.luminousplus import ChuniLuminousPlus


class ChuniVerse(ChuniLuminousPlus):
    def __init__(self, core_cfg: CoreConfig, game_cfg: ChuniConfig) -> None:
        super().__init__(core_cfg, game_cfg)
        self.version = ChuniConstants.VER_CHUNITHM_VERSE

    async def handle_cm_get_user_preview_api_request(self, data: Dict) -> Dict:
        user_data = await super().handle_cm_get_user_preview_api_request(data)

        # Does CARD MAKER 1.35 work this far up?
        user_data["lastDataVersion"] = "2.30.00"
        return user_data

    async def handle_get_game_course_level_api_request(self, data: Dict) -> Dict:
        game_course_level_list = []
        
        course_levels = await self.data.profile.get_game_course_levels()
        
        if course_levels:
            for course in course_levels:
                game_course_level_list.append({
                    "courseId": course["courseId"],
                    "startDate": course["startDate"],
                    "endDate": course["endDate"]
                })
        
        return {
            "length": len(game_course_level_list),
            "gameCourseLeveList": game_course_level_list
        }
    
    async def handle_get_game_uc_condition_api_request(self, data: Dict) -> Dict:
        game_unlock_challenge_condition_list = []
        
        unlock_conditions = await self.data.profile.get_game_unlock_challenge_conditions()
        
        if unlock_conditions:
            for condition in unlock_conditions:
                condition_list = []
                
                if "conditionList" in condition and condition["conditionList"]:
                    for cond in condition["conditionList"]:
                        condition_list.append(cond)
                
                game_unlock_challenge_condition_list.append({
                    "unlockChallengeId": condition["unlockChallengeId"],
                    "length": len(condition_list),
                    "conditionList": condition_list
                })

        return {
            "length": len(game_unlock_challenge_condition_list),
            "gameUnlockChallengeConditionList": game_unlock_challenge_condition_list
        }

    async def handle_get_user_uc_api_request(self, data: Dict) -> Dict:
        user_id = data.get("userId")
        
        if not user_id:
            user_id = await self.get_current_user_id()
        
        user_unlock_challenge_list = []
        
        user_challenges = await self.data.profile.get_user_unlock_challenges(user_id)
        
        if user_challenges:
            for challenge in user_challenges:
                user_unlock_challenge_list.append(challenge)
        
        return {
            "userId": user_id,
            "length": len(user_unlock_challenge_list),
            "userUnlockChallengeList": user_unlock_challenge_list
        }

    async def handle_get_user_rec_music_api_request(self, data: Dict) -> Dict:
        user_id = data.get("userId")
        
        if not user_id:
            user_id = await self.get_current_user_id()
        
        user_rec_music_list = []
        
        recommended_music = await self.data.profile.get_user_recommended_music(user_id)
        
        if recommended_music:
            for music in recommended_music:
                user_rec_music_list.append(music)
        
        return {
            "length": len(user_rec_music_list),
            "userRecMusicList": user_rec_music_list
        }

    async def handle_get_user_rec_rating_api_request(self, data: Dict) -> Dict:
        user_id = data.get("userId")
        
        if not user_id:
            user_id = await self.get_current_user_id()
        
        user_rec_rating_list = await self.data.profile.get_user_rec_rating(user_id)
        
        if user_rec_rating_list is None:
            return {
                "length": 0,
                "userRecRatingList": []
            }
        
        return {
            "length": len(user_rec_rating_list),
            "userRecRatingList": user_rec_rating_list
        }