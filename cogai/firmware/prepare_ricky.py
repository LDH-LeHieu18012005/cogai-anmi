"""Register the canonical Ricky board without overwriting source or settings."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent / 'xiaozhi-esp32'
board = root / 'main/boards/ricky-war-tank'
for name in ('config.h', 'config.json', 'ricky_war_tank.cc', 'network_error.ogg'):
    if not (board / name).is_file():
        raise SystemExit(f'Missing canonical board file: {name}')
config = json.loads((board / 'config.json').read_text('utf-8'))
if config['type'] != 'ricky-war-tank' or config['target'] != 'esp32s3':
    raise SystemExit('Unexpected board identity.')

kconfig = root / 'main/Kconfig.projbuild'
text = kconfig.read_text('utf-8')
if 'config BOARD_TYPE_RICKY_WAR_TANK\n' not in text:
    marker = '    config BOARD_TYPE_RYMCU_BIGSMART\n'
    if marker not in text:
        raise SystemExit('Unsupported upstream board menu.')
    entry = '    config BOARD_TYPE_RICKY_WAR_TANK\n        bool "Ricky War Tank (AnMi, motors disabled)"\n        depends on IDF_TARGET_ESP32S3\n\n'
    text = text.replace(marker, entry + marker, 1)
marker = 'choice DISPLAY_OLED_TYPE\n    depends on '
if marker + 'BOARD_TYPE_RICKY_WAR_TANK || ' not in text:
    if marker not in text:
        raise SystemExit('Unsupported upstream OLED selection.')
    text = text.replace(marker, marker + 'BOARD_TYPE_RICKY_WAR_TANK || ', 1)
if text != kconfig.read_text('utf-8'):
    kconfig.write_text(text, 'utf-8', newline='\n')

cmake = root / 'main/CMakeLists.txt'
text = cmake.read_text('utf-8')
if 'if(CONFIG_BOARD_TYPE_RICKY_WAR_TANK)' not in text:
    marker = 'if(CONFIG_BOARD_TYPE_BREAD_COMPACT_WIFI)'
    if marker not in text:
        raise SystemExit('Unsupported upstream CMake board selection.')
    text = text.replace(marker, '''if(CONFIG_BOARD_TYPE_RICKY_WAR_TANK)
    set(BOARD_DIR "ricky-war-tank")
    set(BUILTIN_TEXT_FONT font_noto_sans_basic_14_1)
    set(BUILTIN_ICON_FONT font_material_symbols_14_1)
elseif(CONFIG_BOARD_TYPE_BREAD_COMPACT_WIFI)''', 1)
if 'set(BOARD_EXTRA_EMBED_FILES' not in text:
    text = text.replace('    set(BOARD_DIR "ricky-war-tank")', '    set(BOARD_DIR "ricky-war-tank")\n    set(BOARD_EXTRA_EMBED_FILES "${CMAKE_CURRENT_SOURCE_DIR}/boards/ricky-war-tank/network_error.ogg")', 1)
    text = text.replace('EMBED_FILES ${LANG_SOUNDS} ${COMMON_SOUNDS}', 'EMBED_FILES ${LANG_SOUNDS} ${COMMON_SOUNDS} ${BOARD_EXTRA_EMBED_FILES}', 1)
if text != cmake.read_text('utf-8'):
    cmake.write_text(text, 'utf-8', newline='\n')
print('Ricky registered. Canonical board source, GPIO and user settings preserved.')
