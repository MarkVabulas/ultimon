import subprocess
import re
import wx

from typing import List
from GUI.Markdown import Markdown

class TerminalPanel(Markdown):
	def __init__(self, parent):
		Markdown.__init__(self, parent)
		
		global log_writer
		log_writer = self.log_writer_thunk

		global clear_log_writer
		clear_log_writer = self.log_writer_thunk

	def PerformUpdate(self, message):
		length = len(self.rtc.GetValue())
		self.rtc.SetInsertionPoint(length)

		ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
		message = ansi_escape.sub('', message)

		self.AddContent(message + '\n')
		self.rtc.ShowPosition(self.rtc.GetLastPosition())
	
	def log_writer_thunk(self, message):
		wx.CallAfter(self.PerformUpdate, message)
			
	def clear_log_writer_thunk(self):
		wx.CallAfter(self.rtc.Clear)
	

class TerminalMessageSender:
	def __init__(self):
		self._target : TerminalPanel | None = None
	
	def SetTarget(self, target):
		self._target = target

	def WriteToTerminal(self, message):
		print(message)
		if self._target is not None:
			wx.CallAfter(self._target.PerformUpdate, message)
			
	def ClearTerminal(self):
		if self._target is not None:
			wx.CallAfter(self._target.rtc.Clear)
		
	def RunThis(self, args : List[str], cwd : str, shell=True, id : int | None = None) -> subprocess.Popen[str] | None:
		
		process = None

		try:
			full_args = str(' '.join(args))
			self.WriteToTerminal(f"### > __{full_args}__")

			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

			process = subprocess.Popen(args=args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=shell, cwd=cwd, text=True, startupinfo=startupinfo, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
		except Exception as ex:
			self.WriteToTerminal('An exception of type {0} occurred. Arguments:\n\t{1!r}'.format(type(ex).__name__, ex.args))
		return process
	
	def FollowProcess(self, process : subprocess.Popen[str]) -> None:
		try:
			if process.stdout is not None:
				while True:
					try:
						line = process.stdout.readline()
						if not line:
							break
						self.WriteToTerminal('\t\t' + line)
					except StopIteration:
						break
		except Exception as ex:
			self.WriteToTerminal('An exception of type {0} occurred. Arguments:\n\t{1!r}'.format(type(ex).__name__, ex.args))
