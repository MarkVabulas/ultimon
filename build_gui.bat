
cd Server
winget install -e --silent --id Python.Python.3.11 --scope user
call python3 -m pip install -r requirements.txt
call python3 -m PyInstaller -y -F --clean --noconsole --hidden-import wx --hidden-import wx._xml UltimateSensorMonitorGUI.py 
copy .\dist\UltimateSensorMonitorGUI.exe ..\
cd ..