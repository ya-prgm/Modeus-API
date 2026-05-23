def get_default_headers():
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "connection": "keep-alive",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

def get_auth_headers(bearer_token: str):
    return {
        **get_default_headers(),
        "authorization": f"Bearer {bearer_token}",
        "accept": "application/json, text/plain, */*",
        "referer": "https://utmn.modeus.org/students-app/my-results",
    }