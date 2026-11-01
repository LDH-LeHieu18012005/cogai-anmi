import asyncio
import json
import sqlite3
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app.ai import AI, ProviderFailure
from app.config import Settings
from app.main import create_app
from app.models import Analysis, ChatInput, Consent, ReframeInput, ScreeningInput
from app.safety import redact, rule_risk
from app.screening import score_screening


@pytest.fixture
def system(tmp_path):
    app = create_app(Settings(data_dir=tmp_path, mode="demo"))
    with TestClient(app) as client:
        yield app, client


def start(client, persist=False, external_ai=False):
    return client.post("/api/session", json={"accepted": True, "adult": True, "persist": persist, "external_ai": external_ai})


def test_requires_explicit_consent_and_adult(system):
    _, client = system
    assert client.post("/api/session", json={"accepted": False, "adult": True}).status_code == 422
    assert client.post("/api/session", json={"accepted": True, "adult": False}).status_code == 422
    assert client.get("/api/records").status_code == 401
    assert start(client).status_code == 201
    assert "httponly" in client.cookies.__repr__().lower() or "cogai_session" in client.cookies
    assert start(client).status_code == 409


def test_cookie_attributes_and_origin_checks(system):
    _, client = system
    result = start(client)
    cookie = result.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie and "path=/api" in cookie
    assert client.post("/api/moods", json={"score": 4}, headers={"Origin": "https://outside.example"}).status_code == 403
    assert client.post("/api/moods", json={"score": 4}, headers={"Origin": "http://localhost:5173"}).status_code == 201


def test_no_persistence_means_no_content_records(system):
    app, client = system
    start(client)
    result = client.post("/api/chat", json={"message": "Mình lo về kỳ thi"})
    assert result.status_code == 200 and result.json()["mode"] == "demo"
    assert client.post("/api/moods", json={"score": 2, "note": "Nội dung riêng tư"}).json()["saved"] is False
    assert client.get("/api/records").json()["records"] == []
    with app.state.store.connection() as db:
        assert db.execute("SELECT count(*) FROM records").fetchone()[0] == 0


def test_persistence_is_encrypted_and_survives_restart(system, tmp_path):
    app, client = system
    start(client, persist=True)
    text = "Một ghi chú cá nhân cần được bảo vệ"
    response = client.post("/api/moods", json={"score": 4, "note": text})
    assert response.status_code == 201
    with app.state.store.connection() as db:
        raw = db.execute("SELECT payload FROM records").fetchone()[0]
        assert text.encode() not in raw
        assert raw.startswith(b"gAAAA")
    restarted = create_app(Settings(data_dir=tmp_path))
    with TestClient(restarted) as other:
        other.cookies.update(client.cookies)
        assert other.get("/api/records").json()["records"][0]["payload"]["note"] == text


def test_sessions_cannot_read_or_rate_another_sessions_record(system):
    app, first = system
    start(first, persist=True)
    saved = first.post("/api/moods", json={"score": 3}).json()
    with TestClient(app) as second:
        start(second, persist=True)
        assert second.get("/api/records").json()["records"] == []
        assert second.post("/api/feedback", json={"record_id": saved["record_id"], "helpfulness": 5}).status_code == 404
    assert first.post("/api/feedback", json={"record_id": saved["record_id"], "helpfulness": 4}).status_code == 201


def test_delete_revokes_cookie_records_and_inflight_writes(system):
    app, client = system
    start(client, persist=True)
    token = client.cookies.get("cogai_session")
    session = app.state.store.session(token)
    client.post("/api/moods", json={"score": 4})
    assert client.delete("/api/session").json()["deleted"] is True
    assert client.get("/api/export").status_code == 401
    with app.state.store.connection() as db:
        assert db.execute("SELECT count(*) FROM records").fetchone()[0] == 0
    with pytest.raises(Exception) as exc:
        app.state.store.save(session, "chat", {"message": "late response"})
    assert exc.value.status_code == 401


def test_expired_session_is_rejected_and_removed(system):
    app, client = system
    start(client, persist=True)
    client.post("/api/moods", json={"score": 4})
    with app.state.store.connection() as db:
        db.execute("UPDATE sessions SET expires=?", (time.time() - 1,))
    assert client.get("/api/records").status_code == 401
    with app.state.store.connection() as db:
        assert db.execute("SELECT count(*) FROM records").fetchone()[0] == 0


@pytest.mark.parametrize("text", ["Tôi muốn chết", "toi muon tu tu", "I want to kill myself", "Tôi muốn làm hại bản thân"])
def test_urgent_input_bypasses_reframing(system, text):
    _, client = system
    start(client)
    result = client.post("/api/reframe", json={"situation": "Hôm nay rất khó", "thought": text}).json()
    assert result["blocked"] is True
    assert result["risk"]["level"] == "high"
    assert "candidates" not in result


def test_ambiguous_input_requests_check_in_and_context_is_checked(system):
    _, client = system
    start(client)
    result = client.post("/api/chat", json={"message": "Em không muốn tiếp tục nữa"}).json()
    assert result["risk"]["level"] == "check_in"
    assert "hay bạn" in result["reply"]
    result = client.post("/api/chat", json={"message": "Tôi đang ở nhà", "history": [{"role": "user", "content": "Tôi muốn chết"}]}).json()
    # Client-supplied history is not authoritative anymore.
    assert result["risk"]["level"] == "check_in"


def test_chat_restores_context_and_reset_preserves_diary(system):
    _, client = system
    start(client, persist=True)
    client.post("/api/chat", json={"message": "Tôi muốn chết"})
    history = client.get("/api/chat").json()
    assert len(history["turns"]) == 2
    assert history["risk"]["level"] == "high"
    assert client.post("/api/chat", json={"message": "Tôi đang ở nhà", "history": []}).json()["risk"]["level"] == "high"
    assert client.post("/api/chat/reset", json={}).status_code == 200
    assert client.get("/api/chat").json()["turns"] == []
    assert any(r["kind"] == "chat" for r in client.get("/api/records").json()["records"])


def test_ephemeral_chat_restores_without_disk_records(system):
    _, client = system
    start(client)
    client.post("/api/chat", json={"message": "Tôi lo kỳ thi"})
    assert len(client.get("/api/chat").json()["turns"]) == 2
    assert client.get("/api/records").json()["records"] == []
    client.delete("/api/session")
    assert client.get("/api/chat").status_code == 401


def test_vietnamese_slowly_is_not_confused_with_self_harm():
    assert rule_risk("Tôi muốn làm từ từ, không vội").level == "low"
    assert rule_risk("Tôi muốn tự tử").level == "high"


@pytest.mark.parametrize("kind,score,band", [("PHQ-9", 0, "Tối thiểu"), ("PHQ-9", 5, "Nhẹ"), ("PHQ-9", 10, "Vừa"), ("PHQ-9", 15, "Khá nặng"), ("PHQ-9", 20, "Nặng"), ("GAD-7", 15, "Nặng"), ("GAD-7", 10, "Vừa")])
def test_screening_cutpoints(kind, score, band):
    count = 9 if kind == "PHQ-9" else 7
    answers = [max(0, min(3, score - index * 3)) for index in range(count)]
    result = score_screening(ScreeningInput(kind=kind, answers=answers))
    assert result["score"] == score and result["band"] == band


def test_ninth_item_triggers_support_even_with_low_total(system):
    _, client = system
    start(client)
    result = client.post("/api/screenings", json={"kind": "PHQ-9", "answers": [0] * 8 + [1]}).json()
    assert result["score"] == 1 and result["requires_support"] is True


@pytest.mark.parametrize("answers", [[0] * 8, [0] * 8 + [4], [0] * 8 + [True], [0] * 8 + [1.5]])
def test_invalid_answers_are_not_scored(system, answers):
    _, client = system
    start(client)
    assert client.post("/api/screenings", json={"kind": "PHQ-9", "answers": answers}).status_code == 422


def test_reframe_real_save_and_feedback(system):
    _, client = system
    start(client, persist=True)
    result = client.post("/api/reframe", json={"situation": "Tôi bị nhắc vì đi muộn", "thought": "Tôi làm gì cũng hỏng", "lenses": ["CBT", "ACT", "CFT"]}).json()
    assert not result["blocked"] and len(result["candidates"]) == 3
    assert result["analysis"]["possible_patterns"] == []
    assert "minh họa" in result["candidates"][0]["review"]
    record = client.get("/api/records").json()["records"][0]
    assert record["id"] == result["record_id"]
    assert client.post("/api/feedback", json={"record_id": result["record_id"], "helpfulness": 3}).status_code == 201


def test_export_includes_records_beyond_diary_limit(system):
    app, client = system
    start(client, persist=True)
    session = app.state.store.session(client.cookies.get("cogai_session"))
    with app.state.store.connection() as db:
        encrypted = app.state.store.cipher.encrypt(b'{"score":3,"note":"test"}')
        db.executemany("INSERT INTO records VALUES (?,?,?,?,?)", [(str(n), session["id"], "mood", encrypted, time.time()) for n in range(503)])
    assert len(client.get("/api/records").json()["records"]) == 500
    assert len(client.get("/api/export").json()["records"]) == 503


def test_body_and_ai_rate_limits(system):
    _, client = system
    start(client)
    assert client.post("/api/chat", content=b"x" * 33000).status_code == 413
    for _ in range(10):
        assert client.post("/api/chat", json={"message": "Xin chào"}).status_code == 200
    result = client.post("/api/chat", json={"message": "Xin chào"})
    assert result.status_code == 429 and result.headers["Retry-After"] == "60"


def test_live_mode_requires_key_and_external_consent(tmp_path):
    app = create_app(Settings(data_dir=tmp_path, mode="live"))
    with pytest.raises(RuntimeError):
        with TestClient(app):
            pass
    app = create_app(Settings(data_dir=tmp_path, mode="live", llm_api_key="test-only-key"))
    with TestClient(app) as client:
        assert start(client).status_code == 403


def test_safety_provider_failure_does_not_continue_generation(tmp_path, monkeypatch):
    ai = AI(Settings(data_dir=tmp_path, mode="live", llm_api_key="fake"))
    calls = []
    async def broken(task, data, schema, **kwargs):
        calls.append(task)
        raise ProviderFailure("offline")
    monkeypatch.setattr(ai, "complete", broken)
    result = asyncio.run(ai.reframe(ReframeInput(situation="Tôi đi học", thought="Tôi đang lo")))
    assert result["blocked"] is True and result["risk"]["level"] == "unavailable"
    assert len(calls) == 2  # the risk check is retried once, generation never starts


def test_output_check_blocks_unreviewed_live_reply(tmp_path, monkeypatch):
    from app.ai import ChatReply, ModelRisk, OutputCheck
    ai = AI(Settings(data_dir=tmp_path, mode="live", llm_api_key="fake"))
    async def replies(task, data, schema, **kwargs):
        if schema is ModelRisk:
            return ModelRisk(level="low", reason="test")
        if schema is ChatReply:
            return ChatReply(reply="A reply that must be withheld")
        return OutputCheck(allow=False)
    monkeypatch.setattr(ai, "complete", replies)
    result = asyncio.run(ai.chat("Tôi lo kỳ thi", []))
    # Withheld after a low-risk check: a neutral "say it again", never the draft, no safety stop.
    assert result["withheld"] is True and result["risk"]["level"] == "low"
    assert "must be withheld" not in result["reply"]


def test_live_transport_contract_and_redaction(tmp_path, monkeypatch):
    ai = AI(Settings(data_dir=tmp_path, mode="live", llm_api_key="fake"))
    requests = []
    async def post(self, url, **kwargs):
        requests.append(kwargs)
        return httpx.Response(200, request=httpx.Request("POST", url), json={"choices": [{"message": {"content": '{"reply":"Xin chào bạn"}'}}]})
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    from app.ai import ChatReply
    result = asyncio.run(ai.complete("Reply", {"text": "Email user@example.org, gọi 0912345678"}, ChatReply))
    wire = json.dumps(requests[0]["json"], ensure_ascii=False)
    assert "user@example.org" not in wire and "0912345678" not in wire
    assert requests[0]["json"]["store"] is False
    assert result.reply == "Xin chào bạn"


def test_bad_provider_json_is_a_failure(tmp_path, monkeypatch):
    ai = AI(Settings(data_dir=tmp_path, mode="live", llm_api_key="fake"))
    async def post(self, url, **kwargs):
        return httpx.Response(200, request=httpx.Request("POST", url), json={"choices": [{"message": {"content": "not json"}}]})
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    from app.ai import ChatReply
    with pytest.raises(ProviderFailure):
        asyncio.run(ai.complete("Reply", {}, ChatReply))
