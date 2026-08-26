from pathlib import Path
import json
from grokbots.cli import main

def test_roster_and_run(tmp_path: Path, capsys) -> None:
    assert main(["roster"]) == 0
    capsys.readouterr()
    workspace = str(tmp_path)
    assert main(["run", "--topic", "factory", "--account", "tonywhelan", "--workspace", workspace]) == 0
    out = capsys.readouterr().out
    job = json.loads(out)
    assert job["status"] == "awaiting_human"
    job_id = job["id"]
    token = f"APPROVE:{job_id}:tonywhelan"
    assert main(["approve", "--id", job_id, "--actor", "tonywhelan", "--token", token, "--workspace", workspace]) == 0
    capsys.readouterr()
    assert main(["publish", "--id", job_id, "--actor", "tonywhelan", "--url", "https://x.com/tonywhelan/status/1", "--workspace", workspace]) == 0
    capsys.readouterr()
    assert main(["show", "--id", job_id, "--workspace", workspace]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["status"] == "published"
