"""Control Plane: approvals that are bound to one exact payload.

An approval that says "you may send an email" authorises every email. An
approval bound to the hash of one message authorises that message and nothing
else, so a payload edited after sign off no longer matches and the send fails.

This reference uses an HMAC over the action, the target and the payload hash.
A production system uses an asymmetric signature so that holding the verifier
does not let you mint approvals.
"""

import hashlib
import hmac

from .ledger import payload_hash

# Illustrative only. A real key lives in a secret store and never in a repository.
DEMO_KEY = b"reference-implementation-key-not-for-production"


def _material(action, target, digest):
    return f"{action}|{target}|{digest}".encode("utf-8")


def sign(action, target, payload, key=DEMO_KEY):
    """What a human does when they approve one specific action."""
    digest = payload_hash(payload)
    return {
        "action": action,
        "target": target,
        "payload_sha256": digest,
        "signature": hmac.new(key, _material(action, target, digest), hashlib.sha256).hexdigest(),
    }


def verify(approval, action, target, payload, key=DEMO_KEY):
    """Return (ok, reason). Any mismatch is a refusal, never a warning."""
    if not approval:
        return False, "this action requires a signed approval and none was supplied"
    digest = payload_hash(payload)
    if approval.get("action") != action:
        return False, f"approval was for {approval.get('action')!r}, not {action!r}"
    if approval.get("target") != target:
        return False, f"approval named target {approval.get('target')!r}, not {target!r}"
    if approval.get("payload_sha256") != digest:
        return False, ("the payload changed after it was approved. The approval covers "
                       f"{approval.get('payload_sha256', '')[:12]}, this payload is "
                       f"{digest[:12]}")
    expected = hmac.new(key, _material(action, target, digest), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, approval.get("signature", "")):
        return False, "the approval signature does not verify"
    return True, "approval verifies against this exact payload"
