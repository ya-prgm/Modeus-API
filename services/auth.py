import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import asyncio
import json
from utils.headers import get_default_headers
from database.mmap_db import MmapDB

class AuthenticationError(Exception):
    pass

class ModeusAuth:
    _locks = {}

    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.bearer_token = None
        self.session = httpx.AsyncClient(http2=True)
        if login not in self._locks:
            self._locks[login] = asyncio.Lock()

    def _is_valid_jwt(self, token):
        """Проверка, является ли токен валидным JWT."""
        if not token or token.count('.') != 2:
            print(f"Token {token} is not a valid JWT (must have 2 periods)")
            return False
        return True

    async def authenticate(self):
        """Аутентификация с проверкой кэша и отладкой."""
        print(f"Starting authentication for {self.login}")
        async with self._locks[self.login]:
            cached_token = await MmapDB.get_session(self.login)
            if cached_token and self._is_valid_jwt(cached_token):
                print(f"Using cached token: {cached_token}")
                self.bearer_token = cached_token
                return

            print("Cached token invalid or missing, performing full authentication")
            await self._perform_authentication()
            if not self._is_valid_jwt(self.bearer_token):
                raise AuthenticationError(f"Received invalid token: {self.bearer_token}")
            print(f"New bearer token after auth: {self.bearer_token}")
            await MmapDB.save_session(self.login, self.bearer_token)

    async def _perform_authentication(self):
        """Полный процесс аутентификации с отладкой."""
        print("Getting ADFS URL")
        adfs_url = await self._get_adfs_url()
        print(f"ADFS URL: {adfs_url}")
        
        print("Getting SAML response")
        saml_response = await self._get_saml_response(adfs_url)
        if not saml_response:
            raise AuthenticationError("Invalid login or password")
        print(f"SAML response (first 100 chars): {saml_response[:100]}")
        
        relay_state = self._get_relay_state(adfs_url)
        print(f"Relay state: {relay_state}")
        
        print("Posting common auth")
        return_common_auth = await self._post_common_auth(saml_response, relay_state)
        print(f"Return common auth URL: {return_common_auth}")
        
        self.bearer_token = await self._get_bearer_token(return_common_auth)

    async def is_token_valid(self):
        if not self.bearer_token:
            print("No token present")
            return False
        try:
            url = "https://utmn.modeus.org/schedule-calendar/assets/app.config.json"
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Accept": "application/json, text/plain, */*",
            }
            print(f"Checking token validity with URL: {url}")
            print(f"Headers: {json.dumps(headers, ensure_ascii=False)}")
            response = await self.session.get(url, headers=headers)
            print(f"Token validation response status: {response.status_code}")
            print(f"Token validation response: {response.text[:1000]}")
            return response.status_code in (200, 304)
        except httpx.HTTPError as e:
            print(f"Token validation failed: {str(e)}")
            return False

    async def ensure_valid_token(self):
        if not await self.is_token_valid():
            await self.authenticate()

    async def _get_adfs_url(self):
        client_id = 'sKir7YQnOUu4G0eCfn3tTxnBfzca'
        state = '7920b21bc'
        nonce = '05cd7363dbab4bae101'
        url = f"https://auth.modeus.org/oauth2/authorize?client_id={client_id}&redirect_uri=https%3A%2F%2Futmn.modeus.org%2F&response_type=id_token&scope=openid&state={state}&nonce={nonce}"
        headers = {
            **get_default_headers(),
            "Cookie": "tc01=8830352afb43f20dbe66ff5eb40e79e0",
            "Host": "auth.modeus.org",
            "Referer": "https://utmn.modeus.org/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-site",
            "Upgrade-Insecure-Requests": "1",
        }
        response = await self.session.get(url, headers=headers, follow_redirects=False)
        print(f"ADFS redirect status: {response.status_code}")
        print(f"ADFS redirect headers: {json.dumps(dict(response.headers), ensure_ascii=False)}")
        return response.headers['Location']

    async def _get_saml_response(self, url):
        headers = {
            **get_default_headers(),
            "cache-control": "max-age=0",
            "content-type": "application/x-www-form-urlencoded",
            "host": "fs.utmn.ru",
            "origin": "https://fs.utmn.ru",
            "referer": '',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        }
        data = {
            'UserName': self.login,
            'Password': self.password,
            'AuthMethod': 'FormsAuthentication'
        }
        print(f"Posting SAML request to: {url}")
        print(f"SAML request headers: {json.dumps(headers, ensure_ascii=False)}")
        print(f"SAML request data: {json.dumps(data, ensure_ascii=False)}")
        response = await self.session.post(url, headers=headers, data=data, follow_redirects=True)
        print(f"SAML response status: {response.status_code}")
        print(f"SAML response content (first 1000 chars): {response.text[:1000]}")
        soup = BeautifulSoup(response.text, 'html.parser')
        error_span = soup.find('span', id='errorText')
        if error_span and "Неверный идентификатор пользователя или пароль" in error_span.text:
            print("Authentication failed: Invalid login or password")
            return None
        saml_input = soup.find('input', {'name': 'SAMLResponse'})
        if not saml_input:
            print("SAMLResponse input not found in response")
        return saml_input.get('value') if saml_input else None

    def _get_relay_state(self, url):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        relay_state = query_params.get('RelayState', [None])[0]
        print(f"Extracted RelayState from URL: {relay_state}")
        return relay_state

    async def _post_common_auth(self, saml_response, relay_state):
        headers = {
            **get_default_headers(),
            "cache-control": "max-age=0",
            "content-type": "application/x-www-form-urlencoded",
            "host": "auth.modeus.org",
            "origin": "https://fs.utmn.ru",
            "referer": "https://fs.utmn.ru/",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "cross-site",
            "upgrade-insecure-requests": "1",
        }
        data = {'SAMLResponse': saml_response, 'RelayState': relay_state}
        print(f"Posting common auth to: https://auth.modeus.org/commonauth")
        print(f"Common auth headers: {json.dumps(headers, ensure_ascii=False)}")
        print(f"Common auth data (first 100 chars): {json.dumps(data, ensure_ascii=False)[:100]}")
        response = await self.session.post('https://auth.modeus.org/commonauth', headers=headers, data=data, follow_redirects=False)
        print(f"Common auth response status: {response.status_code}")
        print(f"Common auth response headers: {json.dumps(dict(response.headers), ensure_ascii=False)}")
        return response.headers['Location']

    async def _get_bearer_token(self, url):
        headers = {
            **get_default_headers(),
            "Cache-Control": "max-age=0",
            "Host": "auth.modeus.org",
            "Referer": "https://fs.utmn.ru/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Upgrade-Insecure-Requests": "1",
        }
        print(f"Fetching bearer token from URL: {url}")
        response = await self.session.get(url, headers=headers, follow_redirects=False)
        print(f"Bearer token response status: {response.status_code}")
        print(f"Bearer token response headers: {json.dumps(dict(response.headers), ensure_ascii=False)}")
        parsed_url = urlparse(response.headers['Location'])
        fragment = parsed_url.fragment
        params = parse_qs(fragment)
        print(f"URL fragment: {fragment}")
        print(f"Parsed params: {params}")
        token = params.get('id_token', [None])[0]
        print(f"Extracted token: {token}")
        return token

    async def close(self):
        await self.session.aclose()