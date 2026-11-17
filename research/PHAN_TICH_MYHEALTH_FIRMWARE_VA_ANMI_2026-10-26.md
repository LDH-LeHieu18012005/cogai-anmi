# Phân tích firmware MyHealth và khả năng tích hợp AnMi

Ngày kiểm tra: 26/10/2026. Phương pháp: đọc tĩnh file nhị phân tại workspace, phân tích header/segment/partition, kiểm tra checksum và hash nhúng, đọc chuỗi ASCII/UTF-8, đối chiếu mã backend AnMi và tài liệu nguồn chính thức. Không chạy firmware, không nạp thiết bị, không kết nối tới máy chủ được tìm thấy trong file.

## 1. Kết luận về file

`MyHealth-EchoEar-ESP32S3-N16R8-full.bin` là ảnh flash đầy đủ cho ESP32-S3, có bootloader ở đầu file, bảng phân vùng, ứng dụng và tài nguyên giao diện/nhận dạng giọng đánh thức. Dấu vết trong chương trình cho thấy đây là firmware thuộc họ XiaoZhi, được tùy biến cho MyHealth/EchoEar. Chưa xác định được chính xác repository, commit hoặc tác giả của bản tùy biến.

Đây là chương trình đã biên dịch để nạp vào vi điều khiển. Nó không phải mã nguồn, ứng dụng Windows, hay toàn bộ hệ thống AI AnMi. Thiết bị đảm nhận thu/phát âm thanh, giao diện và truyền thông; hội thoại thông minh cần backend tương thích. Có thành phần nhận giọng đánh thức cục bộ, nhưng không có căn cứ cho rằng mô hình hội thoại lớn chạy ngay trên ESP32.

### Dữ kiện trực tiếp từ file

| Thuộc tính | Kết quả |
|---|---|
| Kích thước | 16.777.216 byte = 16 MiB |
| SHA-256 toàn file | `ba1cd1e3db21c729c607cc6776032fa8d745c262efa490d0a6a32e03070593cd` |
| Chip ID trong bootloader và ứng dụng | `9`, tương ứng ESP32-S3 |
| Flash khai báo trong header | 16 MB, DIO, 80 MHz |
| Tên project trong application descriptor | `poseai` |
| Phiên bản ứng dụng | `2.0.0-dev` |
| Thời điểm build tự khai báo | `Oct 7 2026`, `17:10:01`; không có múi giờ |
| ESP-IDF tự khai báo | `v5.5.3` |
| ELF SHA-256 ghi trong descriptor | `c8e83da63dc0951fa6c0e5d39dc566ab222e64cc40f27df7d22a3c19186e6406` |
| Dấu vết tùy biến | `MyHealth`, `MyHealthFace`, `myhealth-echoear`, `./main/boards/echoear/EchoEar.cc` |
| Dấu vết nền tảng | `XIAOZHI_STATE_EVENTS`, `WebsocketProtocol`, `OpusEncoderWrapper`, `OpusDecoderWrapper` |

Thời điểm build là metadata do quá trình build ghi vào, không phải chứng thực độc lập về ngày tạo file. Tên `poseai` không chứng minh một mô hình AI hay nhà cung cấp cụ thể.

`N16R8` trong tên file thường chỉ cấu hình 16 MB flash, 8 MB PSRAM. Phân tích xác nhận cấu hình flash 16 MB; dung lượng PSRAM thực tế và phiên bản PCB phải xác minh trên thiết bị. Các sản phẩm mang tên EchoEar có nhiều biến thể, không thể chọn firmware chỉ theo tên hoặc dung lượng bộ nhớ.

### Bố cục flash

| Thành phần | Địa chỉ bắt đầu | Dung lượng vùng | Ý nghĩa |
|---|---:|---:|---|
| Bootloader | `0x000000` | Trước bảng phân vùng | Khởi động chương trình |
| Partition table | `0x008000` | Bảng nằm trong vùng 4 KiB | Mô tả các phân vùng |
| `nvs` | `0x009000` | 16 KiB | Cấu hình lưu bền vững |
| `otadata` | `0x00D000` | 8 KiB | Trạng thái chọn ứng dụng OTA |
| `phy_init` | `0x00F000` | 4 KiB | Vùng dữ liệu PHY |
| `ota_0` | `0x010000` | 4 MiB | Ứng dụng hiện có |
| `ota_1` | `0x410000` | 4 MiB | Vùng ứng dụng dự phòng, đang toàn `0xFF` |
| `assets` | `0x810000` | 8.323.072 byte, khoảng 7,94 MiB | Font, biểu cảm, tài nguyên âm thanh/mô hình đánh thức |

Ứng dụng, bao gồm hash cuối ảnh, dài 2.177.392 byte. Vì vậy 16 MiB không phải dung lượng riêng của mã chương trình: file bao gồm tài nguyên và nhiều vùng đệm trống.

Kết quả kiểm tra:

- XOR checksum từng ảnh bootloader và ứng dụng: khớp.
- SHA-256 nhúng của từng ảnh bootloader và ứng dụng: khớp.
- MD5 bảng phân vùng: khớp, `0c490bdad83140aa056fb52f68f75e49`.
- Các vùng `nvs`, `otadata`, `ota_1` trong file đều toàn `0xFF`. Không có cấu hình Wi-Fi đã lưu trong NVS của ảnh này; vẫn có địa chỉ server mặc định được biên dịch vào ứng dụng.

Các kiểm tra này xác nhận tính toàn vẹn nội bộ của những cấu trúc đã kiểm tra. Chúng không xác thực tác giả, không chứng minh firmware an toàn, cũng không thay thế kiểm tra chạy trên phần cứng.

## 2. Chương trình có những gì?

### Kết nối máy chủ

Có địa chỉ sau trong ứng dụng:

```text
wss://intercommunicable-dupable-tim.ngrok-free.dev/xiaozhi/v1/
```

Đây là dấu vết về một endpoint WebSocket mặc định thông qua ngrok. Chưa kiểm tra nó còn hoạt động hay thuộc về ai. Không thể suy ra model AI, prompt, cơ sở dữ liệu hay mức bảo mật của backend chỉ từ URL này.

Có các tên header `Authorization`, `Protocol-Version`, `Device-Id`, `Client-Id`, phù hợp giao thức thiết bị XiaoZhi. Có cả mã/thông báo thư viện MQTT, nhưng sự hiện diện của thư viện không chứng minh cấu hình vận hành thực tế dùng MQTT.

### Trang cấu hình cục bộ

Nhúng sẵn HTML/JavaScript tiếng Việt, với:

- Trường `ws_url`: “Địa chỉ máy chủ hội thoại”.
- Trường `token`: “Token thiết bị”.
- Địa chỉ cục bộ `http://192.168.4.1/`.
- Các đường dẫn `/scan`, `/config`, `/reboot`.
- Mã phía trình duyệt kiểm tra scheme `ws:`/`wss:`.
- Hướng dẫn rằng để trống token khi lưu sẽ thay thế token cũ.

Điều này cho thấy firmware được thiết kế để người dùng đổi server mà không cần biên dịch lại. Việc lưu cấu hình, kết nối và xác thực có hoạt động đúng hay không cần kiểm tra trên thiết bị.

### Âm thanh và biểu cảm

Có dấu vết Opus encode/decode, resampling, ESP-SR/WakeNet và driver codec ES8311/ES7210. Đây là bằng chứng về các thành phần phần mềm có trong ảnh, không phải phép đo xác nhận chip thật trên PCB.

Vùng assets có bảng tên tài nguyên: `font_puhui_common_20_4.bin`, `srmodels.bin`, các icon pin/Wi-Fi/micro/loa, `Happy.eaf`, `Sad.eaf`, `angry.eaf`, `confused.eaf`, `cry.eaf`, `listen.eaf`, `neutral.eaf`, `shocked.eaf`, `sleep.eaf`, `winking.eaf`, `index.json`.

Có thông báo `Face A ready: 12 moods, 20 fps target`. Đây là mục tiêu/khai báo trong mã, chưa phải kết quả đo số biểu cảm hoạt động hay tốc độ hiển thị thực tế. Có thông báo yêu cầu nạp đầy đủ assets nếu thiếu tài nguyên EchoEar.

## 3. Muốn tự làm ra file tương tự cần gì?

Cần phân biệt ba việc:

1. **Nạp lại ảnh có sẵn:** cần đúng thiết bị và công cụ flash. Chưa cần mã nguồn.
2. **Cho thiết bị nói chuyện bằng AnMi:** cần backend hiểu giao thức của firmware. Với bản này có thể thử đổi `ws_url` trước.
3. **Tự build firmware AnMi mang nhận diện riêng:** cần source firmware, cấu hình phần cứng, tài nguyên và toolchain.

### Để tái tạo đúng bản MyHealth này

Nên lấy từ người cung cấp firmware:

- Repository và commit của bản tùy biến MyHealth, đặc biệt mã `MyHealthFace` và `main/boards/echoear/EchoEar.cc`.
- `sdkconfig`, `sdkconfig.defaults`, bảng phân vùng CSV.
- `idf_component.yml`, `dependencies.lock` và các component được sửa riêng.
- Assets gốc và công cụ đóng gói chúng.
- Phiên bản ESP-IDF/toolchain; ảnh hiện tại ghi `v5.5.3`.
- Schematic, BOM, pin map, phiên bản PCB và thông tin màn hình/touch/audio.
- Source hoặc đặc tả backend `/xiaozhi/v1/`, gồm sự kiện riêng nếu có.
- Lệnh build, `flash_args` hoặc `flasher_args.json`, và thông tin giấy phép tài nguyên.

File `.bin` cho phép phân tích và có thể giải mã ngược một phần, nhưng không khôi phục nguyên vẹn source, comment, cấu trúc dự án và quy trình build. Không có source vẫn có thể xây firmware tương đương từ XiaoZhi; chưa thể hứa tái tạo đúng từng byte bản MyHealth.

### Quy trình build thông thường

1. Chốt đúng board: GPIO, màn hình, touch, codec, mic, loa, PSRAM, nguồn và nút bấm.
2. Chọn commit firmware, dùng phiên bản ESP-IDF mà commit đó yêu cầu. Không lấy nhánh mới nhất rồi mặc định dùng IDF 5.5.3: README upstream hiện yêu cầu IDF 6.x.
3. Trong môi trường ESP-IDF đã thiết lập, chọn `esp32s3`, cấu hình đúng board, flash/PSRAM, ngôn ngữ, giao thức, assets và phân vùng.
4. Biên dịch, kiểm tra kích thước ứng dụng, đóng gói assets và ghép ảnh theo đúng địa chỉ từ kết quả build.
5. Nạp lên một thiết bị thử, đọc serial log, kiểm tra màn hình, mic, loa, Wi-Fi và kết nối server.
6. Giữ source, commit, cấu hình, dependency lock và checksum cùng mỗi bản phát hành.

Ví dụ lệnh định hướng, chưa chạy và không đủ để tự tái tạo bản MyHealth khi thiếu source/cấu hình:

```powershell
idf.py set-target esp32s3
idf.py menuconfig
idf.py build
```

Với esptool đời mới, có thể ghép theo `flash_args` do build sinh ra. Cần xác nhận assets đã có trong danh sách; nếu không phải thêm theo bảng phân vùng của chính build:

```powershell
# Chạy từ thư mục build của dự án firmware đã cấu hình hoàn chỉnh.
esptool --chip esp32s3 merge-bin -o AnMi-full.bin --pad-to-size 16MB '@flash_args'
```

Các đời esptool cũ có thể dùng tên lệnh dạng gạch dưới. Không trộn ví dụ CLI của hai phiên bản. Ảnh hiện tại có bootloader ở offset 0 nên phù hợp dạng full image nạp tại `0x0`; chỉ thực hiện sau khi xác minh board và sao lưu thiết bị. Nạp toàn bộ ảnh này sẽ ghi đè cả vùng cấu hình NVS.

## 4. AnMi hiện có gì và còn thiếu gì?

Đã đọc mã hiện tại trong `cogai/backend/app`, không đọc khóa API hay file `.env`.

| Thành phần | Bằng chứng trong mã | Ý nghĩa khi tích hợp thiết bị |
|---|---|---|
| Lõi hội thoại | `dialogue.py`, `Dialogue.chat()` | Có thể dùng chung giữa web và thiết bị |
| API chat | `main.py:247`, `POST /api/chat` | Đầu vào văn bản qua HTTP, chưa phải endpoint XiaoZhi |
| Hội thoại bằng giọng nói | `voice.py:268`, `POST /api/voice/turn` | Có quy trình nhận âm thanh → transcript → hội thoại → giọng đọc |
| Định dạng nhận vào | `voice.py:139`, `read_audio()` | WebM/Ogg/WAV/MP4 có container; chưa trực tiếp nhận từng frame Opus thô |
| Giọng đọc | `config.py`, `voice.py` | Có adapter giọng đọc; cần chuyển đầu ra về dạng âm thanh thiết bị nhận được |
| Phiên người dùng | `main.py:142`, cookie `cogai_session` | Cần cơ chế ghép đôi và xác thực thiết bị gắn đúng tài khoản |
| Quyền xử lý giọng nói | `voice.py:116`, `authorized()` | Thiết bị cần đi qua cùng quyền đồng ý và kiểm tra trạng thái |
| Cổng WebSocket XiaoZhi | Không tìm thấy khai báo trong `backend/app` hiện tại | Phần tích hợp chính cần bổ sung |

**Không thể chỉ nhập URL `/api/chat` vào firmware là dùng được.** Hai bên khác giao thức, định dạng âm thanh và cách xác thực.

Luồng tích hợp tham khảo, chưa phải thiết kế đã chốt:

```text
Mic/loa/màn hình EchoEar
          ↕ Wi-Fi, WebSocket và Opus
Cổng thiết bị tương thích XiaoZhi
          ↕ đổi âm thanh, ghép phiên, chuyển sự kiện
STT → lõi hội thoại AnMi → kiểm tra đầu ra → TTS
```

Cổng thiết bị cần xử lý:

- Handshake và cặp thông điệp `hello`; thương lượng version, codec, sample rate, frame duration theo client thật.
- Frame âm thanh nhị phân, thông điệp điều khiển `listen`, `abort`, trạng thái STT/TTS và kết thúc lượt.
- Đóng gói hoặc giải mã Opus đầu vào thành định dạng STT nhận được. Frame Opus thô không phải file Ogg/WebM hoàn chỉnh.
- Chuyển MP3/WAV đầu ra TTS thành luồng Opus đúng thông số đã thương lượng.
- Ánh xạ `emotion` và trạng thái nghe/nghĩ/nói sang giao diện thiết bị, bao gồm các mở rộng MyHealth nếu có.
- Token riêng cho thiết bị, ghép đôi tài khoản, thu hồi quyền và tách ngữ cảnh giữa người dùng. MAC address chỉ là định danh, không đủ làm bí mật xác thực.
- Hủy lượt cũ khi người dùng ngắt lời, reconnect, timeout và giới hạn bộ nhớ/thời lượng.
- Dùng lại kiểm tra an toàn đầu vào/đầu ra và quyền đồng ý của AnMi; chỉ phát nội dung được phép phục vụ.

Tài liệu XiaoZhi là điểm bắt đầu. Bản MyHealth là bản tùy biến nên cần đối chiếu log và message thật; không mặc định mọi chi tiết của tài liệu upstream mới nhất đều tương thích.

## 5. Các hướng thực hiện có thể chọn

| Hướng | Làm gì | Ưu điểm | Phần đánh đổi |
|---|---|---|---|
| Giữ firmware, thêm cổng thiết bị cho AnMi | Dùng trang cấu hình đổi `ws_url`/token tới backend của mình | Nhanh kiểm chứng kết nối, tận dụng lõi AnMi hiện có | Vẫn mang nhận diện MyHealth và phụ thuộc hành vi firmware đóng |
| Build firmware AnMi từ source phù hợp | Tùy biến tên, màn hình, biểu cảm, cấu hình kết nối và cập nhật | Chủ động sản phẩm và phát hành | Cần source/board/assets, công cụ build và kiểm thử phần cứng |
| Dùng server XiaoZhi nguồn mở làm cầu nối | Tận dụng phần xử lý thiết bị/âm thanh, tích hợp lõi AnMi | Có sẵn nhiều chức năng thiết bị | Thêm hệ thống để vận hành; phải kiểm soát việc lưu phiên, dữ liệu và đường đi qua lõi AnMi |

Khuyến nghị nghiên cứu: kiểm chứng hướng thứ nhất trên một thiết bị trước. Khi mic → AnMi → loa đã hoạt động, mới quyết định giữ hay thay firmware để làm thương hiệu và giao diện riêng. Nếu hiện chỉ có file, có thể kiểm tra giao thức bằng client giả lập nhưng kết quả đó chưa chứng minh thiết bị thật hoạt động.

## 6. Mốc kiểm chứng để biết đã làm được

1. **Thiết bị khởi động:** xác minh model/PCB, flash/PSRAM, serial log và assets.
2. **Kết nối:** lưu địa chỉ server, handshake thành công, xác thực thiết bị và nhận `hello`.
3. **Một lượt nói:** lời người dùng → transcript tiếng Việt → trả lời từ đúng lõi AnMi → loa phát và kết thúc đúng trạng thái.
4. **Hội thoại liên tục:** nhiều lượt giữ ngữ cảnh, ngắt lời hủy âm thanh cũ, mất mạng kết nối lại ổn định.
5. **Tách người dùng:** đổi tài khoản/thu hồi token không rò lịch sử hay tiếp tục phục vụ phiên cũ.
6. **Chất lượng thực tế:** đo độ trễ từ dừng nói tới âm thanh đầu tiên, nghe thử ở môi trường có tiếng nền, kiểm tra tự thu lại tiếng loa và độ ổn định nguồn.
7. **Tự phát hành:** build lại từ source và assets đã khóa phiên bản, tạo ảnh full có manifest/checksum, thử cập nhật và khôi phục.

Chưa có phép đo độ trễ, chất lượng tiếng Việt, AEC, thời lượng pin, độ ổn định hoặc kết quả chạy trên phần cứng trong lần kiểm tra này. Chưa xác minh backend cũ đang hoạt động. Chưa có căn cứ để đưa ra thời gian/chi phí triển khai chính xác khi chưa chốt thiết bị và phạm vi.

## 7. Nguồn đối chiếu

- [Espressif: định dạng firmware ESP32-S3](https://docs.espressif.com/projects/esptool/en/latest/esp32s3/advanced-topics/firmware-image-format.html): cấu trúc header, segment, checksum, SHA-256.
- [Espressif: esptool basic commands](https://docs.espressif.com/projects/esptool/en/latest/esp32s3/esptool/basic-commands.html): đọc/ghi flash, ghép ảnh, padding và flash arguments.
- [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32): firmware nền, tính năng âm thanh, SDK yêu cầu của nhánh hiện tại.
- [XiaoZhi WebSocket protocol](https://github.com/78/xiaozhi-esp32/blob/main/docs/websocket.md): handshake, frame âm thanh và sự kiện điều khiển.
- [EchoEar README ở tag v2.0.5](https://github.com/78/xiaozhi-esp32/blob/v2.0.5/main/boards/echoear/README.md): ví dụ lịch sử về chọn board, build, assets và bố cục flash. Tag này chỉ để tham khảo, chưa được xác định là nguồn của file MyHealth.
- [XiaoZhi custom board guide](https://raw.githubusercontent.com/78/xiaozhi-esp32/main/docs/custom-board.md): pin map, cấu hình board, nhận diện riêng và kênh cập nhật.
- [xinnan-tech/xiaozhi-esp32-server](https://github.com/xinnan-tech/xiaozhi-esp32-server): một lựa chọn backend nguồn mở để tham khảo phần giao tiếp thiết bị.

Các kết luận cụ thể về file MyHealth xuất phát từ file tại workspace; các liên kết trên giải thích định dạng và hệ sinh thái, không xác thực tác giả của firmware này.

## 8. Bổ sung: robot trắng/tím trong ảnh và link Shopee người dùng cung cấp

### Phạm vi xác minh

Người dùng xác nhận đang có thiết bị khác với EchoEar, gửi ảnh robot vỏ trắng, viền mặt tím, hai sừng, màn hình chữ nhật và link sản phẩm:

`https://shopee.vn/product/280566046/44719511159`

Trang Shopee không truy cập được bằng công cụ duyệt web trong phiên này; tìm kiếm theo mã sản phẩm chưa trả về tài liệu kỹ thuật xác định. Không được coi thông số của EchoEar hoặc file MyHealth là thông số của robot này.

Đã đọc HTML và JavaScript công khai của `xiaozhi.vn`. Trong [data/items.js](https://xiaozhi.vn/data/items.js) có mục `Monster Desk` với ảnh `data/hinhtb/aio/monter.webp`, nhưng các trường `manifest`, `diagram`, `download`, `diyUrl` ở mục đó đang trống. Đây là đầu mối về tên thương mại, chưa chứng minh cùng nhà bán, cùng sản phẩm hoặc cùng bo mạch với link Shopee. Không dùng thông tin này để khẳng định chip, độ phân giải, codec hoặc GPIO của thiết bị người dùng.

Từ ảnh chỉ xác nhận được hình dáng và màn hình chữ nhật; chưa xác định loại LCD/OLED, kích thước, độ phân giải, touch, số micro, công suất loa, pin, chip hay dung lượng bộ nhớ.

### Khả năng tận dụng repo 78/xiaozhi-esp32

Repo người dùng gửi là nền firmware phù hợp để nghiên cứu tích hợp. Nó có các lớp board, audio và protocol để dùng lại, nhưng không có căn cứ chọn một board cụ thể chỉ từ vỏ robot.

Phải đối chiếu ít nhất:

| Thông tin thiết bị thật | Quyết định kỹ thuật phụ thuộc vào nó |
|---|---|
| Chip và module chính xác | Target build và tính năng audio được hỗ trợ |
| Flash, PSRAM và mode bộ nhớ | Cấu hình SDK, phân vùng và giới hạn tài nguyên |
| Model/revision PCB, board type firmware hiện tại | Có thể dùng board có sẵn hay cần port |
| Driver, bus, độ phân giải, GPIO màn hình | Driver và cách hiển thị biểu cảm/font |
| Micro, codec/ampli, bus và GPIO audio | Thu âm/phát loa, gain và đường tham chiếu AEC |
| USB/UART, nút BOOT/RESET và firmware gốc | Cách đọc log, sao lưu, nạp và phục hồi |
| Menu cấu hình server, OTA/bootstrap hiện tại | Có thể giữ firmware hay phải build mới |

Đặc biệt: “cùng ESP32-S3 N16R8” chưa đủ để tương thích. Không nạp ảnh EchoEar/MyHealth lên robot này khi chưa đối chiếu phần cứng.

### Phát hiện mới từ mã upstream: có thể đổi backend qua bootstrap

Đã đọc trực tiếp các file upstream:

- [`main/Kconfig.projbuild`](https://raw.githubusercontent.com/78/xiaozhi-esp32/main/main/Kconfig.projbuild): có cấu hình `OTA_URL`; mô tả dùng endpoint này để kiểm tra phiên bản và lấy địa chỉ server.
- [`main/boards/common/wifi_board.cc`](https://raw.githubusercontent.com/78/xiaozhi-esp32/main/main/boards/common/wifi_board.cc): bật hiển thị cấu hình OTA trong Wi-Fi manager của upstream hiện tại.
- [`main/ota.cc`](https://raw.githubusercontent.com/78/xiaozhi-esp32/main/main/ota.cc): đọc `wifi/ota_url`, xử lý phần JSON `websocket` và lưu cấu hình đó vào NVS.
- [`main/application.cc`](https://raw.githubusercontent.com/78/xiaozhi-esp32/main/main/application.cc): chọn MQTT nếu phản hồi bootstrap có cấu hình MQTT, nếu không thì chọn WebSocket khi có cấu hình WebSocket.
- [`main/protocols/websocket_protocol.cc`](https://raw.githubusercontent.com/78/xiaozhi-esp32/main/main/protocols/websocket_protocol.cc): đọc `url`, `token`, `version` từ namespace `websocket`.

Hệ quả: với firmware có giữ hành vi upstream tương ứng, đôi khi chỉ cần đổi địa chỉ OTA/bootstrap để server của mình cấp địa chỉ WebSocket. Không bắt buộc phải thay firmware chỉ để đổi backend. Nhưng firmware trên máy Shopee chưa được đọc, nên đây là một khả năng cần kiểm chứng, không phải tính năng đã xác nhận trên máy đó.

Phân biệt ba loại địa chỉ:

- **OTA/bootstrap URL:** HTTP(S), trả JSON cấu hình, thời gian và thông tin cập nhật khi cần.
- **WebSocket URL:** WS(S), kênh hội thoại âm thanh.
- **Firmware download URL:** HTTP(S), tải file chương trình để cập nhật.

Không nhập một WebSocket URL vào ô OTA URL. Tên mục “OTA” cũng không có nghĩa mọi lần truy cập đều phải tải/nạp firmware.

Ví dụ phần JSON cấu hình hội thoại mà mã upstream hiện tại có thể đọc, chỉ để giải thích cấu trúc; chưa phải phản hồi bootstrap hoàn chỉnh đã kiểm thử cho robot:

```json
{
  "websocket": {
    "url": "wss://anmi.example/xiaozhi/v1/",
    "token": "DEVICE_TOKEN",
    "version": 1
  }
}
```

`anmi.example` là miền minh họa, không phải server đã triển khai. Nếu chọn hướng WebSocket, bootstrap không nên đồng thời cấp cấu hình MQTT khiến firmware chọn đường khác. Chi tiết activation, thời gian hệ thống và protocol version phải khớp phiên bản firmware thực tế.

### Ba tình huống triển khai

1. **Firmware hiện tại cho đổi WebSocket trực tiếp:** thêm cổng thiết bị vào AnMi, cấu hình URL/token, thử nguyên firmware hiện tại.
2. **Chỉ cho đổi OTA/bootstrap:** bổ sung endpoint bootstrap và cổng WebSocket vào AnMi, cấp cấu hình server qua JSON; có thể vẫn giữ firmware hiện tại nếu tương thích.
3. **Không đổi được backend hoặc cần giao diện AnMi riêng:** xác định board, lấy source/config phù hợp rồi build firmware AnMi. Nếu thiếu schematic cần thêm ảnh PCB, log và phân tích cấu hình; có thể phải port driver.

Đổi persona trên cloud XiaoZhi thành “AnMi” chỉ là đổi cấu hình hội thoại của dịch vụ đó. Nó không tự dùng lịch sử, dữ liệu, quyền đồng ý, chính sách và lõi hội thoại đang có trong backend CogAI. Thiết lập MCP cũng không tự biến toàn bộ luồng hội thoại thành backend AnMi.

### Phần mềm cần làm trên AnMi nếu chọn tích hợp trực tiếp

- Cổng thiết bị `/xiaozhi/v1/` hoặc đường dẫn tương đương do mình quản lý.
- Bootstrap nếu firmware cần lấy cấu hình qua OTA URL.
- Device registry, ghép đôi tài khoản và token thu hồi được.
- Audio adapter Opus vào/ra; xử lý các phiên bản frame theo client thật.
- Dùng lại lõi hội thoại, kiểm tra đầu ra và giọng đọc của AnMi; tách các adapter có thể tái sử dụng khỏi ngữ cảnh request trình duyệt.
- Trạng thái nghe/nghĩ/nói, emotion, hủy lượt cũ và khôi phục sau mất mạng.
- Máy chủ mà thiết bị truy cập được qua mạng, TLS phù hợp và chứng chỉ được firmware tin cậy. Địa chỉ `127.0.0.1` trên máy tính không phải địa chỉ backend dùng được từ robot.

### Thứ tự kiểm chứng được đề xuất

1. Ghi lại firmware version, board type, trang cấu hình và cách phục hồi. Xác nhận firmware gốc/backup trước khi ghi flash.
2. Kiểm tra khả năng đổi WebSocket hoặc OTA URL; chọn một trong ba tình huống trên.
3. Làm kết nối và một lượt nói tiếng Việt đi trọn qua backend AnMi.
4. Kiểm tra giữ ngữ cảnh đúng người dùng, ngắt lời, reconnect, quyền dữ liệu và đường xử lý hỗ trợ của AnMi.
5. Sau khi kênh thoại hoạt động mới thay biểu cảm, logo, tên hiển thị, rồi xem xét wake word riêng. Giao diện web SVG hiện tại không tự trở thành assets chạy trên màn hình vi điều khiển; wake word “AnMi” cũng cần hỗ trợ riêng từ engine/model đánh thức.

Không cần mua thêm model AI chỉ để đặt tên robot; cần phân biệt chi phí phần cứng, dịch vụ STT/LLM/TTS và máy chủ. Chưa đủ dữ liệu để ước tính ngân sách hay thời gian chính xác.

### Nội dung có thể hỏi người bán

> Mình muốn dùng thiết bị này với backend riêng dựa trên 78/xiaozhi-esp32. Bạn cho mình xin model/revision bo mạch, chip và dung lượng flash/PSRAM, board type đang dùng, link firmware gốc hoặc source cùng sơ đồ chân màn hình và audio. Firmware hiện tại có cho đổi OTA URL hoặc WebSocket URL sang server riêng không? Có cách sao lưu/khôi phục firmware qua USB không?

Đây là nội dung soạn sẵn cho người dùng, chưa gửi tới người bán. Chỉ cần ảnh trang cấu hình có version/board/server có thể giúp xác định hướng tiếp theo trước khi mở vỏ máy.
