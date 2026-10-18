$ErrorActionPreference = 'Stop'
$efinityInstallerPath = 'C:\Users\Gluis\Downloads\efinity-2026.1.132-windows-x64.msi'
$efinityWindowsInstaller = New-Object -ComObject WindowsInstaller.Installer
$efinityDatabase = $efinityWindowsInstaller.GetType().InvokeMember('OpenDatabase', 'InvokeMethod', $null, $efinityWindowsInstaller, @($efinityInstallerPath, 0))
function Read-EfinityMsiRows([string]$Query, [int]$Columns) {
    $efinityView = $efinityDatabase.GetType().InvokeMember('OpenView', 'InvokeMethod', $null, $efinityDatabase, @($Query))
    $efinityView.GetType().InvokeMember('Execute', 'InvokeMethod', $null, $efinityView, $null) | Out-Null
    $efinityRows = @()
    while ($efinityRecord = $efinityView.GetType().InvokeMember('Fetch', 'InvokeMethod', $null, $efinityView, $null)) {
        $efinityValues = @()
        for ($efinityColumn = 1; $efinityColumn -le $Columns; $efinityColumn++) {
            $efinityValues += [string]$efinityRecord.GetType().InvokeMember('StringData', 'GetProperty', $null, $efinityRecord, @($efinityColumn))
        }
        $efinityRows += ,$efinityValues
    }
    $efinityView.GetType().InvokeMember('Close', 'InvokeMethod', $null, $efinityView, $null) | Out-Null
    return ,$efinityRows
}
$efinityProperties = @{}
foreach ($efinityRow in (Read-EfinityMsiRows 'SELECT `Property`, `Value` FROM `Property`' 2)) {
    if ($efinityRow[0] -match '^(ProductName|ProductVersion|Manufacturer|ProductCode|UpgradeCode|ALLUSERS|MSIINSTALLPERUSER|INSTALLLEVEL|ARPNOREPAIR|ARPNOMODIFY|INSTALLDIR|TARGETDIR)$' -or $efinityRow[0] -match '(?i)license|eula|agree') {
        $efinityProperties[$efinityRow[0]] = $efinityRow[1]
    }
}
$efinityFeatures = Read-EfinityMsiRows 'SELECT `Feature`, `Feature_Parent`, `Title`, `Description`, `Level` FROM `Feature`' 5
$efinityLicenseControls = @()
foreach ($efinityRow in (Read-EfinityMsiRows 'SELECT `Dialog_`, `Control`, `Type`, `Property`, `Text` FROM `Control`' 5)) {
    if (($efinityRow[0] + ' ' + $efinityRow[1] + ' ' + $efinityRow[3]) -match '(?i)license|eula|agree') {
        if ($efinityRow[0] -eq 'LicenseAgreementDlg' -and $efinityRow[1] -eq 'LicenseText') {
            [System.IO.File]::WriteAllText((Join-Path $PSScriptRoot 'installer-license.rtf'), $efinityRow[4], [System.Text.Encoding]::ASCII)
        }
        $efinityLicenseControls += [pscustomobject]@{ Dialog=$efinityRow[0]; Control=$efinityRow[1]; Type=$efinityRow[2]; Property=$efinityRow[3]; TextLength=$efinityRow[4].Length; TextPrefix=$efinityRow[4].Substring(0, [Math]::Min(180,$efinityRow[4].Length)) }
    }
}
$efinityConditions = Read-EfinityMsiRows 'SELECT `Condition`, `Description` FROM `LaunchCondition`' 2
$efinityActions = Read-EfinityMsiRows 'SELECT `Action`, `Type`, `Source`, `Target` FROM `CustomAction`' 4
$efinityDirectories = Read-EfinityMsiRows 'SELECT `Directory`, `Directory_Parent`, `DefaultDir` FROM `Directory`' 3
$efinitySummary = [pscustomobject]@{ Properties=$efinityProperties; Features=$efinityFeatures; LaunchConditions=$efinityConditions; LicenseControls=$efinityLicenseControls; CustomActions=$efinityActions; Directories=$efinityDirectories; DatabaseMode='ReadOnly'; Installed=$false }
$efinitySummary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'installer-metadata.json') -Encoding utf8
$efinitySummary | Select-Object Properties,Features,LaunchConditions | ConvertTo-Json -Depth 8
