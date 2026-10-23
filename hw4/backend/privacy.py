"""Keep passwords out of the chat: never stored in chat_messages, never sent to the model.

Two checks run on every chat message before it is saved or given to the agent:
1. Phrases that introduce a password ("my password is X", "password: X", "reset my password to X")
   -> X is removed. Works for guests and logged-in shoppers.
2. Logged-in shoppers only: each longer word in the message is checked against their stored
   password hash (the same PBKDF2 check as login). A match means they typed their real password,
   even with no lead-in phrase, so it is removed. The password itself is never stored or logged.
"""

import re

import auth

REDACTED = "[password removed]"
MIN_CANDIDATE_LEN = 6
MAX_HASH_CHECKS = 20  # ~55 ms each, so at most about a second per message

# "password is X", "pwd: X", "passcode = X", "password to X", "password should be X", ...
LEAD_IN = re.compile(
    r"\b(?:pass\s?(?:word|code|phrase)|pwd|pw)s?\b\s*(?:is|was|=|:|-|to|should be|will be|would be)\s*"
    r"[\"'“‘]?(?P<secret>[^\s\"'”’]+)",
    re.IGNORECASE,
)
# Words that follow "password to/is" in normal sentences, not real passwords.
NOT_SECRETS = {
    "something", "anything", "what", "the", "a", "an", "my", "it", "be", "reset", "change", "new",
    "forgotten", "forgot", "wrong", "incorrect", "correct", "right", "safe", "secure", "stronger", "longer",
    "shown", "visible", "saved", "stored", "reset?", "work", "working", "not",
}


PUNCTUATION = ".,!?;:()[]{}<>\"'“”‘’"


def _word_spans(text: str) -> list[tuple[int, int]]:
    """(start, end) of each whitespace-separated word, with surrounding punctuation trimmed off."""
    spans = []
    for m in re.finditer(r"\S+", text):
        start, end = m.start(), m.end()
        while start < end and text[start] in PUNCTUATION:
            start += 1
        while end > start and text[end - 1] in PUNCTUATION:
            end -= 1
        if end > start:
            spans.append((start, end))
    return spans


def find_secret_spans(text: str, password_hash: str | None = None) -> list[tuple[int, int]]:
    """Character positions in the text that hold a password."""
    spans: set[tuple[int, int]] = set()
    for m in LEAD_IN.finditer(text):
        start, end = m.span("secret")
        while end > start and text[end - 1] in PUNCTUATION:
            end -= 1
        if end > start and text[start:end].lower() not in NOT_SECRETS:
            spans.add((start, end))
    if password_hash:
        by_word: dict[str, list[tuple[int, int]]] = {}
        for start, end in _word_spans(text):
            if end - start >= MIN_CANDIDATE_LEN:
                by_word.setdefault(text[start:end], []).append((start, end))
        # Words with digits or symbols look most like passwords, so check those first.
        for word in sorted(by_word, key=str.isalpha)[:MAX_HASH_CHECKS]:
            if auth.verify_password(word, password_hash):
                spans.update(by_word[word])  # every place they typed it
    return sorted(spans)


def clean_message(text: str, password_hash: str | None = None) -> tuple[str, bool]:
    """Return the message with any passwords replaced by "[password removed]", and whether anything was removed."""
    spans = find_secret_spans(text, password_hash)
    if not spans:
        return text, False
    out, last = [], 0
    for start, end in spans:
        if start < last:  # overlapping match, already removed
            continue
        out += [text[last:start], REDACTED]
        last = end
    out.append(text[last:])
    return "".join(out), True
