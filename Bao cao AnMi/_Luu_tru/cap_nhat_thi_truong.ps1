$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$root = Join-Path (Get-Location) 'Bao cao AnMi'
$source = Join-Path $root 'AnMi_Pitch_CogAILab_Chinh_cau_chu_v3.pptx'
$target = Join-Path $root 'AnMi_Pitch_CogAILab.pptx'
if (Test-Path -LiteralPath $target) { throw 'Output exists.' }
Copy-Item -LiteralPath $source -Destination $target
$z = [IO.Compression.ZipFile]::Open($target, [IO.Compression.ZipArchiveMode]::Update)
function Read-Part($path) {
 $r=[IO.StreamReader]::new($z.GetEntry($path).Open())
 try { $x=[Xml.XmlDocument]::new(); $x.PreserveWhitespace=$true; $x.LoadXml($r.ReadToEnd()); return ,$x } finally { $r.Dispose() }
}
function Write-Part($path,$xml) {
 $old=$z.GetEntry($path); if($old){$old.Delete()}
 $e=$z.CreateEntry($path); $s=$e.Open()
 $settings=[Xml.XmlWriterSettings]::new();$settings.Encoding=[Text.UTF8Encoding]::new($false)
 $w=[Xml.XmlWriter]::Create($s,$settings)
 try {$xml.Save($w)} finally {$w.Dispose();$s.Dispose()}
}
function Namespaces($x) {
 $n=[Xml.XmlNamespaceManager]::new($x.NameTable)
 $n.AddNamespace('a','http://schemas.openxmlformats.org/drawingml/2006/main')
 $n.AddNamespace('p','http://schemas.openxmlformats.org/presentationml/2006/main')
 $n.AddNamespace('r','http://schemas.openxmlformats.org/officeDocument/2006/relationships')
 return ,$n
}
function Set-Text($paragraph,$ns,$value) {
 $nodes=$paragraph.SelectNodes('.//a:t',$ns)
 if(!$nodes.Count){throw 'Missing text'}
 $nodes[0].InnerText=$value
 for($j=1;$j -lt $nodes.Count;$j++){$nodes[$j].InnerText=''}
}
function Escape-Xml($value){return [Security.SecurityElement]::Escape($value)}
$script:shapeId=1
function Text-Box($text,$x,$y,$w,$h,$size,$color='1F2020',$bold=$false,$link='') {
 $script:shapeId++
 $id=$script:shapeId;$xx=[int]($x*914400);$yy=[int]($y*914400);$ww=[int]($w*914400);$hh=[int]($h*914400)
 $sz=[int]($size*100);$b=if($bold){'1'}else{'0'};$escaped=Escape-Xml $text
 $hlink=if($link){'<a:hlinkClick r:id="'+$link+'"/>'}else{''}
 return @"
<p:sp><p:nvSpPr><p:cNvPr id="$id" name="Market text $id"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="$xx" y="$yy"/><a:ext cx="$ww" cy="$hh"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t"><a:noAutofit/></a:bodyPr><a:lstStyle/><a:p><a:pPr><a:lnSpc><a:spcPct val="115000"/></a:lnSpc><a:buNone/></a:pPr><a:r><a:rPr lang="vi-VN" sz="$sz" b="$b"><a:solidFill><a:srgbClr val="$color"/></a:solidFill><a:latin typeface="Be Vietnam Pro"/><a:ea typeface="Be Vietnam Pro"/><a:cs typeface="Be Vietnam Pro"/>$hlink</a:rPr><a:t>$escaped</a:t></a:r><a:endParaRPr lang="vi-VN" sz="$sz"/></a:p></p:txBody></p:sp>
"@
}
function Panel($x,$y,$w,$h,$color) {
 $script:shapeId++;$id=$script:shapeId;$xx=[int]($x*914400);$yy=[int]($y*914400);$ww=[int]($w*914400);$hh=[int]($h*914400)
 return "<p:sp><p:nvSpPr><p:cNvPr id='$id' name='Market panel $id'/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x='$xx' y='$yy'/><a:ext cx='$ww' cy='$hh'/></a:xfrm><a:prstGeom prst='roundRect'><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val='$color'/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr></p:sp>"
}
try {
 # Refresh the existing evidence summary without changing its other research or product content.
 $x=Read-Part 'ppt/slides/slide6.xml';$n=Namespaces $x
 foreach($p in $x.SelectNodes('//a:p',$n)) {
  $t=($p.SelectNodes('.//a:t',$n)|ForEach-Object {$_.InnerText}) -join ''
  switch($t) {
   '12 đơn vị' {Set-Text $p $n 'Kế hoạch'}
   'Quy mô khảo sát dự kiến: 300 người tại doanh nghiệp, THPT và đại học ở Hưng Yên. Chưa có hợp đồng trả phí.' {Set-Text $p $n 'Dự kiến 12 đơn vị, 300 người; kiểm chứng nhu cầu dùng, thiết bị và khả năng chi trả.'}
   'Đã có: nhu cầu, công nghệ · Bước đầu: sản phẩm, khảo sát thị trường' {Set-Text $p $n 'Nhu cầu, công nghệ: có căn cứ · Sản phẩm, thị trường: cần kiểm chứng'}
  }
 }
 Write-Part 'ppt/slides/slide6.xml' $x
 $x=Read-Part 'ppt/notesSlides/notesSlide6.xml';$n=Namespaces $x
 foreach($p in $x.SelectNodes('//a:p',$n)) {
  $t=($p.SelectNodes('.//a:t',$n)|ForEach-Object {$_.InnerText}) -join ''
  if($t.Length -gt 100) {
   $t=$t.Replace('Đồng thời, nhóm đã khảo sát tại doanh nghiệp, trường THPT và đại học trên địa bàn tỉnh Hưng Yên. ', '')
   $start=$t.IndexOf('Thị trường:')
   if($start -lt 0){throw 'Missing market note'}
   $t=$t.Substring(0,$start)+'Thị trường: tra cứu nguồn công khai cho thấy nhu cầu hỗ trợ tâm lý và khoảng trống tiếp cận, nhưng chưa có dữ liệu trực tiếp để xác minh nhu cầu dùng CogAI, mua AnMi và khả năng chi trả. Quy mô 12 đơn vị, 300 người là kế hoạch khảo sát, không phải mẫu đã thu thập. Hai slide tiếp theo trình bày công nghệ và sản phẩm; sau đó là slide thị trường với nguồn nghiên cứu và kế hoạch kiểm chứng.'
   Set-Text $p $n $t
  }
 }
 Write-Part 'ppt/notesSlides/notesSlide6.xml' $x
 # A dedicated market slide is inserted immediately before the business model.
 $shapes=[Collections.Generic.List[string]]::new()
 $shapes.Add((Text-Box 'THỊ TRƯỜNG' .88 .38 11 .3 15 '3A6AD6' $true))
 $shapes.Add((Text-Box 'Có nhu cầu hỗ trợ; cần kiểm chứng sức mua' .88 .85 11.6 .65 29 '1F2020' $true))
 $columns=@(
  @{X=.88;Number='21,7%';Body='Vị thành niên có vấn đề sức khỏe tâm thần trong 12 tháng';Sample='5.996 cặp vị thành niên–cha/mẹ';Source='V-NAMHS · dữ liệu 2021 [1]'},
  @{X=4.82;Number='8,4%';Body='Trong nhóm có vấn đề, đã tiếp cận dịch vụ hỗ trợ hoặc tư vấn';Sample='Khoảng trống tiếp cận hỗ trợ';Source='V-NAMHS · dữ liệu 2021 [1]'},
  @{X=8.76;Number='30,5%';Body='Công nhân sàng lọc dương tính với triệu chứng trầm cảm';Sample='1.200 công nhân · ngoài Hưng Yên';Source='Dữ liệu 2019 · công bố 2020 [2]'}
 )
 foreach($c in $columns) {
  $shapes.Add((Panel $c.X 1.68 3.7 2.42 'F0F4FC'))
  $shapes.Add((Text-Box $c.Number ($c.X+.2) 1.87 3.3 .7 38 '3A6AD6' $true))
  $shapes.Add((Text-Box $c.Body ($c.X+.2) 2.66 3.3 .8 15))
  $shapes.Add((Text-Box $c.Sample ($c.X+.2) 3.48 3.3 .3 11 '3B3B3B'))
  $shapes.Add((Text-Box $c.Source ($c.X+.2) 3.81 3.3 .24 10 '3B3B3B'))
 }
 $shapes.Add((Text-Box 'Hưng Yên: có hướng nghiên cứu hỗ trợ số' .88 4.35 11.6 .35 17 '1F2020' $true))
 $shapes.Add((Text-Box 'Y-MIND có địa bàn Hưng Yên; bài công bố là đề cương nghiên cứu, chưa phải kết quả hiệu quả. [3]' .88 4.82 11.55 .48 14))
 $shapes.Add((Panel .88 5.48 11.58 .92 '3A6AD6'))
 $shapes.Add((Text-Box 'Kế hoạch khảo sát: 12 đơn vị, 300 người' 1.08 5.59 11.15 .33 17 'FFFFFF' $true))
 $shapes.Add((Text-Box 'Kiểm chứng mức sử dụng, nhu cầu AnMi và khả năng chi trả; chưa có hợp đồng trả phí.' 1.08 6.01 11.15 .26 12 'FFFFFF'))
 $shapes.Add((Text-Box 'Nguồn công khai; không phải khảo sát do nhóm thực hiện. Kết quả sàng lọc không phải chẩn đoán.' .88 6.58 11.55 .28 11 '3B3B3B'))
 $shapes.Add((Text-Box '[1] V-NAMHS 2022' .88 6.98 2.9 .24 10 '3A6AD6' $false 'rId3'))
 $shapes.Add((Text-Box '[2] Nghiên cứu công nhân 2020' 4.05 6.98 3.65 .24 10 '3A6AD6' $false 'rId4'))
 $shapes.Add((Text-Box '[3] Y-MIND · PLOS ONE 2025' 8.05 6.98 3.7 .24 10 '3A6AD6' $false 'rId5'))
 $shapes.Add((Text-Box '09' 12.1 7.03 .4 .25 14 '3B3B3B'))
 [xml]$newSlide='<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'+($shapes -join '')+'</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
 Write-Part 'ppt/slides/slide14.xml' $newSlide
 [xml]$rels='<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout2.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/notesSlide14.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://qcmhr.org/docman/reports/15-vnamhs-report-eng-15-feb-2023/file" TargetMode="External"/><Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://pmc.ncbi.nlm.nih.gov/articles/PMC7216084/" TargetMode="External"/><Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://doi.org/10.1371/journal.pone.0332875" TargetMode="External"/></Relationships>'
 Write-Part 'ppt/slides/_rels/slide14.xml.rels' $rels
 $notes=Read-Part 'ppt/notesSlides/notesSlide6.xml';$n=Namespaces $notes
 foreach($p in $notes.SelectNodes('//a:p',$n)) {
  $t=($p.SelectNodes('.//a:t',$n)|ForEach-Object {$_.InnerText}) -join ''
  if($t.Length -gt 100){Set-Text $p $n 'Tra cứu tài liệu cho thấy có nhu cầu hỗ trợ nhưng chưa xác minh được sức mua cho CogAI/AnMi. V-NAMHS, báo cáo năm 2022 với dữ liệu thu thập năm 2021 trên 5.996 cặp vị thành niên–cha/mẹ, ghi nhận 21,7% người 10–17 tuổi có vấn đề sức khỏe tâm thần trong 12 tháng; không đồng nghĩa tất cả có rối loạn tâm thần. Trong nhóm có vấn đề, 8,4% tiếp cận dịch vụ hỗ trợ hoặc tư vấn. Nghiên cứu công bố năm 2020, dữ liệu năm 2019 trên 1.200 công nhân tại Hà Nội, Quảng Ngãi, Đồng Nai, Cần Thơ, ghi nhận 30,5% sàng lọc dương tính triệu chứng trầm cảm; không gồm Hưng Yên và không phải chẩn đoán. Nguồn: https://qcmhr.org/docman/reports/15-vnamhs-report-eng-15-feb-2023/file và https://pmc.ncbi.nlm.nih.gov/articles/PMC7216084/. Tại Hưng Yên, đề cương Y-MIND công bố ngày 07/10/2025 có địa bàn nghiên cứu tại tỉnh: https://doi.org/10.1371/journal.pone.0332875. Đây chưa phải kết quả đánh giá hiệu quả và không chứng minh nhu cầu mua AnMi. Quy mô 12 đơn vị, 300 người là kế hoạch đề xuất, không phải số mẫu đã thu. Cần đo nhu cầu dùng thực tế, duy trì sử dụng, lựa chọn web hay thiết bị và mức sẵn sàng chi trả; phỏng vấn riêng người có quyền quyết định mua tại tổ chức. Chưa có dữ liệu khảo sát riêng được cung cấp để xác minh; không trình bày các nguồn công khai như khảo sát do nhóm thực hiện. Các nguồn chứng minh khoảng trống hỗ trợ, chưa chứng minh hiệu quả hoặc sức mua của CogAI. Từ đó, dự án đề xuất mô hình kinh doanh để kiểm chứng trong thí điểm.'}
  elseif($t -eq '6'){Set-Text $p $n '9'}
 }
 Write-Part 'ppt/notesSlides/notesSlide14.xml' $notes
 $nr=Read-Part 'ppt/notesSlides/_rels/notesSlide6.xml.rels'
 foreach($rel in $nr.DocumentElement.ChildNodes){if($rel.Type.EndsWith('/slide')){$rel.SetAttribute('Target','../slides/slide14.xml')}}
 Write-Part 'ppt/notesSlides/_rels/notesSlide14.xml.rels' $nr
 # Register and order the new slide.
 $pres=Read-Part 'ppt/presentation.xml';$n=Namespaces $pres;$list=$pres.SelectSingleNode('//p:sldIdLst',$n)
 $pr=Read-Part 'ppt/_rels/presentation.xml.rels'
 $nextRid=1+($pr.DocumentElement.ChildNodes | ForEach-Object {[int]($_.Id -replace '\D','')} | Measure-Object -Maximum).Maximum
 $rid="rId$nextRid"
 $rel=$pr.CreateElement('Relationship',$pr.DocumentElement.NamespaceURI);$rel.SetAttribute('Id',$rid);$rel.SetAttribute('Type','http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide');$rel.SetAttribute('Target','slides/slide14.xml');[void]$pr.DocumentElement.AppendChild($rel)
 $node=$pres.CreateElement('p','sldId','http://schemas.openxmlformats.org/presentationml/2006/main');$node.SetAttribute('id','269');[void]$node.SetAttribute('id','http://schemas.openxmlformats.org/officeDocument/2006/relationships',$rid);[void]$list.InsertAfter($node,$list.ChildNodes[7])
 Write-Part 'ppt/presentation.xml' $pres;Write-Part 'ppt/_rels/presentation.xml.rels' $pr
 $ct=Read-Part '[Content_Types].xml'
 foreach($def in @(@('/ppt/slides/slide14.xml','application/vnd.openxmlformats-officedocument.presentationml.slide+xml'),@('/ppt/notesSlides/notesSlide14.xml','application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml'))) {
  $ov=$ct.CreateElement('Override',$ct.DocumentElement.NamespaceURI);$ov.SetAttribute('PartName',$def[0]);$ov.SetAttribute('ContentType',$def[1]);[void]$ct.DocumentElement.AppendChild($ov)
 }
 Write-Part '[Content_Types].xml' $ct
 # Renumber the following slides and their notes.
 foreach($num in 9..13) {
  foreach($kind in @('slides','notesSlides')) {
   $stem=if($kind -eq 'slides'){'slide'}else{'notesSlide'};$path="ppt/$kind/$stem$num.xml";$x=Read-Part $path;$n=Namespaces $x
   foreach($p in $x.SelectNodes('//a:p',$n)) {
    $t=($p.SelectNodes('.//a:t',$n)|ForEach-Object {$_.InnerText}) -join ''
    $expected=if($kind -eq 'slides'){$num.ToString('00')}else{"$num"}
    if($t -eq $expected){$value=if($kind -eq 'slides'){($num+1).ToString('00')}else{"$($num+1)"};Set-Text $p $n $value}
   }
   Write-Part $path $x
  }
 }
 $app=Read-Part 'docProps/app.xml'
 foreach($child in $app.DocumentElement.ChildNodes){if($child.LocalName -eq 'Slides' -or $child.LocalName -eq 'Notes'){$child.InnerText='14'}}
 $an=[Xml.XmlNamespaceManager]::new($app.NameTable);$an.AddNamespace('ep',$app.DocumentElement.NamespaceURI);$an.AddNamespace('vt','http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes')
 $app.SelectSingleNode('//ep:HeadingPairs/vt:vector/vt:variant[6]/vt:i4',$an).InnerText='14'
 $titles=$app.SelectSingleNode('//ep:TitlesOfParts/vt:vector',$an);$title=$app.CreateElement('vt','lpstr','http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes');$title.InnerText='Có nhu cầu hỗ trợ; cần kiểm chứng sức mua';[void]$titles.InsertAfter($title,$titles.ChildNodes[10]);$titles.SetAttribute('size','17')
 Write-Part 'docProps/app.xml' $app
} finally {$z.Dispose()}
Write-Output "Created: $target"
