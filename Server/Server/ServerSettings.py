import os
import configparser, argparse

from pathlib import Path
from typing import Union

from Server.ServerLogger import logger, logging

def bool_arg_helper(v):
	if isinstance(v, bool):
		return v
	if v.lower() in ('yes', 'true', 't', 'y', '1'):
		return True
	elif v.lower() in ('no', 'false', 'f', 'n', '0'):
		return False
	else:
		raise argparse.ArgumentTypeError('Boolean value expected.')

class ExpandUserPath:
	def __new__(cls, path: Union[str, Path]) -> Path:
		if path is not None:
			return Path(path).expanduser().resolve()
		else:
			return Path('')

class ServerSettings:
	def __init__(self):
		self.refresh_time : int
		self.incremental : bool
		self.full_update_iterations : int
		self.source : str
		self.can_elevate : bool
		self.with_server : bool
		self.port : int
		self.password : str
		self.static_folder : Path | None
		self.certificate : Path | None
		self.key : Path | None
		self.log_level: int
		self.using_tls : bool

def get_default_settings() -> ServerSettings:
	server_settings = ServerSettings()
	server_settings.refresh_time = 500
	server_settings.incremental = True
	server_settings.full_update_iterations = 10
	server_settings.source = 'aida64'
	server_settings.can_elevate = True
	server_settings.with_server = True
	server_settings.port = 5779
	server_settings.password = 'UltimateSensorMonitor'
	server_settings.static_folder = ExpandUserPath('static')
	server_settings.certificate = None
	server_settings.key = None
	return server_settings

def save_config(settings : ServerSettings, filename : str):
	config = configparser.ConfigParser()
	config['default'] = \
	{
		'refresh_time': str(settings.refresh_time),
		'incremental': str(settings.incremental),
		'full_update_iterations': str(settings.full_update_iterations),
		'source': str(settings.source),
		'can_elevate': str(settings.can_elevate),
		'with_server': str(settings.with_server),
		'port': str(settings.port),
		'password': str(settings.password),
		'static_folder': str(settings.static_folder),
		'certificate': str(settings.certificate),
		'key': str(settings.key)
	}
	with open(filename, 'w') as configfile:
		config.write(configfile)

def load_config(filename : str) -> ServerSettings:
	if not Path(filename).is_file():
		return get_default_settings()
	
	result = ServerSettings()
	if result is None:
		return get_default_settings()

	config = configparser.ConfigParser()
	config.read(filename)
	section = config['default']
	if 'refresh_time' in section:				result.refresh_time = int(section['refresh_time'])
	if 'incremental' in section:				result.incremental = bool_arg_helper(section['incremental'])
	if 'full_update_iterations' in section:		result.full_update_iterations = int(section['full_update_iterations'])
	if 'source' in section:						result.source = section['source']
	if 'can_elevate' in section:				result.can_elevate = bool_arg_helper(section['can_elevate'])
	if 'with_server' in section:				result.with_server = bool_arg_helper(section['with_server'])
	if 'port' in section:						result.port = int(section['port'])
	if 'password' in section:					result.password = section['password']
	if 'static_folder' in section:				result.static_folder = ExpandUserPath(section['static_folder']) if 'static_folder' in section else None
	if 'certificate' in section:				result.certificate = ExpandUserPath(section['certificate']) if 'certificate' in section else None
	if 'key' in section:						result.key = ExpandUserPath(section['key']) if 'key' in section else None

	if not hasattr(result, 'certificate') or result.static_folder is None or result.static_folder == '' or not result.static_folder.is_dir():
		result.static_folder = None
	if not hasattr(result, 'certificate') or result.certificate is None or result.certificate == '' or not result.certificate.is_file():
		result.certificate = None
	if not hasattr(result, 'key') or result.key is None or result.key == '' or not result.key.is_file():
		result.key = None

	return result

def dump_values(self, writer):
	for k, v in vars(self).items():
		writer(f'\t\t{k} = {v}')

	
def get_settings_at_startup(filename : str):
	# Setup our arguments for the command line
	arg_parser = argparse.ArgumentParser(description='Ultimate Sensor Monitor')
	arg_parser.add_argument('--refresh_time', type=int, help='Time in Milliseconds between data refreshes', default=500)
	arg_parser.add_argument('--incremental', type=bool_arg_helper, nargs='?', help='Send incremental or complete updates', const=True, default=True)
	arg_parser.add_argument('--full_update_iterations', type=int, help='How many updates between full data, if incremental is enabled', default=10)
	arg_parser.add_argument('--source', type=str, help='Selects the source to use for the data (options: aida64, lhm, hwinfo64, none)', default='aida64')
	arg_parser.add_argument('--can_elevate', type=bool_arg_helper, nargs='?', help='Allows the application to ask to restart in order to have higher level permissions', const=True, default=True)
	arg_parser.add_argument('--with_server', type=bool_arg_helper, nargs='?', help='Enables running the Souces without creating a server', const=True, default=True)
	arg_parser.add_argument('--port', type=int, help='Choose the server port', default=5779)
	arg_parser.add_argument('--password', type=str, help='Choose the password', default='UltimateSensorMonitor')
	arg_parser.add_argument('--static_folder', type=ExpandUserPath, help='Choose the static folder', default=None)
	arg_parser.add_argument('--certificate', type=ExpandUserPath, help='TLS certificate path', default=None)
	arg_parser.add_argument('--key', type=ExpandUserPath, help='TLS private key path', default=None)
	arg_parser.add_argument('--log_level', type=int, choices=[logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG], help='Log level value', default=logging.DEBUG)

	config = configparser.ConfigParser()
	if os.path.isfile(filename):
		try: 
			config.read(filename)
			arg_parser.set_defaults(**config['default'])
		except Exception as ex:
			logger.info('An exception of type {0} occurred. Arguments:\n{1!r}'.format(type(ex).__name__, ex.args))

	# Parse arguments
	return arg_parser.parse_args(namespace=ServerSettings())
