import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.agenda import Agenda
from app.config import settings
from app.main import app
from app.parsing.service import (
    BedrockProvider,
    Completion,
    MockProvider,
    ParseError,
    ParseRequest,
    ProviderError,
    get_provider,
    parse_agenda,
)
from tests.conftest import make_token
from tests.test_api import meeting_payload

CASES = json.loads((Path(__file__).parent / "fixtures" / "parse_cases.json").read_text())
TEXT = CASES[0]["text"]


class FakeProvider:
    name = "bedrock"
    model_id = "fake-no-network"

    def __init__(self, text):
        self.text = text

    def complete(self, request):
        return Completion(self.text, 100, 50)


def test_agenda_mock_and_metrics():
    result = parse_agenda(ParseRequest(text=TEXT), MockProvider())
    assert result.draft.items[0].owner == "Олена"
    assert result.metrics.estimated_cost_usd == 0
    assert result.metrics.input_tokens is None


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
async def test_five_agenda_examples(client, case):
    meeting = (await client.post("/api/meetings", json=meeting_payload())).json()
    response = await client.post(
        f"/api/meetings/{meeting['id']}/agenda/parse",
        json={
            "text": case["text"],
            "timezone": case["timezone"],
            "reference_date": case["reference_date"],
        },
    )
    assert response.status_code == case["expected_status"], response.text
    if response.status_code == 200:
        assert response.json()["draft"] == case["expected_agenda"]
    unchanged = (await client.get(f"/api/meetings/{meeting['id']}")).json()
    assert unchanged["agenda"] is None and unchanged["ai_suggestion"] is None
    assert len((await client.get("/api/meetings")).json()) == 1


@pytest.mark.parametrize(
    "output", ["not json", "```json\n{}\n```", "{}", "[]", '{"items": [], "title": "Meeting"}']
)
def test_invalid_agenda_json(output):
    with pytest.raises(ParseError):
        parse_agenda(ParseRequest(text=TEXT), FakeProvider(output))


@pytest.mark.parametrize("deadline", ["tomorrow", "2026-02-30", "30/10/2026"])
def test_invalid_deadlines(deadline):
    agenda = copy.deepcopy(CASES[0]["expected_agenda"])
    agenda["items"][0]["action_items"][0]["deadline"] = deadline
    with pytest.raises(ValidationError):
        Agenda.model_validate(agenda)


@pytest.mark.parametrize("text,zone", [("  ", "UTC"), (TEXT, "Kyiv/Invalid")])
def test_invalid_input(text, zone):
    with pytest.raises(ValidationError):
        ParseRequest(text=text, timezone=zone)


def test_relative_date_requires_reference():
    with pytest.raises(ParseError, match="reference"):
        parse_agenda(ParseRequest(text=CASES[2]["text"]), MockProvider())
    result = parse_agenda(
        ParseRequest(text=CASES[2]["text"], reference_date="2026-12-31"), MockProvider()
    )
    assert str(result.draft.items[0].action_items[0].deadline) == "2027-01-01"


def test_bedrock_disabled_before_client_creation(monkeypatch):
    import sys
    from types import SimpleNamespace

    monkeypatch.setattr(settings, "parse_bedrock_enabled", False)

    def forbidden(*args, **kwargs):
        pytest.fail("AWS client must not be created")

    monkeypatch.setitem(sys.modules, "boto3", SimpleNamespace(client=forbidden))
    with pytest.raises(ProviderError, match="disabled"):
        BedrockProvider().complete(ParseRequest(text=TEXT))


def test_cost_uses_configured_rates(monkeypatch):
    monkeypatch.setattr(settings, "parse_input_usd_per_million", 1.0)
    monkeypatch.setattr(settings, "parse_output_usd_per_million", 5.0)
    result = parse_agenda(
        ParseRequest(text=TEXT), FakeProvider(json.dumps(CASES[0]["expected_agenda"]))
    )
    assert result.metrics.estimated_cost_usd == pytest.approx(0.00035)


async def test_parse_edit_save_existing_meeting_and_isolation(client):
    meeting = (await client.post("/api/meetings", json=meeting_payload())).json()
    url = f"/api/meetings/{meeting['id']}/agenda"
    response = await client.post(url + "/parse", json={"text": TEXT, "timezone": "Europe/Kyiv"})
    assert response.status_code == 200, response.text
    original = response.json()["draft"]
    final = copy.deepcopy(original)
    final["items"][0]["topic"] = "Reviewed release"
    final["items"][0]["owner"] = "Taras"
    final["items"][0]["action_items"][0]["deadline"] = "2026-11-01"
    assert (await client.get(f"/api/meetings/{meeting['id']}")).json()["agenda"] is None
    saved = await client.put(url, json={"agenda": final, "ai_suggestion": original})
    assert saved.status_code == 200, saved.text
    body = saved.json()
    assert body["agenda"] == final and body["ai_suggestion"] == original
    for key in ["id", "title", "place", "starts_at", "ends_at", "description"]:
        assert body[key] == meeting[key]
    assert (await client.get(f"/api/meetings/{meeting['id']}")).json() == body
    assert len((await client.get("/api/meetings")).json()) == 1
    # A normal meeting edit must retain both agenda JSONB columns.
    updated = await client.put(
        f"/api/meetings/{meeting['id']}", json=meeting_payload(title="Updated")
    )
    assert updated.json()["ai_suggestion"] == original
    assert updated.json()["agenda"] == final
    headers = {"Authorization": f"Bearer {make_token('bob')}"}
    assert (
        await client.post(url + "/parse", json={"text": TEXT}, headers=headers)
    ).status_code == 404
    assert (
        await client.put(url, json={"agenda": final, "ai_suggestion": original}, headers=headers)
    ).status_code == 404
    assert (await client.get(f"/api/meetings/{meeting['id']}", headers=headers)).status_code == 404
    client.headers.clear()
    assert (await client.post(url + "/parse", json={"text": TEXT})).status_code == 401
    assert (
        await client.put(url, json={"agenda": final, "ai_suggestion": original})
    ).status_code == 401


async def test_failed_save_preserves_previous_state(client):
    meeting = (await client.post("/api/meetings", json=meeting_payload())).json()
    url = f"/api/meetings/{meeting['id']}/agenda"
    original = CASES[0]["expected_agenda"]
    assert (
        await client.put(url, json={"agenda": {"items": []}, "ai_suggestion": original})
    ).status_code == 422
    assert (await client.get(f"/api/meetings/{meeting['id']}")).json()["agenda"] is None


async def test_provider_error_no_save(client):
    class Broken(FakeProvider):
        def complete(self, request):
            raise ProviderError("Unavailable")

    app.dependency_overrides[get_provider] = lambda: Broken("")
    meeting = (await client.post("/api/meetings", json=meeting_payload())).json()
    response = await client.post(f"/api/meetings/{meeting['id']}/agenda/parse", json={"text": TEXT})
    assert response.status_code == 503
    assert (await client.get(f"/api/meetings/{meeting['id']}")).json()["agenda"] is None


async def test_kyiv_without_system_tzdata(client):
    import zoneinfo

    previous_path = zoneinfo.TZPATH
    zoneinfo.reset_tzpath([])
    zoneinfo.ZoneInfo.clear_cache()
    try:
        response = await client.post("/api/parse", json={"text": TEXT, "timezone": "Europe/Kyiv"})
        assert response.status_code == 200, response.text
    finally:
        zoneinfo.reset_tzpath(previous_path)
        zoneinfo.ZoneInfo.clear_cache()


@pytest.mark.parametrize("zone", [" Europe/Kyiv ", "\u00a0Europe/Kyiv\u00a0"])
def test_pasted_kyiv_timezone_whitespace(zone):
    assert ParseRequest(text=TEXT, timezone=zone).timezone == "Europe/Kyiv"
