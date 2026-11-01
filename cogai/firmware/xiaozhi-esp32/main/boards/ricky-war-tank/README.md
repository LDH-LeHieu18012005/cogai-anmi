# Ricky War Tank / AnMi

Custom ESP32-S3 board, 16 MB flash and 8 MB octal PSRAM. Pin assignments
come from the original firmware analysis supplied by the operator on 2026-10-26.
This board has not yet been compiled or validated on physical hardware.

| Function | GPIO |
|---|---|
| Microphone WS / SCK / DIN | 4 / 5 / 6 |
| Speaker DOUT / BCLK / LRCK | 7 / 15 / 16 |
| BOOT button | 0 |
| WS2812 RGB LED | 48 |
| SSD1306 SDA / SCL | 41 / 42, address 0x3C |
| Motor driver inputs | 39 / 40 / 43 / 44, held LOW |

UART output on 43/44 is disabled by selecting USB Serial/JTAG console.
No motor control tools are registered. A missing OLED falls back to NoDisplay.
The selected display is 128x64; the physical panel dimensions still need checking.

Build with ESP-IDF release/v6.1:

```sh
python3 scripts/build.py ricky-war-tank --name ricky-war-tank --language vi-VN --wake-word disabled
```

Set the OTA URL to `http://<laptop LAN IP>:8000/xiaozhi/ota/` in Wi-Fi setup.
The default `anmi.local` is only a placeholder and requires name resolution.
Register the station MAC with CogAI before connecting. Use a trusted LAN.
An offline spoken fallback and verified support-number configuration remain to
be implemented before hardware acceptance. Do not flash a bread-compact-wifi
image: that board uses motor pins as volume buttons.
