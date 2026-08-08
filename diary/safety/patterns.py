"""Regex patterns used by the content safety scanner.

Each pattern is paired with a finding code and severity in scanner.py.
Patterns favor precision over exhaustive coverage for v1; false negatives
are mitigated by the local denylists (real names, school/workplace terms)
which the maintainer populates in content/denylists/.
"""

from __future__ import annotations

import math
import re

AWS_ACCESS_KEY_ID = re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")

GENERIC_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(api[_-]?key|secret|token|password|passwd|access[_-]?key|client[_-]?secret)\b"
    r"\s*[:=]\s*['\"]?[A-Za-z0-9_\-/+=]{8,}['\"]?"
)

PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
)

SLACK_TOKEN = re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")

GITHUB_TOKEN = re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")

GOOGLE_API_KEY = re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")

JWT_LOOKALIKE = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")

URL_WITH_EMBEDDED_CREDENTIALS = re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")

EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

PHONE = re.compile(
    r"(?<!\d)(\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)"
)

SSN_US = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

ADDRESS_HINT = re.compile(
    r"\b\d{1,5}\s+([A-Za-z0-9]+\s){1,4}"
    r"(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl)\b",
    re.IGNORECASE,
)

BIRTHDATE_NEAR_BORN = re.compile(
    r"\bborn\b[^.\n]{0,30}\b(19|20)\d{2}\b", re.IGNORECASE
)

HIGH_ENTROPY_TOKEN_CANDIDATE = re.compile(r"\b[A-Za-z0-9_\-]{24,}\b")


def shannon_entropy(token: str) -> float:
    if not token:
        return 0.0
    counts: dict[str, int] = {}
    for ch in token:
        counts[ch] = counts.get(ch, 0) + 1
    length = len(token)
    return -sum(
        (count / length) * math.log2(count / length) for count in counts.values()
    )
