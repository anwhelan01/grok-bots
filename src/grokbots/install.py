from __future__ import annotations

from pathlib import Path
import os
import shutil
import stat
from .fleet import FLEET

ROOT = Path(__file__).resolve().parents[2]

class InstallError(RuntimeError):
    pass

def profile_source(name: str) -> Path:
    path = ROOT / "profiles" / name / "SOUL.md"
    if not path.is_file():
        raise InstallError(f"missing SOUL.md for {name}")
    return path

def skill_sources() -> list[Path]:
    skills = ROOT / "skills"
    return sorted(p for p in skills.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())

def render_profile(dest: Path, name: str, dry_run: bool = False, force: bool = False) -> list[str]:
    actions: list[str] = []
    src = profile_source(name)
    profile_home = dest / "profiles" / name
    soul = profile_home / "SOUL.md"
    if soul.is_file() and not force:
        if soul.read_text() != src.read_text():
            raise InstallError(
                f"refusing to overwrite existing profile {name} at {soul}. "
                "This fleet must not clobber a live Hermes roster. Pass force=True only after backup."
            )
        actions.append(f"KEEP {soul}")
        return actions
    actions.append(f"{'DRY ' if dry_run else ''}WRITE {soul}")
    if not dry_run:
        profile_home.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, soul)
        os.chmod(soul, stat.S_IRUSR | stat.S_IWUSR)
        env = profile_home / ".env"
        if not env.exists():
            env.write_text("# Profile-scoped secrets only. Do not copy from default.\n")
            os.chmod(env, stat.S_IRUSR | stat.S_IWUSR)
        skills_home = profile_home / "skills"
        skills_home.mkdir(parents=True, exist_ok=True)
        for skill in skill_sources():
            target = skills_home / skill.name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(skill, target)
            actions.append(f"SKILL {name}/{skill.name}")
    return actions

def install_fleet(hermes_home: Path, dry_run: bool = False, force: bool = False) -> list[str]:
    hermes_home = Path(hermes_home).expanduser().resolve()
    actions: list[str] = []
    shared = hermes_home / "workspace" / "grok-bots"
    actions.append(f"{'DRY ' if dry_run else ''}MKDIR {shared}")
    if not dry_run:
        shared.mkdir(parents=True, exist_ok=True)
        (shared / "jobs").mkdir(exist_ok=True)
    for bot in FLEET:
        actions.extend(render_profile(hermes_home, bot.name, dry_run=dry_run, force=force))
    return actions
