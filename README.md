# Clavex AI OS

> A hackable, file-based and AI-provider-agnostic operating system for your
> work, life or business.
> Built by Clavex on the **WAT framework**: Workflows → Agents → Tools.

Clavex AI OS is the public skeleton of the operating system Clavex AI
Solutions Ltd built and uses to run governance, knowledge, product work,
delivery, client operations, deterministic automation and organisational
memory. The private business context has been removed, while the 12-layer
architecture and operating discipline remain available for anyone to clone
and customise.

## Why this exists

Most people use AI as a chat window. The results can be impressive one message
at a time but unreliable across a real process. The fix is architectural, not
simply a bigger prompt:

- **Workflows** (markdown SOPs) say *what* to do and in what order
- **Agents** (Claude Code, Codex, Gemini or another harness) decide and coordinate
- **Tools** (plain Python scripts) execute deterministically

If each improvised AI step is 90% accurate, a five-step process succeeds 59%
of the time. Move execution into deterministic tools and the agent only has to
orchestrate — that is how the system stays reliable.

## Quickstart (10 minutes)

```bash
git clone https://github.com/jefkins/Clavex-AIOS.git
cd Clavex-AIOS
cp .env.example .env          # add your API keys
```

1. Open the folder in your AI coding tool (Claude Code, Codex CLI, Gemini CLI)
2. It reads `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` → which point to `OS.md`,
   the operating contract
3. Say: *"Read OS.md and run the daily startup workflow"*
4. Start replacing placeholders with your own life or business — see
   `docs/GETTING-STARTED.md`

## The structure

| Folder | What lives there |
|---|---|
| `01-governance/` | Your rules: principles, policies and non-negotiables |
| `02-knowledge/` | Domain knowledge the AI should draw on |
| `03-engineering-os/` | The machinery: skills, workflows and context routing |
| `04-clavex-os-product/` | Reusable capabilities and products being built |
| `05-delivery-os/` | How opportunities become controlled, supported outcomes |
| `06-clients/` | Per-client workspaces (gitignored — client data never commits) |
| `07-scripts/` | Deterministic Python tools — the T in WAT |
| `08-references/` | External standards and source material |
| `09-deployments/` | Development, staging and production release state |
| `10-templates/` | Reusable starting points |
| `11-archive/` | Retired content — nothing is deleted, it is archived |
| `12-memory/` | Persistent memory: strategy, decisions, lessons and ideas |
| `13-governance-planes/` | Privacy and Control planes: what a model may see, what an agent may do. Runnable, with tests |

Numbering is deliberate: it fixes the order in listings and gives every
concern one clear home. Read [the architecture guide](docs/ARCHITECTURE.md) for
the layer boundaries, request-to-output flow and extension rules.

## Core ideas worth stealing even if you do not clone

1. **One operating contract** (`OS.md`) every AI harness reads first —
   AI-provider-agnostic by design
2. **Intent routing** (`03-engineering-os/context-router/`) — load only the
   context the task needs, not the whole repo
3. **File-based memory** (`12-memory/`) — the system gets smarter because
   sessions write back what they learned
4. **Skills as plain markdown** — processes any AI can follow, with no
   provider lock-in
5. **Secrets in `.env` only** — enforced by contract and `.gitignore`
6. **Two governance planes** (`13-governance-planes/`): classify and redact
   before a model is called, and deny by default before an agent acts. Run
   `python 13-governance-planes/demo.py` to watch an approved message get
   refused after one word of it changed

## Author

Built by **Jefkins Nwabenu** — Founder, Clavex AI Solutions Ltd, applying AI
automation to the UK health & social care sector.
LinkedIn: https://www.linkedin.com/in/jefkins-nwabenu-digital-ai

MIT licensed. Fork it, customise it and make it useful. If it helps you, a
GitHub star helps other builders find it.
