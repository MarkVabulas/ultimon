
mkdir Deploy
mkdir Deploy\static

cd Client
call npm install
call npm run release
copy .\dist\index.html ..\Deploy\static

cd ..\Server
call python3 -m pip install -r requirements.txt
call python3 -m PyInstaller -y -F --clean UltimateSensorMonitor.py
copy .\dist\UltimateSensorMonitor.exe ..\Deploy

cd ..
