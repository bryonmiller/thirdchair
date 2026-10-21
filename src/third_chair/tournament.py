"""Tournament schedule, model configuration, call planning, and resumable execution."""

from __future__ import annotations

import itertools
import json
import math
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .client import OpenAICompatibleClient, is_openrouter
from .policies import (POLICY_LABEL, POLICY_NAME, DELAYED_LABEL, DELAYED_MESSAGE,
                       DELAYED_VERIFICATION, POST_VERIFICATION_STUDY, validate_delayed_scenario)
from .runner import ModelSeat, run_match
from .provenance import MAX_TOKENS, fingerprint, pair_identity, run_manifest, seat_config, source_digest
from .scenario import load_scenario


@dataclass(frozen=True)
class ModelConfig:
    label: str
    base_url: str
    model: str
    api_key_env: str
    temperature: float | None
    extra_headers: dict[str, str]
    max_tokens: int = MAX_TOKENS
    send_seed: bool = True
    timeout: int = 180
    provider: dict[str, Any] | None = None
    reasoning: dict[str, Any] | None = None


def _positive_int(value: Any, name: str) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _validate_model_config(item: dict[str, Any]) -> None:
    if not isinstance(item, dict):
        raise ValueError("Each model configuration must be an object")
    unknown = set(item) - set(ModelConfig.__dataclass_fields__)
    if unknown:
        raise ValueError(f"Unknown model configuration fields: {', '.join(sorted(unknown))}")
    for name in ("label", "base_url", "model", "api_key_env"):
        if not isinstance(item.get(name), str) or not item[name].strip():
            raise ValueError(f"{name} must be a non-empty string")
    temperature = item.get("temperature", 0.2)
    if temperature is not None and (
        type(temperature) not in {int, float} or not math.isfinite(temperature)
        or not 0 <= temperature <= 2
    ):
        raise ValueError("temperature must be null or a finite number from 0 to 2")
    _positive_int(item.get("max_tokens", MAX_TOKENS), "max_tokens")
    _positive_int(item.get("timeout", 180), "timeout")
    if type(item.get("send_seed", True)) is not bool:
        raise ValueError("send_seed must be a boolean")
    headers = item.get("extra_headers", {})
    if not isinstance(headers, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in headers.items()
    ):
        raise ValueError("extra_headers must map strings to strings")
    provider = item.get("provider")
    if provider is not None:
        if not isinstance(provider, dict) or set(provider) - {
            "only", "order", "allow_fallbacks", "require_parameters"
        }:
            raise ValueError("provider supports only, order, allow_fallbacks and require_parameters")
        for name in ("only", "order"):
            if name in provider and (
                not isinstance(provider[name], list) or not provider[name]
                or not all(isinstance(v, str) and v.strip() for v in provider[name])
                or len(set(provider[name])) != len(provider[name])
            ):
                raise ValueError(f"provider.{name} must be a non-empty list of unique slugs")
        for name in ("allow_fallbacks", "require_parameters"):
            if name in provider and type(provider[name]) is not bool:
                raise ValueError(f"provider.{name} must be a boolean")
    reasoning = item.get("reasoning")
    if reasoning is not None:
        if not isinstance(reasoning, dict) or set(reasoning) - {"effort", "max_tokens", "enabled", "exclude"}:
            raise ValueError("reasoning supports effort, max_tokens, enabled and exclude")
        for name in ("enabled", "exclude"):
            if name in reasoning and type(reasoning[name]) is not bool:
                raise ValueError(f"reasoning.{name} must be a boolean")
        if "effort" in reasoning and reasoning["effort"] not in (
            "none", "minimal", "low", "medium", "high", "xhigh", "max"
        ):
            raise ValueError("Unknown reasoning.effort")
        if "effort" in reasoning and "max_tokens" in reasoning:
            raise ValueError("Use reasoning.effort or reasoning.max_tokens, not both")
        if "max_tokens" in reasoning:
            _positive_int(reasoning["max_tokens"], "reasoning.max_tokens")
            if reasoning["max_tokens"] >= item.get("max_tokens", MAX_TOKENS):
                raise ValueError("max_tokens must exceed reasoning.max_tokens to leave output room")
        if reasoning.get("enabled") is False and (
            "max_tokens" in reasoning or reasoning.get("effort", "none") != "none"
        ):
            raise ValueError("Disabled reasoning conflicts with the requested reasoning budget")


def load_model_configs(path: str | Path) -> list[ModelConfig]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"models"}:
        raise ValueError("Model configuration must be an object containing only models")
    raw_models = data.get("models")
    if not isinstance(raw_models, list) or len(raw_models) < 3:
        raise ValueError("The tournament requires at least three configured models")
    configs: list[ModelConfig] = []
    for item in raw_models:
        _validate_model_config(item)
        configs.append(
            ModelConfig(
                label=str(item["label"]),
                base_url=str(item["base_url"]),
                model=str(item["model"]),
                api_key_env=str(item["api_key_env"]),
                temperature=item.get("temperature", 0.2),
                extra_headers=dict(item.get("extra_headers") or {}),
                max_tokens=item.get("max_tokens", MAX_TOKENS),
                send_seed=item.get("send_seed", True),
                timeout=item.get("timeout", 180),
                provider=item.get("provider"),
                reasoning=item.get("reasoning"),
            )
        )
    labels = [item.label for item in configs]
    if len(labels) != len(set(labels)):
        raise ValueError("Model labels must be unique")
    return configs


def configuration_issues(configs: list[ModelConfig]) -> list[str]:
    """Offline checks only: live availability and parameter support need a smoke run."""
    issues = []
    for config in configs:
        if "replace-with" in config.model.lower():
            issues.append(f"{config.label}: replace the placeholder with an exact model ID")
        if not os.environ.get(config.api_key_env):
            issues.append(f"{config.label}: environment variable {config.api_key_env} is not set")
        if is_openrouter(config.base_url):
            provider = config.provider or {}
            only = provider.get("only", [])
            if len(only) != 1 or any("replace-with" in slug.lower() for slug in only):
                issues.append(f"{config.label}: pin one provider endpoint with provider.only")
            if provider.get("allow_fallbacks") is not False:
                issues.append(f"{config.label}: set provider.allow_fallbacks to false")
            if provider.get("require_parameters") is not True:
                issues.append(f"{config.label}: set provider.require_parameters to true")
            if config.model.startswith("openrouter/") or any(
                token in config.model.lower() for token in (":nitro", ":floor", ":free", "latest")
            ):
                issues.append(f"{config.label}: use a fixed model ID without an automatic routing alias")
            if any(name.lower() == "x-openrouter-metadata" and value.lower() != "enabled"
                   for name, value in config.extra_headers.items()):
                issues.append(f"{config.label}: X-OpenRouter-Metadata must be enabled")
    return issues


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
                provider=config.provider,
                reasoning=config.reasoning,
                timeout=config.timeout,
            ),
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            send_seed=config.send_seed,
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
    fixed_a: str | None = None,
    fixed_b: str | None = None,
    mediator_policy: str = "llm",
    mediator_label: str | None = None,
    order_seed: int | None = None,
    complete_panel: bool = False,
) -> list[dict[str, Any]]:
    if repetitions < 1:
        raise ValueError("repetitions must be at least one")
    if len(labels) != len(set(labels)) or len(labels) < 3:
        raise ValueError("Use at least three distinct model labels")
    if bool(fixed_a) != bool(fixed_b):
        raise ValueError("Specify both fixed actor labels")
    if fixed_a and (fixed_a not in labels or fixed_b not in labels):
        raise ValueError("Fixed actors must be configured model labels")
    if mediator_policy not in {"llm", POLICY_NAME, DELAYED_MESSAGE,
                               DELAYED_VERIFICATION, POST_VERIFICATION_STUDY}:
        raise ValueError("Unknown mediator policy")
    if {POLICY_LABEL, DELAYED_LABEL} & set(labels):
        raise ValueError("Configured model labels cannot use reserved policy labels")
    if mediator_policy != "llm" and not fixed_a:
        raise ValueError("Scheduled or scripted mediation requires fixed actors")
    if mediator_label and (not fixed_a or mediator_label not in labels):
        raise ValueError("A selected mediator requires fixed actors and a configured label")
    if mediator_policy in {POLICY_NAME, DELAYED_VERIFICATION} and mediator_label:
        raise ValueError("A scripted-only policy does not select an LLM mediator")
    if mediator_policy in {DELAYED_MESSAGE, POST_VERIFICATION_STUDY} and (
        not mediator_label or len({fixed_a, fixed_b, mediator_label}) != 3
    ):
        raise ValueError("The post-verification study requires three distinct fixed model labels")
    if not modes or len(modes) != len(set(modes)) or not set(modes) <= {"active", "empty"}:
        raise ValueError("modes must contain active, empty, or both")
    schedule: list[dict[str, Any]] = []
    paths = [Path(path) for path in scenario_paths]
    if not paths or len({p.resolve() for p in paths}) != len(paths):
        raise ValueError("Use a non-empty list of distinct scenario paths")
    if complete_panel:
        from .panel import validate_panel_inputs
        validate_panel_inputs(paths, labels, rotation, modes, repetitions, seed,
                              order_seed, fixed_a, fixed_b, mediator_policy, mediator_label)
        paths.sort(key=lambda p: str(p.resolve()))
        modes = ["active", "empty"]
    scenario_ids: set[str] = set()
    family_indices: dict[str, int] = {}
    for scenario_index, scenario_path in enumerate(paths):
        scenario = load_scenario(scenario_path)
        if scenario["id"] in scenario_ids:
            raise ValueError("Scenario IDs must be unique within a schedule")
        scenario_ids.add(scenario["id"])
        family = scenario.get("design", {}).get("family_id", scenario["id"])
        family_index = family_indices.setdefault(family, len(family_indices))
        if mediator_policy in {DELAYED_MESSAGE, DELAYED_VERIFICATION, POST_VERIFICATION_STUDY}:
            validate_delayed_scenario(scenario)
        if mediator_policy == POST_VERIFICATION_STUDY:
            role_sets = [(fixed_a, fixed_b, mediator_label, DELAYED_MESSAGE),
                         (fixed_a, fixed_b, DELAYED_LABEL, DELAYED_VERIFICATION)]
        else:
            mediator_labels = ([POLICY_LABEL] if mediator_policy == POLICY_NAME else
                               [DELAYED_LABEL] if mediator_policy == DELAYED_VERIFICATION else
                               [mediator_label] if mediator_label else sorted(labels))
            assignments_for_case = ([(fixed_a, fixed_b, label) for label in mediator_labels] if fixed_a else
                                    assignments(labels, rotation, reverse=bool(scenario_index % 2)))
            role_sets = [(*roles, mediator_policy) for roles in assignments_for_case]
        for repetition in range(1, repetitions + 1):
            for assignment_index, (a, b, mediator, policy) in enumerate(role_sets):
                pair_seed = (
                    None
                    if seed is None
                    else seed
                    + family_index * 1_000_000
                    + repetition * 10_000
                    + (0 if fixed_a else assignment_index) * 100
                )
                if complete_panel:
                    # One mapping per family/repetition, shared by all truth cells,
                    # role permutations and arms. No collisions at >100 repeats.
                    pair_seed = seed + family_index * repetitions + repetition - 1
                for mode in modes:
                    identity = fingerprint({"scenario": scenario, "seed": pair_seed,
                                            "roles": [a, b, mediator], "repetition": repetition,
                                            "mediator_policy": policy})
                    match_id = (
                        f"{scenario['id']}__a-{a}__b-{b}__m-{mediator}__"
                        f"r{repetition:02d}__{identity[:16]}__{mode}"
                    )
                    schedule.append(
                        {
                            "match_id": match_id,
                            "scenario_path": scenario_path,
                            "scenario_id": scenario["id"],
                            "scenario_sha256": fingerprint(scenario),
                            "rounds": int(scenario["rounds"]),
                            "a": a,
                            "b": b,
                            "mediator": mediator,
                            "mode": mode,
                            "repetition": repetition,
                            "seed": pair_seed,
                            "mediator_policy": policy,
                            "order_seed": order_seed,
                        }
                    )
                    if complete_panel:
                        schedule[-1]["coverage_design"] = "factorial24-full-v1"
    if order_seed is not None:
        # Keep paired conditions adjacent, randomize pair order and within-pair order.
        blocks = [schedule[i:i + len(modes)] for i in range(0, len(schedule), len(modes))]
        rng = random.Random(order_seed)
        rng.shuffle(blocks)
        for block in blocks:
            rng.shuffle(block)
        schedule = [item for block in blocks for item in block]
    return schedule


def estimate_calls(schedule: list[dict[str, Any]]) -> int:
    total = 0
    for item in schedule:
        total += int(item["rounds"]) * 4
        if item["mode"] == "active":
            policy = item.get("mediator_policy", "llm")
            total += int(item["rounds"]) if policy == "llm" else int(policy == DELAYED_MESSAGE)
    return total


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Incomplete JSONL at {path}:{number}; preserve it and use a new output") from exc
    return records


def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def run_schedule(
    *, schedule: list[dict[str, Any]], model_seats: dict[str, ModelSeat],
    output: str | Path,
    coverage_contract: dict[str, Any] | None = None,
) -> None:
    if coverage_contract is not None or any(row.get("coverage_design") for row in schedule):
        from .panel import validate_panel_schedule
        validate_panel_schedule(schedule, coverage_contract)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    events_path = output_path.with_suffix(output_path.suffix + ".events.jsonl")
    existing = _read_jsonl(output_path)
    completed: set[str] = set()
    source_hash = source_digest()
    order_seeds = {item.get("order_seed") for item in schedule}
    policies = {item.get("mediator_policy", "llm") for item in schedule}
    if len(order_seeds) != 1:
        raise ValueError("Use one execution-order seed per schedule")
    for record in existing:
        if (coverage_contract is not None
                and record.get("coverage_contract_sha256") != fingerprint(coverage_contract)):
            raise ValueError("Complete-panel coverage contract changed; use a new output")
        if record.get("run_status") not in {"succeeded", "failed"}:
            raise ValueError("Output contains an unfinished match; preserve it and use a new output")
        manifest = record.get("manifest")
        if not manifest or manifest.get("source_sha256") != source_hash:
            raise ValueError("Output has missing/incompatible provenance; use a new output path")
        if manifest.get("execution_order_seed") not in order_seeds:
            raise ValueError("Execution-order seed changed; use a new output path")
        if manifest.get("mediator_policy", "llm") not in policies:
            raise ValueError("Mediator policy changed; use a new output path")
        for role in ("a", "b", "mediator"):
            previous = manifest["roles"][role]
            label = previous["label"]
            if label not in model_seats or previous != seat_config(model_seats[label]):
                raise ValueError("Model configuration changed; use a new output path")
        match_id = record.get("match_id")
        if not match_id or match_id in completed:
            raise ValueError("Output has missing or duplicate match IDs")
        completed.add(match_id)
    interrupted = {event["match_id"] for event in _read_jsonl(events_path)} - completed
    if interrupted:
        raise ValueError("Interrupted calls exist in the event journal; preserve them and use a new output/repetition")

    bound = []
    for item in schedule:
        scenario = load_scenario(item["scenario_path"])
        if fingerprint(scenario) != item["scenario_sha256"]:
            raise ValueError("Scenario changed after planning; rebuild the schedule")
        manifest = run_manifest(scenario, {role: model_seats[item[role]] for role in ("a", "b", "mediator")},
                                order_seed=item.get("order_seed"),
                                mediator_policy=item.get("mediator_policy", "llm"))
        for previous in existing:
            if previous["scenario_id"] == item["scenario_id"] and previous["manifest"]["scenario_sha256"] != manifest["scenario_sha256"]:
                raise ValueError("Scenario changed; use a new output path")
        match_id = f"{pair_identity(manifest, item['repetition'], item['seed'])}__{item['mode']}"
        bound.append(item | {"match_id": match_id})
    if len({item["match_id"] for item in bound}) != len(bound):
        raise ValueError("Schedule contains duplicate match identities")
    remaining = [item for item in bound if item["match_id"] not in completed]
    for index, item in enumerate(remaining, 1):
        print(f"[{index}/{len(remaining)}] {item['scenario_id']} | {item['mode']} | "
              f"A={item['a']} B={item['b']} M={item['mediator']}")
        record = run_match(
            scenario_path=item["scenario_path"], model_a=model_seats[item["a"]],
            model_b=model_seats[item["b"]], mediator_model=model_seats[item["mediator"]],
            mode=item["mode"], repetition=item["repetition"], seed=item["seed"],
            order_seed=item.get("order_seed"),
            mediator_policy=item.get("mediator_policy", "llm"),
            event_sink=lambda event: _append_jsonl(events_path, event),
        )
        if record["match_id"] != item["match_id"]:
            raise RuntimeError("Configuration changed during execution; inspect the event journal")
        record["execution_position"] = next(i for i, row in enumerate(bound, 1)
                                            if row["match_id"] == item["match_id"])
        if coverage_contract is not None:
            record["coverage_contract_sha256"] = fingerprint(coverage_contract)
        _append_jsonl(output_path, record)
