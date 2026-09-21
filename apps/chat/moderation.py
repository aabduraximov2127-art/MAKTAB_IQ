"""Chat moderation: detects swearing / insults (Uzbek, Russian, English) in chat messages.

Matching is token based (not substring based) so innocent words that merely *contain* a
bad stem are not flagged. Text is normalised first: lower-cased, Cyrillic transliterated
to Latin, common leetspeak undone, apostrophes dropped and repeated letters collapsed
("fuuuck" -> "fuk").
"""

import re
import unicodedata

_CYR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "s", "ч": "c", "ш": "s", "щ": "s",
    "ъ": "", "ы": "i", "ь": "", "э": "e", "ю": "u", "я": "a", "ў": "o", "қ": "q", "ғ": "g", "ҳ": "x",
}
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i"})
_APOSTROPHES = "'`’ʻʼ‘´"

# Stems matched as token *prefixes* (covers suffixes: "fuck" -> fucking, fucker ...).
# Written in the normalised (Latin) form; the matcher collapses repeated letters itself.
PREFIX_STEMS = {
    # Uzbek
    "sikay", "sikaman", "sikdim", "sikib", "siktir", "siqtir", "sikish", "sikkan",
    "qotoq", "qotog", "kotak", "chochqa", "haromi", "jalab", "jalap", "fohis",
    "onangni", "otangni", "ammingni", "amingni", "kaltafahm", "ahmoq", "axmoq", "tentak", "behayo", "bexayo",
    # Russian (transliterated from Cyrillic, or typed in Latin)
    "xuy", "xui", "xue", "xuya", "huy", "naxu", "poxu", "zaxu", "oxue", "oxui", "nahu", "pohu", "zahu", "raspizd", "zapizd", "pizd", "bliat", "blyat", "bladi", "bladsk",
    "eban", "ebat", "ebal", "zaeb", "poeb", "ueb", "naeb", "mudak", "mudil",
    "pidor", "pidar", "pidr", "gandon", "govn", "zalup", "slux", "mrazi", "mraz",
    "debil", "idiot", "dolbo", "suka", "sukin",
    # English
    "fuck", "fuk", "fck", "shit", "bitch", "bastard", "asshole", "cunt", "whore", "slut", "dumbass", "moron",
}

# Short / ambiguous words matched only as whole tokens.
EXACT_WORDS = {
    "sik", "dick", "ass", "tupoi", "tupoy", "lox", "loh", "urod", "tvar", "tvari", "jopa", "hui", "ebu",
    "blad", "blat", "dermo", "cmo", "stupid", "loser", "retard", "retarded", "pidoras", "pidaras",
}

# Innocent words that start with a flagged stem.
EXCEPTIONS = {"shitake", "shitaki", "assam", "assamble"}

_TOKEN_RE = re.compile(r"[a-z]+")
# "f u c k" / "f.u.c.k" style obfuscation: 4+ single letters separated by spaces/dots/dashes.
_SPACED_RE = re.compile(r"(?:\b[a-z][\s._\-*]+){3,}[a-z]\b")


def _collapse(word: str) -> str:
    return re.sub(r"(.)\1+", r"\1", word)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").lower()
    for ch in _APOSTROPHES:
        text = text.replace(ch, "")
    text = text.translate(_LEET)
    return "".join(_CYR.get(ch, ch) for ch in text)


_COLLAPSED_PREFIXES = {_collapse(s) for s in PREFIX_STEMS}
_COLLAPSED_EXACT = {_collapse(w) for w in EXACT_WORDS}


def _hit(token: str) -> bool:
    c = _collapse(token)
    if c in EXCEPTIONS:
        return False
    if c in _COLLAPSED_EXACT:
        return True
    return any(c.startswith(stem) for stem in _COLLAPSED_PREFIXES if len(stem) >= 3)


def find_profanity(text: str) -> list[str]:
    """Return the (normalised) offending words found in ``text``; empty list if clean."""
    norm = normalize(text)
    found: list[str] = []
    for token in _TOKEN_RE.findall(norm):
        if _hit(token) and token not in found:
            found.append(token)
    for match in _SPACED_RE.findall(norm):
        squashed = re.sub(r"[^a-z]", "", match)
        if _hit(squashed) and squashed not in found:
            found.append(squashed)
    return found
