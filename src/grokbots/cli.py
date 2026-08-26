from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .fleet import FLEET, fleet_dict
from .install import install_fleet
from .models import Brief
from .pipeline import Pipeline

def _pipeline(ns: argparse.Namespace) -> Pipeline:
    return Pipeline(Path(ns.workspace))

def cmd_roster(_: argparse.Namespace) -> int:
    for bot in FLEET:
        print(f"{bot.name:8} {bot.title:16} grok={bot.grok_role:18} publish={bot.may_publish}")
    return 0

def cmd_map(_: argparse.Namespace) -> int:
    print(json.dumps(fleet_dict(), indent=2))
    return 0

def cmd_run(ns: argparse.Namespace) -> int:
    brief = Brief(topic=ns.topic, account=ns.account, channel=ns.channel)
    pipe = _pipeline(ns)
    job = pipe.run_until_gate(brief)
    print(job.dump())
    print(f"status={job.status.value} id={job.id}", file=sys.stderr)
    if job.status.value == "awaiting_human":
        print(f"approve with: grokbots approve --id {job.id} --actor {ns.account} --token APPROVE:{job.id}:{ns.account}", file=sys.stderr)
    return 0

def cmd_approve(ns: argparse.Namespace) -> int:
    pipe = _pipeline(ns)
    job = pipe.load(ns.id)
    job = pipe.approve(job, ns.actor, ns.token)
    print(job.dump())
    return 0

def cmd_publish(ns: argparse.Namespace) -> int:
    pipe = _pipeline(ns)
    job = pipe.load(ns.id)
    job = pipe.mark_published(job, ns.actor, ns.url)
    print(job.dump())
    return 0

def cmd_show(ns: argparse.Namespace) -> int:
    pipe = _pipeline(ns)
    job = pipe.load(ns.id)
    print(job.dump())
    return 0

def cmd_install(ns: argparse.Namespace) -> int:
    actions = install_fleet(Path(ns.hermes_home), dry_run=ns.dry_run)
    for line in actions:
        print(line)
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="grokbots", description="Hermes mapping of the Grok Bot content factory.")
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--workspace", default="./workspace")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("roster", parents=[parent]).set_defaults(func=cmd_roster)
    sub.add_parser("map", parents=[parent]).set_defaults(func=cmd_map)
    run = sub.add_parser("run", parents=[parent])
    run.add_argument("--topic", required=True)
    run.add_argument("--account", required=True)
    run.add_argument("--channel", default="x")
    run.set_defaults(func=cmd_run)
    ap = sub.add_parser("approve", parents=[parent])
    ap.add_argument("--id", required=True)
    ap.add_argument("--actor", required=True)
    ap.add_argument("--token", required=True)
    ap.set_defaults(func=cmd_approve)
    pb = sub.add_parser("publish", parents=[parent])
    pb.add_argument("--id", required=True)
    pb.add_argument("--actor", required=True)
    pb.add_argument("--url", required=True)
    pb.set_defaults(func=cmd_publish)
    sh = sub.add_parser("show", parents=[parent])
    sh.add_argument("--id", required=True)
    sh.set_defaults(func=cmd_show)
    inst = sub.add_parser("install", parents=[parent])
    inst.add_argument("--hermes-home", default="~/.hermes")
    inst.add_argument("--dry-run", action="store_true")
    inst.set_defaults(func=cmd_install)
    return p

def main(argv: list[str] | None = None) -> int:
    ns = build_parser().parse_args(argv)
    return ns.func(ns)

if __name__ == "__main__":
    raise SystemExit(main())
