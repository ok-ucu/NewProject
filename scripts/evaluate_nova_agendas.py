#!/usr/bin/env python3
"""Run via backend Python/stdin. Default: preflight only; explicit flag permits five calls."""

import argparse
import hashlib
import json
import logging
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.config import settings
from app.parsing import bedrock
from app.parsing.service import (
    PROMPT_VERSION,
    NovaBedrockProvider,
    ParseError,
    ParseRequest,
    ProviderError,
    parse_agenda,
)


def redact(value):
    """Synthetic source/output only; redact recognizable secrets even in hostile output."""
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        patterns = [
            r"(?:AKIA|ASIA)[A-Z0-9]{16}",
            r"gh[pousr]_[A-Za-z0-9]{30,}",
            r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}",
            r"-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?-----END [^-]*PRIVATE KEY-----",
        ]
        for pattern in patterns:
            value = re.sub(pattern, "<redacted-secret>", value)
        return value
    return value


def emit(record):
    print(json.dumps(redact(record), ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-five-paid-calls", action="store_true")
    args = parser.parse_args()
    path = Path("/app/app/parsing/mock_cases.json")
    cases = json.loads(path.read_text())
    assert [c["id"] for c in cases] == [
        "ukrainian",
        "english-email",
        "relative-dates",
        "non-agenda",
        "prompt-injection",
    ]
    assert (
        settings.parse_provider,
        settings.parse_bedrock_api,
        settings.parse_region,
        settings.parse_model_id,
        settings.parse_bedrock_enabled,
    ) == ("bedrock", "converse", "eu-north-1", "eu.amazon.nova-2-lite-v1:0", True), (
        "Backend is not configured for the approved Nova run"
    )
    requests = [
        ParseRequest(**{k: c[k] for k in ["text", "timezone", "reference_date"]}) for c in cases
    ]
    emit(
        {
            "event": "evaluation_preflight",
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "execute": args.confirm_five_paid_calls,
            "max_calls": 5,
            "model": settings.parse_model_id,
            "region": settings.parse_region,
            "prompt_version": PROMPT_VERSION,
            "fixture_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "case_ids": [c["id"] for c in cases],
            "evidence_environment": "local Docker; real Bedrock only with explicit flag",
            "estimated_cost_usd": None,
        }
    )
    if not args.confirm_five_paid_calls:
        return
    # No verified rates: do not emit a misleading configured USD estimate.
    settings.parse_input_usd_per_million = None
    settings.parse_output_usd_per_million = None
    original_transport = bedrock.invoke_converse
    captured = {}

    def transport(*a, **kw):
        payload = original_transport(*a, **kw)  # Same application SDK config; retries=0.
        captured["stop_reason"] = payload.get("stopReason")
        captured["usage"] = payload.get("usage")
        captured["original_model_text"] = "".join(
            b["text"]
            for b in payload.get("output", {}).get("message", {}).get("content", [])
            if isinstance(b, dict) and isinstance(b.get("text"), str)
        )
        return payload

    class CaptureLog(logging.Handler):
        def emit(self, record):
            captured["sanitized_log"] = json.loads(record.getMessage())

    logger = logging.getLogger("app.parsing.service")
    logger.handlers = [CaptureLog()]
    logger.propagate = False
    bedrock.invoke_converse = transport
    for case, request in zip(cases, requests, strict=True):
        captured.clear()
        row = {
            "case_id": case["id"],
            "input": request.model_dump(mode="json"),
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "provider": "bedrock",
            "model": settings.parse_model_id,
            "bedrock_api": "converse",
            "prompt_version": PROMPT_VERSION,
            "estimated_cost_usd": None,
            "final_agenda_saved": False,
            "field_analysis": {
                "status": "pending human review",
                "correct": None,
                "incorrect": None,
                "invented": None,
            },
        }
        try:
            result = parse_agenda(request, NovaBedrockProvider())
            row.update(validation="valid", result=result.model_dump(mode="json"))
        except ParseError:
            row.update(validation="rejected", error_category="agenda_validation_error")
        except ProviderError as exc:
            row.update(
                validation="not_reached",
                error_category="provider_error",
                provider_diagnostics=exc.diagnostics,
            )
        except Exception:
            # Do not dump unexpected exception text or traceback with SDK/private data.
            row.update(validation="not_reached", error_category="unexpected_local_error")
            row.update(captured)
            emit(row)
            return 1
        row.update(captured)
        emit(row)
        # Stop on provider failures: no automatic retries of access/credentials/quota errors.
        if row["validation"] == "not_reached":
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
