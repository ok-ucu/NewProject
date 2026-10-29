import json
from types import SimpleNamespace

import pytest

from app.config import Settings, settings
from app.parsing.service import (
    PROMPT_VERSION,
    Completion,
    MockProvider,
    ParseError,
    ParseRequest,
    ProviderError,
    parse_agenda,
)
from tests.test_api import meeting_payload
from tests.test_parsing import CASES, TEXT


@pytest.mark.parametrize(
    "new,old,expected",
    [
        ("new-profile", "legacy-profile", "new-profile"),
        (None, "legacy-profile", "legacy-profile"),
    ],
)
def test_parser_model_env_aliases(monkeypatch, new, old, expected):
    monkeypatch.delenv("PARSER_MODEL", raising=False)
    if new:
        monkeypatch.setenv("PARSER_MODEL", new)
    monkeypatch.setenv("PARSE_MODEL_ID", old)
    assert Settings(_env_file=None).parse_model_id == expected


def records(caplog):
    return [json.loads(r.message) for r in caplog.records if r.name == "app.parsing.service"]


def test_mock_json_metrics(caplog):
    result = parse_agenda(ParseRequest(text=TEXT), MockProvider())
    log = records(caplog)[-1]
    assert log["provider"] == "mock"
    assert log["prompt_version"] == result.metrics.prompt_version == PROMPT_VERSION
    assert log["model"] == "local-agenda-fixtures-v1"
    assert log["input_tokens"] is None and log["output_tokens"] is None
    assert log["estimated_cost_usd"] == 0
    assert log["latency_ms"] >= 0
    assert TEXT not in caplog.text


def test_validation_error_keeps_actual_usage(caplog, monkeypatch):
    monkeypatch.setattr(settings, "parse_input_usd_per_million", None)
    monkeypatch.setattr(settings, "parse_output_usd_per_million", None)

    class Fake:
        name = "bedrock"
        model_id = "test-only"

        def complete(self, request):
            return Completion("invalid JSON", 123, 45)

    with pytest.raises(ParseError):
        parse_agenda(ParseRequest(text=TEXT), Fake())
    log = records(caplog)[-1]
    assert log["status"] == "validation_error"
    assert log["input_tokens"] == 123 and log["output_tokens"] == 45
    assert log["estimated_cost_usd"] is None


def test_provider_error_unknown_usage(caplog):
    class Fake:
        name = "bedrock"
        model_id = "test-only"

        def complete(self, request):
            raise ProviderError("private error")

    with pytest.raises(ProviderError):
        parse_agenda(ParseRequest(text=TEXT), Fake())
    log = records(caplog)[-1]
    assert log["status"] == "provider_error"
    assert log["input_tokens"] is None and log["estimated_cost_usd"] is None
    assert "private error" not in caplog.text


def test_hello_prints_returned_fields_without_network(monkeypatch, capsys):
    from app.parsing import hello

    def fake(model, region, prompt, max_tokens):
        assert model == "configured-profile" and max_tokens == 64
        return {
            "content": [{"type": "text", "text": "hello fixture"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 7, "output_tokens": 2},
        }

    monkeypatch.setattr(settings, "parse_model_id", "configured-profile")
    monkeypatch.setattr(hello, "invoke_messages", fake)
    hello.main()
    result = json.loads(capsys.readouterr().out)
    assert result["stop_reason"] == "end_turn"
    assert result["usage"] == {"input_tokens": 7, "output_tokens": 2}
    assert result["response"][0]["text"] == "hello fixture"


def test_messages_transport_with_fake_client(monkeypatch):
    import io
    import sys

    from app.parsing.bedrock import invoke_messages

    def invoke(**kwargs):
        assert kwargs["modelId"] == "configured-profile"
        body = json.loads(kwargs["body"])
        assert body["anthropic_version"] == "bedrock-2023-05-31"
        assert body["messages"][0]["content"] == "fixture"
        return {"body": io.BytesIO(b'{"stop_reason":"end_turn"}')}

    monkeypatch.setitem(
        sys.modules,
        "boto3",
        SimpleNamespace(client=lambda *args, **kwargs: SimpleNamespace(invoke_model=invoke)),
    )
    assert (
        invoke_messages("configured-profile", "eu-north-1", "fixture")["stop_reason"] == "end_turn"
    )


async def test_manual_save_after_provider_error(client, monkeypatch):
    from app.main import app
    from app.parsing.service import get_provider

    class Broken:
        name = "bedrock"
        model_id = "fake"

        def complete(self, request):
            raise ProviderError("Bedrock unavailable")

    app.dependency_overrides[get_provider] = lambda: Broken()
    meeting = (await client.post("/api/meetings", json=meeting_payload())).json()
    url = f"/api/meetings/{meeting['id']}/agenda"
    assert (await client.post(url + "/parse", json={"text": TEXT})).status_code == 503
    assert (await client.get(f"/api/meetings/{meeting['id']}")).json()["agenda"] is None
    saved = await client.put(
        url, json={"agenda": CASES[0]["expected_agenda"], "ai_suggestion": None}
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["ai_suggestion"] is None
    assert saved.json()["agenda"] == CASES[0]["expected_agenda"]
    assert len((await client.get("/api/meetings")).json()) == 1
