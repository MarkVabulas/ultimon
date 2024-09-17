#! /usr/bin/env python3

import os, signal, sys, time
os.add_dll_directory(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import json, argparse
import threading, asyncio

from pathlib import Path
from typing import Union

from elevate import elevate
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler 

from Sources.BaseSourceInterface import BaseSourceInterface
from Sources.SourceAida64 import SourceAida64
from Sources.SourceHWiNFO64 import SourceHWiNFO64

from Server.ServerSettings import ServerSettings
from Server.ServerModule import ServerModule

from ServerLogger import logger, logging

class ExpandUserPath:
	def __new__(cls, path: Union[str, Path]) -> Path:
		return Path(path).expanduser().resolve()
		
def webserver_main(server : ServerModule):
	server.run_webserver()

def bool_arg_helper(v):
	if isinstance(v, bool):
		return v
	if v.lower() in ('yes', 'true', 't', 'y', '1'):
		return True
	elif v.lower() in ('no', 'false', 'f', 'n', '0'):
		return False
	else:
		raise argparse.ArgumentTypeError('Boolean value expected.')
	
class StaticIndexWatchdog(FileSystemEventHandler):
	def __init__(self):
		self.need_suggest_refresh = False
	
	def on_any_event(self, event):
		self.need_suggest_refresh = True

async def main():
	# Setup our arguments for the command line
	arg_parser = argparse.ArgumentParser(description='Ultimate Sensor Monitor')
	arg_parser.add_argument('--refresh_time', type=int, help='Time in Milliseconds between data refreshes', default=500)
	arg_parser.add_argument('--incremental', type=bool_arg_helper, nargs='?', help='Send incremental or complete updates', const=True, default=True)
	arg_parser.add_argument('--full_update_iterations', type=int, help='How many updates between full data, if incremental is enabled', default=10)
	arg_parser.add_argument('--source', type=str, help='Selects the source to use for the data (options: aida64, lhm, hwinfo64, none)', default='lhm')
	arg_parser.add_argument('--can_elevate', type=bool_arg_helper, nargs='?', help='Allows the application to ask to restart in order to have higher level permissions', const=True, default=True)
	arg_parser.add_argument('--with_server', type=bool_arg_helper, nargs='?', help='Enables running the Souces without creating a server', const=True, default=True)
	arg_parser.add_argument('--port', type=int, help='Choose the server port', default=5779)
	arg_parser.add_argument('--password', type=str, help='Choose the password', default='UltimateSensorMonitor')
	arg_parser.add_argument('--static_folder', type=ExpandUserPath, help='Choose the static folder', default=None)
	arg_parser.add_argument('--certificate', type=ExpandUserPath, help='TLS certificate path', default=None)
	arg_parser.add_argument('--key', type=ExpandUserPath, help='TLS private key path', default=None)
	arg_parser.add_argument('--log_level', type=int, choices=[logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG], help='Log level value', default=logging.DEBUG)

	# Parse arguments
	server_settings = arg_parser.parse_args(namespace=ServerSettings())
	print(sys.argv[1:])

	if (server_settings.source == 'lhm' or server_settings.source == 'hwinfo64') and server_settings.can_elevate == True:
		elevate()

	# Set logging level
	logger.setLevel(server_settings.log_level)

	# Default = not using TLS
	server_settings.using_tls = False
	# Test for certificates / key pair
	if server_settings.certificate and server_settings.key:
		server_settings.using_tls = True
		logger.info('Using certificate: %s', server_settings.certificate)
		logger.info('Using private key: %s', server_settings.key)
	elif server_settings.certificate or server_settings.key:
		sys.exit('You must specify both certificate and key.')
	else:
		server_settings.using_tls = False

	server = None
	observer = None
	if (server_settings.with_server):
		server = ServerModule(server_settings)
		threading.Thread(target=webserver_main, args=[server]).start()

	refresh_time = float(server_settings.refresh_time)/1000.0

	data_source = None
	match server_settings.source:
		case 'aida64':
			data_source = SourceAida64()
		case 'lhm':
			from Sources.SourceLibreHardwareMonitor import SourceLibreHardwareMonitor
			data_source = SourceLibreHardwareMonitor()
		case 'hwinfo64':
			data_source = SourceHWiNFO64()

	just_incremented : bool = False
	full_update : int = 0

	watchdog : StaticIndexWatchdog  = StaticIndexWatchdog()

	if server is not None:
		if server_settings.static_folder is not None and server_settings.static_folder != '':
			logger.info(f'Watching file for changes: {str(server_settings.static_folder)}/index.html')
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
	# We need to keep the SIGINT->SIGTERM signal so that the webserver will stop on Ctrl-C, as well
	signal.signal(signal.SIGINT, lambda _1, _2: signal.raise_signal(signal.SIGTERM))
	try:
		loop = asyncio.get_event_loop()
		loop.run_until_complete(main())
	except KeyboardInterrupt:
		try:
			signal.raise_signal(signal.SIGTERM)
			sys.exit(130)
		except SystemExit:
			os._exit(130)
