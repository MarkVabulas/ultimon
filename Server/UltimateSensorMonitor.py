#! /usr/bin/env python3

import os, signal, sys, time
my_path = os.path.dirname(os.path.realpath(__file__))
os.add_dll_directory(my_path)
sys.path.append(my_path)

cwd = os.getcwd()
os.add_dll_directory(cwd)
sys.path.append(cwd)

config_file = 'usm.ini'

import json
import threading, asyncio

from typing import Dict
from pathlib import Path

from elevate import elevate
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler 

from Sources.BaseSourceInterface import BaseSourceInterface
from Sources.SourceAida64 import SourceAida64
from Sources.SourceHWiNFO64 import SourceHWiNFO64

from Server.ServerSettings import ServerSettings, get_settings_at_startup, dump_values
from Server.ServerModule import ServerModule
from Server.ServerLogger import logger, logging
		
def webserver_main(server : ServerModule):
	try:
		server.run_webserver()
	except:
		os._exit(0)
	
class StaticIndexWatchdog(FileSystemEventHandler):
	def __init__(self):
		self.need_suggest_refresh = False
	
	def on_any_event(self, event):
		self.need_suggest_refresh = True

async def main():
	server_settings : ServerSettings
	
	try:
		server_settings = get_settings_at_startup(config_file)

		if not server_settings.static_folder or not server_settings.static_folder.is_dir():
			server_settings.static_folder = Path(cwd + '\\static')

		dump_values(server_settings, logger.info)
	except Exception as ex:
		print('An exception of type {0} occurred. Arguments:\n\t{1!r}'.format(type(ex).__name__, ex.args))
		return

	if (server_settings.source == 'lhm' or server_settings.source == 'hwinfo64') and server_settings.can_elevate == True:
		elevate()

	# Set logging level
	logger.setLevel(server_settings.log_level)

	# Default = not using TLS
	server_settings.using_tls = False
	# Test for certificates / key pair
	if server_settings.certificate is not None and server_settings.certificate.is_file() and server_settings.key is not None and server_settings.key.is_file():
		server_settings.using_tls = True
		logger.info('Using certificate: %s', server_settings.certificate)
		logger.info('Using private key: %s', server_settings.key)
	elif (server_settings.certificate is not None and server_settings.certificate.is_file()) or (server_settings.key is not None and server_settings.key.is_file()):
		sys.exit('You must specify both certificate and key.')
	else:
		server_settings.using_tls = False

	server = None
	observer = None
	if server_settings.with_server:
		server = ServerModule(server_settings)
		threading.Thread(target=webserver_main, args=[server]).start()
	
	refresh_time = float(server_settings.refresh_time)/1000.0
	
	data_source = None
	try:
		match server_settings.source:
			case 'aida64':
				data_source = SourceAida64()
			case 'lhm':
				from Sources.SourceLibreHardwareMonitor import SourceLibreHardwareMonitor
				data_source = SourceLibreHardwareMonitor()
			case 'hwinfo64':
				data_source = SourceHWiNFO64()
	except Exception as ex:
		print('An exception of type {0} occurred. Arguments:\n\t{1!r}'.format(type(ex).__name__, ex.args))
	
	just_incremented : bool = False
	full_update : int = 0

	watchdog : StaticIndexWatchdog  = StaticIndexWatchdog()
	
	if server is not None:
		if server_settings.static_folder is not None and server_settings.static_folder != '':
			logger.info(f'Watching file for changes: {str(server_settings.static_folder)}\\index.html')
			observer = PollingObserver()
			observer.schedule(watchdog, str(server_settings.static_folder)+'\\index.html', recursive=False)
			observer.start()
			logger.info(f'observing: {str(observer.is_alive())}')

	try:
		while data_source is None or data_source.can_loop():
			if data_source is not None:
				data_source.source_once()
				values = data_source.get_values() if (server_settings.incremental and full_update > 0) else data_source.get_all_values()
			else:
				values = {}
			values_length = len(values)

		#	os.system('cls')
		#	logger.info(f'values: {values_length}')

			if server_settings.incremental:
				if not just_incremented:
					if values_length == 0:
						refresh_time += 0.01
						just_incremented = True
					else:
						refresh_time -= 0.001
						if refresh_time < 0.05:
							refresh_time = 0.05
				else:
					just_incremented = False
			full_update = server_settings.full_update_iterations if full_update <= 0 else full_update-1

		#	logger.info(json.dumps(values))
			
			if server is not None:
				if values_length > 0:
					await server.send_sensor_update(json.dumps(values))
				elif data_source is not None:
					await server.send_sensor_update(json.dumps(data_source.get_all_values()))
				else:
					await server.send_sensor_update('{}')
				
				if watchdog.need_suggest_refresh:
					await server.send_suggest_refresh()
					watchdog.need_suggest_refresh = False

		#	logger.info(f'Refresh Time: {refresh_time}s, iterations until full update: {full_update}')
			time.sleep(refresh_time)
	except KeyboardInterrupt:
		pass
	
	if observer is not None:
		observer.stop()
		observer.join()

	# We can't read from the shared memory, so panic and get out of here!
	print('Please run your sensor source and restart the server')
	signal.raise_signal(signal.SIGTERM)

if __name__ == '__main__':
	# Set logging level
	logger.setLevel(10)

	# We need to keep the SIGINT->SIGTERM signal so that the webserver will stop on Ctrl-C, as well
	signal.signal(signal.SIGINT, lambda _1, _2: signal.raise_signal(signal.SIGTERM))
	signal.signal(signal.SIGTERM, lambda _1, _2: os._exit(0))
	try:
		loop = asyncio.get_event_loop()
		loop.run_until_complete(main())
	except KeyboardInterrupt:
		try:
			signal.raise_signal(signal.SIGTERM)
			sys.exit(0)
		except SystemExit:
			os._exit(0)
	except:
		os._exit(0)

