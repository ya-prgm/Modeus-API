from services.auth import ModeusAuth
import httpx
import json
from database.mmap_db import MmapDB

class GradesRetrievalError(Exception):
    pass

class ModeusGrades:
    def __init__(self, auth: ModeusAuth):
        self.auth = auth
        self._grades_cache = None
        self._courses_cache = None

    async def _fetch_json(self, url: str, data: dict):
        """Fetch JSON data with exact headers and print debugging."""
        headers = {
            "content-type": "application/json",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ru-RU",
            "authorization": f"Bearer {self.auth.bearer_token}",
            "origin": "https://utmn.modeus.org",
            "priority": "u=1, i",
            "referer": "https://utmn.modeus.org/students-app/my-results?aprId=153465b4-754e-4180-b551-e59e02355e92&studentId=f18fa631-c57b-40a2-92ed-70a2007c2bfc",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }
        print(f"Fetching URL: {url}")
        print(f"Request headers: {json.dumps(headers, ensure_ascii=False)}")
        print(f"Request payload: {json.dumps(data, ensure_ascii=False)}")
        
        try:
            response = await self.auth.session.post(url, headers=headers, json=data)
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {json.dumps(dict(response.headers), ensure_ascii=False)}")
            print(f"Response content (first 1000 chars): {response.text[:1000]}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Unexpected error in _fetch_json: {str(e)}")
            raise

    async def _get_courses(self, initial_data: dict):
        """Get courses with print debugging."""
        print(f"Starting _get_courses for login: {self.auth.login}")
        print(f"Initial data: {json.dumps(initial_data, ensure_ascii=False)}")
        
        url = "https://utmn.modeus.org/students-app/api/pages/student-card/my/academic-period-results-table/primary"
        try:
            data = await self._fetch_json(url, initial_data)
            print(f"Raw courses response: {json.dumps(data, ensure_ascii=False)[:1000]}")
            
            courses_dict = {
                course['courseUnitRealizationIds'][0]: course['name']
                for course in data.get('academicCourses', [])
            }
            for realization in data.get('courseUnitRealizations', []):
                courses_dict.setdefault(realization['id'], realization['name'])
            
            print(f"Found {len(courses_dict)} courses")
            print(f"Courses dictionary: {json.dumps(courses_dict, ensure_ascii=False)}")
            return courses_dict, data
        except Exception as e:
            print(f"Error in _get_courses: {str(e)}")
            raise

    async def _prepare_second_data(self, first_response: dict, initial_data: dict):
        """Prepare data for second request with print debugging."""
        print("Preparing data for second request")
        print(f"First response: {json.dumps(first_response, ensure_ascii=False)[:1000]}")
        
        try:
            second_data = {
                'courseUnitRealizationId': [cur['id'] for cur in first_response.get('courseUnitRealizations', [])],
                'academicCourseId': [course['id'] for course in first_response.get('academicCourses', [])],
                'lessonId': [
                    lesson['id'] for cur in first_response.get('courseUnitRealizations', [])
                    for lesson in cur.get('lessons', [])
                ],
                'lessonRealizationTemplateId': list({
                    lesson['lessonRealizationTemplateId'] for cur in first_response.get('courseUnitRealizations', [])
                    for lesson in cur.get('lessons', [])
                }),
                **{k: initial_data[k] for k in ['personId', 'studentId', 'aprId', 'academicPeriodStartDate', 'academicPeriodEndDate']}
            }
            print(f"Prepared second data: {json.dumps(second_data, ensure_ascii=False)}")
            return second_data
        except Exception as e:
            print(f"Error in _prepare_second_data: {str(e)}")
            raise

    async def get_grades(self):
        """Get grades with maximum speed and print debugging."""
        login = self.auth.login
        print(f"Starting get_grades for login: {login}")
        if self._grades_cache:
            print(f"Returning grades from local cache for {login}")
            print(f"Cached grades: {json.dumps(self._grades_cache, ensure_ascii=False)}")
            return self._grades_cache
        cached_grades = await MmapDB.get_grades(login)
        if cached_grades and isinstance(cached_grades, dict):
            self._grades_cache = cached_grades
            print(f"Returning grades from mmap cache for {login}")
            print(f"Mmap cached grades: {json.dumps(cached_grades, ensure_ascii=False)}")
            print(cached_grades)
            return cached_grades
        print(f"Fetching profile for {login}")
        profile = await MmapDB.get_profile(login)
        if not profile or "service" not in profile:
            print(f"Profile data not found or incomplete for {login}")
            raise GradesRetrievalError("Profile data not found or incomplete")
        initial_data = profile["service"]
        print(f"Profile service data: {json.dumps(initial_data, ensure_ascii=False)}")
        print(f"Ensuring valid token for {login}")
        is_valid = await self.auth.is_token_valid()
        print(f"Current token validity: {is_valid}")
        if not is_valid:
            print(f"Token invalid or missing, re-authenticating for {login}")
            await self.auth.authenticate()
            print(f"New bearer token: {self.auth.bearer_token}")
        else:
            print(f"Token is valid: {self.auth.bearer_token}")
        print("Fetching courses and first response")
        courses, first_response = await self._get_courses(initial_data)
        
        print("Preparing and fetching second response")
        second_data = await self._prepare_second_data(first_response, initial_data)
        second_url = "https://utmn.modeus.org/students-app/api/pages/student-card/my/academic-period-results-table/secondary"
        second_response = await self._fetch_json(second_url, second_data)
        print("Extracting grades from response")
        grades = {
            control_obj['courseUnitRealizationId']: {
                'id': control_obj['courseUnitRealizationId'],
                'name': courses.get(control_obj['courseUnitRealizationId'], "Unknown"),
                'result': control_obj['resultCurrent']['resultValue']
            }
            for control_obj in second_response.get('courseUnitRealizationControlObjects', [])
            if control_obj.get('resultCurrent') and control_obj['courseUnitRealizationId'] in courses
        }
        print(f"Extracted grades: {json.dumps(grades, ensure_ascii=False)}")
        print(f"Caching grades for {login}")
        self._grades_cache = grades
        self._courses_cache = courses
        await MmapDB.save_grades(login, grades)
        print(f"Grades successfully retrieved and cached for {login}")
        print(grades)
        return grades