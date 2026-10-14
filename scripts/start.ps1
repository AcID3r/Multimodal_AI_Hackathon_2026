$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$taskPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $taskPython)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $taskPython -m pip install -r backend/requirements.txt
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
if (-not (Test-Path -LiteralPath "dataset/metadata.json")) {
    & $taskPython -m scripts.build_dataset --demo
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Write-Host "Open http://127.0.0.1:8000 - press Ctrl+C to stop."
& $taskPython -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
