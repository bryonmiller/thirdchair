"""Tournament schedule, model configuration, call planning, and resumable execution."""

from __future__ import annotations

import itertools
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .client import OpenAICompatibleClient
from .runner import ModelSeat, run_match
from .scenario import load_scenario


@dataclass(frozen=True)
class ModelConfig:
    label: str
    base_url: str
    model: str
    api_key_env: str
    temperature: float
    extra_headers: dict[str, str]


def load_model_configs(path: str | Path) -> list[ModelConfig]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_models = data.get("models")
    if not isinstance(raw_models, list) or len(raw_models) < 3:
        raise ValueError("The tournament requires at least three configured models")
    configs: list[ModelConfig] = []
    for item in raw_models:
        configs.append(
            ModelConfig(
                label=str(item["label"]),
                base_url=str(item["base_url"]),
                model=str(item["model"]),
                api_key_env=str(item["api_key_env"]),
                temperature=float(item.get("temperature", 0.2)),
                extra_headers=dict(item.get("extra_headers") or {}),
            )
        )
    labels = [item.label for item in configs]
    if len(labels) != len(set(labels)):
        raise ValueError("Model labels must be unique")
    return configs


def build_model_seats(configs: list[ModelConfig]) -> dict[str, ModelSeat]:
    seats: dict[str, ModelSeat] = {}
    for config in configs:
        api_key = os.environ.get(config.api_key_env)
        if not api_key:
            raise ValueError(f"Required environment variable is not set: {config.api_key_env}")
        seats[config.label] = ModelSeat(
            label=config.label,
            client=OpenAICompatibleClient(
                base_url=config.base_url,
                api_key=api_key,
                model=config.model,
                extra_headers=config.extra_headers,
            ),
            temperature=config.temperature,
        )
    return seats


def assignments(labels: list[str], rotation: str, reverse: bool = False) -> list[tuple[str, str, str]]:
    if rotation not in {"balanced", "full"}:
        raise ValueError("rotation must be balanced or full")
    result: list[tuple[str, str, str]] = []
    for trio in itertools.combinations(sorted(labels), 3):
        if rotation == "full":
            result.extend(itertools.permutations(trio, 3))
            continue
        x, y, z = trio
        if reverse:
            result.extend([(y, x, z), (z, y, x), (x, z, y)])
        else:
            result.extend([(x, y, z), (y, z, x), (z, x, y)])
    return result


def build_schedule(
    *,
    scenario_paths: Iterable[str | Path],
    labels: list[str],
    rotation: str,
    modes: list[str],
    repetitions: int,
    seed: int | None,
) -> list[dict[str, Any]]:
    if not modes or not set(modes) <= {"active", "empty"}:
        raise ValueError("modes must contain active, empty, or both")
    schedule: list[dict[str, Any]] = []
    paths = [Path(path) for path in scenario_paths]
    for scenario_index, scenario_path in enumerate(paths):
        scenario = load_scenario(scenario_path)
        role_sets = assignments(labels, rotation, reverse=bool(scenario_index % 2))
        for repetition in range(1, repetitions + 1):
            for assignment_index, (a, b, mediator) in enumerate(role_sets):
                pair_seed = (
                    None
                    if seed is None
                    else seed
                    + scenario_index * 1_000_000
                    + repetition * 10_000
                    + assignment_index * 100
                )
                for mode in modes:
                    match_id = (
                        f"{scenario['id']}__a-{a}__b-{b}__m-{mediator}__"
                        f"r{repetition:02d}__{mode}"
                    )
                    schedule.append(
                        {
                            "match_id": match_id,
                            "scenario_path": scenario_path,
                            "scenario_id": scenario["id"],
                            "rounds": int(scenario["rounds"]),
                            "a": a,
                            "b": b,
                            "mediator": mediator,
                            "mode": mode,
                            "repetition": repetition,
                            "seed": pair_seed,
                        }
                    )
    return schedule


def estimate_calls(schedule: list[dict[str, Any]]) -> int:
    total = 0
    for item in schedule:
        per_round = 5 if item["mode"] == "active" else 4
        total += int(item["rounds"]) * per_round
    return total


def _existing_match_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    result: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if value.get("match_id"):
                result.add(value["match_id"])
    return result


def run_schedule(
    *,
    schedule: list[dict[str, Any]],
    model_seats: dict[str, ModelSeat],
    output: str | Path,
) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = _existing_match_ids(output_path)
    remaining = [item for item in schedule if item["match_id"] not in completed]
    for index, item in enumerate(remaining, 1):
        print(
            f"[{index}/{len(remaining)}] {item['scenario_id']} | {item['mode']} | "
            f"A={item['a']} B={item['b']} M={item['mediator']}"
        )
        record = run_match(
            scenario_path=item["scenario_path"],
            model_a=model_seats[item["a"]],
            model_b=model_seats[item["b"]],
            mediator_model=model_seats[item["mediator"]],
            mode=item["mode"],
            repetition=item["repetition"],
            seed=item["seed"],
        )
        record["match_id"] = item["match_id"]
        with output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

