$dpFiles = Get-ChildItem -Path 'C:\malsum\mimune-no-uraniwa\dp' -Filter *.html -Recurse
$modifiedFiles = @()

foreach ($file in $dpFiles) {
    $content = [System.IO.File]::ReadAllText($file.FullName)
    if ($content -match '(\.typo-btn\s*\{[^}]*?color\s*:\s*#fff)(;)') {
        $newContent = [regex]::Replace($content, '(\.typo-btn\s*\{[^}]*?color\s*:\s*#fff)(;)', ' !important')
        if ($content -ne $newContent) {
            [System.IO.File]::WriteAllText($file.FullName, $newContent, (New-Object System.Text.UTF8Encoding($false)))
            $modifiedFiles += $file.FullName
        }
    }
}

Write-Output '--- TASK 2 REPLACEMENTS ---'
Write-Output "Total files modified for color: $($modifiedFiles.Count)"
$modifiedFiles | ForEach-Object { Write-Output  }
