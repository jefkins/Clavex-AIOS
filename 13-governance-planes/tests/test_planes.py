"""Tests for the two planes.

The assertion that matters most is not that a refusal raises. It is that on a
refusal the executor was never called. Every negative test below checks the
executor's call list, because a denial that still reaches the executor is not
a denial.

Run: python -m pytest 13-governance-planes/tests -q
"""

import sys
from importlib import import_module
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

classify_mod = import_module("13-governance-planes.privacy.classify")
redact_mod = import_module("13-governance-planes.privacy.redact")
route_mod = import_module("13-governance-planes.privacy.route")
gateway_mod = import_module("13-governance-planes.control.gateway")
approvals = import_module("13-governance-planes.control.approval")
policy = import_module("13-governance-planes.control.policy")


class Spy:
    """An executor that records every call, so a test can prove it got none."""

    def __init__(self):
        self.calls = []

    def __call__(self, target, payload):
        self.calls.append((target, payload))
        return "executed"


@pytest.fixture
def gw(tmp_path, monkeypatch):
    monkeypatch.setattr(import_module("13-governance-planes.control.ledger"),
                        "LEDGER_PATH", tmp_path / "ledger.jsonl")
    g = gateway_mod.Gateway()
    g.spy = Spy()
    g.register("spy", g.spy)
    return g


# --- privacy plane ---------------------------------------------------------

def test_plain_text_is_public():
    level, spans = classify_mod.classify("Summarise the delivery notes.")
    assert level == classify_mod.PUBLIC and spans == []


def test_contact_details_are_personal():
    level, _ = classify_mod.classify("Email a@b.com or call 07700 900123.")
    assert level == classify_mod.PERSONAL


def test_identifier_in_health_context_is_special_category():
    level, _ = classify_mod.classify("Call 07700 900123 about the dementia diagnosis.")
    assert level == classify_mod.SPECIAL


def test_redaction_is_stable_and_reversible():
    text = "Write to a@b.com, copy a@b.com."
    redacted, restore_map, _ = redact_mod.redact(text)
    assert "a@b.com" not in redacted
    assert redacted.count("[EMAIL_1]") == 2      # same value, same token
    assert redact_mod.restore(redacted, restore_map) == text


def test_special_category_has_no_destination():
    decision = route_mod.route("NHS number 943 476 5919, dementia diagnosis confirmed.")
    assert decision.allowed is False and decision.destination is None


# --- control plane ---------------------------------------------------------

def test_deny_by_default_for_unknown_principal():
    assert policy.decide("agent:nobody", "document.read").allowed is False


def test_unknown_action_cannot_be_assessed_so_is_refused():
    assert policy.decide("human:director", "something.new").allowed is False


def test_forbidden_actions_are_refused_even_to_the_director():
    assert policy.decide("human:director", "policy.edit").allowed is False


def test_missing_capability_never_reaches_the_executor(gw):
    with pytest.raises(gateway_mod.Refusal) as caught:
        gw.submit("agent:assistant", "email.send", "a@b.com", "hello", "spy")
    assert caught.value.stage == "policy"
    assert gw.spy.calls == []


def test_high_risk_action_without_approval_never_reaches_the_executor(gw):
    with pytest.raises(gateway_mod.Refusal) as caught:
        gw.submit("human:director", "email.send", "a@b.com", "hello", "spy")
    assert caught.value.stage == "approval"
    assert gw.spy.calls == []


def test_approval_is_bound_to_one_payload(gw):
    approval = approvals.sign("email.send", "a@b.com", "original")
    gw.submit("human:director", "email.send", "a@b.com", "original", "spy",
              approval=approval)
    assert len(gw.spy.calls) == 1
    with pytest.raises(gateway_mod.Refusal) as caught:
        gw.submit("human:director", "email.send", "a@b.com", "tampered", "spy",
                  approval=approval)
    assert caught.value.stage == "approval"
    assert len(gw.spy.calls) == 1              # still one, the second never ran


def test_approval_for_one_target_does_not_authorise_another(gw):
    approval = approvals.sign("email.send", "a@b.com", "hello")
    with pytest.raises(gateway_mod.Refusal):
        gw.submit("human:director", "email.send", "elsewhere@c.com", "hello", "spy",
                  approval=approval)
    assert gw.spy.calls == []


def test_special_category_is_refused_before_the_executor(gw):
    with pytest.raises(gateway_mod.Refusal) as caught:
        gw.submit("agent:assistant", "document.summarise", "notes",
                  "dementia diagnosis for 07700 900123", "spy")
    assert caught.value.stage == "privacy"
    assert gw.spy.calls == []


def test_unregistered_executor_is_refused(gw):
    with pytest.raises(gateway_mod.Refusal) as caught:
        gw.submit("agent:assistant", "document.read", "x", "hello", "nowhere")
    assert caught.value.stage == "executor"


# --- the two planes together ------------------------------------------------

def test_personal_data_is_redacted_before_the_executor_sees_it(gw):
    gw.submit("agent:assistant", "document.summarise", "notes",
              "Reply to jane@example.com about Thursday.", "spy")
    _, payload = gw.spy.calls[0]
    assert "jane@example.com" not in payload and "[EMAIL_1]" in payload


def test_the_ledger_records_the_hash_and_never_the_payload(gw, tmp_path):
    ledger = import_module("13-governance-planes.control.ledger")
    secret = "Reply to jane@example.com about Thursday."
    gw.submit("agent:assistant", "document.summarise", "notes", secret, "spy")
    written = (tmp_path / "ledger.jsonl").read_text()
    assert "jane@example.com" not in written
    assert ledger.payload_hash(secret) in written


def test_a_refusal_is_recorded_as_well_as_a_success(gw, tmp_path):
    with pytest.raises(gateway_mod.Refusal):
        gw.submit("agent:assistant", "email.send", "a@b.com", "hello", "spy")
    assert '"outcome": "denied"' in (tmp_path / "ledger.jsonl").read_text()
