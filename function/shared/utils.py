import random
import string
from typing import Optional

import validators

from .config import DEFAULT_SHORT_CODE_LENGTH, MAX_URL_LENGTH


def generate_short_code(length: int = DEFAULT_SHORT_CODE_LENGTH) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def validate_url(url: str) -> Optional[str]:
    if not url:
        return "URL cannot be empty"

    if len(url) > MAX_URL_LENGTH:
        return f"URL too long (max {MAX_URL_LENGTH} characters)"

    if not validators.url(url):
        return "Invalid URL format"

    return None


def validate_short_code(short_code: str) -> Optional[str]:
    if not short_code:
        return "Short code not provided"

    if not short_code.isalnum() or len(short_code) != DEFAULT_SHORT_CODE_LENGTH:
        return "Invalid short code format"

    return None
