import array
import io
import json
import math

import av
import httpx
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.ai import ChatReply, ModelRisk, OutputCheck
from app.config import Settings
from app.devices import Devices
from app.main import create_app
from app.research import AppraisalState

MAC = 'aa:bb:cc:dd:ee:01'


def tone(rate, seconds, amplitude):
    return array.array('h', [int(amplitude*math.sin(2*math.pi*220*i/rate)) for i in range(int(rate*seconds))]).tobytes()


def opus_uplink(pcm, rate=16000):
    """What the device microphone sends: 60 ms Opus packets."""
    encoder = av.CodecContext.create('libopus', 'w')
    encoder.sample_rate, encoder.layout, encoder.format = rate, 'mono', 's16'
    encoder.options = {'frame_duration': '60'}
    encoder.open()
    step, packets = rate*60//1000*2, []
    for index in range(0, len(pcm)-step+1, step):
        frame = av.AudioFrame(format='s16', layout='mono', samples=step//2)
        frame.planes[0].update(pcm[index:index+step])
        frame.sample_rate, frame.pts = rate, index//2
        packets += [bytes(p) for p in encoder.encode(frame)]
    return packets


def mp3(seconds=0.4):
    out = io.BytesIO()
    with av.open(out, 'w', format='mp3') as container:
        stream = container.add_stream('libmp3lame', rate=24000, layout='mono')
        pcm = tone(24000, seconds, 3000)
        frame = av.AudioFrame(format='s16', layout='mono', samples=len(pcm)//2)
        frame.planes[0].update(pcm)
        frame.sample_rate = 24000
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)
    return out.getvalue()


@pytest.fixture
def gateway(tmp_path, monkeypatch):
    import edge_tts
    heard = {'text': 'Hôm nay tôi mệt vì làm ca'}
    spoken = []

    class Communicate:
        def __init__(self, text, voice, **kwargs):
            spoken.append(text)
        async def stream(self):
            yield {'type': 'audio', 'data': mp3()}
    monkeypatch.setattr(edge_tts, 'Communicate', Communicate)

    async def post(self, url, **kwargs):
        assert url.endswith('/audio/transcriptions') and kwargs['files']['file'][2] == 'audio/wav'
        return httpx.Response(200, request=httpx.Request('POST', url), json={'text': heard['text']})
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)

    async def complete(task, data, schema, **kwargs):
        if schema is ModelRisk:
            return ModelRisk(level='low', reason='synthetic')
        if schema is ChatReply:
            return ChatReply(reply='Mình đang nghe bạn. Hôm nay điều gì làm bạn mệt nhất?')
        if schema is OutputCheck:
            return OutputCheck(allow=True)
        return AppraisalState()
    config = Settings(data_dir=tmp_path, mode='live', llm_api_key='synthetic', transcription_model='stt',
                      device_gateway=True)
    app = create_app(config)
    monkeypatch.setattr(app.state.ai, 'complete', complete)
    token = Devices(app.state.store, config).add(MAC, 'Ricky test')
    with TestClient(app) as client:
        yield client, token, heard, spoken


def converse(client, token, packets):
    headers = {'Authorization': 'Bearer '+token, 'Protocol-Version': '1', 'Device-Id': MAC.upper(), 'Client-Id': 'c1'}
    with client.websocket_connect('/xiaozhi/v1/', headers=headers) as ws:
        ws.send_text(json.dumps({'type': 'hello', 'version': 1, 'transport': 'websocket',
                                 'audio_params': {'format': 'opus', 'sample_rate': 16000, 'channels': 1, 'frame_duration': 60}}))
        hello = json.loads(ws.receive_text())
        assert hello['type'] == 'hello' and hello['audio_params']['sample_rate'] == 24000
        ws.send_text(json.dumps({'type': 'listen', 'state': 'start', 'mode': 'auto'}))
        while True:  # AnMi greets first; listen again once the greeting has finished
            message = ws.receive()
            if message.get('text') and json.loads(message['text']).get('state') == 'stop':
                break
        ws.send_text(json.dumps({'type': 'listen', 'state': 'start', 'mode': 'auto'}))
        for packet in packets:
            ws.send_bytes(packet)
        events, audio = [], 0
        while True:
            message = ws.receive()
            if message.get('bytes') is not None:
                audio += 1
                continue
            event = json.loads(message['text'])
            events.append(event)
            if event['type'] == 'tts' and event['state'] == 'stop':
                return events, audio


def speech_then_pause():
    return opus_uplink(tone(16000, 1.2, 6000)+b'\0'*16000*2*2)


def test_ota_hands_only_registered_devices_their_websocket(gateway):
    client, token, _, _ = gateway
    assert client.post('/xiaozhi/ota/', headers={'Device-Id': '11:22:33:44:55:66'}, json={}).status_code == 403
    result = client.post('/xiaozhi/ota/', headers={'Device-Id': MAC}, json={}).json()
    assert result['websocket'] == {'url': 'ws://testserver/xiaozhi/v1/', 'token': token, 'version': 1}
    assert result['server_time']['timezone_offset'] == 420


def test_websocket_rejects_unknown_token_or_other_device(gateway):
    client, token, _, _ = gateway
    for headers in ({'Authorization': 'Bearer wrong', 'Device-Id': MAC}, {'Authorization': 'Bearer '+token, 'Device-Id': '11:22:33:44:55:66'}):
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect('/xiaozhi/v1/', headers=headers) as ws:
                ws.receive_text()


def test_device_turn_runs_anmi_journey_and_streams_opus_reply(gateway):
    client, token, _, spoken = gateway
    events, audio = converse(client, token, speech_then_pause())
    kinds = [(e['type'], e.get('state')) for e in events]
    assert kinds[0] == ('stt', None) and events[0]['text'] == 'Hôm nay tôi mệt vì làm ca'
    assert ('tts', 'start') in kinds and ('tts', 'sentence_start') in kinds
    assert audio > 0 and spoken and 'mệt nhất' in ' '.join(spoken), events


def test_high_risk_on_device_speaks_support_without_web_only_hint(gateway):
    client, token, heard, spoken = gateway
    heard['text'] = 'Tôi muốn chết'
    events, audio = converse(client, token, speech_then_pause())
    said = ' '.join(e['text'] for e in events if e.get('state') == 'sentence_start')
    assert '115' in said and 'mục Hỗ trợ' not in said and 'mệt nhất' not in said
    assert any(e['type'] == 'llm' and e['emotion'] == 'caring' for e in events)
    assert audio > 0


def test_silence_is_not_sent_to_speech_recognition(gateway, monkeypatch):
    client, token, _, _ = gateway
    async def post(self, url, **kwargs):
        raise AssertionError('silence must not reach the provider')
    monkeypatch.setattr(httpx.AsyncClient, 'post', post)
    headers = {'Authorization': 'Bearer '+token, 'Device-Id': MAC}
    with client.websocket_connect('/xiaozhi/v1/', headers=headers) as ws:
        ws.send_text(json.dumps({'type': 'hello', 'audio_params': {'format': 'opus', 'sample_rate': 16000, 'channels': 1, 'frame_duration': 60}}))
        ws.receive_text()
        ws.send_text(json.dumps({'type': 'listen', 'state': 'start', 'mode': 'auto'}))
        for packet in opus_uplink(b'\0'*16000*2*3):
            ws.send_bytes(packet)
        ws.send_text(json.dumps({'type': 'listen', 'state': 'stop'}))
