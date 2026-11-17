$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$root=Join-Path (Get-Location) 'Bao cao AnMi'
$path=Join-Path $root 'AnMi_Pitch_CogAILab.pptx'
$backup=Join-Path $root '_Luu_tru/AnMi_Pitch_Truoc_cap_nhat_tin_hieu_nguoi_mua.pptx'
if(Test-Path -LiteralPath $backup){throw 'Backup exists'}
Copy-Item -LiteralPath $path -Destination $backup
$url='https://www.wtwco.com/en-vn/insights/2023/10/vietnam-employers-look-to-enhance-benefits-to-attract-and-retain-talent'
$z=[IO.Compression.ZipFile]::Open($path,[IO.Compression.ZipArchiveMode]::Update)
function Read-Part($name){$r=[IO.StreamReader]::new($z.GetEntry($name).Open());try{$x=[Xml.XmlDocument]::new();$x.PreserveWhitespace=$true;$x.LoadXml($r.ReadToEnd());return ,$x}finally{$r.Dispose()}}
function Write-Part($name,$x){$e=$z.GetEntry($name);$e.Delete();$s=$z.CreateEntry($name).Open();$settings=[Xml.XmlWriterSettings]::new();$settings.Encoding=[Text.UTF8Encoding]::new($false);$w=[Xml.XmlWriter]::Create($s,$settings);try{$x.Save($w)}finally{$w.Dispose();$s.Dispose()}}
function NS($x){$n=[Xml.XmlNamespaceManager]::new($x.NameTable);$n.AddNamespace('a','http://schemas.openxmlformats.org/drawingml/2006/main');$n.AddNamespace('p','http://schemas.openxmlformats.org/presentationml/2006/main');return ,$n}
function Set-Text($node,$n,$text){$ts=$node.SelectNodes('.//a:t',$n);if(!$ts.Count){throw 'Missing text node'};$ts[0].InnerText=$text;for($i=1;$i -lt $ts.Count;$i++){$ts[$i].InnerText=''}}
try{
 $x=Read-Part 'ppt/slides/slide6.xml';$n=NS $x
 $updates=@{
  '31'='25%'
  '32'='tổ chức muốn cải thiện phúc lợi hỗ trợ sức khỏe tinh thần.'
  '1001'='WTW 2023 · 219 tổ chức tại Việt Nam'
  '1002'='Hưng Yên: dự kiến phỏng vấn 12 đơn vị về mức trả phí, số suất và ngân sách; chưa xác nhận sức mua.'
 }
 foreach($id in $updates.Keys){$s=$x.SelectSingleNode("//p:sp[p:nvSpPr/p:cNvPr[@id='$id']]",$n);if(!$s){throw "Missing shape $id"};Set-Text $s $n $updates[$id]}
 # Keep the market badge consistent with evidence that signals interest, not validated sales.
 $badge=$x.SelectSingleNode('//p:sp[p:nvSpPr/p:cNvPr[@id="11"]]',$n)
 Set-Text $badge $n 'Tín hiệu'
 $plan=$x.SelectSingleNode('//p:sp[p:nvSpPr/p:cNvPr[@id="1002"]]',$n)
 $plan.SelectSingleNode('p:spPr/a:xfrm/a:ext',$n).SetAttribute('cy','736600')
 Write-Part 'ppt/slides/slide6.xml' $x
 $rels=Read-Part 'ppt/slides/_rels/slide6.xml.rels'
 $rel=@($rels.DocumentElement.ChildNodes|Where-Object Id -eq 'rIdMarketSource')
 if($rel.Count -ne 1){throw 'Missing market source link'}
 $rel[0].SetAttribute('Target',$url)
 Write-Part 'ppt/slides/_rels/slide6.xml.rels' $rels
 $notes=Read-Part 'ppt/notesSlides/notesSlide6.xml';$nn=NS $notes
 foreach($p in $notes.SelectNodes('//a:p',$nn)){
  $t=($p.SelectNodes('.//a:t',$nn)|ForEach-Object {$_.InnerText}) -join ''
  if($t.Length -gt 100){
   $cut=$t.IndexOf('Thị trường:');if($cut -lt 0){throw 'Missing market section'}
   $t=$t.Substring(0,$cut)+'Thị trường: WTW Benefits Trends Survey 2023 khảo sát 219 tổ chức tại Việt Nam trong tháng 3–4/2023; 25% muốn cải thiện phúc lợi hỗ trợ sức khỏe tinh thần. Đây là tín hiệu quan tâm từ người mua tổ chức, không phải tỷ lệ sẵn sàng trả phí cho CogAI; không phải dữ liệu riêng Hưng Yên, trường học hoặc khảo sát do nhóm thực hiện. Nguồn: '+$url+'. Chưa có phản hồi sơ cấp, ngân sách được xác nhận hay hợp đồng trả phí để chứng minh sức mua tại Hưng Yên. Kế hoạch đề xuất: phỏng vấn 12 đại diện có vai trò quyết định mua tại doanh nghiệp, công đoàn và nhà trường; xác nhận nhu cầu, người duyệt, nguồn ngân sách, số suất, mức giá chấp nhận, điều kiện và thời điểm thí điểm trả phí. Đối chiếu mức giá tổ chức 15.000 đồng/suất/tháng và 12.000 đồng với hợp đồng trên 1.000 suất; các mức này là đề xuất, chưa được người mua xác nhận. Khảo sát 300 người dùng dự kiến là nhánh riêng để đo nhu cầu sử dụng, lựa chọn web hay AnMi và khả năng duy trì; câu trả lời của người dùng không thay thế quyết định ngân sách của tổ chức. Không quy đổi 25% thành số khách hàng hay doanh thu dự báo. Hai slide tiếp theo trình bày chi tiết công nghệ và sản phẩm.'
   Set-Text $p $nn $t
  }
 }
 Write-Part 'ppt/notesSlides/notesSlide6.xml' $notes
}finally{$z.Dispose()}
Write-Output 'Updated market card with employer-side evidence; kept 13 slides.'
