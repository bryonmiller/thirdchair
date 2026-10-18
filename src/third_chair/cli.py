"""Command-line interface for Third Chair."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import load_records, render_markdown, summarize_records
from .policies import LinkedVerificationPolicy, POLICY_LABEL, POLICY_NAME
from .runner import ModelSeat
from .scenario import evidence_text, load_scenario
from .tournament import (
    build_model_seats,
    build_schedule,
    configuration_issues,
    estimate_calls,
    load_model_configs,
    run_schedule,
)


ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ROOT / "eval_data" / "scenarios"


def _scenario_paths(value: str) -> list[Path]:
    if value == "port-disclosure":
        return [SCENARIOS / "port-sanctions.json",
                ROOT / "eval_data" / "variants" / "port-sanctions-disclosed.json"]
    if value == "all":
        return sorted(SCENARIOS.glob("*.json"))
    path = Path(value)
    if path.exists():
        return [path]
    candidate = SCENARIOS / f"{value}.json"
    if candidate.exists():
        return [candidate]
    raise ValueError(f"Unknown scenario: {value}")


def _modes(value: str) -> list[str]:
    modes = [item.strip() for item in value.split(",") if item.strip()]
    if not modes or not set(modes) <= {"active", "empty"}:
        raise ValueError("modes must contain active, empty, or both")
    return modes


def _cmd_list(_: argparse.Namespace) -> int:
    for path in sorted(SCENARIOS.glob("*.json")):
        scenario = load_scenario(path)
        print(f"{scenario['id']}\t{scenario['title']}")
    return 0


def _cmd_preview(args: argparse.Namespace) -> int:
    scenario = load_scenario(_scenario_paths(args.scenario)[0])
    print(f"{scenario['title']}\n")
    print(f"{scenario['one_line']}\n")
    for episode in scenario["episodes"]:
        print(f"ROUND {episode['round']} | {episode['clock']}")
        print(episode["public_event"])
        for seat in ("a", "b", "mediator"):
            items = episode["evidence"].get(seat, [])
            if items:
                print(f"\nEvidence to {seat.upper()}:\n{evidence_text(items)}")
        print()
    return 0


def _schedule_from_args(args: argparse.Namespace):
    configs = load_model_configs(args.models)
    return configs, build_schedule(
        scenario_paths=_scenario_paths(args.scenario),
        labels=[item.label for item in configs],
        rotation=args.rotation,
        modes=_modes(args.modes),
        repetitions=args.repetitions,
        seed=args.seed,
        fixed_a=args.actor_a,
        fixed_b=args.actor_b,
        mediator_policy=args.mediator_policy,
        order_seed=args.order_seed,
    )


def _cmd_plan(args: argparse.Namespace) -> int:
    configs, schedule = _schedule_from_args(args)
    print(f"Models: {', '.join(item.label for item in configs)}")
    print(f"Matches: {len(schedule)}")
    print(f"Planned model turns before retries: {estimate_calls(schedule)}")
    active = sum(item["mode"] == "active" for item in schedule)
    empty = sum(item["mode"] == "empty" for item in schedule)
    print(f"Active mediator matches: {active}")
    print(f"Empty-chair matches: {empty}")
    print(f"Mediator policy: {args.mediator_policy}; execution-order seed: {args.order_seed}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    configs, schedule = _schedule_from_args(args)
    issues = configuration_issues(configs)
    if issues:
        raise ValueError("Configuration is not ready:\n" + "\n".join(issues))
    model_seats = build_model_seats(configs)
    if args.mediator_policy == POLICY_NAME:
        model_seats[POLICY_LABEL] = ModelSeat(POLICY_LABEL, LinkedVerificationPolicy(),
                                            temperature=None, max_tokens=1, send_seed=False)
    run_schedule(
        schedule=schedule,
        model_seats=model_seats,
        output=args.output,
    )
    print(f"Wrote {args.output}")
    return 0


def _cmd_check_config(args: argparse.Namespace) -> int:
    configs = load_model_configs(args.models)
    issues = configuration_issues(configs)
    for config in configs:
        print(f"{config.label}: {config.model}; max_tokens={config.max_tokens}; "
              f"temperature={config.temperature}; send_seed={config.send_seed}; "
              f"provider={json.dumps(config.provider)}; reasoning={json.dumps(config.reasoning)}")
    for issue in issues:
        print(f"ACTION REQUIRED: {issue}")
    print("Offline configuration check only. No API calls or credits used. "
          "Model availability and parameter support still require a live smoke run.")
    return 1 if issues else 0


def _cmd_summarize(args: argparse.Namespace) -> int:
    summary = summarize_records(load_records(args.inputs))
    rendered = (
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
        if args.format == "json"
        else render_markdown(summary)
    )
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="third-chair",
        description="Run a rotating three-model cyber-crisis mediation tournament",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-scenarios")
    list_parser.set_defaults(func=_cmd_list)

    preview = subparsers.add_parser("preview")
    preview.add_argument("--scenario", default="grid-vote")
    preview.set_defaults(func=_cmd_preview)

    check = subparsers.add_parser("check-config", help="Check configuration locally without API calls")
    check.add_argument("--models", required=True)
    check.set_defaults(func=_cmd_check_config)

    for command, handler in (("plan", _cmd_plan), ("run", _cmd_run)):
        sub = subparsers.add_parser(command)
        sub.add_argument("--models", required=True)
        sub.add_argument("--scenario", default="all")
        sub.add_argument("--rotation", choices=["balanced", "full"], default="balanced")
        sub.add_argument("--actor-a", help="Fix State A across all mediator candidates")
        sub.add_argument("--actor-b", help="Fix State B across all mediator candidates")
        sub.add_argument("--mediator-policy", choices=["llm", POLICY_NAME], default="llm")
        sub.add_argument("--order-seed", type=int,
                         help="Shuffle paired blocks and condition order reproducibly")
        sub.add_argument("--modes", default="active,empty")
        sub.add_argument("--repetitions", type=int, default=1)
        sub.add_argument("--seed", type=int, default=4100)
        if command == "run":
            sub.add_argument("--output", default="results/matches.jsonl")
        sub.set_defaults(func=handler)

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("inputs", nargs="+")
    summarize.add_argument("--format", choices=["json", "markdown"], default="markdown")
    summarize.add_argument("--output")
    summarize.set_defaults(func=_cmd_summarize)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if getattr(args, "repetitions", 1) < 1:
        raise ValueError("repetitions must be at least one")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
