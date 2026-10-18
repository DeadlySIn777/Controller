# Run the disconnected engineering bench from any working directory.
# Set CONTROLLER_PYTHON to a Python 3.11+ executable to select a runtime.
$controllerPython = $env:CONTROLLER_PYTHON
if ([string]::IsNullOrWhiteSpace($controllerPython)) {
    $controllerPython = 'python'
}
& $controllerPython -X utf8 (Join-Path $PSScriptRoot 'tools/validate_controller.py') @args
if (-not $?) {
    if ($null -ne $LASTEXITCODE) { exit $LASTEXITCODE }
    exit 1
}
exit $LASTEXITCODE
