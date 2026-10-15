# Guardrails and gates, explained from scratch

> If you have ever watched an AI agent confidently do something you did not
> want it to do, this document is about the fix. No prior security knowledge
> assumed.

## 1. The problem

An agent is fast, confident and does not know the difference between these two
things:

```
write a draft to a file          send that draft to 400 customers
```

To the model they are both "a task". To you, one is reversible in a second and
the other is a Monday morning you will remember for years.

Most AI setups have nothing that separates them. The agent is given a
credential, or a tool that holds one, and from then on the only thing standing
between a confident mistake and the outside world is the quality of its
reasoning. That is not a control. It is a hope.

Writing the rule down does not help either. An agent can read a markdown file
telling it never to send email without approval, reason its way to an
exception, and send the email. **A written rule is a standard. It is not a
boundary.**

## 2. The core idea: three jobs, three parties

The fix is to stop one component doing all three jobs.

| Job | Who does it | Can it be talked out of it |
|---|---|---|
| Decide what *should* happen | the agent | yes, it is a language model |
| Decide what is *permitted* | a gate, in plain code | no, it does not read prompts |
| Actually *perform* the action | an executor holding the credential | it only acts when told |

**Agents propose. Deterministic systems authorise. Executors perform.**

The gate is ordinary code. It has no model in it. You cannot persuade an `if`
statement, which is exactly why the decision lives there.

## 3. What a gate actually is

A short checklist, run in order. Any failure stops everything.

```
is there a registered executor for this at all     no -> stop
is the requester a real, known identity            no -> stop
does this identity hold this specific power        no -> stop
does policy permit that power in this context      no -> stop
did a human sign this exact action and payload     no -> stop
record the decision, before anything happens     cannot -> stop
                                                       |
                                                       v
                                            the executor runs
```

Two details carry most of the value.

**The decision is recorded before the action runs, not after.** If it cannot be
recorded, it does not proceed. An action nobody can find afterwards is
indistinguishable from one that never happened.

**The executor is the only code holding a credential.** The agent never has the
API key. It cannot send an email by deciding to, only by submitting a request
that survives the checklist.

## 4. Signing, and why a confirmation click is not the same thing

Most tools ask "Are you sure? [y/N]". That is better than nothing and much
weaker than it looks. It proves somebody pressed a key. It does not prove
*what* they agreed to, and nothing stops the same yes being reused.

A signature fixes both. The human signs a message that includes the exact
action, the exact target and a fingerprint of the exact payload.

> Think of it as signing one specific cheque, with the amount and the payee
> already filled in, rather than signing a blank chequebook and trusting
> whoever holds it.

Four properties make it worth the effort:

- **It is bound to the payload.** Change one word after signing and the
  fingerprint no longer matches, so the action stops.
- **The private key is not in the repository.** It is encrypted and held by the
  person. The system has only the public half, so it can *check* a signature
  and can never *create* one. An agent that reads the whole codebase still
  cannot sign anything.
- **It is one time.** Once an approval is spent, it is recorded as spent and
  cannot be replayed. Yesterday's approval cannot authorise today's send.
- **It expires.** An unused approval goes stale, so an old one found lying
  around is worthless.

In `13-governance-planes/control/approval.py` you can see a small version of
this. Run the demo and watch an approved message get refused after one word of
it changed.

## 5. Not everything needs a signature

Asking a human to sign every file read would be useless, because people
rubber-stamp anything that happens fifty times a day. So actions carry a risk
tier, and the tier decides what evidence is required.

| Tier | Looks like | What it needs |
|---|---|---|
| Low | read a file, summarise a note | nothing, it is reversible and local |
| Medium | write to internal storage, draft a message | identity and capability |
| High | send email, publish code, deploy, delete, pay | all of the above **plus a signature** |

The rule of thumb: **does this leave the building, and can I take it back.** If
it leaves and you cannot, a human signs.

Data sensitivity raises the tier on its own. The same action on ordinary notes
and on health records is not the same action.

## 6. A worked example: letting an agent publish code

This is the part people find most surprising, so here it is end to end. An
agent proposes to push a commit to GitHub.

**Step 1. The agent asks. It cannot proceed.** It prepares a request and stops.
This is what it looks like in practice when an agent reaches a gate:

```
Shadow v5 is ready. Please sign the new approval:

  python external_action_gate.py approve \
     --private-key "$HOME/.keys/approval-private-key.pem" \
     --payload  .tmp/payload.json \
     --output   .tmp/approval.json \
     --action   infrastructure.activate_runtime \
     --target   infrastructure:runtime

Then tell me signed.
```

The agent is not asking permission as a politeness. It genuinely cannot
continue. There is no path from where it is standing to the outside world.

**Step 2. The capability is narrow.** The agent does not hold "GitHub access".
It holds one power: push to a feature branch. Policy allows branch names
beginning `feat/`, `fix/`, `chore/` or `review/` and refuses `main`, release
branches, tags, force pushes and anything using refspec syntax. The request is
rejected for shape before it even reaches the gate.

**Step 3. The human signs the exact thing.** Not "a push". This base commit,
this target commit, this branch name.

**Step 4. The credential appears only at the moment of use.** It is injected
from a password vault when the push runs and is never written into the
repository, the agent's context or a config file. **Holding the power to use a
credential and holding the credential are two different things.** If an agent's
configuration leaked tomorrow, it would contain no key.

**Step 5. Verify what actually happened.** After the push, the remote is read
back and the commit on the server is compared with the commit that was
approved. Trust the outcome, not the command's exit code.

**Step 6. Everything is recorded** under one id: what was asked, what was
decided, what ran, what came back.

Notice what is not in that list. No general GitHub token. No permanent
authority. Nothing that could have merged to `main` even if the agent had tried.

## 7. Guarding the guards

A guardrail anyone can quietly edit is decoration. So changing the rules is
itself gated.

In the private system this repository is drawn from, a commit that touches a
hook, a policy file or the gate's own code is refused unless the same commit
also includes a written decision explaining why, and regression tests proving
the guardrail still works.

Smaller habits matter too. `git add .` is blocked, because staging in bulk is
how credentials get committed by accident. Staging a file that looks like a key
is blocked outright.

The gate also refuses certain actions to *everyone*, including the person who
administers the system: editing the policy through the gate, granting itself a
capability, rewriting the ledger. If the most privileged identity can quietly
widen its own powers, there were never any powers, only suggestions.

## 8. What it costs

An honest list, because people discover these on day two and conclude the
system is broken.

- **It is slower.** Some things now need you, and you are not always at your
  desk.
- **You will be stopped by your own system,** usually when you are in a hurry.
  That is the feature working, and it does not feel like it at the time.
- **Bypass has to exist.** A guardrail that cannot be overridden in a genuine
  emergency gets deleted instead of bypassed. So bypass is available, loud, and
  recorded. The goal is not to make it impossible. It is to make it a decision
  somebody made, rather than something that just happened.
- **An identity is not a person.** Anything holding your session is, to the
  gate, you. This layer limits what an identity may do. It does not prove who
  is typing.

## 9. Where to see it working

| Idea here | Code in this repository |
|---|---|
| The checklist, in order | `control/gateway.py` |
| Deny by default, capabilities, risk tiers | `control/policy.py` |
| Signing bound to an exact payload | `control/approval.py` |
| Recorded before it runs, hash not content | `control/ledger.py` |
| What a model may see | `privacy/` |
| All of it, in forty seconds | `python 13-governance-planes/demo.py` |

The version in this repository is a reference implementation, deliberately
small enough to read in one sitting. `README.md` in this directory lists
exactly what it does not do, and the list is longer than the code.

## 10. The one sentence to take away

> Your agents are instructed. Until you build this, they were never authorised.
