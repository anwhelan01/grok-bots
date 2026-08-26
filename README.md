# grok-bots

Grok Bot content factory, mapped onto Hermes Bot Mode, with the parts the marketing post left out.

Source pitch: [Scotty Beam on Grok Bot](https://x.com/ScottyBeamIO/status/2090174525468033116) via [k3ss_official](https://x.com/k3ss_official/status/2090196599985062061).

This repo is the production contract. It is not a hosted Grok Bot clone. It is nine isolated Hermes profiles sharing a workspace of artifacts, plus a state machine you can run offline.

## What the tweet got right

Content is a headcount problem. One person doing research, copy, visuals, analytics, timing, and publishing is six jobs with a context-switch tax.

Named specialists plus a shared working surface is the right shape.

## What the tweet got wrong

| Claim | Reality |
|---|---|
| Each Grok Bot gets its own computer | Grok Bots share one account-scoped VM. Isolated screens, shared cookies and files. |
| Hermes works the same way | Hermes Bot Mode is an isolated profile under `~/.hermes/profiles/<name>/`. Shared computer has to be a workspace directory you invent. |
| Nothing lands on the human | That is how you ship a ban. x-ops already forbids Halo posting. This repo keeps that rule. |
| Record-once teaching replaces process | Useful later. Useless until artifacts have a schema and a gate. |
| Six roles is the team | Missing editor and compliance. Both are in this fleet. |

## Mapping

| Grok Bot role | Hermes profile | Artifact |
|---|---|---|
| Chief of Staff | `rae` | `job.json` |
| Researcher | `scout` | `research.json` |
| Writer | `scribe` | `draft.json` |
| Visualiser | `frame` | `visual.json` |
| *(missing)* | `reed` | `edit.json` |
| *(missing)* | `gate` | `compliance.json` |
| Analyst | `tally` | `analysis.json` |
| Scheduler | `clock` | `schedule.json` |
| Publisher | `press` | `package.json` only |

None of them may publish.

## Pipeline

```
intake -> research -> draft -> visual -> edit -> compliance -> schedule -> awaiting_human
                                                                      |
                                                              APPROVE:id:account
                                                                      v
                                                              packaged -> published (human URL)
```

## Install

```bash
python3 -m pip install -e '.[dev]'
pytest
grokbots roster
grokbots run --topic "Grok Bot content factory" --account tonywhelan
grokbots install --hermes-home ~/.hermes --dry-run
```

Then in Hermes Desktop Bot Mode each profile is a Bot. Shared files: `~/.hermes/workspace/grok-bots/jobs/<id>/`.

```
hermes model    # xAI Grok OAuth
hermes -p scout chat
```

## Hard rules

- press never posts, likes, RTs, follows, or DMs
- Human assigns the account
- Label AI media
- Approval token is exact: `APPROVE:<job_id>:<account>`
- Related desks: `x-ops`, `hermes-floor`, `kanban-surface`. Do not merge rosters.
