$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root
if (-not (Test-Path ".env")) {
    throw "Create a server-only .env from .env.staging.example first."
}
$python = Join-Path $root ".venv\Scripts\python.exe"
$waitress = Join-Path $root ".venv\Scripts\waitress-serve.exe"
if (-not (Test-Path $python) -or -not (Test-Path $waitress)) {
    throw "Install requirements inside .venv before starting."
}
& $python "scripts\staging_preflight.py"
if ($LASTEXITCODE -ne 0) { throw "Staging preflight failed." }
& $waitress "--listen=127.0.0.1:8008" "config.wsgi:application"
if ($LASTEXITCODE -ne 0) { throw "Waitress process exited with an error." }
