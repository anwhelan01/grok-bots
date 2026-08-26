from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

@dataclass(frozen=True)
class BotSpec:
    name: str
    title: str
    grok_role: str
    hermes_profile: str
    job: str
    writes: tuple[str, ...]
    reads: tuple[str, ...]
    may_publish: bool
    isolated_memory: bool
    shared_workspace: bool

FLEET: tuple[BotSpec, ...] = (
    BotSpec("rae", "Chief of Staff", "Chief of Staff", "rae", "Route briefs, enforce the state machine, never write copy.", ("job.json", "handoff.md"), ("brief.json",), False, True, True),
    BotSpec("scout", "Researcher", "Researcher", "scout", "Pull sources, extract claims, refuse unsourced certainty.", ("research.json",), ("brief.json", "job.json"), False, True, True),
    BotSpec("scribe", "Writer", "Writer", "scribe", "Turn sourced claims into voice-locked copy. No new facts.", ("draft.json",), ("research.json", "voice.md"), False, True, True),
    BotSpec("frame", "Visualiser", "Visualiser", "frame", "Produce a visual brief and prompt pack. Never invent brand assets.", ("visual.json",), ("draft.json", "style.md"), False, True, True),
    BotSpec("reed", "Editor", "(missing in original)", "reed", "Cut fat, kill cliche, flag unsourced claims, send back if needed.", ("edit.json",), ("draft.json", "visual.json", "research.json"), False, True, True),
    BotSpec("gate", "Compliance", "(missing in original)", "gate", "Hard-stop auto-post, unlabelled media, account mix-ups, banned claims.", ("compliance.json",), ("edit.json", "draft.json", "brief.json"), False, True, True),
    BotSpec("tally", "Analyst", "Analyst", "tally", "Read winners.jsonl and tell the floor what actually moved.", ("analysis.json",), ("winners.jsonl", "draft.json"), False, True, True),
    BotSpec("clock", "Scheduler", "Scheduler", "clock", "Propose a slot. Never fire a post.", ("schedule.json",), ("compliance.json", "analysis.json"), False, True, True),
    BotSpec("press", "Publisher", "Publisher", "press", "Package the post for a human. Posting is out of band.", ("package.json",), ("schedule.json", "edit.json", "visual.json"), False, True, True),
)

BY_NAME = {bot.name: bot for bot in FLEET}
GROK_MAP = {bot.grok_role: bot for bot in FLEET if not bot.grok_role.startswith("(")}
STAGE_OWNER = {
    "intake": "rae", "research": "scout", "draft": "scribe", "visual": "frame",
    "edit": "reed", "compliance": "gate", "schedule": "clock",
    "awaiting_human": "rae", "packaged": "press", "published": "press",
}

def fleet_dict() -> list[dict[str, Any]]:
    rows = []
    for bot in FLEET:
        rows.append({
            "name": bot.name, "title": bot.title, "grok_role": bot.grok_role,
            "hermes_profile": bot.hermes_profile, "job": bot.job,
            "writes": list(bot.writes), "reads": list(bot.reads),
            "may_publish": bot.may_publish, "isolated_memory": bot.isolated_memory,
            "shared_workspace": bot.shared_workspace,
        })
    return rows

def load_fleet(path: Path | None = None) -> list[dict[str, Any]]:
    if path is None:
        return fleet_dict()
    return json.loads(Path(path).read_text())
