# Serialize one bounded successor after the currently owned monitor exits.
# No native/GPU compute job, heavy slot, process stop, or system setting change.
$ErrorActionPreference = 'Stop'
$nextRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$previousRoot = Split-Path -Parent $nextRoot
$previousStatePath = Join-Path $previousRoot 'resource-status.json'
$armStatePath = Join-Path $nextRoot 'arm-status.json'
$nextScript = Join-Path $nextRoot 'watch_resources.ps1'
$expectedPid = 38228
$expectedOldScript = (Join-Path $previousRoot 'watch_resources.ps1').Replace('\','/')
$previousState = Get-Content -LiteralPath $previousStatePath -Raw | ConvertFrom-Json
if ($previousState.pid -ne $expectedPid -or $previousState.phase -ne 'RUNNING') { throw 'Current own monitor identity/status changed before arming' }
$oldDeadline = [DateTimeOffset]::Parse($previousState.until_utc)
$armingDeadline = $oldDeadline.AddMinutes(5)
$oldProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $expectedPid"
if (-not $oldProcess -or -not $oldProcess.CommandLine.Replace('\','/').Contains($expectedOldScript)) { throw 'Current PID is not the expected own monitor' }
$oldCreated = $oldProcess.CreationDate
@{phase='ARMED_WAITING_PREVIOUS'; pid=$PID; previous_pid=$expectedPid; previous_until_utc=$oldDeadline.ToString('o'); new_duration_minutes=60; heavy_slots_added=0; previous_process_created=$oldCreated.ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $armStatePath -Encoding utf8
while ([DateTimeOffset]::UtcNow -lt $armingDeadline) {
    $oldProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $expectedPid"
    $oldStillOwned = $oldProcess -and $oldProcess.CreationDate -eq $oldCreated
    if (-not $oldStillOwned -and [DateTimeOffset]::UtcNow -ge $oldDeadline) {
        $finished = Get-Content -LiteralPath $previousStatePath -Raw | ConvertFrom-Json
        if ($finished.pid -ne $expectedPid -or $finished.phase -ne 'COMPLETE') { throw 'Previous monitor did not finish successfully; successor not started' }
        @{phase='STARTING_BOUNDED_SUCCESSOR'; pid=$PID; previous_pid=$expectedPid; utc=[DateTimeOffset]::UtcNow.ToString('o'); heavy_slots_added=0} | ConvertTo-Json | Set-Content -LiteralPath $armStatePath -Encoding utf8
        & $nextScript -DurationMinutes 60
        $lastState = Get-Content -LiteralPath (Join-Path $nextRoot 'resource-status.json') -Raw | ConvertFrom-Json
        @{phase=$lastState.phase; pid=$PID; previous_pid=$expectedPid; utc=[DateTimeOffset]::UtcNow.ToString('o'); heavy_slots_added=0} | ConvertTo-Json | Set-Content -LiteralPath $armStatePath -Encoding utf8
        exit
    }
    Start-Sleep -Seconds 2
}
throw 'Previous own monitor did not exit within bounded handover; no duplicate monitor started'
