"""Explicit one-shot real Bedrock smoke command. Never called by tests or app startup."""

import json

from app.config import settings
from app.parsing.bedrock import invoke_messages


def main():
    # Running this command is a deliberate invocation, independent of the app's safety flag.
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
