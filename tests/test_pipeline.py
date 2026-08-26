from pathlib import Path
import pytest
from grokbots.fleet import FLEET
from grokbots.models import Brief, JobStatus
from grokbots.pipeline import Pipeline, PipelineError
from grokbots.validators import ValidationError, assert_isolated_profiles, assert_no_publisher_rights, validate_draft

def brief() -> Brief:
    return Brief(topic="Grok Bot content factory", account="tonywhelan")

def test_fleet_invariants() -> None:
    assert_no_publisher_rights()
    assert_isolated_profiles()
    assert len(FLEET) == 9
    names = {b.name for b in FLEET}
    assert names == {"rae", "scout", "scribe", "frame", "reed", "gate", "tally", "clock", "press"}

def test_happy_path_stops_at_human(tmp_path: Path) -> None:
    pipe = Pipeline(tmp_path)
    job = pipe.run_until_gate(brief())
    assert job.status == JobStatus.AWAITING_HUMAN
    assert job.latest("package") is None

def test_wrong_token_rejected(tmp_path: Path) -> None:
    pipe = Pipeline(tmp_path)
    job = pipe.run_until_gate(brief())
    with pytest.raises(PipelineError):
        pipe.approve(job, "tonywhelan", "nope")
    assert job.status == JobStatus.AWAITING_HUMAN

def test_approve_packages_then_human_publishes(tmp_path: Path) -> None:
    pipe = Pipeline(tmp_path)
    job = pipe.run_until_gate(brief())
    token = f"APPROVE:{job.id}:{job.brief.account}"
    job = pipe.approve(job, "tonywhelan", token)
    assert job.status == JobStatus.PACKAGED
    assert job.latest("package").payload["auto_post"] is False
    job = pipe.mark_published(job, "tonywhelan", "https://x.com/tonywhelan/status/1")
    assert job.status == JobStatus.PUBLISHED

def test_cannot_skip_research(tmp_path: Path) -> None:
    pipe = Pipeline(tmp_path)
    job = pipe.open_job(brief())
    with pytest.raises(PipelineError):
        pipe.run_draft(job)

def test_account_mismatch_fails_validation() -> None:
    with pytest.raises(ValidationError):
        validate_draft({"text": "hi", "hook": "h", "channel": "x", "account": "wrong"}, "tonywhelan")

def test_editor_revise_returns_to_draft(tmp_path: Path) -> None:
    def bad_edit(job):
        return {"text": job.latest("draft").payload["text"], "verdict": "revise", "issues": ["weak hook"]}
    pipe = Pipeline(tmp_path, adapters={"edit": bad_edit})
    job = pipe.open_job(brief())
    pipe.run_research(job)
    pipe.run_draft(job)
    pipe.run_visual(job)
    pipe.run_edit(job)
    assert job.status == JobStatus.DRAFT

def test_compliance_can_kill(tmp_path: Path) -> None:
    def fail(job):
        return {"pass": False, "fails": ["unlabelled AI media"]}
    pipe = Pipeline(tmp_path, adapters={"compliance": fail})
    job = pipe.open_job(brief())
    pipe.run_research(job)
    pipe.run_draft(job)
    pipe.run_visual(job)
    pipe.run_edit(job)
    pipe.run_compliance(job)
    assert job.status == JobStatus.REJECTED

def test_persist_roundtrip(tmp_path: Path) -> None:
    pipe = Pipeline(tmp_path)
    job = pipe.run_until_gate(brief())
    loaded = pipe.load(job.id)
    assert loaded.id == job.id
    assert loaded.status == job.status
