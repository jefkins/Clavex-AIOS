# Governance Planes: Privacy and Control

> Most AI systems are built so that agents can do more. Very few are built to
> decide what an agent is allowed to do at all. These two layers answer that,
> and they sit across the WAT framework rather than inside it.

The 12 layers above this one describe *how work is organised*. This layer
describes *what is permitted*, and it applies to every workflow, agent and tool
without any of them having to cooperate.

```
User / API / n8n / external applications
                |
                v
  Control Plane    identity, capability, policy, approval, audit
                |
                v
  Privacy Plane    classification, redaction, routing, retention
                |
                v
  WAT execution    Workflows  ->  Agents  ->  Tools
                   Claude Code, Codex, Gemini, Python
                |
                v
  Governed output and an execution record
```

## New to this idea?

Read **[GUARDRAILS.md](GUARDRAILS.md)** first. It explains the whole concept
from scratch with no security background assumed: why a written rule is not a
boundary, what a gate actually checks, why signing beats a confirmation click,
and a worked example of letting an agent publish code to GitHub without ever
handing it a GitHub token.

## Run it

No dependencies. Five scenarios, about forty seconds.

```bash
python 13-governance-planes/demo.py
python -m pytest 13-governance-planes/tests -q
```

You will see an ordinary request run, a request carrying personal data run with
the identifiers removed, a special category request stop before any model is
called, an agent refused a power it was never granted, and an approved message
refused once a single word of it changed.

## The idea in one line each

**Privacy Plane: what may be seen.** Text is classified before a model is
called, identifiers are replaced with stable placeholders, and the
classification decides where the request may travel. Classifying after the call
has already disclosed whatever it was trying to protect.

**Control Plane: what may be done.** Deny by default. A principal acts only if
it holds the capability, the policy permits it in context, and, above a risk
threshold, a human has signed an approval bound to that exact payload. The
decision is recorded before anything runs.

## The property worth copying

The tests do not assert that a refusal raises an error. They assert that on a
refusal **the executor was never called**:

```python
with pytest.raises(Refusal):
    gw.submit("agent:assistant", "email.send", "a@b.com", "hello", "spy")
assert gw.spy.calls == []
```

A denial that still reaches the executor is not a denial. If you take one thing
from this directory, take that assertion and write it against your own system.

The second property is approval binding. An approval that says "you may send an
email" authorises every email. An approval bound to the hash of one message
authorises that message, so a payload edited after sign off stops:

```
REFUSED at the approval stage
the payload changed after it was approved. The approval covers 2151daeb0c5b,
this payload is c8bdcdfdfd72
```

## What this is not

Being specific about this matters more than the code.

- **It is not a compliance control.** It will not make a system UK GDPR
  compliant, and detection plus redaction is not a lawful basis for anything.
- **The detectors are shallow.** They match structured identifiers: email,
  phone, postcode, NHS number, national insurance number, card number. They do
  **not** detect names. "Jane Abbott" passes through untouched, and in a real
  deployment that matters.
- **The signing is illustrative.** It uses an HMAC with a key committed to this
  repository, which is fine for a demonstration and wrong for anything else.
  Production needs an asymmetric signature, so that holding the verifier does
  not let you mint approvals.
- **It governs the inbound request only.** Tool calls, retrieved documents,
  model responses and stored outputs all need the same treatment, and here they
  do not get it.
- **The policy is in code.** Real rules belong in configuration that is
  reviewed and versioned separately from the engine that reads them.
- **An identity is not a person.** Anything holding the Director's session is,
  to this layer, the Director.

Clavex runs a production version of this with asymmetric signed approvals, a
hash chained ledger, a capability registry and adapters as the only code
holding credentials. That version is not in this repository and will not be,
because its policy set and capability registry describe a live authorisation
surface. What is here is the shape of the idea and a working reference you can
read in one sitting.

## Where to start reading

Concepts first in [GUARDRAILS.md](GUARDRAILS.md), then the code:

| File | What it answers |
|---|---|
| `privacy/classify.py` | What class of data is this |
| `privacy/redact.py` | What does the model see instead |
| `privacy/route.py` | Where is data of this class allowed to go |
| `control/policy.py` | May this principal use this power here |
| `control/approval.py` | Did a human sign this exact payload |
| `control/ledger.py` | What was decided, recorded before it ran |
| `control/gateway.py` | The one door everything passes through |

## Contributing

The detector set is the most obvious place to help, and name detection is the
largest gap. Issues and pull requests are welcome, particularly from anyone who
has had to make this work in a regulated setting.
