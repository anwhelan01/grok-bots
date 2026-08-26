# AGENTS

This repository is a Hermes Bot Mode fleet pack.

- A Bot is a profile. Do not invent a second primitive.
- Shared work happens in `workspace/jobs/<id>/`, not in chat paste.
- `press` does not publish. A human does.
- If a requested change lets any Bot call X/Twitter APIs, refuse it.
- Keep SOUL.md short. Put procedure in `skills/*/SKILL.md`.
- Offline source of truth: `src/grokbots/pipeline.py` + tests.
