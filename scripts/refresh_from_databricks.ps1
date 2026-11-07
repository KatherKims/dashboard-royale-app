param(
    [string]$Profile = 'dashboard-royale',
    [string]$Notebook = '/Users/katherine.t.kim@tamu.edu/01_data_checks',
    [string]$Volume = 'dbfs:/Volumes/workspace/default/dashboard_royale_source/app_exports',
    [string]$Cli = 'databricks'
)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path $PSScriptRoot -Parent
function Invoke-Dbx {
    param([string[]]$Arguments)
    & $Cli @Arguments
    if ($LASTEXITCODE -ne 0) { throw 'Databricks export failed. Check the CLI path and OAuth login.' }
}
New-Item -ItemType Directory -Force -Path (Join-Path $projectPath 'data'),(Join-Path $projectPath 'notebooks') | Out-Null
foreach ($name in @('analysis_results.json','machine_daily.parquet','machines.parquet','property_daily.parquet','guest_groups.parquet','scenario_net.npz')) {
    Invoke-Dbx -Arguments @('fs','cp',"$Volume/$name",(Join-Path $projectPath "data/$name"),'--overwrite','--profile',$Profile)
}
Invoke-Dbx -Arguments @('workspace','export',$Notebook,'--format','JUPYTER','--file',(Join-Path $projectPath 'notebooks/01_data_checks.ipynb'),'--profile',$Profile)
Invoke-Dbx -Arguments @('workspace','export',$Notebook,'--format','SOURCE','--file',(Join-Path $projectPath 'notebooks/01_data_checks.py'),'--profile',$Profile)
Write-Host 'Refreshed data and notebook snapshots. Review the changes in GitHub Desktop before committing.'
