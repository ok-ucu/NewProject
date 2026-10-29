"""Explicit one-shot real Bedrock smoke command. Never called by tests or app startup."""

import json

from app.config import settings
from app.parsing.bedrock import invoke_converse, invoke_messages


def main():
    # Running this command is a deliberate invocation, independent of the app's safety flag.
    if settings.parse_bedrock_api == "converse":
        raw = invoke_converse(
            settings.parse_model_id,
            settings.parse_region,
            "Reply with one short greeting.",
            max_tokens=64,
        )
        payload = {
            "content": [
                block
                for block in raw.get("output", {}).get("message", {}).get("content", [])
                if "text" in block
            ],
            "stop_reason": raw.get("stopReason"),
            "usage": raw.get("usage"),
        }
    else:
        payload = invoke_messages(
            settings.parse_model_id,
            settings.parse_region,
            "Reply with one short greeting.",
            max_tokens=64,
        )
    print(
        json.dumps(
            {
                "response": payload.get("content"),
                "stop_reason": payload.get("stop_reason"),
                "usage": payload.get("usage"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
