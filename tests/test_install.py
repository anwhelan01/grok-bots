from pathlib import Path
from grokbots.fleet import FLEET
from grokbots.install import install_fleet, profile_source

def test_souls_exist() -> None:
    for bot in FLEET:
        assert profile_source(bot.name).is_file()

def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    actions = install_fleet(tmp_path / "hermes", dry_run=True)
    assert actions
    assert not (tmp_path / "hermes").exists()

def test_install_lays_profiles_and_skills(tmp_path: Path) -> None:
    home = tmp_path / "hermes"
    install_fleet(home, dry_run=False)
    assert (home / "workspace" / "grok-bots" / "jobs").is_dir()
    for bot in FLEET:
        soul = home / "profiles" / bot.name / "SOUL.md"
        assert soul.is_file()
        text = soul.read_text()
        assert bot.name.upper() in text or bot.title in text
        skills = list((home / "profiles" / bot.name / "skills").iterdir())
        assert skills
