param([switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$runDir = Join-Path $root 'var\run'
$pidFile = Join-Path $runDir 'processes.json'

if (!(Test-Path -LiteralPath $python)) { throw 'Missing backend Python environment. See HUONG_DAN_CHAY.md.' }
if (!(Test-Path -LiteralPath (Join-Path $frontend 'node_modules\vite\bin\vite.js'))) { throw 'Missing frontend dependencies. Run npm install in frontend.' }
New-Item -ItemType Directory -Path $runDir -Force | Out-Null

Push-Location -LiteralPath $backend
try {
    & $python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
    & $python -m app.relocate_data
    if ($LASTEXITCODE -ne 0) { throw 'Local data preparation failed.' }
} finally { Pop-Location }

$saved = @()
if (Test-Path -LiteralPath $pidFile) { $saved = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json }
$node = (Get-Command node.exe -ErrorAction Stop).Source

$items = @(
    @{ Name = 'backend'; Exe = $python; Args = '-m uvicorn app.main:app --host 127.0.0.1 --port 8000'; Dir = $backend; Port = 8000 },
    @{ Name = 'worker'; Exe = $python; Args = '-u -m app.worker'; Dir = $backend; Port = 0 },
    @{ Name = 'frontend'; Exe = $node; Args = '"' + (Join-Path $frontend 'node_modules\vite\bin\vite.js') + '" --host 127.0.0.1 --port 5173 --strictPort'; Dir = $frontend; Port = 5173 }
)
$records = @()
foreach ($item in $items) {
    $previous = $saved | Where-Object { $_.name -eq $item.Name } | Select-Object -First 1
    $running = if ($previous) { Get-Process -Id $previous.pid -ErrorAction SilentlyContinue } else { $null }
    if ($running -and $running.StartTime.ToUniversalTime().ToString('o') -eq $previous.started_at) {
        $records += $previous
        Write-Host "$($item.Name) is already running (PID $($running.Id))."
        continue
    }
    if ($item.Port -and (Get-NetTCPConnection -State Listen -LocalPort $item.Port -ErrorAction SilentlyContinue)) {
        throw "Port $($item.Port) is in use by another process. See var\run\processes.json and stop.ps1."
    }
    $process = Start-Process -FilePath $item.Exe -ArgumentList $item.Args -WorkingDirectory $item.Dir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDir "$($item.Name).out.log") -RedirectStandardError (Join-Path $runDir "$($item.Name).err.log") -PassThru
    $records += [pscustomobject]@{ name = $item.Name; pid = $process.Id; started_at = $process.StartTime.ToUniversalTime().ToString('o') }
    ConvertTo-Json -InputObject @($records) | Set-Content -LiteralPath $pidFile -Encoding UTF8
}
ConvertTo-Json -InputObject @($records) | Set-Content -LiteralPath $pidFile -Encoding UTF8

$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $health = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 2
        $page = Invoke-WebRequest 'http://127.0.0.1:5173' -UseBasicParsing -TimeoutSec 2
        if ($health.status -eq 'ok' -and $page.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
    Start-Sleep -Seconds 1
}
if (!$ready) { throw "Startup did not complete. Check logs in $runDir" }
foreach ($record in $records) {
    if (!(Get-Process -Id $record.pid -ErrorAction SilentlyContinue)) { throw "$($record.name) exited. Check logs in $runDir" }
}
Write-Host 'DataClass is ready: http://127.0.0.1:5173' -ForegroundColor Green
Write-Host "Logs: $runDir"
Write-Host 'To stop: powershell -ExecutionPolicy Bypass -File stop.ps1'
if (!$NoBrowser) { Start-Process 'http://127.0.0.1:5173' }
