from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json

from .fleet import STAGE_OWNER
from .models import Artifact, Brief, Job, JobStatus
from .validators import (
    validate_compliance,
    validate_draft,
    validate_edit,
    validate_package,
    validate_research,
    validate_schedule,
    validate_visual,
)


class PipelineError(RuntimeError):
    pass


Adapter = Callable[[Job], dict[str, Any]]


def _default_research(job: Job) -> dict[str, Any]:
    topic = job.brief.topic
    return {
        "claims": [{"text": f"{topic} is a coordination problem, not a talent problem.", "source_i": 0}],
        "sources": [{
            "title": "Operator brief",
            "url": "workspace://brief.json",
            "note": "Seeded from the job brief. Replace with live sources in Hermes.",
        }],
        "unknowns": ["live engagement numbers", "account-specific winners this week"],
    }


def _default_draft(job: Job) -> dict[str, Any]:
    research = job.latest("research")
    assert research is not None
    claim = research.payload["claims"][0]["text"]
    text = f"{claim} The missing piece is the queue, not another idea."
    if job.brief.channel == "x" and len(text) > 280:
        text = text[:277] + "..."
    return {
        "text": text,
        "hook": "headcount, not talent",
        "channel": job.brief.channel,
        "account": job.brief.account,
        "claims_used": [0],
    }


def _default_visual(job: Job) -> dict[str, Any]:
    draft = job.latest("draft")
    assert draft is not None
    return {
        "prompt": f"Quiet desk, one screen, no stock handshake. Caption energy: {draft.payload['hook']}",
        "label_ai": True,
        "aspect": "1:1",
        "alt": "A single workstation with a content queue on screen.",
    }


def _default_edit(job: Job) -> dict[str, Any]:
    draft = job.latest("draft")
    assert draft is not None
    text = draft.payload["text"].replace("  ", " ").strip()
    issues: list[str] = []
    if "guaranteed" in text.lower():
        issues.append("absolute claim")
    verdict = "revise" if issues else "ship"
    return {"text": text, "verdict": verdict, "issues": issues}


def _default_compliance(job: Job) -> dict[str, Any]:
    edit = job.latest("edit")
    visual = job.latest("visual")
    assert edit is not None and visual is not None
    fails: list[str] = []
    if visual.payload.get("label_ai") is not True:
        fails.append("AI media unlabelled")
    if edit.payload["verdict"] != "ship":
        fails.append("editor did not ship")
    for banned in job.brief.hard_nos:
        if banned.lower() in edit.payload["text"].lower():
            fails.append(f"hard-no phrase: {banned}")
    return {"pass": not fails, "fails": fails}


def _default_analysis(job: Job) -> dict[str, Any]:
    return {
        "window": "last_20",
        "signal": "bookmarks beat likes for this account pattern",
        "avoid": ["question-bait openers"],
    }


def _default_schedule(job: Job) -> dict[str, Any]:
    return {
        "slot": "2026-08-26T18:30:00+01:00",
        "timezone": "Europe/London",
        "reason": "weekday evening window from x-ops account notes",
    }


def _default_package(job: Job) -> dict[str, Any]:
    edit = job.latest("edit")
    visual = job.latest("visual")
    schedule = job.latest("schedule")
    assert edit and visual and schedule
    return {
        "text": edit.payload["text"],
        "account": job.brief.account,
        "channel": job.brief.channel,
        "slot": schedule.payload["slot"],
        "visual_prompt": visual.payload["prompt"],
        "label_ai": visual.payload["label_ai"],
        "human_must_post": True,
        "auto_post": False,
    }


DEFAULT_ADAPTERS: dict[str, Adapter] = {
    "research": _default_research,
    "draft": _default_draft,
    "visual": _default_visual,
    "edit": _default_edit,
    "compliance": _default_compliance,
    "analysis": _default_analysis,
    "schedule": _default_schedule,
    "package": _default_package,
}


class Pipeline:
    def __init__(self, workspace: Path, adapters: dict[str, Adapter] | None = None) -> None:
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.adapters = {**DEFAULT_ADAPTERS, **(adapters or {})}

    def job_dir(self, job: Job) -> Path:
        path = self.workspace / "jobs" / job.id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def persist(self, job: Job) -> Path:
        path = self.job_dir(job) / "job.json"
        path.write_text(job.dump())
        return path

    def load(self, job_id: str) -> Job:
        path = self.workspace / "jobs" / job_id / "job.json"
        return Job.from_dict(json.loads(path.read_text()))

    def open_job(self, brief: Brief) -> Job:
        brief.validate()
        job = Job(brief=brief)
        job.log("rae", "intake", f"{brief.account} / {brief.topic}")
        self.persist(job)
        return job

    def _write_artifact(self, job: Job, kind: str, owner: str, payload: dict[str, Any]) -> Artifact:
        dest = self.job_dir(job) / f"{kind}.json"
        dest.write_text(json.dumps(payload, indent=2))
        artifact = Artifact(kind=kind, owner=owner, path=str(dest), payload=payload)
        job.add_artifact(artifact)
        return artifact

    def run_research(self, job: Job) -> Job:
        if job.status != JobStatus.INTAKE:
            raise PipelineError(f"research requires intake, have {job.status.value}")
        payload = self.adapters["research"](job)
        validate_research(payload)
        self._write_artifact(job, "research", "scout", payload)
        job.transition(JobStatus.RESEARCH, "scout", "sources locked")
        self.persist(job)
        return job

    def run_draft(self, job: Job) -> Job:
        if job.status != JobStatus.RESEARCH:
            raise PipelineError(f"draft requires research, have {job.status.value}")
        if job.latest("research") is None:
            raise PipelineError("draft cannot start without research artifact")
        payload = self.adapters["draft"](job)
        validate_draft(payload, job.brief.account)
        self._write_artifact(job, "draft", "scribe", payload)
        job.transition(JobStatus.DRAFT, "scribe", "copy written from sourced claims")
        self.persist(job)
        return job

    def run_visual(self, job: Job) -> Job:
        if job.status != JobStatus.DRAFT:
            raise PipelineError(f"visual requires draft, have {job.status.value}")
        payload = self.adapters["visual"](job)
        validate_visual(payload)
        self._write_artifact(job, "visual", "frame", payload)
        job.transition(JobStatus.VISUAL, "frame", "visual brief")
        self.persist(job)
        return job

    def run_edit(self, job: Job) -> Job:
        if job.status != JobStatus.VISUAL:
            raise PipelineError(f"edit requires visual, have {job.status.value}")
        payload = self.adapters["edit"](job)
        validate_edit(payload)
        self._write_artifact(job, "edit", "reed", payload)
        if payload["verdict"] == "revise":
            job.transition(JobStatus.DRAFT, "reed", "sent back: " + ", ".join(payload["issues"]))
        else:
            job.transition(JobStatus.EDIT, "reed", "ship")
        self.persist(job)
        return job

    def run_compliance(self, job: Job) -> Job:
        if job.status != JobStatus.EDIT:
            raise PipelineError(f"compliance requires edit, have {job.status.value}")
        payload = self.adapters["compliance"](job)
        validate_compliance(payload)
        self._write_artifact(job, "compliance", "gate", payload)
        if payload["pass"]:
            job.transition(JobStatus.COMPLIANCE, "gate", "cleared")
        else:
            job.transition(JobStatus.REJECTED, "gate", "; ".join(payload["fails"]))
        self.persist(job)
        return job

    def run_schedule(self, job: Job) -> Job:
        if job.status != JobStatus.COMPLIANCE:
            raise PipelineError(f"schedule requires compliance, have {job.status.value}")
        analysis = self.adapters["analysis"](job)
        self._write_artifact(job, "analysis", "tally", analysis)
        payload = self.adapters["schedule"](job)
        validate_schedule(payload)
        self._write_artifact(job, "schedule", "clock", payload)
        job.transition(JobStatus.SCHEDULE, "clock", payload["slot"])
        job.transition(JobStatus.AWAITING_HUMAN, "rae", "human gate")
        self.persist(job)
        return job

    def approve(self, job: Job, actor: str, token: str) -> Job:
        if job.status != JobStatus.AWAITING_HUMAN:
            raise PipelineError("approve only from awaiting_human")
        if not token or token.strip() != f"APPROVE:{job.id}:{job.brief.account}":
            raise PipelineError("approval token mismatch")
        job.approval = {"actor": actor, "token_ok": True}
        job.log(actor, "approve", "human signed the package")
        payload = self.adapters["package"](job)
        validate_package(payload, job.brief.account)
        if payload.get("auto_post") is True:
            raise PipelineError("auto_post is forbidden")
        self._write_artifact(job, "package", "press", payload)
        job.transition(JobStatus.PACKAGED, "press", "ready for human publish")
        self.persist(job)
        return job

    def reject(self, job: Job, actor: str, reason: str) -> Job:
        if job.status not in {JobStatus.AWAITING_HUMAN, JobStatus.PACKAGED, JobStatus.INTAKE}:
            raise PipelineError("reject not allowed from this status")
        job.transition(JobStatus.REJECTED, actor, reason)
        self.persist(job)
        return job

    def mark_published(self, job: Job, actor: str, url: str) -> Job:
        if job.status != JobStatus.PACKAGED:
            raise PipelineError("publish receipt requires packaged job")
        if not url.startswith("https://"):
            raise PipelineError("publish receipt needs an https url")
        job.log(actor, "published", url)
        job.transition(JobStatus.PUBLISHED, actor, url)
        self.persist(job)
        return job

    def run_until_gate(self, brief: Brief) -> Job:
        job = self.open_job(brief)
        self.run_research(job)
        self.run_draft(job)
        self.run_visual(job)
        self.run_edit(job)
        if job.status == JobStatus.DRAFT:
            raise PipelineError("editor sent the draft back; stop for a rewrite")
        self.run_compliance(job)
        if job.status == JobStatus.REJECTED:
            return job
        self.run_schedule(job)
        return job

    def owner_for(self, status: JobStatus) -> str:
        return STAGE_OWNER[status.value]
