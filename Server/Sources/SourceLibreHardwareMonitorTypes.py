from typing import Dict

	# Hardware.IHardware @ https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/blob/master/LibreHardwareMonitorLib/Hardware/IHardware.cs
	# Hardware.ISensor @ https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/blob/master/LibreHardwareMonitorLib/Hardware/ISensor.cs

HardwareType : Dict[int, str] = {
	0: 'Motherboard',
	1: 'SuperIO',
	2: 'Cpu',
	3: 'Memory',
	4: 'GpuNvidia',
	5: 'GpuAmd',
	6: 'GpuIntel',
	7: 'Storage',
	8: 'Network',
	9: 'Cooler',
	10: 'EmbeddedController',
	11: 'Psu',
	12: 'Battery'
}

SensorType : Dict[int, str] = {
	0: 'Voltage', # V
	1: 'Current', # A
	2: 'Power', # W
	3: 'Clock', # MHz
	4: 'Temperature', # °C
	5: 'Load', # %
	6: 'Frequency', # Hz
	7: 'Fan', # RPM
	8: 'Flow', # L/h
	9: 'Control', # %
	10: 'Level', # %
	11: 'Factor', # 1
	12: 'Data', # GB = 2^30 Bytes
	13: 'SmallData', # MB = 2^20 Bytes
	14: 'Throughput', # B/s
	15: 'TimeSpan', # Seconds 
	16: 'Energy', # milliwatt-hour (mWh)
	17: 'Noise', # dBA
	18: 'Conductivity', # µS/cm
	19: 'Humidity' # %
}

SensorTypeUnits : Dict[int, str] = {
	0: 'V',
	1: 'A',
	2: 'W',
	3: 'MHz',
	4: '°C',
	5: '%',
	6: 'Hz',
	7: 'RPM',
	8: 'L/h',
	9: '%',
	10: '%',
	11: 'x',
	12: 'GB = 2^30 Bytes',
	13: 'MB = 2^20 Bytes',
	14: 'B/s',
	15: 's',
	16: 'mWh',
	17: 'dBA',
	18: 'µS/cm',
	19: '%'
}