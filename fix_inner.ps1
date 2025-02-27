Get-ChildItem -Recurse -File | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $content = $content -replace 'AC[A-Za-z0-9]{32}', 'REMOVED'
    $content = $content -replace 'hf_[A-Za-z0-9]{40}', 'REMOVED'
    Set-Content $_.FullName -Value $content
}
