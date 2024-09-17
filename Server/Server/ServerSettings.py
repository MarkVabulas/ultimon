from pathlib import Path

class ServerSettings:
	refresh_time : int
	incremental : bool
	full_update_iterations : int
	source : str
	can_elevate : bool
	with_server : bool
	port : int
	password : str
	static_folder : Path
	log_level: int
	certificate : Path
	key : Path
	using_tls : bool
