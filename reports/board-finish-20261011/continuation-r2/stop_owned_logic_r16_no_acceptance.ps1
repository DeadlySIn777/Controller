$ErrorActionPreference='Stop'
$TaskRoot = 'C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller\reports\board-finish-20261011\continuation-r2'
$ScriptPath = Join-Path $TaskRoot 'repair_logic_exact_reuse_returns_r16.py'
$CheckpointPath = Join-Path $TaskRoot 'logic-exact-reuse-return-restoration-r16\checkpoint.json'
$StoppedReceipt = Join-Path $TaskRoot 'logic-exact-reuse-return-restoration-r16\deliberate-stop-no-acceptance.json'
if (Test-Path -LiteralPath $StoppedReceipt) { throw 'Stop receipt already exists' }
$Checkpoint = Get-Content -Raw -LiteralPath $CheckpointPath | ConvertFrom-Json
if (@($Checkpoint.rows | Where-Object { $null -ne $_.repair }).Count -ne 0) { throw 'An accepted addition requires immutable checkpoint preservation first' }
$OwnedProcess = @(Get-CimInstance -ClassName Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match [regex]::Escape('repair_logic_exact_reuse_returns_r16.py') -and $_.CommandLine -match [regex]::Escape('launch_confined_host.py') })
if ($OwnedProcess.Count -ne 1) { throw 'Expected exactly one owned R16 host process' }
$StoppedId = $OwnedProcess[0].ProcessId
$VerifiedCommand = $OwnedProcess[0].CommandLine
Stop-Process -Id $StoppedId
$FinalCheckpoint = Get-Content -Raw -LiteralPath $CheckpointPath | ConvertFrom-Json
if (@($FinalCheckpoint.rows | Where-Object { $null -ne $_.repair }).Count -ne 0) { throw 'Concurrent acceptance: preserve output and review before resuming' }
$Record = [ordered]@{verdict='DELIBERATE_OWNED_R16_STOP_ZERO_ACCEPTED_NEW_GEOMETRY';utc=[DateTime]::UtcNow.ToString('o');pid=$StoppedId;verified_command=$VerifiedCommand;script_sha256=(Get-FileHash -LiteralPath $ScriptPath -Algorithm SHA256).Hash.ToLower();checkpoint_sha256=(Get-FileHash -LiteralPath $CheckpointPath -Algorithm SHA256).Hash.ToLower();rows=@($FinalCheckpoint.rows).Count;accepted_additions=0;reason='Avoid recomputing unchanged source union before every no-barrel singleton; exact reuse successor retains fresh wholebank source equality gates';native_jobs_stopped=0;shared_queue_or_resource_alarm_modified=$false;live_board_changed=$false}
$Record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $StoppedReceipt
$Record | ConvertTo-Json -Depth 3
