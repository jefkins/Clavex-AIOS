"""Control Plane: the policy decision point.

Deny by default. A request is refused unless a rule permits it, and a forbid
beats any permit. The point of writing it this way is that adding a new action
cannot accidentally become allowed; somebody has to decide.

This file is a reference implementation with illustrative rules. A real
deployment keeps its rules in configuration, not in code, and the rule set is
part of what it protects.
"""

ALLOW = "ALLOW"
DENY = "DENY"

# Which principal holds which power. Deny by default means absence is refusal.
CAPABILITIES = {
    "agent:assistant": {"document.read", "document.summarise"},
    "agent:mailer": {"document.read", "email.draft"},
    "human:director": {"document.read", "document.summarise", "email.draft", "email.send"},
}

# Risk tiers decide what extra evidence an action needs before it runs.
RISK = {
    "document.read": 0,
    "document.summarise": 0,
    "email.draft": 1,
    "email.send": 4,          # leaves the building, so it needs a signed approval
    "record.delete": 5,
}

APPROVAL_REQUIRED_FROM = 4
FORBIDDEN = {"policy.edit", "capability.grant", "ledger.rewrite"}


class Decision:
    def __init__(self, verdict, reason, risk, approval_required):
        self.verdict = verdict
        self.reason = reason
        self.risk = risk
        self.approval_required = approval_required

    @property
    def allowed(self):
        return self.verdict == ALLOW

    def __repr__(self):
        return f"<{self.verdict} risk={self.risk}: {self.reason}>"


def decide(principal, action):
    """Answer one question: may this principal use this power, here, now."""
    if action in FORBIDDEN:
        return Decision(DENY, f"{action} is forbidden to every principal, "
                              "including the one that administers the system", 6, False)
    held = CAPABILITIES.get(principal)
    if held is None:
        return Decision(DENY, f"unknown principal {principal!r}", 6, False)
    risk = RISK.get(action)
    if risk is None:
        return Decision(DENY, f"no risk tier is defined for {action!r}, so it cannot be "
                              "assessed, so it is refused", 6, False)
    if action not in held:
        return Decision(DENY, f"{principal} does not hold {action}", risk, False)
    needs_approval = risk >= APPROVAL_REQUIRED_FROM
    return Decision(ALLOW, f"{principal} holds {action}", risk, needs_approval)
