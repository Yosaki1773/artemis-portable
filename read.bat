@echo off
start "artemis-mariadb" /MIN /D mariadb bin\mysqld.exe --console
start /B /WAIT /D artemis ..\python\python.exe read.py %*

taskkill /f /fi "WindowTitle eq artemis-mariadb" /t
