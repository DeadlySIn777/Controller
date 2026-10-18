param([switch]$UartCompileCheck)
$ErrorActionPreference = 'Stop'
# Compile evidence in reports/ESP_SERVICE_BUILD.md was produced with ESP-IDF 5.5.4.
# Paths default to the recorded Windows Espressif installer layout and may be
# overridden with the standard ESP-IDF environment variables.
$requiredIdf = '5.5.4'
$taskTools = if ($env:IDF_TOOLS_PATH) { $env:IDF_TOOLS_PATH } else { 'C:\Espressif' }
$taskSdk = if ($env:IDF_PATH) { $env:IDF_PATH } else { Join-Path $taskTools "frameworks\esp-idf-v$requiredIdf" }
if (-not (Test-Path -LiteralPath "$taskSdk\tools\idf.py")) {
    throw "ESP-IDF $requiredIdf is required. Not found at '$taskSdk'; set IDF_PATH (and IDF_TOOLS_PATH) to the installation."
}
$versionCmake = Get-Content -LiteralPath "$taskSdk\tools\cmake\version.cmake" -Raw
$found = @('MAJOR', 'MINOR', 'PATCH') | ForEach-Object {
    if ($versionCmake -match "IDF_VERSION_$_\s+(\d+)") { $Matches[1] } else { '?' }
}
$foundIdf = $found -join '.'
if ($foundIdf -ne $requiredIdf) {
    throw "ESP-IDF $requiredIdf is required to reproduce the recorded build evidence; '$taskSdk' reports $foundIdf."
}
$taskPython = if ($env:IDF_PYTHON_ENV_PATH) {
    Join-Path $env:IDF_PYTHON_ENV_PATH 'Scripts\python.exe'
} else {
    $venv = Get-ChildItem -LiteralPath (Join-Path $taskTools 'python_env') -Directory -Filter 'idf5.5_py*_env' -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 1
    if ($venv) { Join-Path $venv.FullName 'Scripts\python.exe' } else { $null }
}
if (-not $taskPython -or -not (Test-Path -LiteralPath $taskPython)) {
    throw "No ESP-IDF 5.5 Python environment found under '$taskTools\python_env'; set IDF_PYTHON_ENV_PATH."
}
$env:IDF_PATH = $taskSdk
$env:IDF_TOOLS_PATH = $taskTools
$env:PATH = (Split-Path -Parent $taskPython) + ';' + $env:PATH
. "$taskSdk\export.ps1"
Push-Location -LiteralPath $PSScriptRoot
try {
    if ($UartCompileCheck) {
        & $taskPython "$taskSdk\tools\idf.py" -B .build/uart-compile-check -D 'SDKCONFIG=.build/uart-sdkconfig' -D 'SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.uart-build-check.defaults' build
    } else {
        & $taskPython "$taskSdk\tools\idf.py" -B .build/esp32s3 build
    }
    if ($LASTEXITCODE -ne 0) { throw "ESP-IDF build failed: $LASTEXITCODE" }
} finally { Pop-Location }
