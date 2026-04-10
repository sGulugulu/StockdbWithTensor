param(
    [Parameter(Mandatory = $true, Position = 0)]
    [int]$Year,

    [Parameter(Mandatory = $false, Position = 1)]
    [int]$MaxParallelMonths = 2
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
Set-Location $projectRoot

$masterDir = Join-Path $projectRoot "code/data/formal/master"
$yearDir = Join-Path $masterDir "baostock_fields/$Year"
$yearCsv = Join-Path $masterDir "baostock_fields/$Year.csv"
$fullMaster = Join-Path $masterDir "full_master_${Year}.csv"
$tdxYearRaw = Join-Path $masterDir "tdx_${Year}_raw.csv"
$tdxBase = Join-Path $masterDir "tdx_full_master_base_${Year}.csv"
$checkJson = Join-Path $masterDir "full_master_${Year}_check.json"
$reconcileLog = Join-Path $masterDir "logs/full_master_${Year}_reconcile.log"

Write-Host "Rebuilding full master for year $Year" -ForegroundColor Cyan
Write-Host "Project root: $projectRoot"
Write-Host "Max parallel months: $MaxParallelMonths"

Write-Host ""
Write-Host "[1/4] Cleaning old yearly artifacts..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $yearDir -ErrorAction SilentlyContinue
Remove-Item -Force $yearCsv -ErrorAction SilentlyContinue
Remove-Item -Force $fullMaster -ErrorAction SilentlyContinue
Remove-Item -Force $tdxYearRaw -ErrorAction SilentlyContinue
Remove-Item -Force $tdxBase -ErrorAction SilentlyContinue
Remove-Item -Force $checkJson -ErrorAction SilentlyContinue
Remove-Item -Force $reconcileLog -ErrorAction SilentlyContinue

Write-Host "[2/5] Rebuilding TDX yearly base..." -ForegroundColor Yellow
& wsl bash -lc ".venv/bin/python code/data/build_tdx_year_slice.py --input-path 'code/data/formal/tdx_daily_raw.csv' --output-path 'code/data/formal/master/tdx_${Year}_raw.csv' --year '$Year'"
if ($LASTEXITCODE -ne 0) {
    throw "WSL python command failed: build_tdx_year_slice.py"
}

& wsl bash -lc ".venv/bin/python code/data/build_tdx_full_master_base.py --input-path 'code/data/formal/master/tdx_${Year}_raw.csv' --output-path 'code/data/formal/master/tdx_full_master_base_${Year}.csv' --adjustflag-value '2'"
if ($LASTEXITCODE -ne 0) {
    throw "WSL python command failed: build_tdx_full_master_base.py"
}

Write-Host "[3/5] Re-fetching baostock supplement fields..." -ForegroundColor Yellow
& bash "code/data/run_baostock_master_fields_year.sh" $Year $MaxParallelMonths
if ($LASTEXITCODE -ne 0) {
    throw "bash command failed: run_baostock_master_fields_year.sh $Year $MaxParallelMonths"
}

Write-Host "[4/5] Rebuilding full master..." -ForegroundColor Yellow
& (Join-Path $projectRoot "code/data/build_full_master_for_existing_year.ps1") $Year
if ($LASTEXITCODE -ne 0) {
    throw "PowerShell command failed: build_full_master_for_existing_year.ps1 $Year"
}

Write-Host "[5/5] Running checks..." -ForegroundColor Yellow
python code/data/check_full_master_year.py --year $Year
if ($LASTEXITCODE -ne 0) {
    throw "Python command failed: check_full_master_year.py --year $Year"
}

python code/data/reconcile_full_master_year.py --year $Year
if ($LASTEXITCODE -ne 0) {
    throw "Python command failed: reconcile_full_master_year.py --year $Year"
}

Write-Host ""
Write-Host "Rebuild completed." -ForegroundColor Green
Write-Host "Generated files:"
Write-Host "  $yearCsv"
Write-Host "  $fullMaster"
Write-Host "  $checkJson"
Write-Host "  $reconcileLog"
