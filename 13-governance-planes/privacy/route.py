"""Privacy Plane, step 3: decide where a request of this class may go.

The routing table is the policy. Changing where special category data is
allowed to travel should be a visible edit to this table, not a flag buried in
a call site.
"""

from .classify import PUBLIC, INTERNAL, PERSONAL, SPECIAL
from .redact import redact

ROUTES = {
    PUBLIC:   {"destination": "any_approved_model", "redact": False, "allowed": True},
    INTERNAL: {"destination": "any_approved_model", "redact": False, "allowed": True},
    PERSONAL: {"destination": "approved_model_with_dpa", "redact": True, "allowed": True},
    SPECIAL:  {"destination": None, "redact": True, "allowed": False},
}


class PrivacyDecision:
    def __init__(self, classification, allowed, destination, payload, restore_map, reason):
        self.classification = classification
        self.allowed = allowed
        self.destination = destination
        self.payload = payload
        self.restore_map = restore_map
        self.reason = reason

    def __repr__(self):
        verdict = "ALLOW" if self.allowed else "REFUSE"
        return f"<Privacy {verdict} {self.classification} to {self.destination}>"


def route(text):
    """Classify, redact if the class requires it, and say where it may go."""
    redacted, restore_map, level = redact(text)
    rule = ROUTES[level]
    payload = redacted if rule["redact"] else text
    if not rule["allowed"]:
        return PrivacyDecision(
            level, False, None, payload, restore_map,
            "special category data has no approved model destination. "
            "Handle it in an explicitly approved environment or not at all")
    reason = ("redacted before leaving the process" if rule["redact"]
              else "no personal data detected")
    return PrivacyDecision(level, True, rule["destination"], payload, restore_map, reason)
