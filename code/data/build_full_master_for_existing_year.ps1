param(
    [Parameter(Mandatory = $true, Position = 0)]
    [int]$Year
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
Set-Location $projectRoot

function Resolve-PythonExecutable {
    $candidates = @(
        (Join-Path $projectRoot ".venv\Scripts\python.exe"),
        (Join-Path $projectRoot ".venv\bin\python"),
        "python"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -eq "python") {
            $command = Get-Command python -ErrorAction SilentlyContinue
            if ($command) {
                return $command.Source
            }
            continue
        }
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    throw "Python executable not found. Checked .venv\\Scripts\\python.exe, .venv\\bin\\python, and python in PATH."
}
$pythonExe = Resolve-PythonExecutable

$tdxRaw = Join-Path $projectRoot "code/data/formal/tdx_daily_raw.csv"
$baostockYear = Join-Path $projectRoot "code/data/formal/master/baostock_fields/$Year.csv"
$masterDir = Join-Path $projectRoot "code/data/formal/master"
$tdxYearRaw = Join-Path $masterDir "tdx_${Year}_raw.csv"
$tdxBase = Join-Path $masterDir "tdx_full_master_base_${Year}.csv"
$fullMaster = Join-Path $masterDir "full_master_${Year}.csv"

if (-not (Test-Path $tdxRaw)) {
    throw "Missing TDX raw daily file: $tdxRaw"
}
if (-not (Test-Path $baostockYear)) {
    throw "Missing baostock yearly supplement file: $baostockYear"
}

Write-Host "Building full master for year $Year" -ForegroundColor Cyan
Write-Host "TDX raw input: $tdxRaw"
Write-Host "Baostock supplement: $baostockYear"
Write-Host "Output directory: $masterDir"

& $pythonExe "code/data/build_tdx_year_slice.py" `
    --input-path "code/data/formal/tdx_daily_raw.csv" `
    --output-path "code/data/formal/master/tdx_${Year}_raw.csv" `
    --year $Year
if ($LASTEXITCODE -ne 0) {
    throw "Python command failed: build_tdx_year_slice.py"
}

& $pythonExe "code/data/build_tdx_full_master_base.py" `
    --input-path "code/data/formal/master/tdx_${Year}_raw.csv" `
    --output-path "code/data/formal/master/tdx_full_master_base_${Year}.csv" `
    --adjustflag-value 2
if ($LASTEXITCODE -ne 0) {
    throw "Python command failed: build_tdx_full_master_base.py"
}

& $pythonExe "code/data/merge_baostock_master_fields.py" `
    --tdx-base-path "code/data/formal/master/tdx_full_master_base_${Year}.csv" `
    --baostock-path "code/data/formal/master/baostock_fields/${Year}.csv" `
    --output-path "code/data/formal/master/full_master_${Year}.csv"
if ($LASTEXITCODE -ne 0) {
    throw "Python command failed: merge_baostock_master_fields.py"
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Generated files:"
Write-Host "  $tdxYearRaw"
Write-Host "  $tdxBase"
Write-Host "  $fullMaster"
