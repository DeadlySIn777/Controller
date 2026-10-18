# Bounded local routing monitor. Audible alert only when a measured limit is exceeded.
param([int]$DurationMinutes = 60)
$ErrorActionPreference = 'Stop'
$watchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$watchLog = Join-Path $watchRoot 'resource-samples.jsonl'
$watchState = Join-Path $watchRoot 'resource-status.json'
$watchDeadline = (Get-Date).AddMinutes($DurationMinutes)
$watchCpuLimit = 70
$watchGpuLimit = 80
$watchWattLimit = 350
$watchNvidia = 'C:/Windows/System32/nvidia-smi.exe'
@{phase='RUNNING'; pid=$PID; start_utc=(Get-Date).ToUniversalTime().ToString('o'); until_utc=$watchDeadline.ToUniversalTime().ToString('o'); cpu_limit_percent=$watchCpuLimit; gpu_limit_c=$watchGpuLimit; gpu_limit_w=$watchWattLimit; alert='console beep and logged breach'} | ConvertTo-Json | Set-Content -LiteralPath $watchState -Encoding utf8
try {
    while ((Get-Date) -lt $watchDeadline) {
        $watchCpu = (Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 10).CounterSamples.CookedValue
        $watchGpuLine = & $watchNvidia --query-gpu=temperature.gpu,power.draw --format=csv,noheader,nounits
        if ($LASTEXITCODE -ne 0) { throw 'nvidia-smi query failed' }
        $watchGpuFields = $watchGpuLine.Split(',')
        $watchTemp = [double]::Parse($watchGpuFields[0].Trim(), [Globalization.CultureInfo]::InvariantCulture)
        $watchPower = [double]::Parse($watchGpuFields[1].Trim(), [Globalization.CultureInfo]::InvariantCulture)
        $watchHigh = @()
        if ($watchCpu -gt $watchCpuLimit) { $watchHigh += 'cpu' }
        if ($watchTemp -gt $watchGpuLimit) { $watchHigh += 'gpu_temperature' }
        if ($watchPower -gt $watchWattLimit) { $watchHigh += 'gpu_power' }
        $watchSample = @{utc=(Get-Date).ToUniversalTime().ToString('o'); cpu_percent=[math]::Round($watchCpu,2); gpu_c=$watchTemp; gpu_w=$watchPower; breached=$watchHigh}
        $watchSample | ConvertTo-Json -Compress | Add-Content -LiteralPath $watchLog -Encoding utf8
        if ($watchHigh.Count -gt 0) {
            Write-Output ($watchSample | ConvertTo-Json -Compress)
            try { [console]::Beep(1000, 500) } catch { Write-Output 'Audible alert unavailable; breach remains logged.' }
        }
    }
    @{phase='COMPLETE'; pid=$PID; utc=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $watchState -Encoding utf8
} catch {
    @{phase='FAILED'; pid=$PID; utc=(Get-Date).ToUniversalTime().ToString('o'); reason=$_.Exception.Message} | ConvertTo-Json | Set-Content -LiteralPath $watchState -Encoding utf8
    throw
}
