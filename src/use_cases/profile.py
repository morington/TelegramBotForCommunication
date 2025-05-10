from typing import Optional
from urllib.parse import urlparse

from src.core.domain.entities import DetectGitEntity


def detect_url(url: str) -> bool:
    """
    Проверяет, является ли строка URL

    Args:
        url [str] - Входная строка

    Returns:
        bool
    """
    if url:
        return url.startswith(("http://", "https://"))
    return False


def detect_git_platform(url: str) -> Optional[DetectGitEntity]:
    """
    Проверяет, является ли строка валидной ссылкой на GitHub или GitLab.

    Args:
        url [str] - Входная строка

    Returns:
        Optional[str] - 'github' или 'gitlab' если подходит, иначе None
    """
    if not detect_url(url=url):
        return None

    netloc = urlparse(url).netloc.lower()
    match netloc:
        case host if "github.com" in host:
            return DetectGitEntity.github
        case host if "gitlab.com" in host:
            return DetectGitEntity.gitlab
        case _:
            return None
