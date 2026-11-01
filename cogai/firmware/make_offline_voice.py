"""Generate the bundled Vietnamese network-error clip; no credentials or API key."""
import asyncio
import array
import io
from pathlib import Path

import av
import edge_tts

MESSAGE = 'Mất kết nối.'


async def main():
    mp3 = bytearray()
    async for chunk in edge_tts.Communicate(MESSAGE, 'vi-VN-HoaiMyNeural').stream():
        if chunk['type'] == 'audio':
            mp3.extend(chunk['data'])
    destination = Path(__file__).parent / 'xiaozhi-esp32/main/boards/ricky-war-tank/network_error.ogg'
    pcm = bytearray()
    with av.open(io.BytesIO(mp3), format='mp3') as source:
        resampler = av.AudioResampler(format='s16', layout='mono', rate=24000)
        for frame in source.decode(audio=0):
            for converted in resampler.resample(frame):
                pcm.extend(bytes(converted.planes[0])[:converted.samples * 2])
        for converted in resampler.resample(None):
            pcm.extend(bytes(converted.planes[0])[:converted.samples * 2])
    samples = array.array('h', pcm)
    active = [i for i, value in enumerate(samples) if abs(value) > 100]
    if not active:
        raise RuntimeError('Speech provider returned silence.')
    # Edge appends silence. Keep 60 ms padding around actual speech; the clip
    # must fit the 1.2 s queue without making the firmware event loop wait.
    samples = samples[max(0, active[0] - 1440):min(len(samples), active[-1] + 1441)]
    if len(samples) > 24000 * 1.1:
        raise RuntimeError('Offline prompt exceeds 1.1 seconds; use a shorter phrase.')
    with av.open(str(destination), 'w', format='ogg') as output:
        stream = output.add_stream('libopus', rate=24000)
        stream.layout = 'mono'
        stream.codec_context.options = {'frame_duration': '60', 'application': 'voip'}
        frame = av.AudioFrame(format='s16', layout='mono', samples=len(samples))
        frame.planes[0].update(samples.tobytes())
        frame.sample_rate = 24000
        for packet in stream.encode(frame):
            output.mux(packet)
        for packet in stream.encode(None):
            output.mux(packet)
    print(f'Bundled offline voice: {destination.name}, {destination.stat().st_size} bytes')


if __name__ == '__main__':
    asyncio.run(main())
