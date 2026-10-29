import json
from types import SimpleNamespace

from app.parsing.lambda_handler import handler
from app.parsing.service import MockProvider
from tests.test_parsing import TEXT


def event(payload):
    return {
        "body": json.dumps(payload),
        "requestContext": {"authorizer": {"jwt": {"claims": {"sub": "test-user"}}}},
    }


def test_lambda_requires_authorizer():
    assert handler({"body": "{}"}, None)["statusCode"] == 401


def test_lambda_mock_no_database(monkeypatch, caplog):
    monkeypatch.setattr("app.parsing.lambda_handler.get_provider", lambda: MockProvider())
    result = handler(
        event({"text": TEXT, "timezone": "Europe/Kyiv"}), SimpleNamespace(aws_request_id="test")
    )
    assert result["statusCode"] == 200
    assert json.loads(result["body"])["draft"]["items"][0]["owner"] == "Олена"
    assert TEXT not in caplog.text
    assert '"status": 200' in caplog.text


def test_lambda_invalid_json_and_timezone():
    broken = event({})
    broken["body"] = "not json"
    assert handler(broken, None)["statusCode"] == 422
    assert handler(event({"text": TEXT, "timezone": "bad/zone"}), None)["statusCode"] == 422


def test_lambda_provider_error(monkeypatch):
    from app.parsing.service import ProviderError

    class Unavailable:
        name = "bedrock"
        model_id = "test-only"

        def complete(self, request):
            raise ProviderError("private AWS error")

    monkeypatch.setattr("app.parsing.lambda_handler.get_provider", lambda: Unavailable())
    result = handler(event({"text": TEXT}), None)
    assert result["statusCode"] == 503
    assert "private AWS error" not in result["body"]


def test_lambda_rejects_invalid_base64():
    request = event({})
    request.update(body="!not-base64!", isBase64Encoded=True)
    assert handler(request, None)["statusCode"] == 422


def test_lambda_rejects_oversized_body():
    request = event({})
    request["body"] = "x" * 100001
    assert handler(request, None)["statusCode"] == 413
