from typing import Dict, List

class PathManagement:
	def __init__(self, root : str):
		self.root = root
		
		self.root_client = root + '\\Client'
		self.root_client_dist = self.root_client + '\\dist'
		self.root_scratch = root + '\\.Scratch'
		self.root_deploy = root + '\\Deploy'
		self.root_deploy_static = self.root_deploy + '\\static'
		self.root_deploy_static_index = self.root_deploy_static + '\\index.html'
		self.root_deploy_config = self.root_deploy + '\\usm.ini'
		self.root_deploy_cert = self.root_deploy + '\\selfsigned.crt'
		self.root_deploy_key = self.root_deploy + '\\private.key'
		self.root_deploy_server = self.root_deploy + '\\UltimateSensorMonitor.exe'
		self.root_server = root + '\\Server'
		self.root_server_dist = self.root_server + '\\dist'

		self.path_defines : Dict[str, str] = {
			'root_client_dist': self.root_client_dist,
			'root_client': self.root_client,
			'root_scratch': self.root_scratch,
			'root_deploy_static_index': self.root_deploy_static_index,
			'root_deploy_static': self.root_deploy_static,
			'root_deploy_cert': self.root_deploy_cert,
			'root_deploy_key': self.root_deploy_key,
			'root_deploy_config': self.root_deploy_config,
			'root_deploy_server': self.root_deploy_server,
			'root_deploy': self.root_deploy,
			'root_server_dist': self.root_server_dist,
			'root_server': self.root_server
		}
	
	def GetPath(self, path_name : str):
		return self.path_defines[path_name]

	def SplitThenReplacePaths(self, command : str) -> List[str]:
		def replace_placeholder_paths(input : str) -> str:
			try:
				for placeholder_path, actual_path in self.path_defines.items():
					while placeholder_path in input:
						input = input.replace(placeholder_path, actual_path)
				return input
			except Exception as ex:
				print('An exception of type {0} occurred. Arguments:\n\t{1!r}'.format(type(ex).__name__, ex.args))
			return ''
		
		args = command.split()
		for index, data in enumerate(args):
			args[index] = replace_placeholder_paths(data)

		return args
	
	def GetPathStrings(self):
		path_strings =  \
			f'- `Running from:                        {self.root}`\n' + \
			f'- `Client source code directory:        {self.root_client}`\n' + \
			f'- `Server source code directory:        {self.root_server}`\n' + \
			f'- `Scratch/Temporary directory:         {self.root_scratch}`\n' + \
			f'- `Deploy directory (for the builds):   {self.root_deploy}`\n' + \
			f'- `Server executable:                   {self.root_deploy_server}`\n' + \
			f'- `Encryption Certificate:              {self.root_deploy_cert}`\n' + \
			f'- `Certificate Key:                     {self.root_deploy_key}`\n' + \
			f'- `Server executable config:            {self.root_deploy_config}`\n' + \
			f'- `Static directory for HTML:           {self.root_deploy_static}`\n' \
			f'- `Client HTML filename:                {self.root_deploy_static_index}`\n'
		  
		return path_strings
