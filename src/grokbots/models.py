from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import json
import uuid

class JobStatus(str, Enum):
    INTAKE = "intake"
    RESEARCH = "research"
    DRAFT = "draft"
    VISUAL = "visual"
    EDIT = "edit"
    COMPLIANCE = "compliance"
    SCHEDULE = "schedule"
    AWAITING_HUMAN = "awaiting_human"
    PACKAGED = "packaged"
    PUBLISHED = "published"
    REJECTED = "rejected"
    BLOCKED = "blocked"

TERMINAL = {JobStatus.PUBLISHED, JobStatus.REJECTED, JobStatus.BLOCKED}
HUMAN_GATED = {JobStatus.AWAITING_HUMAN}

ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.INTAKE: {JobStatus.RESEARCH, JobStatus.REJECTED},
    JobStatus.RESEARCH: {JobStatus.DRAFT, JobStatus.BLOCKED},
    JobStatus.DRAFT: {JobStatus.VISUAL, JobStatus.BLOCKED},
    JobStatus.VISUAL: {JobStatus.EDIT, JobStatus.DRAFT, JobStatus.BLOCKED},
    JobStatus.EDIT: {JobStatus.COMPLIANCE, JobStatus.DRAFT, JobStatus.REJECTED, JobStatus.BLOCKED},
    JobStatus.COMPLIANCE: {JobStatus.SCHEDULE, JobStatus.EDIT, JobStatus.REJECTED},
    JobStatus.SCHEDULE: {JobStatus.AWAITING_HUMAN, JobStatus.BLOCKED},
    JobStatus.AWAITING_HUMAN: {JobStatus.PACKAGED, JobStatus.REJECTED, JobStatus.EDIT},
    JobStatus.PACKAGED: {JobStatus.PUBLISHED, JobStatus.REJECTED},
    JobStatus.PUBLISHED: set(),
    JobStatus.REJECTED: set(),
    JobStatus.BLOCKED: {JobStatus.RESEARCH, JobStatus.DRAFT, JobStatus.EDIT},
}

def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

@dataclass
class Brief:
    topic: str
    account: str
    channel: str = "x"
    voice: str = "peer, no sycophancy, no tutorial voice"
    hard_nos: list[str] = field(default_factory=lambda: ["auto-post", "engagement bait", "unlabelled AI media"])
    must_cite: bool = True
    max_posts: int = 1
    notes: str = ""

    def validate(self) -> None:
        if not self.topic.strip():
            raise ValueError("brief.topic is required")
        if not self.account.strip():
            raise ValueError("brief.account is required")
        if self.max_posts < 1:
            raise ValueError("brief.max_posts must be >= 1")

@dataclass
class Artifact:
    kind: str
    owner: str
    path: str
    payload: dict[str, Any]
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class Event:
    at: str
    actor: str
    action: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class Job:
    brief: Brief
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: JobStatus = JobStatus.INTAKE
    artifacts: list[Artifact] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    approval: dict[str, Any] | None = None
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)

    def log(self, actor: str, action: str, detail: str) -> None:
        self.events.append(Event(at=utcnow(), actor=actor, action=action, detail=detail))
        self.updated_at = utcnow()

    def add_artifact(self, artifact: Artifact) -> None:
        self.artifacts.append(artifact)
        self.log(artifact.owner, "artifact", artifact.kind)

    def latest(self, kind: str) -> Artifact | None:
        for artifact in reversed(self.artifacts):
            if artifact.kind == kind:
                return artifact
        return None

    def transition(self, dest: JobStatus, actor: str, reason: str) -> None:
        allowed = ALLOWED_TRANSITIONS[self.status]
        if dest not in allowed:
            raise ValueError(f"illegal transition {self.status.value} -> {dest.value}")
        prev = self.status
        self.status = dest
        self.log(actor, "transition", f"{prev.value}->{dest.value}: {reason}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "brief": asdict(self.brief),
            "approval": self.approval,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "events": [e.to_dict() for e in self.events],
        }

    def dump(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        brief = Brief(**data["brief"])
        job = cls(
            brief=brief,
            id=data["id"],
            status=JobStatus(data["status"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            approval=data.get("approval"),
        )
        job.artifacts = [Artifact(**item) for item in data.get("artifacts", [])]
        job.events = [Event(**item) for item in data.get("events", [])]
        return job
