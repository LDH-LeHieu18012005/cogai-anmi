"""Exercise the real device transport and codecs without calling paid services."""
import array
import asyncio
import io
import math
import random
from types import SimpleNamespace

import av
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.config import Settings
from app.devices import Devices
from app.dialogue import reply_ready
from app.storage import Store
from app.xiaozhi import END_SILENCE_MS, FRAME_MS, GREETING, Decoder, Endpointer, opus_frames, sentences, xiaozhi_router

MAC = 'aa:bb:cc:dd:ee:ff'


def microphone_packets():
    codec = av.CodecContext.create('libopus', 'w')
    codec.sample_rate, codec.layout, codec.format = 16000, 'mono', 's16'
    codec.options = {'frame_duration': '60'}
    codec.open()
    packets = []
    for index in range(8):
        samples = array.array('h', [int(6000 * math.sin(2 * math.pi * 440 * (index * 960 + n) / 16000)) for n in range(960)])
        frame = av.AudioFrame(format='s16', layout='mono', samples=960)
        frame.planes[0].update(samples.tobytes())
        frame.sample_rate, frame.pts = 16000, index * 960
        packets.extend(bytes(p) for p in codec.encode(frame))
    packets.extend(bytes(p) for p in codec.encode(None))
    return packets


def speech_mp3():
    buffer = io.BytesIO()
    with av.open(buffer, 'w', format='mp3') as container:
        stream = container.add_stream('mp3', rate=24000)
        stream.layout = 'mono'
        frame = av.AudioFrame(format='s16', layout='mono', samples=2400)
        frame.planes[0].update(array.array('h', [2000] * 2400).tobytes())
        frame.sample_rate = 24000
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)
    return buffer.getvalue()


@pytest.fixture
def gateway(tmp_path):
    config = Settings(data_dir=tmp_path, device_gateway=True)
    store = Store(config)
    devices = Devices(store, config)
    token = devices.add(MAC, 'Ricky test')
    calls = []
    async def recognize(session, audio, mime, extension):
        assert audio.startswith(b'RIFF') and mime == 'audio/wav'
        assert session['consent']['persist'] is False
        state.session_ids.append(session['id'])
        return state.transcript
    async def speech(session, text):
        calls.append(('speech', text))
        if state.slow_speech:
            await asyncio.sleep(60)
        yield speech_mp3()
    async def chat(session, data):
        calls.append(('chat', data.message, data.channel))
        if state.replaced:
            # The checked reply was announced, then final_gate replaced it with support.
            reply_ready.get()('Mình đang nghe bạn, kể tiếp nhé.')
            await asyncio.sleep(0.2)
            return {'reply': 'Mình muốn ưu tiên sự an toàn của bạn lúc này.', 'risk': {'requires_support': True}}
        return {'reply': 'Mình đang nghe bạn.', 'risk': {'requires_support': False}}
    async def limited(session, operation):
        return await operation
    state = SimpleNamespace(transcript='Hôm nay công việc khá mệt.', session_ids=[], slow_speech=False, store=store, replaced=False)
    voice = SimpleNamespace(recognize=recognize, speech_chunks=speech)
    dialogue = SimpleNamespace(chat=chat, safety_event=lambda *args: calls.append(('safety', args[1])))
    app = FastAPI()
    app.include_router(xiaozhi_router(store, config, dialogue, limited, voice))
    with TestClient(app) as client:
        yield client, devices, token, calls, state


def connect(client, token, **headers):
    return client.websocket_connect('/xiaozhi/v1/', headers={'Authorization': 'Bearer ' + token, 'Device-Id': MAC, **headers})


def hello(ws):
    ws.send_json({'type': 'hello', 'version': 1, 'transport': 'websocket', 'audio_params': {'format': 'opus', 'sample_rate': 16000, 'channels': 1, 'frame_duration': 60}})
    response = ws.receive_json()
    assert response['type'] == 'hello' and response['audio_params']['sample_rate'] == 24000
    # The first listen of a conversation is answered with AnMi's greeting.
    ws.send_json({'type': 'listen', 'state': 'start', 'mode': 'auto'})
    messages, audio = receive_turn(ws)
    assert any(m.get('text') == GREETING for m in messages) and audio


def send_turn(ws):
    ws.send_json({'type': 'listen', 'state': 'start', 'mode': 'manual'})
    for packet in microphone_packets():
        ws.send_bytes(packet)
    ws.send_json({'type': 'listen', 'state': 'stop'})


def receive_turn(ws):
    messages, audio = [], []
    while True:
        event = ws.receive()
        if event.get('bytes') is not None:
            audio.append(event['bytes'])
            continue
        import json
        message = json.loads(event['text'])
        messages.append(message)
        if message.get('type') == 'tts' and message.get('state') == 'stop':
            return messages, audio


def test_registry_and_ota(gateway):
    client, devices, token, _, _ = gateway
    assert client.post('/xiaozhi/ota/').status_code == 403
    response = client.post('/xiaozhi/ota/', headers={'Device-Id': MAC}).json()
    assert response['websocket'] == {'url': 'ws://testserver/xiaozhi/v1/', 'token': token, 'version': 1}
    assert response['server_time']['timezone_offset'] == 420
    assert token not in devices.path.read_text('utf-8')
    assert 'token' not in devices.list()[0]
    replacement = devices.add(MAC.upper(), 'new token')
    assert devices.by_token(token) is None
    assert devices.by_token(replacement)['mac'] == MAC
    assert devices.remove(MAC) and devices.token(MAC) is None


def test_tokens_from_host_secret_and_tls_tunnel(tmp_path):
    config = Settings(data_dir=tmp_path, device_gateway=True, device_tokens=f'{MAC.upper()}=secret-from-kaggle')
    store = Store(config)
    devices = Devices(store, config)
    assert devices.token(MAC) == 'secret-from-kaggle' and devices.by_token('secret-from-kaggle')['mac'] == MAC
    assert devices.by_token('secret-from-kaggl') is None
    app = FastAPI()
    app.include_router(xiaozhi_router(store, config, SimpleNamespace(), None, SimpleNamespace()))
    with TestClient(app, base_url='http://anmi.example.invalid') as client:
        result = client.post('/xiaozhi/ota/', headers={'Device-Id': MAC, 'X-Forwarded-Proto': 'https'}).json()
    assert result['websocket']['url'] == 'wss://anmi.example.invalid/xiaozhi/v1/'
    assert result['websocket']['token'] == 'secret-from-kaggle'


def test_websocket_rejects_unknown_token_and_wrong_mac(gateway):
    client, _, token, _, _ = gateway
    for secret, mac in [('wrong', MAC), (token, '00:00:00:00:00:00')]:
        with pytest.raises(WebSocketDisconnect):
            with connect(client, secret, **{'Device-Id': mac}):
                pass


def test_real_opus_turn_uses_anmi_pipeline_and_can_repeat(gateway):
    client, _, token, calls, _ = gateway
    with connect(client, token) as ws:
        hello(ws)
        for _ in range(2):
            send_turn(ws)
            messages, audio = receive_turn(ws)
            assert any(m['type'] == 'stt' for m in messages)
            assert any(m.get('state') == 'sentence_start' for m in messages)
            assert audio and any(Decoder().pcm(packet) for packet in audio)
    assert len([c for c in calls if c[0] == 'chat']) == 2
    assert ('safety', 'device_transcript') in calls


def test_empty_transcript_returns_to_listening(gateway):
    client, _, token, calls, state = gateway
    state.transcript = ''
    with connect(client, token) as ws:
        hello(ws)
        send_turn(ws)
        messages, audio = receive_turn(ws)
        assert not audio and not any(c[0] == 'chat' for c in calls)
        state.transcript = 'Mình muốn nói tiếp.'
        send_turn(ws)
        assert receive_turn(ws)[1]


def test_provider_error_still_finishes_turn(gateway):
    client, _, token, _, state = gateway
    # A non-string transcript makes ChatInput fail, exercising the background
    # exception path that previously left the robot waiting indefinitely.
    state.transcript = {'invalid': True}
    with connect(client, token) as ws:
        hello(ws)
        send_turn(ws)
        messages, audio = receive_turn(ws)
        assert any(m['type'] == 'alert' for m in messages) and not audio


def test_new_connection_gets_new_guest_session(gateway):
    client, _, token, _, state = gateway
    for _ in range(2):
        with connect(client, token) as ws:
            hello(ws)
            send_turn(ws)
            assert receive_turn(ws)[1]
    assert len(set(state.session_ids)) == 2
    with state.store.connection() as db:
        assert db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0] == 0


def test_abort_cancels_synthesis_and_next_turn_works(gateway):
    client, _, token, _, state = gateway
    with connect(client, token) as ws:
        hello(ws)
        state.slow_speech = True
        send_turn(ws)
        while ws.receive_json().get('state') != 'start':
            pass
        ws.send_json({'type': 'abort'})
        assert ws.receive_json()['state'] == 'stop'
        state.slow_speech = False
        send_turn(ws)
        assert receive_turn(ws)[1]


def test_reply_replaced_by_support_after_it_started_is_stopped(gateway):
    client, _, token, calls, state = gateway
    state.replaced = True
    with connect(client, token) as ws:
        hello(ws)
        send_turn(ws)
        messages, audio = receive_turn(ws)
    said = [m['text'] for m in messages if m.get('state') == 'sentence_start']
    assert said[-1] == 'Mình muốn ưu tiên sự an toàn của bạn lúc này.'
    assert ('speech', 'Mình muốn ưu tiên sự an toàn của bạn lúc này.') in calls
    assert any(m.get('emotion') == 'caring' for m in messages)


def test_greeting_is_synthesised_once_and_replayed(gateway):
    client, _, token, calls, _ = gateway
    for _ in range(2):
        with connect(client, token) as ws:
            hello(ws)
    assert calls.count(('speech', GREETING)) == 1


def test_long_sentences_are_spoken_clause_by_clause():
    parts = sentences('Nghe bạn nói mệt sau ca làm, mình thấy rõ sự vất vả đó. Bạn có thể kể thêm về ca làm, '
                      'và lúc về nhà thì bạn thường làm gì để nghỉ ngơi?')
    assert parts[0] == 'Nghe bạn nói mệt sau ca làm,' and parts[1].startswith('mình thấy rõ')
    assert parts[2] == 'Bạn có thể kể thêm về ca làm,' and parts[3].startswith('và lúc về nhà')
    assert sentences('Mình đang nghe bạn.') == ['Mình đang nghe bạn.']


def test_streamed_opus_matches_whole_clip_length():
    mp3 = speech_mp3()
    assert len(opus_frames(mp3)) >= 2  # 0.1 s of speech plus the encoder tail


def test_unsupported_audio_is_rejected(gateway):
    client, _, token, _, _ = gateway
    with connect(client, token) as ws:
        ws.send_json({'type': 'hello', 'audio_params': {'sample_rate': 48000}})
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
        assert exc.value.code == 1003


def test_malformed_messages_do_not_crash_connection(gateway):
    client, _, token, _, _ = gateway
    with connect(client, token) as ws:
        ws.send_text('{')
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()
    with connect(client, token) as ws:
        hello(ws)
        ws.send_json([])
        ws.send_text('{')
        send_turn(ws)
        assert receive_turn(ws)[1]


def test_endpointer_detects_speech_without_initial_silence_and_bounds_long_wait():
    endpoint = Endpointer(5)
    quiet = b'\0' * 1920
    loud = array.array('h', [6000, -6000] * 480).tobytes()
    for _ in range(200):
        assert not endpoint.add(quiet)
    assert len(endpoint.pcm) <= 32000
    assert not endpoint.add(loud)
    assert not endpoint.add(loud)
    assert not endpoint.add(loud)
    assert endpoint.speaking
    pause = END_SILENCE_MS//FRAME_MS
    for _ in range(pause-1):  # a pause between sentences does not end the turn
        assert not endpoint.add(quiet)
    assert endpoint.add(quiet)
    endpoint.reset()
    for _ in range(3):
        endpoint.add(loud)
    assert endpoint.speaking


def frame(amplitude, seed):
    """60 ms of noise-like audio at a given RMS-ish amplitude."""
    rng = random.Random(seed)
    return array.array('h', [int(rng.gauss(0, amplitude)) for _ in range(960)]).tobytes()


def test_endpointer_ends_turn_in_a_noisy_cafe():
    # Background chatter well above the fixed quiet-room level used to stall at 45 s.
    endpoint = Endpointer(45)
    ended = [endpoint.add(frame(900, n)) for n in range(120)]
    # Within seconds, not 45 s, the chatter is learned as background (an empty
    # transcript for that stretch keeps the robot listening).
    assert any(ended[:110])
    endpoint.reset()
    # Speech with short gaps between words, then the person stops talking.
    for n in range(50):
        level = 6000 if n % 6 else 1000
        assert not endpoint.add(frame(level, 100 + n))
    assert endpoint.speaking
    ended_after = None
    for n in range(60):
        if endpoint.add(frame(900, 200 + n)):
            ended_after = n + 1
            break
    assert ended_after is not None and ended_after * FRAME_MS <= END_SILENCE_MS + 300
    # The room's level is remembered for the next turn.
    endpoint.reset()
    for n in range(10):
        assert not endpoint.add(frame(900, 300 + n))
    assert not endpoint.speaking
