$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$root=Join-Path (Get-Location) 'Bao cao AnMi'
$path=Join-Path $root 'AnMi_Pitch_CogAILab.pptx'
$backup=Join-Path $root '_Luu_tru/AnMi_Pitch_CogAILab_Truoc_gop_thi_truong.pptx'
if(Test-Path -LiteralPath $backup){throw 'Backup exists'}
Copy-Item -LiteralPath $path -Destination $backup
$z=[IO.Compression.ZipFile]::Open($path,[IO.Compression.ZipArchiveMode]::Update)
function Read-Part($name){$r=[IO.StreamReader]::new($z.GetEntry($name).Open());try{$x=[Xml.XmlDocument]::new();$x.PreserveWhitespace=$true;$x.LoadXml($r.ReadToEnd());return ,$x}finally{$r.Dispose()}}
function Write-Part($name,$x){$e=$z.GetEntry($name);if($e){$e.Delete()};$s=$z.CreateEntry($name).Open();$settings=[Xml.XmlWriterSettings]::new();$settings.Encoding=[Text.UTF8Encoding]::new($false);$w=[Xml.XmlWriter]::Create($s,$settings);try{$x.Save($w)}finally{$w.Dispose();$s.Dispose()}}
function NS($x){$n=[Xml.XmlNamespaceManager]::new($x.NameTable);$n.AddNamespace('a','http://schemas.openxmlformats.org/drawingml/2006/main');$n.AddNamespace('p','http://schemas.openxmlformats.org/presentationml/2006/main');$n.AddNamespace('r','http://schemas.openxmlformats.org/officeDocument/2006/relationships');return ,$n}
function Set-Text($node,$n,$text){$ts=$node.SelectNodes('.//a:t',$n);$ts[0].InnerText=$text;for($i=1;$i -lt $ts.Count;$i++){$ts[$i].InnerText=''}}
function Format-Text($node,$n,$size,$spacing){foreach($prop in $node.SelectNodes('.//a:rPr | .//a:endParaRPr',$n)){$prop.SetAttribute('sz',"$size")};foreach($sp in $node.SelectNodes('.//a:lnSpc/a:spcPts',$n)){$sp.SetAttribute('val',"$spacing")}}
try{
 $marketNotes=Read-Part 'ppt/notesSlides/notesSlide14.xml';$mn=NS $marketNotes
 $details=($marketNotes.SelectNodes('//a:p',$mn)|ForEach-Object {($_.SelectNodes('.//a:t',$mn)|ForEach-Object {$_.InnerText}) -join ''}|Where-Object {$_.Length -gt 100}) -join ' '
 $x=Read-Part 'ppt/slides/slide6.xml';$n=NS $x
 $metric=$x.SelectSingleNode('//p:sp[p:nvSpPr/p:cNvPr[@id="31"]]',$n)
 Set-Text $metric $n '8,4%';Format-Text $metric $n 3600 4320
 foreach($c in $metric.SelectNodes('.//a:rPr/a:solidFill/a:srgbClr',$n)){$c.SetAttribute('val','3A6AD6')}
 $desc=$x.SelectSingleNode('//p:sp[p:nvSpPr/p:cNvPr[@id="32"]]',$n)
 Set-Text $desc $n 'vị thành niên có vấn đề sức khỏe tâm thần đã tiếp cận dịch vụ hỗ trợ trong 12 tháng.'
 Format-Text $desc $n 1200 1550
 $desc.SelectSingleNode('p:spPr/a:xfrm/a:ext',$n).SetAttribute('cy','749300')
 # Use the existing empty lower portion of the market card.
 $source=$desc.CloneNode($true)
 $source.SelectSingleNode('p:nvSpPr/p:cNvPr',$n).SetAttribute('id','1001');$source.SelectSingleNode('p:nvSpPr/p:cNvPr',$n).SetAttribute('name','Nguon thi truong')
 Set-Text $source $n 'V-NAMHS 2022 · dữ liệu 2021'
 Format-Text $source $n 900 1150
 $source.SelectSingleNode('p:spPr/a:xfrm/a:off',$n).SetAttribute('y','3810000');$source.SelectSingleNode('p:spPr/a:xfrm/a:ext',$n).SetAttribute('cy','190500')
 $pr=$source.SelectSingleNode('.//a:rPr',$n);$hl=$x.CreateElement('a','hlinkClick','http://schemas.openxmlformats.org/drawingml/2006/main');[void]$hl.SetAttribute('id','http://schemas.openxmlformats.org/officeDocument/2006/relationships','rIdMarketSource');[void]$pr.AppendChild($hl)
 [void]$x.SelectSingleNode('//p:spTree',$n).AppendChild($source)
 $plan=$desc.CloneNode($true)
 $plan.SelectSingleNode('p:nvSpPr/p:cNvPr',$n).SetAttribute('id','1002');$plan.SelectSingleNode('p:nvSpPr/p:cNvPr',$n).SetAttribute('name','Ke hoach kiem chung thi truong')
 Set-Text $plan $n 'Dự kiến: 12 đơn vị, 300 người; kiểm chứng nhu cầu CogAI/AnMi và khả năng chi trả.'
 Format-Text $plan $n 1050 1350
 $plan.SelectSingleNode('p:spPr/a:xfrm/a:off',$n).SetAttribute('y','4064000');$plan.SelectSingleNode('p:spPr/a:xfrm/a:ext',$n).SetAttribute('cy','635000')
 [void]$x.SelectSingleNode('//p:spTree',$n).AppendChild($plan)
 Write-Part 'ppt/slides/slide6.xml' $x
 $rels=Read-Part 'ppt/slides/_rels/slide6.xml.rels'
 $rel=$rels.CreateElement('Relationship',$rels.DocumentElement.NamespaceURI);$rel.SetAttribute('Id','rIdMarketSource');$rel.SetAttribute('Type','http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink');$rel.SetAttribute('Target','https://qcmhr.org/docman/reports/15-vnamhs-report-eng-15-feb-2023/file');$rel.SetAttribute('TargetMode','External');[void]$rels.DocumentElement.AppendChild($rel)
 Write-Part 'ppt/slides/_rels/slide6.xml.rels' $rels
 $notes=Read-Part 'ppt/notesSlides/notesSlide6.xml';$nn=NS $notes
 foreach($p in $notes.SelectNodes('//a:p',$nn)){$t=($p.SelectNodes('.//a:t',$nn)|ForEach-Object {$_.InnerText}) -join '';if($t.Length -gt 100){$cut=$t.IndexOf('Thị trường:');if($cut -lt 0){throw 'Market notes missing'};$t=$t.Substring(0,$cut)+'Thị trường: '+$details+' Hai slide tiếp theo trình bày chi tiết công nghệ và sản phẩm.';Set-Text $p $nn $t}}
 Write-Part 'ppt/notesSlides/notesSlide6.xml' $notes
 # Unregister and remove the extra slide and its notes.
 $pres=Read-Part 'ppt/presentation.xml';$pn=NS $pres
 $rels=Read-Part 'ppt/_rels/presentation.xml.rels'
 $extra=@($rels.DocumentElement.ChildNodes|Where-Object Target -eq 'slides/slide14.xml')
 if($extra.Count -ne 1){throw 'Expected exactly one extra market slide'}
 $rid=$extra[0].Id
 $id=$pres.SelectSingleNode("//p:sldId[@r:id='$rid']",$pn)
 [void]$id.ParentNode.RemoveChild($id);[void]$rels.DocumentElement.RemoveChild($extra[0])
 Write-Part 'ppt/presentation.xml' $pres;Write-Part 'ppt/_rels/presentation.xml.rels' $rels
 $ct=Read-Part '[Content_Types].xml'
 foreach($ov in @($ct.DocumentElement.ChildNodes)){if($ov.PartName -in @('/ppt/slides/slide14.xml','/ppt/notesSlides/notesSlide14.xml')){[void]$ct.DocumentElement.RemoveChild($ov)}}
 Write-Part '[Content_Types].xml' $ct
 foreach($part in @('ppt/slides/slide14.xml','ppt/slides/_rels/slide14.xml.rels','ppt/notesSlides/notesSlide14.xml','ppt/notesSlides/_rels/notesSlide14.xml.rels')){$z.GetEntry($part).Delete()}
 foreach($num in 9..13){foreach($kind in @('slides','notesSlides')){$stem=if($kind -eq 'slides'){'slide'}else{'notesSlide'};$part="ppt/$kind/$stem$num.xml";$x=Read-Part $part;$n=NS $x;$expected=if($kind -eq 'slides'){($num+1).ToString('00')}else{"$($num+1)"};$replacement=if($kind -eq 'slides'){$num.ToString('00')}else{"$num"};foreach($p in $x.SelectNodes('//a:p',$n)){$t=($p.SelectNodes('.//a:t',$n)|ForEach-Object {$_.InnerText}) -join '';if($t -eq $expected){Set-Text $p $n $replacement}};Write-Part $part $x}}
 $app=Read-Part 'docProps/app.xml';$an=[Xml.XmlNamespaceManager]::new($app.NameTable);$an.AddNamespace('ep',$app.DocumentElement.NamespaceURI);$an.AddNamespace('vt','http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes')
 foreach($child in $app.DocumentElement.ChildNodes){if($child.LocalName -in @('Slides','Notes')){$child.InnerText='13'}}
 $app.SelectSingleNode('//ep:HeadingPairs/vt:vector/vt:variant[6]/vt:i4',$an).InnerText='13'
 $titles=$app.SelectSingleNode('//ep:TitlesOfParts/vt:vector',$an);foreach($t in @($titles.ChildNodes)){if($t.InnerText -eq 'Có nhu cầu hỗ trợ; cần kiểm chứng sức mua'){[void]$titles.RemoveChild($t)}};$titles.SetAttribute('size','16')
 Write-Part 'docProps/app.xml' $app
}finally{$z.Dispose()}
Write-Output 'Updated existing market card on slide 6; removed extra slide; restored 13 slides.'
