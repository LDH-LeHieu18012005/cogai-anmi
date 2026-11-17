$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression
$folder = $PSScriptRoot
$source = Join-Path $folder 'AnMi_Pitch_CogAILab.pptx'
$target = Join-Path $folder 'AnMi_Pitch_CogAILab_Chinh_cau_chu_v3.pptx'
if (Test-Path -LiteralPath $target) { throw 'Output already exists.' }
Copy-Item -LiteralPath $source -Destination $target
$script:changes = [Collections.Generic.List[object]]::new()
$replacements = @{
 2 = @{
  1 = 'Khoảng trống trong tiếp cận hỗ trợ tâm lý'
  11 = '18,4% sinh viên tìm đến chuyên gia tâm lý; 72,6% tìm bạn bè, 54,3% tìm gia đình.'
  12 = 'Trong mẫu khảo sát, công nhân không sử dụng y tế nhà máy để hỗ trợ tâm lý; có thể do lo ngại kỳ thị, mất việc.'
 }
 3 = @{ 1 = 'CogAI: nền tảng AI với 4 chức năng'; 7 = 'Xem xét suy nghĩ tiêu cực' }
 4 = @{ 1 = 'Quy trình xử lý tin nhắn gồm 6 bước' }
 5 = @{
  1 = 'CogAI và các nhóm giải pháp hiện có'
  21 = 'Hỗ trợ phát hiện sớm, chuyển ca phù hợp tới chuyên gia'
  22 = 'Khác biệt: tiếng Việt · ẩn danh · lớp an toàn độc lập · chuyển ca nguy cơ cao tới người thật'
 }
 6 = @{
  0 = 'CƠ SỞ KIỂM CHỨNG'
  1 = 'Mức độ kiểm chứng của CogAI'
  16 = 'Dự kiến'
  17 = '12 đơn vị'
  18 = 'Quy mô khảo sát dự kiến: 300 người tại doanh nghiệp, THPT và đại học ở Hưng Yên. Chưa có hợp đồng trả phí.'
  19 = 'Đã có: nhu cầu, công nghệ · Bước đầu: sản phẩm, khảo sát thị trường'
 }
 7 = @{ 1 = 'Kết quả nghiên cứu công nghệ lõi'; 24 = 'Cao hơn PADO trên cả 4 bộ; chi phí' }
 8 = @{ 1 = 'Chi phí linh kiện AnMi: 490.500 đ/bộ'; 8 = 'Tổng chi phí'; 10 = 'Gồm phụ kiện và giao mẫu; công phát triển, lắp ráp thuộc quỹ lương.' }
 9 = @{
  1 = 'B2B2C kết hợp gói cá nhân'
  2 = 'B2B2C tại Hưng Yên: doanh nghiệp, công đoàn, nhà trường trả phí theo suất; người dùng tiếp cận qua tổ chức. Báo cáo tổng hợp ẩn danh.'
  14 = 'Mục tiêu hợp đồng và suất trả phí'
 }
 10 = @{
  1 = 'Dự kiến: thu–chi dương năm 3, lũy kế năm 4'
  2 = 'Chênh lệch thu–chi lũy kế (triệu đồng)'
  9 = 'Kịch bản cơ sở'
  27 = 'Chi phí dự toán'
  33 = 'Chênh lệch thu–chi'
  39 = 'Kịch bản cơ sở: lũy kế dương tháng 10 năm 4; kịch bản thuận lợi: năm 3. Số liệu trước thuế.'
 }
 11 = @{
  0 = 'NHU CẦU VỐN'
  1 = 'Ngân sách năm đầu: 933,74 triệu đồng'
  2 = 'Phân bổ ngân sách'
  28 = 'Tổng ngân sách'
  30 = 'Nhu cầu vốn tối đa theo tháng: 1.292,82 triệu (kịch bản cơ sở). Nguồn huy động chưa được xác nhận.'
 }
 12 = @{
  1 = 'Lộ trình triển khai theo điều kiện'
  10 = '10 AnMi, thử nghiệm với sinh viên'
  11 = 'Điều kiện: đạt kiểm thử tích hợp, an toàn'
  22 = 'Mục tiêu thí điểm: ≥ 70% hoàn thành sàng lọc · ≥ 30% còn dùng sau 4 tuần · 100% ca nguy cơ cao thấy kênh khẩn cấp dưới 1 phút'
  23 = 'Mục tiêu cuối năm 2: 10 hợp đồng, 3.000 suất trả phí · Giai đoạn 0 đang thực hiện'
 }
 13 = @{ 1 = 'Đội ngũ và nhu cầu hỗ trợ'; 17 = 'Đề nghị hỗ trợ' }
}
$noteReplacements = @{
 1 = @(@('Câu chuyện bắt đầu từ một vấn đề rất thật.', 'Trước hết là nhu cầu tiếp cận hỗ trợ tâm lý.'))
 2 = @(@('Nghĩa là nhu cầu có thật nhưng rất ít người đi đến đúng chỗ.', 'Các kết quả cho thấy khoảng trống trong tiếp cận hỗ trợ chuyên môn.'))
 3 = @(@('nhận ra sớm khi mình “không ổn”', 'nhận biết sớm khó khăn về sức khỏe tinh thần'))
 5 = @(@('CogAI làm cửa ngõ phát hiện sớm', 'CogAI hỗ trợ phát hiện sớm'), @('Những khác biệt này có bằng chứng đến đâu? Chúng em tách bạch bốn loại bằng chứng.', 'Mức độ kiểm chứng được trình bày theo bốn nhóm.'))
 6 = @(
  @('Chúng em tách bạch bốn loại bằng chứng và nói rõ mức độ của từng loại.', 'Mức độ kiểm chứng được trình bày theo bốn nhóm: nhu cầu, công nghệ, sản phẩm và thị trường.'),
  @(' – nhưng nhóm chưa có khảo sát riêng.', '. Đồng thời, nhóm đã khảo sát tại doanh nghiệp, trường THPT và đại học trên địa bàn tỉnh Hưng Yên.'),
  @('Thị trường: chưa có hợp đồng và chưa có khảo sát mức sẵn sàng chi trả; sẽ khảo sát khoảng 10 đơn vị trong giai đoạn MVP, sau đó thí điểm tại một đến hai doanh nghiệp.', 'Thị trường: đã khảo sát bước đầu tại doanh nghiệp, trường THPT và đại học trên địa bàn tỉnh Hưng Yên; chưa có hợp đồng trả phí và chưa khảo sát mức sẵn sàng chi trả. Quy mô khảo sát dự kiến trong giai đoạn MVP là 12 đơn vị, 300 người, thuộc các doanh nghiệp, trường THPT và đại học tại Hưng Yên. Đây là mục tiêu kế hoạch, chưa phải số đơn vị và người đã tham gia khảo sát. Nội dung khảo sát gồm nhu cầu hỗ trợ tâm lý, khả năng tiếp cận và mức sẵn sàng chi trả. Sau đó thí điểm tại một đến hai doanh nghiệp.')
 )
 7 = @(@('bài báo ghi nhận hỗ trợ Ghi nhận hỗ trợ NAFOSTED', 'bài báo ghi nhận hỗ trợ NAFOSTED'))
 9 = @(@('Mô hình B2B2C:', 'Mô hình B2B2C kết hợp gói cá nhân:'))
 12 = @(@('khảo sát mức sẵn sàng chi trả tại khoảng 10 doanh nghiệp KCN', 'dự kiến khảo sát nhu cầu, khả năng tiếp cận và mức sẵn sàng chi trả của 300 người tại 12 đơn vị (doanh nghiệp, trường THPT và đại học ở Hưng Yên)'))
}
$zip = [IO.Compression.ZipFile]::Open($target, [IO.Compression.ZipArchiveMode]::Update)
try {
 foreach ($kind in @('slides', 'notesSlides')) {
  foreach ($number in 1..13) {
   $stem = if ($kind -eq 'slides') {'slide'} else {'notesSlide'}
   $path = "ppt/$kind/$stem$number.xml"
   $entry = $zip.GetEntry($path)
   if (!$entry) { continue }
   $reader = [IO.StreamReader]::new($entry.Open())
   $xml = [Xml.XmlDocument]::new()
   $xml.PreserveWhitespace = $true
   $xml.LoadXml($reader.ReadToEnd())
   $reader.Dispose()
   $ns = [Xml.XmlNamespaceManager]::new($xml.NameTable)
   $ns.AddNamespace('a', 'http://schemas.openxmlformats.org/drawingml/2006/main')
   $ns.AddNamespace('p', 'http://schemas.openxmlformats.org/presentationml/2006/main')
   $paras = $xml.SelectNodes('//a:p', $ns)
   $dirty = $false
   for ($i = 0; $i -lt $paras.Count; $i++) {
    $texts = $paras[$i].SelectNodes('.//a:t', $ns)
    $old = ($texts | ForEach-Object { $_.InnerText }) -join ''
    $new = $old
    if ($kind -eq 'slides' -and $replacements.ContainsKey($number) -and $replacements[$number].ContainsKey($i)) {
     $new = $replacements[$number][$i]
    } elseif ($kind -eq 'notesSlides' -and $noteReplacements.ContainsKey($number)) {
     $pairs = $noteReplacements[$number]
     if ($pairs[0] -is [string]) { $pairs = ,$pairs }
     foreach ($pair in $pairs) {
      if ($pair[0].Length -lt 10) { throw 'Invalid replacement phrase.' }
      $new = $new.Replace($pair[0], $pair[1])
     }
    }
    if ($old -eq $new) { continue }
    if (!$texts.Count) { throw "No text node in $path paragraph $i" }
    $offset = 0
    for ($j = 0; $j -lt $texts.Count; $j++) {
     $length = if ($j -eq $texts.Count - 1) { $new.Length - $offset } else { [Math]::Min($texts[$j].InnerText.Length, $new.Length - $offset) }
     $texts[$j].InnerText = $new.Substring($offset, $length)
     $offset += $length
    }
    if ($kind -eq 'slides' -and $number -eq 6 -and $i -eq 17) {
     foreach ($prop in $paras[$i].SelectNodes('.//a:rPr | a:endParaRPr', $ns)) { $prop.SetAttribute('sz', '2400') }
     $paras[$i].SelectSingleNode('a:pPr/a:lnSpc/a:spcPts', $ns).SetAttribute('val', '2880')
    }
    if ($kind -eq 'slides' -and $number -eq 6 -and $i -eq 18) {
     # The market update needs more lines; use the free space above the footer.
     $shape = $paras[$i].SelectSingleNode('ancestor::p:sp', $ns)
     $shape.SelectSingleNode('p:spPr/a:xfrm/a:ext', $ns).SetAttribute('cy', '1645920')
     foreach ($prop in $paras[$i].SelectNodes('.//a:rPr | a:endParaRPr', $ns)) { $prop.SetAttribute('sz', '1200') }
     $paras[$i].SelectSingleNode('a:pPr/a:lnSpc/a:spcPts', $ns).SetAttribute('val', '1620')
    }
    $script:changes.Add([pscustomobject]@{ Slide=$number; Kind=$kind; Before=$old; After=$new })
    $dirty = $true
   }
   if ($dirty) {
    $entry.Delete()
    $newEntry = $zip.CreateEntry($path, [IO.Compression.CompressionLevel]::Optimal)
    $stream = $newEntry.Open()
    $settings = [Xml.XmlWriterSettings]::new()
    $settings.Encoding = [Text.UTF8Encoding]::new($false)
    $writer = [Xml.XmlWriter]::Create($stream, $settings)
    $xml.Save($writer)
    $writer.Dispose()
    $stream.Dispose()
   }
  }
 }
} finally { $zip.Dispose() }
$log = [Collections.Generic.List[string]]::new()
$log.Add('# Điều chỉnh câu chữ bản pitching')
$log.Add('')
$log.Add('Giữ nguyên số liệu nghiên cứu, giá, dự toán và mốc thời gian. Ghi nhận khảo sát bước đầu theo thông tin người dùng cung cấp. Bổ sung mục tiêu khảo sát dự kiến 12 đơn vị, 300 người; đây không phải kết quả thực tế. Giữ nguyên tệp gốc và các bản trước.')
$log.Add('')
foreach ($c in $script:changes) {
 $label = if ($c.Kind -eq 'slides') {'Slide'} else {'Ghi chú slide'}
 $log.Add("- ${label} $($c.Slide): $($c.Before)")
 $log.Add("  → $($c.After)")
}
[IO.File]::WriteAllLines((Join-Path $folder 'AnMi_Pitch_Nhat_ky_chinh_sua_v3.md'), $log, [Text.UTF8Encoding]::new($false))
Write-Output "Saved: $target"
Write-Output "Changed paragraphs: $($script:changes.Count)"
