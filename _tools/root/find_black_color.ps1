$dpFiles = Get-ChildItem -Path 'C:\malsum\mimune-no-uraniwa\dp' -Include *.html, *.css -Recurse

foreach ($file in $dpFiles) {
    $content = [System.IO.File]::ReadAllText($file.FullName)
    if ($content -match '\.typo-btn[^{]*\{[^}]*color\s*:\s*(#000|black|#333333|#333|#111)') {
        Write-Output "Found in $($file.FullName)"
    }
}
