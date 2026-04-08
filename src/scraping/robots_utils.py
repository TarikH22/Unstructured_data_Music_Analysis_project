from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


DEFAULT_USER_AGENT = "ResearchBot/1.0"


def get_headers(user_agent=DEFAULT_USER_AGENT):
    return {"User-Agent": user_agent}


def robots_url_for(target_url):
    parsed = urlparse(target_url)
    return f"{parsed.scheme}://{parsed.netloc}/robots.txt"


def is_allowed_by_robots(target_url, user_agent=DEFAULT_USER_AGENT):
    parser = RobotFileParser()
    parser.set_url(robots_url_for(target_url))
    try:
        parser.read()
        return parser.can_fetch(user_agent, target_url)
    except Exception:
        # If robots.txt is unreachable, caller can decide fallback behavior.
        return False
