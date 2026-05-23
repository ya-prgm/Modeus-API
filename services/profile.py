from services.auth import ModeusAuth
from utils.headers import get_auth_headers
import httpx
import json
import logging
from database.mmap_db import MmapDB

logger = logging.getLogger(__name__)

class ProfileRetrievalError(Exception):
    pass

class ModeusProfile:
    def __init__(self, auth: ModeusAuth):
        self.auth = auth
        self._profile_cache = None

    async def get_profile(self):
        """Получение профиля с кэшированием."""
        login = self.auth.login
        if self._profile_cache:
            logger.info(f"Profile for {login} retrieved from local cache")
            return self._profile_cache
        cached_profile = await MmapDB.get_profile(login)
        if cached_profile:
            self._profile_cache = cached_profile
            logger.info(f"Profile for {login} retrieved from mmap cache")
            return cached_profile
        await self.auth.ensure_valid_token()
        headers = get_auth_headers(self.auth.bearer_token)
        url = "https://utmn.modeus.org/students-app/api/pages/student-card/my/primary"
        try:
            response = await self.auth.session.get(url, headers=headers)
            response.raise_for_status()
            profile_data = response.json()

            service_data = {
                "personId": profile_data['personId'],
                "studentId": profile_data['id'],
                "aprId": profile_data['academicPeriodRealizations'][1]['id'],
                "academicPeriodStartDate": profile_data['academicPeriodRealizations'][1]['startDate'] + "T00:00:00.000Z",
                "academicPeriodEndDate": profile_data['academicPeriodRealizations'][1]['endDate'] + "T00:00:00.000Z",
                "curriculumFlowId": profile_data['curriculumFlow']['id'],
                "curriculumPlanId": profile_data['curriculumFlow']['curriculumPlanId'],
                "withMidcheckModulesIncluded": False
            }

            result = {
                "fullName": profile_data.get("fullName", ""),
                "birthDate": profile_data.get("birthDate", ""),
                "email": profile_data.get("contactInformation", {}).get("email", ""),
                "phone": profile_data.get("contactInformation", {}).get("phone", ""),
                "specialtyCode": profile_data.get("specialtyCode", ""),
                "specialtyName": profile_data.get("specialtyName", ""),
                "profile": profile_data.get("profile", {}).get("name", ""),
                "learningStartDate": profile_data.get("learningStartDate", ""),
                "citizenship": profile_data.get("citizenship", {}).get("name", ""),
                "service": service_data
            }
            self._profile_cache = result
            await MmapDB.save_profile(login, result)
            logger.info(f"Profile for {login} fetched and cached")
            return result

        except httpx.HTTPStatusError as e:
            raise ProfileRetrievalError(f"Failed to retrieve profile: {str(e)}")
        except json.JSONDecodeError:
            raise ProfileRetrievalError("Failed to parse profile data")