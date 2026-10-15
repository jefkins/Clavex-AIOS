"""Privacy Plane, step 2: remove what the model does not need to see.

Redaction is reversible inside the process and nowhere else. The map that
restores the original values stays local, is never logged, and never travels
with the request. A redaction scheme that ships its own key has redacted
nothing.
"""

from .classify import classify


def redact(text):
    """Return (redacted_text, restore_map, classification).

    Each detected span becomes a stable placeholder such as [EMAIL_1]. The same
    value redacts to the same token within one call, so a model can still reason
    about "the same person" without being told who they are.
    """
    level, spans = classify(text)
    restore, seen, counts = {}, {}, {}
    out, cursor = [], 0
    for start, end, kind, _ in spans:
        original = text[start:end]
        if original in seen:
            token = seen[original]
        else:
            counts[kind] = counts.get(kind, 0) + 1
            token = f"[{kind.upper()}_{counts[kind]}]"
            seen[original] = token
            restore[token] = original
        out.append(text[cursor:start])
        out.append(token)
        cursor = end
    out.append(text[cursor:])
    return "".join(out), restore, level


def restore(text, restore_map):
    """Put the original values back, for the local caller only."""
    for token, original in restore_map.items():
        text = text.replace(token, original)
    return text
