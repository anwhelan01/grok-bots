from __future__ import annotations

from typing import Any
from .fleet import FLEET

REQUIRED_RESEARCH_KEYS = {"claims", "sources", "unknowns"}
REQUIRED_DRAFT_KEYS = {"text", "hook", "channel", "account"}
REQUIRED_VISUAL_KEYS = {"prompt", "label_ai", "aspect"}
REQUIRED_EDIT_KEYS = {"text", "verdict", "issues"}
REQUIRED_COMPLIANCE_KEYS = {"pass", "fails"}
REQUIRED_SCHEDULE_KEYS = {"slot", "timezone", "reason"}
REQUIRED_PACKAGE_KEYS = {"text", "account", "channel", "human_must_post"}

class ValidationError(ValueError):
    pass

def _require(payload: dict[str, Any], keys: set[str], kind: str) -> None:
    missing = sorted(keys - set(payload))
    if missing:
        raise ValidationError(f"{kind} missing keys: {missing}")

def validate_research(payload: dict[str, Any]) -> None:
    _require(payload, REQUIRED_RESEARCH_KEYS, "research")
    if not payload["sources"] or not payload["claims"]:
        raise ValidationError("research needs claims and sources")
    for source in payload["sources"]:
        if not source.get("url") or not source.get("title"):
            raise ValidationError("each source needs url and title")

def validate_draft(payload: dict[str, Any], account: str) -> None:
    _require(payload, REQUIRED_DRAFT_KEYS, "draft")
    if payload["account"] != account:
        raise ValidationError("draft.account does not match brief.account")
    text = payload["text"].strip()
    if not text:
        raise ValidationError("draft.text is empty")
    if payload["channel"] == "x" and len(text) > 280:
        raise ValidationError("X draft exceeds 280 characters")

def validate_visual(payload: dict[str, Any]) -> None:
    _require(payload, REQUIRED_VISUAL_KEYS, "visual")
    if payload["label_ai"] is not True:
        raise ValidationError("visual.label_ai must be true")

def validate_edit(payload: dict[str, Any]) -> None:
    _require(payload, REQUIRED_EDIT_KEYS, "edit")
    if payload["verdict"] not in {"ship", "revise"}:
        raise ValidationError("edit.verdict must be ship or revise")

def validate_compliance(payload: dict[str, Any]) -> None:
    _require(payload, REQUIRED_COMPLIANCE_KEYS, "compliance")
    if payload["pass"] is True and payload["fails"]:
        raise ValidationError("compliance cannot pass with fails")
    if payload["pass"] is False and not payload["fails"]:
        raise ValidationError("compliance fail requires fails[]")

def validate_schedule(payload: dict[str, Any]) -> None:
    _require(payload, REQUIRED_SCHEDULE_KEYS, "schedule")

def validate_package(payload: dict[str, Any], account: str) -> None:
    _require(payload, REQUIRED_PACKAGE_KEYS, "package")
    if payload["human_must_post"] is not True:
        raise ValidationError("package.human_must_post must be true")
    if payload["account"] != account:
        raise ValidationError("package.account does not match brief")

def assert_no_publisher_rights() -> None:
    offenders = [bot.name for bot in FLEET if bot.may_publish]
    if offenders:
        raise ValidationError(f"bots marked may_publish: {offenders}")

def assert_isolated_profiles() -> None:
    names = [bot.hermes_profile for bot in FLEET]
    if len(names) != len(set(names)):
        raise ValidationError("duplicate hermes profiles")
    if any(not bot.isolated_memory for bot in FLEET):
        raise ValidationError("every bot must have isolated memory")
