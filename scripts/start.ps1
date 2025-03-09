$mariadb = Start-Process -NoNewWindow -PassThru -WorkingDirectory mariadb mariadb\bin\mysqld.exe --console
Start-Process -Wait -NoNewWindow -WorkingDirectory artemis python\python.exe index.py

Stop-Process $mariadb.Id

Write-Output .
Write-Output "ARTEMiS has stopped."
