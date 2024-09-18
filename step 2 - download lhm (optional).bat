
mkdir Deploy

mkdir Scratch

cd Scratch
curl -L -J --output LibreHardwareMonitor.zip https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/download/v0.9.3/LibreHardwareMonitor-net472.zip
powershell Expand-Archive -Force LibreHardwareMonitor.zip .
copy LibreHardwareMonitorLib.dll ..\Deploy\
copy LibreHardwareMonitorLib.xml ..\Deploy\
copy HidSharp.dll ..\Deploy\

cd .. 
