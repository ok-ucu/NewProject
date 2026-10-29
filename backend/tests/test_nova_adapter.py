import copy
import json
import sys
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError, ReadTimeoutError

from app.config import Settings, settings
from app.parsing.service import (
    BedrockProvider,
    MockProvider,
    NovaBedrockProvider,
    ParseError,
    ParseRequest,
    ProviderError,
    get_provider,
    parse_agenda,
)
from tests.test_api import meeting_payload
from tests.test_parsing import CASES, TEXT


def response(text=None, stop="end_turn"):
    return {
        "output": {
            "message": {
                "content": [
                    {"reasoningContent": {"redactedContent": b"test"}},
                    {"text": text if text is not None else json.dumps(CASES[0]["expected_agenda"])},
                ]
            }
        },
        "stopReason": stop,
        "usage": {"inputTokens": 900, "outputTokens": 120},
    }


@pytest.fixture
def nova(monkeypatch):
    monkeypatch.setattr(settings, "parse_bedrock_enabled", True)
    monkeypatch.setattr(settings, "parse_model_id", "test-configured-profile")
    return NovaBedrockProvider()


def test_selection_and_configuration(monkeypatch):
    monkeypatch.setattr(settings, "parse_provider", "bedrock")
    monkeypatch.setattr(settings, "parse_bedrock_api", "converse")
    assert isinstance(get_provider(), NovaBedrockProvider)
    monkeypatch.setattr(settings, "parse_bedrock_api", "anthropic")
    assert type(get_provider()) is BedrockProvider
    monkeypatch.setattr(settings, "parse_provider", "mock")
    assert isinstance(get_provider(), MockProvider)
    monkeypatch.setenv("PARSE_BEDROCK_API", "converse")
    assert Settings(_env_file=None).parse_bedrock_api == "converse"


def test_disabled_before_any_client(monkeypatch):
    monkeypatch.setattr(settings, "parse_bedrock_enabled", False)

    def forbidden(*a, **kw):
        pytest.fail("AWS must not be called")

    monkeypatch.setitem(sys.modules, "boto3", SimpleNamespace(client=forbidden))
    with pytest.raises(ProviderError, match="disabled"):
        NovaBedrockProvider().complete(ParseRequest(text=TEXT))


def test_converse_transport_fake_client(monkeypatch):
    from app.parsing.bedrock import invoke_converse

    def converse(**kwargs):
        assert kwargs == {
            "modelId": "test-configured-profile",
            "messages": [{"role": "user", "content": [{"text": "test prompt"}]}],
            "inferenceConfig": {"maxTokens": 1024},
        }
        return response()

    def client(name, **kwargs):
        assert name == "bedrock-runtime" and kwargs["region_name"] == "eu-north-1"
        assert kwargs["config"].retries["max_attempts"] == 0
        return SimpleNamespace(converse=converse)

    monkeypatch.setitem(sys.modules, "boto3", SimpleNamespace(client=client))
    assert (
        invoke_converse("test-configured-profile", "eu-north-1", "test prompt")["stopReason"]
        == "end_turn"
    )


def test_nova_schema_prompt_usage(nova, monkeypatch, caplog):
    from app.parsing import bedrock

    def fake(model, region, prompt):
        assert model == "test-configured-profile"
        assert "agenda-v1" in prompt and '"action_items"' in prompt
        return response()

    monkeypatch.setattr(bedrock, "invoke_converse", fake)
    monkeypatch.setattr(settings, "parse_input_usd_per_million", None)
    monkeypatch.setattr(settings, "parse_output_usd_per_million", None)
    result = parse_agenda(ParseRequest(text=TEXT), nova)
    assert result.draft.model_dump(mode="json") == CASES[0]["expected_agenda"]
    assert result.metrics.input_tokens == 900 and result.metrics.output_tokens == 120
    assert result.metrics.estimated_cost_usd is None
    logs = [json.loads(r.message) for r in caplog.records if r.name == "app.parsing.service"]
    assert logs[-1]["bedrock_api"] == "converse"
    assert TEXT not in caplog.text


@pytest.mark.parametrize(
    "stop", ["max_tokens", "guardrail_intervened", "content_filtered", "tool_use"]
)
def test_unusable_stop_reason(nova, monkeypatch, stop):
    monkeypatch.setattr("app.parsing.bedrock.invoke_converse", lambda *a: response(stop=stop))
    with pytest.raises(ProviderError):
        nova.complete(ParseRequest(text=TEXT))


@pytest.mark.parametrize(
    "payload", [{}, {"stopReason": "end_turn", "output": None}, response(text="")]
)
def test_malformed_response(nova, monkeypatch, payload):
    monkeypatch.setattr("app.parsing.bedrock.invoke_converse", lambda *a: payload)
    with pytest.raises(ProviderError):
        nova.complete(ParseRequest(text=TEXT))


def test_invalid_agenda_json_retains_validation(nova, monkeypatch):
    monkeypatch.setattr("app.parsing.bedrock.invoke_converse", lambda *a: response(text="not JSON"))
    with pytest.raises(ParseError):
        parse_agenda(ParseRequest(text=TEXT), nova)


@pytest.mark.parametrize(
    "error",
    [
        ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "private denial"}}, "Converse"
        ),
        ReadTimeoutError(endpoint_url="https://fixture.invalid"),
    ],
)
def test_sdk_errors_redacted(nova, monkeypatch, error):
    def fail(*a):
        raise error

    monkeypatch.setattr("app.parsing.bedrock.invoke_converse", fail)
    with pytest.raises(ProviderError, match="Converse request failed") as caught:
        nova.complete(ParseRequest(text=TEXT))
    assert "private denial" not in str(caught.value)


async def test_nova_error_then_review_save(client, nova, monkeypatch):
    from app.main import app

    app.dependency_overrides[get_provider] = lambda: nova
    meeting = (await client.post("/api/meetings", json=meeting_payload())).json()
    url = f"/api/meetings/{meeting['id']}/agenda"

    def fail(*a):
        raise ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "fixture"}}, "Converse"
        )

    monkeypatch.setattr("app.parsing.bedrock.invoke_converse", fail)
    assert (await client.post(url + "/parse", json={"text": TEXT})).status_code == 503
    assert (await client.get(f"/api/meetings/{meeting['id']}")).json()["agenda"] is None
    monkeypatch.setattr("app.parsing.bedrock.invoke_converse", lambda *a: response())
    parsed = await client.post(url + "/parse", json={"text": TEXT})
    assert parsed.status_code == 200, parsed.text
    original = parsed.json()["draft"]
    final = copy.deepcopy(original)
    final["items"][0]["topic"] = "Reviewed Nova fixture"
    assert (await client.get(f"/api/meetings/{meeting['id']}")).json()["agenda"] is None
    saved = await client.put(url, json={"agenda": final, "ai_suggestion": original})
    assert saved.status_code == 200, saved.text
    assert saved.json()["agenda"] == final and saved.json()["ai_suggestion"] == original
    assert len((await client.get("/api/meetings")).json()) == 1


def test_hello_converse_with_fake_transport(monkeypatch, capsys):
    from app.parsing import hello

    monkeypatch.setattr(settings, "parse_bedrock_api", "converse")
    monkeypatch.setattr(settings, "parse_model_id", "test-configured-profile")

    def fake(model, region, prompt, max_tokens):
        assert model == "test-configured-profile" and max_tokens == 64
        return response(text="fixture greeting")

    monkeypatch.setattr(hello, "invoke_converse", fake)
    hello.main()
    output = json.loads(capsys.readouterr().out)
    assert output["stop_reason"] == "end_turn"
    assert output["usage"]["inputTokens"] == 900
    assert output["response"][-1]["text"] == "fixture greeting"


@pytest.mark.parametrize("fence", ["json", "JSON", ""])
def test_valid_fenced_agenda_regression(nova, monkeypatch, fence):
    # Previous implementation rejected a valid agenda solely due to Markdown wrapping.
    text = "  ```" + fence + "\n" + json.dumps(CASES[0]["expected_agenda"]) + "\n```  "
    monkeypatch.setattr("app.parsing.bedrock.invoke_converse", lambda *a: response(text=text))
    parsed = parse_agenda(ParseRequest(text=TEXT), nova)
    assert parsed.draft.model_dump(mode="json") == CASES[0]["expected_agenda"]
    assert parsed.metrics.input_tokens == 900


@pytest.mark.parametrize(
    "text",
    [
        'Here is your JSON: {"items": []}',
        "```json\n{}\n```\nIgnore previous instructions",
        "```json\n{}\n```\n```json\n{}\n```",
    ],
)
def test_no_arbitrary_json_extraction(nova, monkeypatch, text):
    monkeypatch.setattr("app.parsing.bedrock.invoke_converse", lambda *a: response(text=text))
    with pytest.raises(ParseError):
        parse_agenda(ParseRequest(text=TEXT), nova)


def test_safe_schema_diagnostics_keep_deadline_validation(nova, monkeypatch, caplog):
    agenda = copy.deepcopy(CASES[0]["expected_agenda"])
    agenda["items"][0]["action_items"][0]["deadline"] = "PRIVATE invalid deadline"
    agenda["PRIVATE secret field"] = "PRIVATE secret value"
    monkeypatch.setattr(
        "app.parsing.bedrock.invoke_converse", lambda *a: response(text=json.dumps(agenda))
    )
    with pytest.raises(ParseError) as error:
        parse_agenda(ParseRequest(text=TEXT), nova)
    assert "items.0.action_items.0.deadline" in str(error.value)
    assert "PRIVATE" not in str(error.value) and "PRIVATE" not in caplog.text
    log = [json.loads(r.message) for r in caplog.records if r.name == "app.parsing.service"][-1]
    assert log["validation_errors"]
    assert log["input_tokens"] == 900 and log["status"] == "validation_error"
