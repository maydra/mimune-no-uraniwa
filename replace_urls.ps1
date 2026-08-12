$htmlFiles = Get-ChildItem -Path 'C:\malsum\mimune-no-uraniwa' -Filter *.html -Recurse

$oldUrl = 'https://script.google.com/macros/s/AKfycbxbuP7GLEAwodsiLog16LZDZA0hnqlK0A21fx8Vq2-n-_gq_5EudLVMJy0yXk1KYO19lA/exec'
$newUrl = 'https://script.google.com/macros/s/AKfycbwJbfRW7-pS0h1n_qJvDR_uwTtqf6NSbogPrdE_d6lilWe8reC4CtmrwvqZM33wZ7HNww/exec'

$urlReplacements = @{}

foreach ($file in $htmlFiles) {
    try {
        $content = [System.IO.File]::ReadAllText($file.FullName)
        if ($content.Contains($oldUrl)) {
            $count = ([regex]::Matches($content, [regex]::Escape($oldUrl))).Count
            $urlReplacements[$file.FullName] = $count
            $newContent = $content.Replace($oldUrl, $newUrl)
            [System.IO.File]::WriteAllText($file.FullName, $newContent, (New-Object System.Text.UTF8Encoding($false)))
        }
    } catch {
        Write-Error "Error processing : "
    }
}

Write-Output '--- URL REPLACEMENTS ---'
$totalUrls = 0
$urlReplacements.GetEnumerator() | ForEach-Object { 
    Write-Output "$($_.Name) ($($_.Value) matches)"
    $totalUrls += $_.Value
}
Write-Output "Total files modified: $($urlReplacements.Count)"
Write-Output "Total URLs replaced: $totalUrls"
