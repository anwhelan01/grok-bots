# Contributing

This is an operator desk, not a framework playground.

1. Change the state machine and the tests in the same commit.
2. Do not add a Bot that `may_publish=True`.
3. Do not add a transition that skips `awaiting_human`.
4. SOUL.md files stay short. Procedure lives in skills.
5. `pytest` must stay green with no network.
