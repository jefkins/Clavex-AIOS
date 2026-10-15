"""Privacy Plane, step 1: decide what class of data this text is.

Classification happens before a model sees anything. A system that classifies
after the call has already disclosed whatever it was trying to protect.

The detectors here are deliberately simple and deliberately incomplete. They
catch the obvious shapes (email, phone, national insurance number, postcode,
card number) so the plane has something real to route on. They are not a
compliance control and they will miss things a determined reader would spot.
"""

import re

PUBLIC = "PUBLIC"
INTERNAL = "INTERNAL"
PERSONAL = "PERSONAL"
SPECIAL = "SPECIAL_CATEGORY"

# Ordered most specific first: the first pattern to match a span owns it.
DETECTORS = [
    ("card", SPECIAL, re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    ("nino", SPECIAL, re.compile(r"\b[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]\b")),
    ("nhs_number", SPECIAL, re.compile(r"\b\d{3}[ -]?\d{3}[ -]?\d{4}\b")),
    ("email", PERSONAL, re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b")),
    ("phone_uk", PERSONAL, re.compile(r"\b(?:0|\+44)\s?\d{3,4}[\s-]?\d{3}[\s-]?\d{3,4}\b")),
    ("postcode_uk", PERSONAL,
     re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b", re.I)),
]

# Words that signal health or care context. Presence alongside a personal
# identifier is what makes a record special category, not the word alone.
HEALTH_HINTS = re.compile(
    r"\b(diagnos\w+|medication|prescrib\w+|care plan|safeguard\w+|mental health|"
    r"gp|surgery|dementia|discharge)\b", re.I)

ORDER = {PUBLIC: 0, INTERNAL: 1, PERSONAL: 2, SPECIAL: 3}


def find_spans(text):
    """Every detected span as (start, end, kind, classification), non overlapping."""
    spans = []
    taken = []
    for kind, level, pattern in DETECTORS:
        for m in pattern.finditer(text):
            if any(s < m.end() and m.start() < e for s, e in taken):
                continue
            taken.append((m.start(), m.end()))
            spans.append((m.start(), m.end(), kind, level))
    return sorted(spans)


def classify(text):
    """Return (classification, spans).

    An identifier in health or care context is escalated to special category,
    because the pairing is what makes it sensitive. A phone number on its own
    is personal data; the same number beside a diagnosis is not.
    """
    spans = find_spans(text)
    level = PUBLIC
    for _, _, _, span_level in spans:
        if ORDER[span_level] > ORDER[level]:
            level = span_level
    if spans and HEALTH_HINTS.search(text) and ORDER[level] < ORDER[SPECIAL]:
        level = SPECIAL
    if level == PUBLIC and HEALTH_HINTS.search(text):
        level = INTERNAL
    return level, spans
