from typing import Dict, List

class BaseSourceInterface:
	def source_once(self):
		pass

	def can_loop(self) -> bool:
		pass
	
	def get_values(self) -> Dict[str, Dict[str, str]]:
		pass

	def get_all_values(self) -> Dict[str, Dict[str, str]]:
		pass