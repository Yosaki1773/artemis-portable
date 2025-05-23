$artemis_repo = "Hay1tsme/artemis"
$artemis_branch = "develop"

$artemis_location = Join-Path $(Get-Location) "artemis"

python/python.exe scripts/update-artemis.py "$artemis_repo" "$artemis_branch"

Set-Location "$artemis_location"
Write-Output "[INFO] Updating dependencies..."
../python/python.exe -m pip install --no-warn-script-location -r requirements.txt

Write-Output "[INFO] Migrating databases..."
$mariadb = Start-Process -NoNewWindow -PassThru -WorkingDirectory ..\mariadb ..\mariadb\bin\mysqld.exe --console
../python/python.exe dbutils.py upgrade
Stop-Process $mariadb.Id

Write-Output "ARTEMiS update finished."
