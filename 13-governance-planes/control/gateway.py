"""Control Plane: the only door to an effect.

Every stage below answers a different question and none can be skipped:

    privacy      may this data go to this kind of destination
    capability   does this principal hold this power at all
    policy       may that power be used in this context
    approval     did a human sign this exact action, target and payload
    ledger       is the decision recorded before anything happens
    execute      the executor is the only code that touches the outside world

The property worth testing is not that a refusal raises an error. It is that
on a refusal the executor is never called. A denial that still reaches the
executor is not a denial.
"""

from ..privacy.route import route
from . import approval as approvals
from .ledger import new_correlation_id, payload_hash, record
from .policy import decide


class Refusal(Exception):
    """Raised instead of acting. Carries the stage and the reason."""

    def __init__(self, stage, reason, correlation_id):
        super().__init__(f"[{stage}] {reason}")
        self.stage = stage
        self.reason = reason
        self.correlation_id = correlation_id


class Gateway:
    """Holds no credential. Executors hold credentials; the gateway holds the rules."""

    def __init__(self):
        self._executors = {}

    def register(self, name, executor):
        self._executors[name] = executor

    def submit(self, principal, action, target, payload, executor,
               approval=None, apply_privacy=True):
        correlation_id = new_correlation_id()
        digest = payload_hash(payload)

        def refuse(stage, reason):
            record({"correlation_id": correlation_id, "outcome": "denied", "stage": stage,
                    "principal": principal, "action": action, "target": target,
                    "payload_sha256": digest, "reason": reason})
            raise Refusal(stage, reason, correlation_id)

        if executor not in self._executors:
            refuse("executor", f"no executor is registered for {executor!r}")

        sent = payload
        classification = "NOT_ASSESSED"
        if apply_privacy and isinstance(payload, str):
            privacy = route(payload)
            classification = privacy.classification
            if not privacy.allowed:
                refuse("privacy", privacy.reason)
            sent = privacy.payload

        verdict = decide(principal, action)
        if not verdict.allowed:
            refuse("policy", verdict.reason)

        if verdict.approval_required:
            ok, reason = approvals.verify(approval, action, target, payload)
            if not ok:
                refuse("approval", reason)

        record({"correlation_id": correlation_id, "outcome": "authorised",
                "principal": principal, "action": action, "target": target,
                "payload_sha256": digest, "classification": classification,
                "risk": verdict.risk})

        try:
            result = self._executors[executor](target, sent)
        except Exception as exc:
            record({"correlation_id": correlation_id, "outcome": "failed",
                    "action": action, "target": target, "error": str(exc)})
            raise
        record({"correlation_id": correlation_id, "outcome": "executed",
                "action": action, "target": target})
        return {"correlation_id": correlation_id, "classification": classification,
                "result": result}
