import json

import pytest
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    ParamValidationError,
    ReadTimeoutError,
)

from app.config import settings
from app.parsing.errors import safe_provider_error
from app.parsing.service import NovaBedrockProvider, ParseRequest, ProviderError, parse_agenda
from tests.test_parsing import TEXT


@pytest.mark.parametrize(
    "code,category",
    [
        ("ThrottlingException", "throttling"),
        ("ServiceQuotaExceededException", "quota"),
        ("AccessDeniedException", "authorization_or_model_access"),
        ("ExpiredTokenException", "credentials_expired_or_invalid"),
        ("ValidationException", "invalid_request_or_model_profile"),
        ("ResourceNotFoundException", "model_or_profile_not_found"),
    ],
)
def test_safe_client_error_metadata(code, category, monkeypatch, caplog):
    monkeypatch.setattr(settings, "parse_bedrock_enabled", True)
    error = ClientError(
        {
            "Error": {"Code": code, "Message": "PRIVATE prompt secret token"},
            "ResponseMetadata": {
                "HTTPStatusCode": 429,
                "RequestId": "test-request-123",
                "HTTPHeaders": {"authorization": "PRIVATE credential"},
            },
        },
        "Converse",
    )

    def fail(*args):
        raise error

    monkeypatch.setattr("app.parsing.bedrock.invoke_converse", fail)
    with pytest.raises(ProviderError) as caught:
        parse_agenda(ParseRequest(text=TEXT), NovaBedrockProvider())
    log = [json.loads(r.message) for r in caplog.records if r.name == "app.parsing.service"][-1]
    assert log["aws_error_code"] == code
    assert log["aws_http_status"] == 429 and log["aws_request_id"] == "test-request-123"
    assert log["error_category"] == category and log["status"] == "provider_error"
    assert log["input_tokens"] is None and log["output_tokens"] is None
    assert "PRIVATE" not in caplog.text and TEXT not in caplog.text
    assert "PRIVATE" not in str(caught.value)


@pytest.mark.parametrize(
    "error,category",
    [
        (ReadTimeoutError(endpoint_url="https://PRIVATE.invalid"), "network_timeout"),
        (NoCredentialsError(), "credentials_unavailable"),
        (ParamValidationError(report="PRIVATE input"), "local_request_validation"),
        (KeyError("PRIVATE generated data"), "invalid_response"),
        (BotoCoreError(), "sdk_error"),
    ],
)
def test_safe_sdk_categories(error, category):
    result = safe_provider_error(error)
    assert result["error_category"] == category
    assert result["aws_request_id"] is None and result["aws_http_status"] is None
    assert "PRIVATE" not in json.dumps(result)


def test_unknown_aws_fields_are_not_logged():
    error = ClientError(
        {
            "Error": {"Code": "PRIVATE-value", "Message": "PRIVATE"},
            "ResponseMetadata": {"HTTPStatusCode": "PRIVATE", "RequestId": "PRIVATE\nprompt"},
        },
        "Converse",
    )
    result = safe_provider_error(error)
    assert result["aws_error_code"] == "UnknownClientError"
    assert result["aws_request_id"] is None and result["aws_http_status"] is None
    assert "PRIVATE" not in json.dumps(result)
