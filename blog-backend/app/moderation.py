import re

BLOCKED_WORDS = [
    "porn",
    "pornography",
    "xxx",
    "nude",
    "nudes",
    "naked",
    "sex",
    "sexy",
    "sexual",
    "nsfw",
    "hentai",
    "escort",
    "prostitute",
    "fuck",
    "fucking",
    "fucker",
    "motherfucker",
    "motherfucking",
    "shit",
    "bitch",
    "bastard",
    "asshole",
    "cunt",
    "dick",
    "cock",
    "pussy",
    "whore",
    "slut",
    "rape",
    "molest",
]

_PATTERN = re.compile(
    r"(?<![a-zA-Z0-9])(" + "|".join(re.escape(word) for word in BLOCKED_WORDS) + r")(?![a-zA-Z0-9])",
    re.IGNORECASE,
)


def contains_blocked_language(text: str | None) -> bool:
    if not text:
        return False
    return bool(_PATTERN.search(text))


def censor(text: str | None) -> str | None:
    if not text:
        return text
    return _PATTERN.sub(lambda match: "*" * len(match.group(0)), text)
