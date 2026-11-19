$ErrorActionPreference = 'Stop'
$pidFile = Join-Path $PSScriptRoot 'var\run\processes.json'
if (!(Test-Path -LiteralPath $pidFile)) {
    Write-Host 'No DataClass processes recorded.'
    exit 0
}
$records = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
foreach ($record in $records) {
    $process = Get-Process -Id $record.pid -ErrorAction SilentlyContinue
    if ($process -and $process.StartTime.ToUniversalTime().ToString('o') -eq $record.started_at) {
        & taskkill.exe /PID $process.Id /T /F | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Could not stop $($record.name)." }
        Write-Host "Stopped $($record.name) (PID $($process.Id))."
    }
}
Remove-Item -LiteralPath $pidFile
