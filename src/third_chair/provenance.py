"""Public configuration identity. Credentials never belong in a run manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from . import __version__
from .policies import SHARED_PREFIX, SHARED_PROTOCOL_VERSION
from .schema import ACTOR_RESPONSE_CONTRACT

SCORING_VERSION = "baseline-0.4.0"
MAX_TOKENS = 1400


def fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def source_digest() -> str:
    root = Path(__file__).parent
    return fingerprint({p.name: p.read_text(encoding="utf-8") for p in sorted(root.glob("*.py"))})


def shared_protocol_digest() -> str:
    path = Path(__file__).resolve().parents[2] / "docs" / "shared_prefix_protocol.md"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def public_endpoint(url: str | None) -> str | None:
    if not url:
        return None
    parts = urlsplit(url)
    # Drop userinfo, query parameters and fragments, all of which may carry secrets.
    host = parts.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    if parts.port:
        host += f":{parts.port}"
    return urlunsplit((parts.scheme, host, parts.path, "", ""))


def seat_config(seat: Any) -> dict[str, Any]:
    return {
        "label": seat.label,
        "requested_model": seat.client.model,
        "temperature": seat.temperature,
        "max_tokens": seat.max_tokens,
        "send_seed": seat.send_seed,
        "provider": getattr(seat.client, "provider", None),
        "reasoning": getattr(seat.client, "reasoning", None),
        "provider_metadata_required": getattr(seat.client, "provider_metadata_required", False),
        "endpoint": public_endpoint(getattr(seat.client, "url", None)),
        "endpoint_sha256": fingerprint(getattr(seat.client, "url", None)),
        "timeout_seconds": getattr(seat.client, "timeout", None),
        "extra_header_names": sorted(getattr(seat.client, "extra_headers", {})),
        "extra_headers_sha256": fingerprint(getattr(seat.client, "extra_headers", {})),
    }


def run_manifest(
    scenario: dict[str, Any], seats: dict[str, Any], evidence_id_mode: str = "opaque",
    *, order_seed: int | None = None, mediator_policy: str = "llm",
    control_design: str = "independent_matched_runs",
) -> dict[str, Any]:
    value = {
        "package_version": __version__,
        "actor_response_contract": ACTOR_RESPONSE_CONTRACT,
        "scoring_version": SCORING_VERSION,
        "control_design": control_design,
        "evidence_id_mode": evidence_id_mode,
        "execution_order_seed": order_seed,
        "mediator_policy": mediator_policy,
        "source_sha256": source_digest(),
        "scenario_sha256": fingerprint(scenario),
        "roles": {role: seat_config(seat) for role, seat in seats.items()},
    }
    if mediator_policy == SHARED_PREFIX:
        value.update(protocol_version=SHARED_PROTOCOL_VERSION,
                     protocol_sha256=shared_protocol_digest())
    return value | {"configuration_id": fingerprint(value)}


def pair_identity(manifest: dict[str, Any], repetition: int, seed: int | None) -> str:
    return fingerprint({"configuration_id": manifest["configuration_id"],
                        "repetition": repetition, "seed": seed})
