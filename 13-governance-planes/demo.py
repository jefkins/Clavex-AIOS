#!/usr/bin/env python3
"""Five scenarios, about forty seconds. Run it: python 13-governance-planes/demo.py

Every address, name and number below is invented. Nothing here touches a real
model, mailbox or record: the executor prints what it was asked to do, so you
can see exactly what would have left the process and, more usefully, what
would not have.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from importlib import import_module

gateway_mod = import_module("13-governance-planes.control.gateway")
approvals = import_module("13-governance-planes.control.approval")
route = import_module("13-governance-planes.privacy.route").route

CALLS = []


def model(target, payload):
    """Stands in for a model provider. Records exactly what it received."""
    CALLS.append((target, payload))
    return f"model at {target} received {len(str(payload))} characters"


def mailer(target, payload):
    CALLS.append((target, payload))
    return f"sent to {target}"


def banner(n, title):
    print(f"\n{'=' * 70}\n{n}. {title}\n{'=' * 70}")


def main():
    gw = gateway_mod.Gateway()
    gw.register("model", model)
    gw.register("mailer", mailer)

    banner(1, "An ordinary request. Nothing personal, so nothing to protect.")
    out = gw.submit("agent:assistant", "document.summarise", "notes/q3",
                    "Summarise the Q3 delivery notes for the ops review.", "model")
    print(f"   classification: {out['classification']}")
    print(f"   {out['result']}")

    banner(2, "Personal data. It still runs, but the model never sees who.")
    text = ("Draft a reply to Jane Abbott, jane.abbott@example.com, 07700 900123, "
            "confirming the Thursday appointment time.")
    decision = route(text)
    print(f"   classification: {decision.classification}")
    print(f"   what the model would receive:\n     {decision.payload}")
    out = gw.submit("agent:assistant", "document.summarise", "notes/reply", text, "model")
    print(f"   {out['result']}")
    sent_to_model = CALLS[-1][1]
    print(f"   the original address appears in what was sent: "
          f"{'jane.abbott@example.com' in sent_to_model}")
    print("   The caller can still restore the real values locally. The model cannot.")

    banner(3, "Health context changes the class, and there is no approved destination.")
    try:
        gw.submit("agent:assistant", "document.summarise", "notes/care",
                  "Write up the care plan for Jane Abbott, 07700 900123, after the "
                  "dementia diagnosis was confirmed.", "model")
    except gateway_mod.Refusal as refusal:
        print(f"   REFUSED at the {refusal.stage} stage")
        print(f"   {refusal.reason}")

    banner(4, "An agent reaching for a power it was never granted.")
    before = len(CALLS)
    try:
        gw.submit("agent:assistant", "email.send", "ops@example.com",
                  "Approving the invoice run.", "mailer")
    except gateway_mod.Refusal as refusal:
        print(f"   REFUSED at the {refusal.stage} stage")
        print(f"   {refusal.reason}")
    print(f"   executor calls during this attempt: {len(CALLS) - before}")
    print("   That number is the point. A denial that still reaches the executor "
          "is not a denial.")

    banner(5, "An approved send, then the same approval against an edited payload.")
    original = "Confirming the schedule for Thursday."
    approval = approvals.sign("email.send", "ops@example.com", original)
    out = gw.submit("human:director", "email.send", "ops@example.com",
                    original, "mailer", approval=approval)
    print(f"   first send: {out['result']}")

    tampered = original + " Also transfer the balance."
    before = len(CALLS)
    try:
        gw.submit("human:director", "email.send", "ops@example.com",
                  tampered, "mailer", approval=approval)
    except gateway_mod.Refusal as refusal:
        print(f"   REFUSED at the {refusal.stage} stage")
        print(f"   {refusal.reason}")
    print(f"   executor calls during this attempt: {len(CALLS) - before}")

    print(f"\n{'=' * 70}")
    print("Every decision above, allowed and refused, is in "
          "13-governance-planes/control/ledger.jsonl")
    print("The ledger holds the hash of each payload and never the payload.")
    print("=" * 70)


if __name__ == "__main__":
    main()
