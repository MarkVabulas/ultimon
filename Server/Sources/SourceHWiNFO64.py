import struct

import win32event
from multiprocessing import shared_memory
from typing import Dict, List
from Sources.BaseSourceInterface import BaseSourceInterface

from Sources.SourceHWiNFO64Types import *

class SharedMemoryMutex:
	def __init__(self, name):
		try:
		#	CloseHandle is automatically called for PyHANDLE
			self._sharedMutex = win32event.OpenMutex(win32event.SYNCHRONIZE, False, name)
		except:
			self._sharedMutex = None
	
	def __enter__(self):
		if self._sharedMutex is not None:
			dwWaitResult = win32event.WaitForSingleObject(self._sharedMutex, win32event.INFINITE)
			match dwWaitResult:
				case win32event.WAIT_OBJECT_0:
					return True
				case win32event.WAIT_ABANDONED:
					return False
			
	def __exit__(self, *args):
		if self._sharedMutex is not None:
			win32event.ReleaseMutex(self._sharedMutex)

class SourceHWiNFO64(BaseSourceInterface):
	def __init__(self):

		# Initialize our variables
		self._changedValues : Dict[str, Dict[str, str]] = {}
		self._keyValues : Dict[str, Dict[str, str]] = {}
		
		print(f"HWINFO_HEADER_MAGIC representation is {HWINFO_HEADER_MAGIC}.")
		print(f"Size of HWiNFOHeader representation is {HWiNFOHeaderFormatSize}.")
		print(f"Size of HWiNFOSensor representation is {HWiNFOSensorFormatSize}.")
		print(f"Size of HWiNFOEntry representation is {HWiNFOEntryFormatSize}.")

		self._sharedMutex = None
		self._sharedMemory = None
		
		try:
			self._sharedMutex = SharedMemoryMutex(SharedMemoryMutexPath)
			with self._sharedMutex:
				self._sharedMemory = shared_memory.SharedMemory(name=SharedMemoryPath, create=False)
		except:
			print('Double check these conditions are met: ')
			print('\t- HWiNFO64 is running in SharedMemory mode')
			print('\t- UltimateSensorMonitor is running as admin')
			print("Press any key to continue...")
			input()
			exit()


	def __del__(self):
		# DON'T FORGET TO CLEANUP the Shared Memory
		if self._sharedMemory is not None and self._sharedMemory:
			self._sharedMemory.close()
	
	def source_once(self):
		if self._sharedMemory is None or self._sharedMutex is None:
			return
		
		with self._sharedMutex:
			# Perform one iteration of the process, where we grab the data

			self._changedValues = {}
			
			if self._sharedMemory is not None:
				idx : int = 0
				sensors : List[HWiNFOSensor] = []
				entries : List[HWiNFOEntry] = []
				try:
					header = HWiNFOHeader(*struct.unpack(HWiNFOHeaderFormat, self._sharedMemory.buf[0:HWiNFOHeaderFormatSize]))
					idx += header.sensor_section_offset
					print(f'magic code={header.magic}, good value={HWINFO_HEADER_MAGIC}')
					print(f"Header: version={header.version}.{header.version2}")
					print(f"Header: last_update={header.last_update}")
					print(f"Header: sensor_section_offset={header.sensor_section_offset}")
					print(f"Header: sensor_element_size={header.sensor_element_size}")
					print(f"Header: sensor_element_count={header.sensor_element_count}")
					print(f"Header: entry_section_offset={header.entry_section_offset}")
					print(f"Header: entry_element_size={header.entry_element_size}")
					print(f"Header: entry_element_count={header.entry_element_count}")
					
					print(f"idx={idx}, expected={header.sensor_section_offset}")

					for i in range(header.sensor_element_count):
						sensor = HWiNFOSensor(*struct.unpack(HWiNFOSensorFormat, self._sharedMemory.buf[idx:idx+HWiNFOSensorFormatSize]))
					#	print(f"Sensor: {sensor.id} [{str(sensor.name_user)}], type= [{sensor.instance}]")
						sensors.append(sensor)
						idx += header.sensor_element_size
					
					print(f"idx={idx}, expected={header.sensor_section_offset + header.sensor_element_size*header.sensor_element_count} and {header.entry_section_offset}")

					for j in range(header.entry_element_count):
						entry = HWiNFOEntry(*struct.unpack(HWiNFOEntryFormat, self._sharedMemory.buf[idx:idx+HWiNFOEntryFormatSize]))
					#	print(f"Entry: {entry.id} [{str(entry.name_user)}], type= [{entry.type}]")
						entries.append(entry)
						idx += header.entry_element_size
						
					print(f"idx={idx}, expected={header.sensor_section_offset + header.sensor_element_size*header.sensor_element_count + header.entry_element_size*header.entry_element_count}")
					
					for entry in entries:
						if entry.sensor_index >= len(sensors):
							print('wtf')
						sensor = sensors[entry.sensor_index]
						self.handle_entry(sensor, entry)

				except Exception as e: 
					print(e.with_traceback)
		print('source_once finished')

	def handle_entry(self, sensor : HWiNFOSensor, entry : HWiNFOEntry):
	#	print(f"Hardware: {hardware.Identifier} [{hardware.Name}], type= [{hardware.HardwareType}]")
		values : Dict[str, str] = {} #[{v.Name, v.Value} for v in hardware.Properties]
		values['SensorID'] = str(sensor.id)
		values['SensorName'] = str(sensor.name_user.decode("utf-8")).replace('\x00', '')
		values['SensorNameOriginal'] = str(sensor.name_original.decode("windows-1252")).replace('\x00', '')
		values['ID'] = str(entry.id)
		values['Type'] = str(entry.type)
		values['Name'] = str(entry.name_user.decode("utf-8")).replace('\x00', '')
		values['NameOriginal'] = str(entry.name_original.decode("windows-1252")).replace('\x00', '')
		values['Unit'] = str(entry.unit.decode("windows-1252")).replace('\x00', '')
		values['Value'] = str(entry.value)

		if values['SensorName'] == values['SensorNameOriginal']:
			del values['SensorNameOriginal']
		if values['Name'] == values['NameOriginal']:
			del values['NameOriginal']
		self.handle_data(str(sensor.id) + str(values['ID']), values)
			
	def handle_data(self, id : str, data : Dict[str, str]):
		id = id.replace('/', '_').replace('\\', '_')

		# Ensure the data exists
		if id not in self._keyValues or (data is not None and self._keyValues[id] != data):
		#	if id in self._keyValues and self._keyValues[id] != data:
		#		print(f'{json.dumps(self._keyValues[id])} vs {json.dumps(data)}')

			self._keyValues[id] = data
			self._changedValues[id] = data
	
	def can_loop(self):
		return self._sharedMemory is not None

	def get_values(self) -> Dict[str, Dict[str, str]]:
		# Let the caller get the info from us
		return self._changedValues

	def get_all_values(self) -> Dict[str, Dict[str, str]]:
		# Let the caller get the info from us
		return self._keyValues
