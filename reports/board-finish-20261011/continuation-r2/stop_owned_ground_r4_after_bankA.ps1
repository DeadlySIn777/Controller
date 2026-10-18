$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path -LiteralPath '.').Path
if ($workspace -ne 'C:\Users\Gluis\OneDrive\Documents\ChatGPT\Controller') { throw 'Unexpected workspace' }
$reportRoot = Join-Path $workspace 'reports\board-finish-20261011\continuation-r2'
$output = Join-Path $reportRoot 'protected-field-return-restoration-r4-stop.json'
if (Test-Path -LiteralPath $output) { throw 'Preserve existing stop receipt' }
$targetProcessId = 33076
$taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $targetProcessId"
if ($null -eq $taskProcess -or $taskProcess.Name -ne 'python.exe' -or $taskProcess.CommandLine -notlike '*launch_confined_host.py*repair_protected_field_returns_r4.py*') { throw 'Exact owned R4 host process not found' }
$checkpointPath = Join-Path $reportRoot 'protected-field-return-restoration-r4\checkpoint.json'
$checkpoint = Get-Content -LiteralPath $checkpointPath -Raw | ConvertFrom-Json
if (@($checkpoint.rows | Where-Object { $_.repair }).Count -ne 4) { throw 'Accepted geometry changed; freeze and review it' }
if (@($checkpoint.rows | Where-Object { $_.net -eq '/motherboard_do/FIELD_B_0V' -and $_.repair }).Count -ne 0) { throw 'FBG accepted geometry changed; preserve it before stopping' }
$snapshot = Join-Path $reportRoot 'protected-field-return-r4-snapshot-bankA'
$proof = @(Get-Content -LiteralPath (Join-Path $snapshot 'bank-proofs.json') -Raw | ConvertFrom-Json)
if ($proof.Count -ne 1 -or -not $proof[0].same_original_source_and_owned_source_zone_fills_in_wholeboard_projection -or $proof[0].source_rooted_named_pads -ne 229) { throw 'Frozen successful FAG bank proof differs' }
$newContext = Join-Path $reportRoot 'field-power\c24-only-core91-root4-source-context-r100\model.pkl'
$newReceipt = Join-Path (Split-Path -Parent $newContext) 'receipt.json'
$next = Get-Content -LiteralPath $newReceipt -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $newContext -Algorithm SHA256).Hash.ToLowerInvariant() -ne $next.model_sha256 -or -not $next.C10036_pad_source_rooted -or -not $next.both_new_C_return_vias_source_rooted) { throw 'Corrected frozen C-only context unavailable' }
$sourceBoard = 'Z:\pcb-runs\claude-finish\integrate\revs\r07-ripup-signals-1.kicad_pcb'
$expectedLive = '0c807b78247740a08c7b5a4a4380f0d8975d10045c9ba505e1e5d353d4cbb8fc'
if ((Get-FileHash -LiteralPath $sourceBoard -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedLive) { throw 'Live source board changed' }
$cpuSeconds = (Get-Process -Id $targetProcessId).CPU
Stop-Process -Id $targetProcessId
Wait-Process -Id $targetProcessId -ErrorAction SilentlyContinue
$record = [ordered]@{
 utc = [DateTime]::UtcNow.ToString('o'); verdict = 'INTENTIONAL_OWNED_HOST_STOP_AFTER_FAG_WHOLEBANK_SUCCESS_NO_FBG_ACCEPTANCE'
 process_id = $targetProcessId; verified_command_line = $taskProcess.CommandLine; cpu_seconds_at_stop = $cpuSeconds
 reason = 'Resume frozen four successful FAG bridges on exact CORE91/C24 context with lazy nearest-port regional search; obsolete C target already source-rooted'
 accepted_FAG_new_zone_shapes_preserved = 4; source_rooted_FAG_named_pads = 229; accepted_FBG_shapes = 0
 original_native_and_live_board_edits = 0; snapshot = $snapshot; checkpoint_sha256 = (Get-FileHash -LiteralPath (Join-Path $snapshot 'checkpoint.json')).Hash.ToLowerInvariant()
 proposed_zones_sha256 = (Get-FileHash -LiteralPath (Join-Path $snapshot 'proposed-zones.pkl')).Hash.ToLowerInvariant()
 successful_bank_proof_sha256 = (Get-FileHash -LiteralPath (Join-Path $snapshot 'bank-proofs.json')).Hash.ToLowerInvariant()
 next_context_model_sha256 = $next.model_sha256; next_context_receipt_sha256 = (Get-FileHash -LiteralPath $newReceipt).Hash.ToLowerInvariant()
 successor_script_sha256 = (Get-FileHash -LiteralPath (Join-Path $reportRoot 'repair_fbg_lazy_existing_returns_r10.py')).Hash.ToLowerInvariant()
 failure_scope = 'Intentional stop, not a native/candidate failure'; independent_new_FAG_one_pad_planner_margin = 'Preserved FAIL5.26nm, explicit normalization/freshsource still required'
 CPU_GPU_alarm_and_KiCad_slots_touched = $false; adopted = $false
}
$record | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $output -Encoding utf8
if ((Get-FileHash -LiteralPath $sourceBoard -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedLive) { throw 'Live source changed during stop' }
[pscustomobject]@{ ProcessId=$targetProcessId; AcceptedFAG=4; AcceptedFBG=0; PreservedSourcePads=229; NextContext=$next.model_sha256 } | ConvertTo-Json -Compress
