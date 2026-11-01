"""Check the bundled clip with the firmware's actual Ogg/Opus demuxer on Linux."""
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent / 'xiaozhi-esp32'
if not root.is_dir():
    root = Path(__file__).resolve().parent / 'firmware'
with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory)
    (temp / 'esp_log.h').write_text('#pragma once\n#define ESP_LOGE(...)\n#define ESP_LOGW(...)\n#define ESP_LOGD(...)\n#define ESP_LOGI(...)\n')
    driver = temp / 'verify.cc'
    driver.write_text(r'''
#include "ogg_demuxer.h"
#include <algorithm>
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
int main(int argc, char** argv) {
    assert(argc == 2);
    std::ifstream input(argv[1], std::ios::binary);
    assert(input.good());
    std::vector<uint8_t> audio((std::istreambuf_iterator<char>(input)), {});
    OggDemuxer demuxer;
    int packets = 0;
    demuxer.OnPacket([&](const uint8_t*, int rate, int duration, size_t size) {
        assert(rate == 24000 && duration == 60 && size > 0 && size <= 2048);
        ++packets;
    });
    size_t offset = 0;
    while (offset < audio.size()) {
        auto count = demuxer.Process(audio.data() + offset, std::min<size_t>(127, audio.size() - offset));
        assert(count > 0);
        offset += count;
    }
    // The local alert must fit the firmware's 1.2 s decode queue, so calling
    // PlaySound from the main event loop never waits for playback to progress.
    assert(demuxer.Finish() && !demuxer.HasError() && packets > 0 && packets <= 20);
    std::cout << "Offline voice valid: " << packets << " mono Opus packets at 24 kHz / 60 ms\n";
}
''')
    demux = root / 'main/audio/demuxer'
    binary = temp / 'verify'
    subprocess.run(['c++', '-std=c++17', '-I' + str(temp), '-I' + str(demux),
                    str(driver), str(demux / 'ogg_demuxer.cc'), '-o', str(binary)], check=True)
    subprocess.run([str(binary), str(root / 'main/boards/ricky-war-tank/network_error.ogg')], check=True)
