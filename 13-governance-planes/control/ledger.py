"""Control Plane: the append only record of every decision.

Two properties matter more than the format.

The ledger records a hash of the payload, never the payload. An audit trail
that stores the sensitive text it was protecting has moved the problem rather
than solved it.

The decision is recorded before the action runs, and the outcome afterwards,
under one correlation id. An action that cannot be recorded does not proceed,
because an unrecordable action is indistinguishable afterwards from one that
never happened.
"""

import hashlib
import json
import time
import uuid
from pathlib import Path

LEDGER_PATH = Path(__file__).resolve().parent / "ledger.jsonl"


def payload_hash(payload):
    data = payload if isinstance(payload, bytes) else str(payload).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def new_correlation_id():
    return str(uuid.uuid4())


def record(entry, path=None):
    """Append one entry and return it. Never rewrites an earlier line.

    The path is resolved at call time, not bound as a default at import. A
    default bound at import cannot be redirected afterwards, which makes the
    ledger untestable and silently writes to the wrong file when it is reused.
    """
    path = Path(path) if path else LEDGER_PATH
    entry = dict(entry)
    entry.setdefault("at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def read(path=None):
    path = Path(path) if path else LEDGER_PATH
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
