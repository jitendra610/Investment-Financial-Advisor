
import re
from collections import defaultdict

import spacy


# Load model once when the application starts.
nlp = spacy.load("en_core_web_sm")


PII_PATTERNS = {
    "EMAIL": re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    ),

    "PHONE": re.compile(
        r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)"
        r"|(?<!\d)(?:\+44[\s-]?7|07)(?:[\s-]?\d){9}(?!\d)"
    ),

    "DOB": re.compile(
        r"\b(?:DOB|date of birth)\s*[:\-]?\s*"
        r"\d{1,2}[/-]\d{1,2}[/-]\d{4}\b",
        re.IGNORECASE,
    ),

    "AGE": re.compile(
        r"\b\d{1,3}\s*(?:years old|year old)\b",
        re.IGNORECASE,
    ),

    "PAN": re.compile(
        r"\b[A-Z]{5}\d{4}[A-Z]\b"
    ),

    "AADHAAR": re.compile(
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
    ),

    "UK_NINO": re.compile(
        r"\b[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b",
        re.IGNORECASE,
    ),
}


def mask_pii(text: str) -> dict:
    """
    Detect PII using spaCy NER and regex.

    Replace detected entities with placeholders.
    Return masked text and a mapping.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    doc = nlp(text)

    spans = []

    # ----------------------------------------
    # STEP 1: spaCy PERSON detection
    # ----------------------------------------

    for ent in doc.ents:

        if ent.label_ == "PERSON":
            spans.append(
                (
                    ent.start_char,
                    ent.end_char,
                    "PERSON",
                )
            )

    # ----------------------------------------
    # STEP 2: Regex detection
    # ----------------------------------------

    for label, pattern in PII_PATTERNS.items():

        for match in pattern.finditer(text):

            spans.append(
                (
                    match.start(),
                    match.end(),
                    label,
                )
            )

    # ----------------------------------------
    # STEP 3: Resolve overlapping entities
    # ----------------------------------------

    # Prefer the longest span when matches overlap.
    spans.sort(
        key=lambda x: (
            -(x[1] - x[0]),
            x[0],
        )
    )

    accepted = []

    for start, end, label in spans:

        overlaps = any(
            start < existing_end
            and end > existing_start
            for existing_start, existing_end, _
            in accepted
        )

        if not overlaps:
            accepted.append(
                (start, end, label)
            )

    accepted.sort(key=lambda x: x[0])

    # ----------------------------------------
    # STEP 4: Replace with dummy placeholders
    # ----------------------------------------

    counters = defaultdict(int)
    mapping = {}

    parts = []
    cursor = 0

    for start, end, label in accepted:

        original = text[start:end]

        counters[label] += 1

        placeholder = (
            f"[{label}_{counters[label]}]"
        )

        mapping[placeholder] = original

        parts.append(text[cursor:start])
        parts.append(placeholder)

        cursor = end

    parts.append(text[cursor:])

    return {
        "masked_text": "".join(parts),
        "entities": list(mapping.keys()),
        "mapping": mapping,
    }
