param(
  [string]$Src,
  [string]$OutJson,
  [string]$PngDir = "",
  [string]$PptxOut = "",
  [int]$PngWidth = 1280
)

$ErrorActionPreference = "Stop"

function Get-ShapeInfo($shp, $depth) {
  $info = [ordered]@{
    name = $shp.Name
    type = [int]$shp.Type
    left = [math]::Round($shp.Left, 1)
    top = [math]::Round($shp.Top, 1)
    w = [math]::Round($shp.Width, 1)
    h = [math]::Round($shp.Height, 1)
  }
  try { if ($shp.Type -eq 1) { $info.auto = [int]$shp.AutoShapeType } } catch {}
  try {
    if ($shp.HasTextFrame -and $shp.TextFrame.HasText) {
      $tr = $shp.TextFrame.TextRange
      $info.text = $tr.Text
      $info.font = $tr.Font.Name
      try { $info.fontFE = $tr.Font.NameFarEast } catch {}
      $info.size = $tr.Font.Size
    }
  } catch {}
  try {
    if ($shp.HasTable) {
      $cells = @()
      $tbl = $shp.Table
      for ($r = 1; $r -le $tbl.Rows.Count; $r++) {
        for ($c = 1; $c -le $tbl.Columns.Count; $c++) {
          $t = $tbl.Cell($r, $c).Shape.TextFrame.TextRange.Text
          if ($t) { $cells += $t }
        }
      }
      $info.table = $cells
    }
  } catch {}
  try { if ($shp.HasSmartArt) { $info.smartart = $true } } catch {}
  try { if ($shp.HasChart) { $info.chart = $true } } catch {}
  if ($shp.Type -eq 6) {
    $kids = @()
    foreach ($g in $shp.GroupItems) { $kids += (Get-ShapeInfo $g ($depth + 1)) }
    $info.items = $kids
  }
  return $info
}

$app = New-Object -ComObject PowerPoint.Application
$before = $app.Presentations.Count
# ReadOnly=-1, Untitled=0, WithWindow=0
$pres = $app.Presentations.Open($Src, -1, 0, 0)

$sw = $pres.PageSetup.SlideWidth
$sh = $pres.PageSetup.SlideHeight
$pngH = [int][math]::Round($PngWidth * $sh / $sw)

$slides = @()
foreach ($s in $pres.Slides) {
  $shapes = @()
  foreach ($shp in $s.Shapes) { $shapes += (Get-ShapeInfo $shp 0) }
  $notes = ""
  try { $notes = $s.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text } catch {}
  $title = ""
  try { if ($s.Shapes.HasTitle) { $title = $s.Shapes.Title.TextFrame.TextRange.Text } } catch {}
  $slides += [ordered]@{
    index = $s.SlideIndex
    layout = [int]$s.Layout
    title = $title
    hidden = [int]$s.SlideShowTransition.Hidden
    shapes = $shapes
    notes = $notes
  }
  if ($PngDir -ne "") {
    $p = Join-Path $PngDir ("{0:D3}.png" -f $s.SlideIndex)
    $s.Export($p, "PNG", $PngWidth, $pngH)
  }
}

$out = [ordered]@{
  file = $Src
  slideWidth = $sw
  slideHeight = $sh
  count = $pres.Slides.Count
  slides = $slides
}
$json = $out | ConvertTo-Json -Depth 30
[System.IO.File]::WriteAllText($OutJson, $json, (New-Object System.Text.UTF8Encoding($false)))

if ($PptxOut -ne "") { $pres.SaveAs($PptxOut, 24) }

$pres.Close()
if ($app.Presentations.Count -eq 0 -and $before -eq 0) { $app.Quit() }
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
"ok: $Src slides=" + $out.count + " size=" + $sw + "x" + $sh
