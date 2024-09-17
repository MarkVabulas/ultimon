# this lets us load other dependent dll's in the same folder
import os, sys

# open up LibreHardwareMonitorLib
import clr
clr.AddReference('LibreHardwareMonitorLib')
from LibreHardwareMonitor import Hardware

import json
from typing import Dict, List
from collections import namedtuple

from Sources.BaseSourceInterface import BaseSourceInterface

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

class SourceLibreHardwareMonitor(BaseSourceInterface):
	__namespace__ = "SourceLibreHardwareMonitor"

	def __init__(self):

		# Initialize our variables
		self._changedValues : Dict[str, Dict[str, str]] = {}
		self._keyValues : Dict[str, Dict[str, str]] = {}

		# init LibreHardwareMonitor
		self._computer = Hardware.Computer()
		self._computer.IsCpuEnabled = True
		self._computer.IsGpuEnabled = True
		self._computer.IsMemoryEnabled = True
		self._computer.IsMotherboardEnabled = True
		self._computer.IsControllerEnabled = True
		self._computer.IsNetworkEnabled = True
		self._computer.IsStorageEnabled = True
		self._computer.Open()

		self.iterate(False)

	def __del__(self):
		self._computer.Close()
	
	def source_once(self):
		self._changedValues = {}

		self.iterate(True)

	#	print(json.dumps(self.get_values()))
	#	print(json.dumps(self.get_all_values()))
			
	def handle_data(self, id : str, data : Dict[str, str]):
		value_key : str = 'Value'
		id = id.replace('/', '_').replace('\\', '_')

		# Ensure the data exists
		if id not in self._keyValues:
			self._keyValues[id] = data
			self._changedValues[id] = data
		elif data is not None:
			# Since the tag isn't an ID, we should store the tag+data into our key/value pairs for lookup later
			if value_key in data:
				if value_key not in self._keyValues[id]:
					self._keyValues[id] = data
					self._changedValues[id] = data
				else:
					if self._keyValues[id] != data:
						self._keyValues[id] = data
						self._changedValues[id] = data
			else:
				if self._keyValues[id] != data:
					self._keyValues[id] = data
					self._changedValues[id] = data

	def handle_hardware(self, hardware : Hardware.IHardware):
	#	print(F"Hardware: {hardware.Identifier} [{hardware.Name}], type= [{hardware.HardwareType}]")
		values : Dict[str, str] = {} #[{v.Name, v.Value} for v in hardware.Properties]
		values['ID'] = str(hardware.Identifier)
		values['Name'] = str(hardware.Name)
		values['Type'] = str(hardware.HardwareType)
		self.handle_data(str(hardware.Identifier), values)

	def handle_sensor(self, sensor):
	#	print(f"\tSensor: {sensor.Identifier} [{sensor.Name}], value: {sensor.Value}")
		values : Dict[str, str] = {}
	#	values['ID'] = str(sensor.Identifier)
		values['Name'] = str(sensor.Name)
		values['Type'] = str(sensor.SensorType)
		values['Value'] = str(sensor.Value) if sensor.Value is not None else json.dumps([str(v.Value) for v in sensor.Values])
		if sensor.Value is None:
			values['TimeSpan'] = str(sensor.ValuesTimeWindow)
		self.handle_data(str(sensor.Identifier), values)

	# Hardware.IHardware @ https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/blob/master/LibreHardwareMonitorLib/Hardware/IHardware.cs
	# Hardware.ISensor @ https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/blob/master/LibreHardwareMonitorLib/Hardware/ISensor.cs
	def iterate(self, update : bool):
		if (update):
			self.update()

		# Perform one iteration of the process, where we grab the data
		for hardware in self._computer.Hardware:
			self.handle_hardware(hardware)
			for subhardware in hardware.SubHardware:
				self.handle_hardware(subhardware)
				for sensor in subhardware.Sensors:
					self.handle_sensor(sensor)
			for sensor in hardware.Sensors:
				self.handle_sensor(sensor)

	def update(self):
		for hardware in self._computer.Hardware:
			hardware.Update()
			for subhardware in hardware.SubHardware:
				subhardware.Update()
	
	def can_loop(self):
		return True

	def get_values(self) -> Dict[str, Dict[str, str]]:
		# Let the caller get the updated info from us
		return self._changedValues

	def get_all_values(self) -> Dict[str, Dict[str, str]]:
		# Let the caller get the complete info from us
		return self._keyValues
