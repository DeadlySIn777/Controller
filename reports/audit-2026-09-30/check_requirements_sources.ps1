[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$attachmentRoot = 'C:/Users/Gluis/.codex/attachments'
$catalogPath = Join-Path $projectRoot 'research/feature-roadmap.json'
$catalog = Get-Content -LiteralPath $catalogPath -Raw | ConvertFrom-Json
$featureSource = Join-Path $projectRoot 'research/user-notes/2026-09-28-feature-platform.txt'
$sourceLines = Get-Content -LiteralPath $featureSource
$markdownCatalog = Get-Content -LiteralPath (Join-Path $projectRoot 'docs/FEATURE_CATALOG.md') -Raw

$sourceMap = @(
    @{ id='1cca518e-ee1d-4dd7-8fdc-59f07d256f21'; archive='research/user-notes/2026-09-28-feature-platform.txt' },
    @{ id='3507637d-97de-4d6e-8c73-f045d5196ff0'; archive='research/user-notes/2026-09-28-plasma-upgrades.txt' },
    @{ id='c11be1d2-610f-4861-a758-865d660d4d99'; archive='research/user-notes/2026-09-28-modbus-expansion.txt' },
    @{ id='d57421ed-db5e-4283-8fe7-1868d02e4419'; archive='research/user-notes/2026-09-28-integration-priority.txt' },
    @{ id='deed7d7d-b936-4606-b4f9-eb8e2bf1739d'; archive='research/user-notes/2026-09-28-esp-industrial-direction.txt' },
    @{ id='f1c97886-c7d8-4bda-bef0-dee62ae94f15'; archive='research/user-notes/2026-09-28-repairability-memory.txt' },
    @{ id='b7f7ac9d-1dc6-4139-8792-481a0ac002bb'; archive='research/architecture-source/2026-09-30-original-note.txt' }
)
$sourceResults = foreach ($source in $sourceMap) {
    $originalPath = Join-Path (Join-Path $attachmentRoot $source.id) 'Pasted text.txt'
    $originalHash = (Get-FileHash -LiteralPath $originalPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $archiveHash = $null
    $manifestHash = $null
    if ($source.archive) {
        $archiveHash = (Get-FileHash -LiteralPath (Join-Path $projectRoot $source.archive) -Algorithm SHA256).Hash.ToLowerInvariant()
        $manifestRecord = $catalog.sources | Where-Object path -eq $source.archive
        $manifestHash = $manifestRecord.sha256
    }
    [ordered]@{
        attachment_id = $source.id
        original_path = $originalPath.Replace('\','/')
        original_bytes = (Get-Item -LiteralPath $originalPath).Length
        original_sha256 = $originalHash
        archive_path = $source.archive
        archive_sha256 = $archiveHash
        archive_equal_original = if ($archiveHash) { $archiveHash -eq $originalHash } else { $null }
        catalogue_recorded_sha256 = $manifestHash
        catalogue_hash_current = if ($manifestHash) { $manifestHash -eq $archiveHash } else { $null }
        source_authority = 'user-supplied advisor note; individual proposals are not adopted decisions without additional authority'
    }
}

$featureRows = foreach ($feature in $catalog.features) {
    $sourceLine = $sourceLines[$feature.source_line - 1]
    $heading = '**' + $feature.id + '. ' + $feature.title + '**'
    [ordered]@{
        id = $feature.id
        number = $feature.number
        title = $feature.title
        description = $feature.description_from_supplied_note
        category = $feature.category
        source_path = 'research/user-notes/2026-09-28-feature-platform.txt'
        original_attachment_id = '1cca518e-ee1d-4dd7-8fdc-59f07d256f21'
        source_line = $feature.source_line
        source_title_exact = $sourceLine.StartsWith(($feature.number.ToString() + '. ' + $feature.title + ' — '))
        source_description_preserved = $sourceLine.Contains($feature.description_from_supplied_note)
        markdown_title_preserved = $markdownCatalog.Contains($heading)
        markdown_description_preserved = $markdownCatalog.Contains($feature.description_from_supplied_note)
        declared_product_status = $feature.product_status
        declared_physical_qualification = $feature.physical_qualification
        delivery_focus = $feature.delivery_focus
        source_flags = $feature.source_flags
        references_from_supplied_note = $feature.references_from_supplied_note
        planning_artifact = 'docs/PLATFORM_ROADMAP.md'
        implementation_evidence_index = 'reports/ENGINEERING_STATUS.md'
        per_feature_implementation_reconciliation = 'not_present; proposal preservation alone is not implementation evidence'
        required_for_initial_product = 'not_established_for_this_full_feature; later confirmed product requirements take precedence'
    }
}
$featureProblems = @($featureRows | Where-Object {
    -not $_.source_title_exact -or -not $_.source_description_preserved -or
    -not $_.markdown_title_preserved -or -not $_.markdown_description_preserved
})
$expectedIds = @(1..200 | ForEach-Object { 'F{0:D3}' -f $_ })
$actualIds = @($catalog.features.id)
$idDifference = @(Compare-Object -ReferenceObject $expectedIds -DifferenceObject $actualIds)
$sourceProblems = @($sourceResults | Where-Object {
    $_.archive_path -and (-not $_.archive_equal_original -or ($_.catalogue_recorded_sha256 -and -not $_.catalogue_hash_current))
})

$coreRows = foreach ($line in (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'REQUIREMENTS_AUDIT.md'))) {
    if ($line -notmatch '^\| R\d{3} \|') { continue }
    $cells = $line.Split('|')
    [ordered]@{
        id = $cells[1].Trim()
        requirement = $cells[2].Trim()
        source_authority = $cells[3].Trim()
        accounting_artifacts = $cells[4].Trim()
        accounting_and_implementation_boundary = $cells[5].Trim()
        audited_evidence_class = 'source/document inspection; not a test execution'
    }
}
$auditedFiles = @(
    Get-Item -LiteralPath (Join-Path $projectRoot 'PROJECT_MEMORY.md')
    Get-Item -LiteralPath (Join-Path $projectRoot 'PROJECT_BRIEFING.md')
    Get-Item -LiteralPath (Join-Path $projectRoot 'README.md')
    Get-Item -LiteralPath (Join-Path $projectRoot 'CNC_CONTROLLER_INVESTIGATION.md')
    Get-ChildItem -LiteralPath (Join-Path $projectRoot 'docs') -File
    Get-ChildItem -LiteralPath (Join-Path $projectRoot 'research/user-notes') -File
    Get-Item -LiteralPath $catalogPath
    Get-Item -LiteralPath (Join-Path $projectRoot 'research/expanded-hardware-target.json')
    Get-Item -LiteralPath (Join-Path $projectRoot 'reports/ENGINEERING_STATUS.md')
    Get-Item -LiteralPath (Join-Path $projectRoot 'reports/COMMERCIAL_DIRECTION.md')
    Get-Item -LiteralPath (Join-Path $projectRoot 'reports/platform-plan-review.json')
)
$fileHashes = foreach ($file in $auditedFiles) {
    [ordered]@{
        path = $file.FullName.Substring($projectRoot.Length + 1).Replace('\','/')
        sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$companionRoot = 'C:/Users/Gluis/claude-worktrees/controller-interface-spec'
$companionFiles = @(
    Get-Item -LiteralPath (Join-Path $companionRoot 'docs/CONTROLLER_INTERFACE_SPEC.md')
    Get-ChildItem -LiteralPath (Join-Path $companionRoot 'docs/interface-spec') -File
    Get-ChildItem -LiteralPath (Join-Path $companionRoot 'spec') -File
)
$companionHashes = foreach ($file in $companionFiles) {
    [ordered]@{
        path = $file.FullName.Substring($companionRoot.Length + 1).Replace('\','/')
        sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$mainHead = (& git -C $projectRoot rev-parse HEAD).Trim()
$companionHead = (& git -C $companionRoot rev-parse HEAD).Trim()
& git -C $projectRoot merge-base --is-ancestor 0d879b2 $mainHead
$companionSpecMerged = $LASTEXITCODE -eq 0
$result = [ordered]@{
    recorded_at_utc = [DateTime]::UtcNow.ToString('o')
    audit_scope = 'visible direct messages, seven named original attachments, six note archives, 200-feature preservation and current planning/memory/status inspection'
    evidence_class = 'source/document inspection; no runtime, target, HDL, circuit or physical tests rerun'
    known_original_attachments = $sourceResults
    originals_with_identical_current_archives = @($sourceResults | Where-Object archive_equal_original -eq $true).Count
    original_without_archive_ids = @($sourceResults | Where-Object { -not $_.archive_path } | ForEach-Object attachment_id)
    feature_count = $featureRows.Count
    unique_feature_ids = @($actualIds | Sort-Object -Unique).Count
    feature_id_difference = $idDifference
    feature_preservation_problems = $featureProblems
    source_hash_problems = $sourceProblems
    all_features_declared_proposals = @($catalog.features | Where-Object product_status -ne 'proposal').Count -eq 0
    core_requirement_rows = $coreRows.Count
    later_user_decision_provenance = 'memory-recorded; independently rechecked original messages unavailable'
    source_files_at_check = $fileHashes
    git_baseline_commit = 'e994311'
    main_head_at_check = $mainHead
    separate_interface_worktree = [ordered]@{
        path = $companionRoot
        branch = 'claude/interface-spec'
        head_at_check = $companionHead
        specification_commit = '0d879b2'
        new_codec_commit = '67b1bfc'
        specification_merged_into_main = $companionSpecMerged
        inspected_specification_files = $companionHashes
        implementation_test_scope = 'not rerun or independently implementation-audited by this source-accounting script'
    }
    accounting_score_observed_before_reconciliation = 76
    manufacturing_ready = $false
}
$result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'requirements-source-check.json') -Encoding utf8
@($featureRows) | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'requirements-feature-trace.json') -Encoding utf8
@($coreRows) | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'requirements-core-trace.json') -Encoding utf8
[ordered]@{
    feature_count=$featureRows.Count
    feature_problems=$featureProblems.Count
    id_problems=$idDifference.Count
    source_hash_problems=$sourceProblems.Count
    original_archive_pairs=@($sourceResults | Where-Object archive_equal_original -eq $true).Count
    core_rows=$coreRows.Count
} | ConvertTo-Json
if ($featureProblems.Count -or $idDifference.Count -or $sourceProblems.Count -or $featureRows.Count -ne 200 -or $coreRows.Count -ne 64) { exit 1 }
