"""Standalone parser behind API Gateway JWT authorizer; no DB imports or writes."""

import base64
import json
import logging

from pydantic import ValidationError

from app.parsing.service import (
    ParseError,
    ParseRequest,
    ProviderError,
    get_provider,
    parse_agenda,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event: dict, context: object) -> dict:
    def response(status, body):
        # Never log raw text, tokens, provider errors, or generated meeting fields.
        logger.info(
            json.dumps({"status": status, "request_id": getattr(context, "aws_request_id", None)})
        )
        return {
            "statusCode": status,
            "headers": {"content-type": "application/json"},
            "body": json.dumps(body),
        }

    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    if not claims.get("sub"):
        return response(401, {"detail": "Authentication required"})
    try:
        raw = event.get("body") or ""
        if len(raw) > 100000:
            return response(413, {"detail": "Request too large"})
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw, validate=True).decode("utf-8")
        request = ParseRequest.model_validate_json(raw)
        result = parse_agenda(request, get_provider())
        return response(200, result.model_dump(mode="json"))
    except ValidationError, ValueError, ParseError:
        return response(422, {"detail": "Check text, JSON, dates and IANA timezone"})
    except ProviderError:
        return response(503, {"detail": "Parser provider unavailable"})
