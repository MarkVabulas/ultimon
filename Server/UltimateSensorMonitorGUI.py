#!/usr/bin/env python
 
import os, signal, subprocess, threading, psutil
import wx.lib, wx.lib.intctrl, wx.lib.scrolledpanel
import wx, wx.adv

from pathlib import Path
from typing import List

from GUI.Markdown import Markdown
from GUI.ResizableStaticText import ResizableStaticText
from GUI.TerminalPanel import TerminalPanel, TerminalMessageSender
from GUI.PathManagement import PathManagement
from GUI.SelfSign import cert_gen

from Server.ServerSettings import ServerSettings, load_config, save_config, dump_values

import GUI.Blurbs

#root = os.path.dirname(os.path.realpath(__file__))
root = os.getcwd()

terminal : TerminalMessageSender = TerminalMessageSender()
paths : PathManagement = PathManagement(root)

system_font : wx.Font | None = None

def add_row(parent : wx.BoxSizer, option, text) -> None: 
	sizer = wx.BoxSizer(orient=wx.HORIZONTAL)
	sizer.Add(option, proportion=2, border=5)
	sizer.AddSpacer(15)
	sizer.Add(text, proportion=3, border=5)

	parent.Add(sizer)
	parent.AddSpacer(5)

class DefaultPanel(wx.lib.scrolledpanel.ScrolledPanel):
	def __init__(self, parent, title):
		wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)
		self.SetupScrolling()

		self.SetThemeEnabled(True)
		self.title = title
		self.parent = parent

		# Finally, put the layout in a sizer for the panel to manage the layout.
		self.sizer = wx.BoxSizer(orient=wx.VERTICAL)
		self.SetSizer(self.sizer)

	def is_complete(self) -> bool:
		return False

	def print_status(self):
		pass

class Intro(DefaultPanel):
	def __init__(self, parent, title):
		DefaultPanel.__init__(self, parent, title)

		self.txt = Markdown(self, allow_download_images=True)
		self.txt.rtc.SetFontScale(1.5)
		self.txt.AddContent(GUI.Blurbs.WelcomeText)

		self.txt.AddContent(paths.GetPathStrings())

		self.sizer.Add(self.txt, 1, wx.EXPAND)

	#	self.Layout()

	def is_complete(self) -> bool:
		return True

class InstallTools(DefaultPanel):
	def __init__(self, parent, title):
		DefaultPanel.__init__(self, parent, title)

		self.python_text = ResizableStaticText(self, self.parent, GUI.Blurbs.InstallPython)
		self.python_text.SetFont(system_font)

		self.install_python_button = wx.adv.CommandLinkButton(self, wx.ID_ANY, mainLabel='Install Python', size=wx.Size(320, 50))
		self.install_python_button.Bind(wx.EVT_BUTTON, self.install_python, id=wx.ID_ANY)
		self.install_python_button.ToolTip = GUI.Blurbs.InstallPython

		self.npm_text = ResizableStaticText(self, self.parent, GUI.Blurbs.InstallNPM)
		self.npm_text.SetFont(system_font)

		self.install_nodejs_button = wx.adv.CommandLinkButton(self, wx.ID_ANY, mainLabel='Install Node.js', size=wx.Size(320, 50))
		self.install_nodejs_button.Bind(wx.EVT_BUTTON, self.install_npm, id=wx.ID_ANY)

		self.lhm_text = ResizableStaticText(self, self.parent, GUI.Blurbs.InstallLHM)
		self.lhm_text.SetFont(system_font)

		self.install_lhm_button = wx.adv.CommandLinkButton(self, wx.ID_ANY, mainLabel='Install LibreHardwareMonitor (optional)', size=wx.Size(320, 50))
		self.install_lhm_button.Bind(wx.EVT_BUTTON, self.install_lhm, id=wx.ID_ANY)

		self.sizer.Add(self.python_text)
		self.sizer.AddSpacer(50)
		self.sizer.Add(self.install_python_button)

		self.sizer.AddSpacer(25)
		self.sizer.Add(wx.StaticLine(self, size=(320,1)))
		self.sizer.AddSpacer(25)

		self.sizer.Add(self.npm_text)
		self.sizer.AddSpacer(50)
		self.sizer.Add(self.install_nodejs_button)

		self.sizer.AddSpacer(25)
		self.sizer.Add(wx.StaticLine(self, size=(320,1)))
		self.sizer.AddSpacer(25)

		self.sizer.Add(self.lhm_text)
		self.sizer.AddSpacer(50)
		self.sizer.Add(self.install_lhm_button)

		self.print_status()

	def is_complete(self) -> bool:
		python_check = self.has_python()
		self.install_python_button.Enabled = not python_check

		npm_check = self.has_npm()
		self.install_nodejs_button.Enabled = not npm_check
		
		lhm_check = self.has_lhm()
		self.install_lhm_button.Enabled = not lhm_check
		
		return python_check and npm_check and lhm_check

	def print_status(self):
		terminal.WriteToTerminal(f'## Python is installed: ***{self.has_python()}***')
		terminal.WriteToTerminal(f'## Node.JS is installed: ***{self.has_npm()}***')
		terminal.WriteToTerminal(f'## Has LibreHardwareMonitor downloaded: ***{self.has_lhm()}***')
	
	def has_python(self) -> bool:
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		
		command = 'python3 --version'
		result = subprocess.run(command.split(), shell=True, capture_output=True, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
		return result != None and result.returncode == 0
	
	def install_python(self, event):
		def run_thread():
			command = 'winget install -e --silent --id Python.Python.3.11 --scope user'
			args = paths.SplitThenReplacePaths(command)
			process = terminal.RunThis(args, root)
			if process is not None:
				terminal.FollowProcess(process)
			self.print_status()
			
		t = threading.Thread(target=run_thread)
		t.start()
	
	def has_npm(self) -> bool:
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

		command = 'npm --version'
		result = subprocess.run(command.split(), shell=True, capture_output=True, startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
		return result != None and result.returncode == 0
		
	def install_npm(self, event):
		def run_thread():
			command = 'winget install -e --silent --id OpenJS.NodeJS --scope user'
			args = paths.SplitThenReplacePaths(command)
			process = terminal.RunThis(args, root)
			if process is not None:
				terminal.FollowProcess(process)
			self.print_status()
			
		t = threading.Thread(target=run_thread)
		t.start()
	
	def has_lhm(self):
		return \
			os.path.isfile(f'{paths.GetPath("root_scratch")}\\LibreHardwareMonitorLib.dll') and \
			os.path.isfile(f'{paths.GetPath("root_scratch")}\\HidSharp.dll')

	def install_lhm(self, event):
		def run_thread():
			commands = [
				f'mkdir root_deploy',
				f'mkdir root_scratch',
				f'curl -L -J --output root_scratch\\LibreHardwareMonitor.zip https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/download/v0.9.3/LibreHardwareMonitor-net472.zip',
				f'powershell Expand-Archive -Force -LiteralPath root_scratch\\LibreHardwareMonitor.zip -DestinationPath root_scratch',
				f'copy root_scratch\\LibreHardwareMonitorLib.dll root_deploy',
				f'copy root_scratch\\LibreHardwareMonitorLib.xml root_deploy',
				f'copy root_scratch\\HidSharp.dll root_deploy',
			]

			for index, command in enumerate(commands):
				args = paths.SplitThenReplacePaths(command)
				process = terminal.RunThis(args, root, id=index)
				if process is not None:
					terminal.FollowProcess(process)

			self.print_status()

		t = threading.Thread(target=run_thread)
		t.start()

class BuildSoftware(DefaultPanel):
	def __init__(self, parent, title):
		DefaultPanel.__init__(self, parent, title)

		self.server_text = ResizableStaticText(self, self.parent, GUI.Blurbs.BuildServer)
		self.server_text.SetFont(system_font)

		self.build_server_button = wx.adv.CommandLinkButton(self, wx.ID_ANY, mainLabel='Build Server Program', size=wx.Size(320, 50))
		self.build_server_button.Bind(wx.EVT_BUTTON, self.build_server, id=wx.ID_ANY)

		self.client_text = ResizableStaticText(self, self.parent, GUI.Blurbs.BuildClient)
		self.client_text.SetFont(system_font)

		self.build_client_button = wx.adv.CommandLinkButton(self, wx.ID_ANY, mainLabel='Build Client HTML', size=wx.Size(320, 50))
		self.build_client_button.Bind(wx.EVT_BUTTON, self.build_client, id=wx.ID_ANY)

		self.cert_text = ResizableStaticText(self, self.parent, GUI.Blurbs.GenerateKey)
		self.cert_text.SetFont(system_font)

		self.gen_cert_button = wx.adv.CommandLinkButton(self, wx.ID_ANY, mainLabel='Generate Certificate (optional)', size=wx.Size(320, 50))
		self.gen_cert_button.Bind(wx.EVT_BUTTON, self.make_cert, id=wx.ID_ANY)

		self.sizer.Add(self.server_text)
		self.sizer.AddSpacer(50)
		self.sizer.Add(self.build_server_button)

		self.sizer.AddSpacer(25)
		self.sizer.Add(wx.StaticLine(self, size=(320,1)))
		self.sizer.AddSpacer(25)

		self.sizer.Add(self.client_text)
		self.sizer.AddSpacer(50)
		self.sizer.Add(self.build_client_button)

		self.sizer.AddSpacer(25)
		self.sizer.Add(wx.StaticLine(self, size=(320,1)))
		self.sizer.AddSpacer(25)

		self.sizer.Add(self.cert_text)
		self.sizer.AddSpacer(50)
		self.sizer.Add(self.gen_cert_button)

		self.print_status()

	def is_complete(self) -> bool:
		return self.has_client() and self.has_server()

	def print_status(self):
		terminal.WriteToTerminal(f'## Server software is ready: ***{self.has_server()}***')
		terminal.WriteToTerminal(f'## Client software is ready: ***{self.has_client()}***')
		terminal.WriteToTerminal(f'## SSL certificate is ready: ***{self.has_cert()}***')

	def has_server(self) -> bool:
		return os.path.isfile(paths.GetPath('root_deploy_server'))
	
	def build_server(self, event):
		def run_thread():
			commands = [
				f'mkdir root_deploy_static',
				f'python3 -m pip install -r requirements.txt',
				f'python3 -m PyInstaller -y -F --clean UltimateSensorMonitor.py',
				f'copy root_server_dist\\UltimateSensorMonitor.exe root_deploy'
			]
			for index, command in enumerate(commands):
				args = paths.SplitThenReplacePaths(command)
				process = terminal.RunThis(args, cwd=paths.GetPath('root_server'), id=index)
				if process is not None:
					terminal.FollowProcess(process)

			self.print_status()

		t = threading.Thread(target=run_thread)
		t.start()
	
	def has_client(self) -> bool:
		return os.path.isfile(paths.GetPath("root_deploy_static_index"))
	
	def build_client(self, event):
		def run_thread():
			commands = [
				f'mkdir root_deploy_static',
				f'npm install',
				f'npm run release',
				f'xcopy /f /s /y /i root_client_dist root_deploy_static'
			]

			for index, command in enumerate(commands):
				args = paths.SplitThenReplacePaths(command)
				process = terminal.RunThis(args, cwd=paths.GetPath('root_client'), id=index)
				if process is not None:
					terminal.FollowProcess(process)

			self.print_status()

		t = threading.Thread(target=run_thread)
		t.start()
	
	def has_cert(self) -> bool:
		return os.path.isfile(paths.GetPath("root_deploy_cert")) and os.path.isfile(paths.GetPath("root_deploy_key"))
	
	def make_cert(self, event):
		cert_gen(paths.GetPath("root_deploy_key"), paths.GetPath("root_deploy_cert"))

		self.print_status()

class RunServer(DefaultPanel):
	def __init__(self, parent, title):
		DefaultPanel.__init__(self, parent, title)

		self.source_types = [ 'aida64', 'hwinfo64', 'lhm' ]

		self.server_process : subprocess.Popen[str] | None = None
		self.server_thread = None

		server_settings = load_config(paths.GetPath('root_deploy_config'))
	#	dump_values(server_settings, terminal.WriteToTerminal)

		self.txt = ResizableStaticText(self, self.parent, GUI.Blurbs.RunServer)
		self.txt.SetFont(system_font)

		self.refresh_time = wx.SpinCtrl(self, size=(250, 20), min=10, max=1000000, initial=500, style=wx.SP_ARROW_KEYS | wx.ALIGN_CENTER, value=str(server_settings.refresh_time))
		self.refresh_time.Bind(wx.EVT_SPINCTRL, self.value_updated)
		self.refresh_time_name = ResizableStaticText(self, self.parent, label='Refresh Time (in ms): ')
		
		self.incremental_updates = wx.CheckBox(self, size=(250, 20), style=wx.CHK_2STATE|wx.ALIGN_RIGHT,)
		self.incremental_updates.SetValue(server_settings.incremental)
		self.incremental_updates.Bind(wx.EVT_CHECKBOX, self.value_updated)
		self.incremental_updates_name = ResizableStaticText(self, self.parent, label='Incremental Updates (saves network bandwidth): ')

		self.full_update_iterations = wx.SpinCtrl(self, size=(250, 20), min=1, max=1000000, initial=10, style=wx.SP_ARROW_KEYS | wx.ALIGN_CENTER, value=str(server_settings.full_update_iterations))
		self.full_update_iterations.Bind(wx.EVT_SPINCTRL, self.value_updated)
		self.full_update_iterations_name = ResizableStaticText(self, self.parent, label='The number of incremental updates between full updates (if incremental is enabled): ')

		self.select_source = wx.Choice(self, size=(250, 20))
		self.select_source.AppendItems(self.source_types)
		self.select_source.SetSelection(self.source_types.index(server_settings.source))
		self.select_source.Bind(wx.EVT_CHOICE, self.value_updated)
		self.select_source_name = ResizableStaticText(self, self.parent, label='Select Source: ')

		self.can_elevate = wx.CheckBox(self, size=(250, 20), style=wx.CHK_2STATE|wx.ALIGN_RIGHT)
		self.can_elevate.SetValue(server_settings.can_elevate)
		self.can_elevate.Bind(wx.EVT_CHECKBOX, self.value_updated)
		self.can_elevate_name = ResizableStaticText(self, self.parent, label='Allow asking for administrator privileges if necessary (might not work without this): ')

		self.run_server = wx.CheckBox(self, size=(250, 20), style=wx.CHK_2STATE|wx.ALIGN_RIGHT)
		self.run_server.SetValue(server_settings.with_server)
		self.run_server.Bind(wx.EVT_CHECKBOX, self.value_updated)
		self.run_server_name = ResizableStaticText(self, self.parent, label='Run the server software (necessary if not testing changes): ')

		self.server_port = wx.lib.intctrl.IntCtrl(self, size=wx.Size(250, 20), min=1, max=65534, value=server_settings.port)
		self.server_port.Bind(wx.EVT_TEXT, self.value_updated)
		self.server_port_name = ResizableStaticText(self, self.parent, label='Port for the server to listen on: ')

		self.server_password = wx.TextCtrl(self, size=(250, 20), value=server_settings.password)
		self.server_password.Bind(wx.EVT_TEXT, self.value_updated)
		self.server_password_name = ResizableStaticText(self, self.parent, label='Password for the server (to prevent unauthorized access): ')

		self.static_folder = wx.DirPickerCtrl(self, size=(250, 20), path=str(server_settings.static_folder))
		self.static_folder.Bind(wx.EVT_DIRPICKER_CHANGED, self.value_updated)
		self.static_folder_name = ResizableStaticText(self, self.parent, label='Folder for storing the Client\'s index.html into')

		self.cert_picker = wx.FilePickerCtrl(self, size=(250, 20), path=str(server_settings.certificate) if server_settings.certificate is not None else '')
		self.cert_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self.value_updated)
		self.cert_picker_name = ResizableStaticText(self, self.parent, label='Select Encryption Certificate (optional): ')
		
		self.key_picker = wx.FilePickerCtrl(self, size=(250, 20), path=str(server_settings.key) if server_settings.key is not None else '')
		self.key_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self.value_updated)
		self.key_picker_name = ResizableStaticText(self, self.parent, label='Select Encryption Key (optional): ')

		self.save_button = wx.adv.CommandLinkButton(self, wx.ID_ANY, mainLabel='Save Settings', size=wx.Size(320, 50))
		self.save_button.Bind(wx.EVT_BUTTON, self.save_only)

		self.save_and_run_button = wx.adv.CommandLinkButton(self, wx.ID_ANY, mainLabel='Save and Run Server', size=wx.Size(320, 50))
		self.save_and_run_button.Bind(wx.EVT_BUTTON, self.save_and_run)
		
		self.stop_server_button = wx.adv.CommandLinkButton(self, wx.ID_ANY, mainLabel='Stop Server', size=wx.Size(320, 50))
		self.stop_server_button.Bind(wx.EVT_BUTTON, self.stop_server)

		self.sizer.Add(self.txt)
		self.sizer.AddSpacer(50)

		add_row(self.sizer, self.refresh_time, self.refresh_time_name)
		add_row(self.sizer, self.incremental_updates, self.incremental_updates_name)
		add_row(self.sizer, self.full_update_iterations, self.full_update_iterations_name)
		add_row(self.sizer, self.select_source, self.select_source_name)
		add_row(self.sizer, self.can_elevate, self.can_elevate_name)
		add_row(self.sizer, self.run_server, self.run_server_name)
		add_row(self.sizer, self.server_port, self.server_port_name)
		add_row(self.sizer, self.server_password, self.server_password_name)
		add_row(self.sizer, self.static_folder, self.static_folder_name)
		add_row(self.sizer, self.cert_picker, self.cert_picker_name)
		add_row(self.sizer, self.key_picker, self.key_picker_name)

		self.sizer.AddSpacer(50)
		self.sizer.Add(self.save_button)
		self.sizer.AddSpacer(15)
		self.sizer.Add(self.save_and_run_button)
		self.sizer.AddSpacer(15)
		self.sizer.Add(self.stop_server_button)

	def is_complete(self) -> bool:
		return True

	def value_updated(self, event):
		self.save_only(event)

		server_settings = load_config(paths.GetPath('root_deploy_config'))
		dump_values(server_settings, terminal.WriteToTerminal)

	def save_only(self, event):
		server_settings = ServerSettings()
		server_settings.refresh_time = self.refresh_time.Value
		server_settings.incremental = self.incremental_updates.Value
		server_settings.full_update_iterations = self.full_update_iterations.Value
		server_settings.source = self.source_types[self.select_source.Selection]
		server_settings.can_elevate = self.can_elevate.Value
		server_settings.with_server = self.run_server.Value
		server_settings.port = self.server_port.Value
		server_settings.password = self.server_password.Value
		server_settings.static_folder = self.static_folder.Path
		server_settings.certificate = self.cert_picker.Path
		server_settings.key = self.key_picker.Path

		save_config(server_settings, paths.GetPath('root_deploy_config'))

	def save_and_run(self, event):
		self.save_only(event)

		self.stop_server(event)

		def run_thread(self : RunServer):
			command = paths.GetPath('root_deploy_server')
			self.server_process = terminal.RunThis([ command ], cwd=paths.GetPath('root_deploy'), shell=False)
			if self.server_process is not None:
				terminal.WriteToTerminal('new pid: ' + str(self.server_process.pid))
				terminal.FollowProcess(self.server_process)

		self.server_thread = threading.Thread(target=run_thread, args=[ self ])
		self.server_thread.start()

		self.save_and_run_button.Disable()
		self.save_button.Disable()
		self.stop_server_button.Enable()
	
	def stop_server(self, event = None):
		if self.server_process is not None:
			self.server_process.send_signal(signal.CTRL_BREAK_EVENT)
			self.server_process.kill()
			self.server_process.terminate()
			self.server_process.wait()

		if self.server_thread is not None and self.server_thread.is_alive():
			self.server_thread.join()

		self.stop_server_button.Disable()
		self.save_button.Enable()
		self.save_and_run_button.Enable()

class MainWindow(wx.Frame):
	def __init__(self, parent, title):
		wx.Frame.__init__(self, parent, -1, title, style=wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.RESIZE_BORDER)
		self.SetThemeEnabled(True)

		self.CloseToTaskbar = True

		self.InitUI()
		self.SetupTaskbar()
		self.SetupMenu()

		self.check_consistency()

		self.Layout()
	
	def SetupTaskbar(self):
		self.taskBarIcon = wx.adv.TaskBarIcon()
		if self.taskBarIcon.IsAvailable() is False:
			raise SystemExit("Cannot access system tray")
		bitmap = wx.ArtProvider.GetBitmap(wx.ART_TIP, wx.ART_CMN_DIALOG)
		self.taskBarIcon.SetIcon(wx.Icon(bitmap), "Tooltip")
		# Create bind events
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		self.Bind(wx.EVT_ICONIZE, self.OnMinimize)
		self.taskBarIcon.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.OnShowFrame)

	def SetupMenu(self):
		self.menubar = wx.MenuBar()

		fileMenu = wx.Menu()
		self.menubar.Append ( fileMenu, '&File' )

		self.Bind ( wx.EVT_MENU, self.on_refresh, fileMenu.Append ( wx.ID_ANY, 'Refresh Components' ) )
		fileMenu.AppendSeparator()
		self.Bind ( wx.EVT_MENU, self.OnClose, fileMenu.Append ( wx.ID_ANY, 'Minimize to Tray' ) )
		fileMenu.AppendSeparator()
		self.Bind ( wx.EVT_MENU, self.OnQuit, fileMenu.Append ( wx.ID_ANY, 'Stop and Quit' ) )

		self.SetMenuBar ( self.menubar )

	def InitUI(self):

		self.splitter = wx.SplitterWindow(self, -1, style=wx.SP_LIVE_UPDATE | wx.SP_3D)

		# Here we create a panel and a notebook on the panel.
		self.top_panel = wx.Panel(self.splitter)
		self.log_panel = TerminalPanel(self.splitter)
		self.organizer = wx.Notebook(self.top_panel)
		self.currentTab : int = 0

		terminal.SetTarget(self.log_panel)

		server_settings = load_config(paths.GetPath('root_deploy_config'))
		if server_settings is not None:
			dump_values(server_settings, terminal.WriteToTerminal)
		
		# Ccreate the page windows as children of the notebook.
		self.panel_intro = Intro(self.organizer, "Intro")
		self.panel_install_tools = InstallTools(self.organizer, "Install Tools")
		self.panel_build_software = BuildSoftware(self.organizer, "Build Software")
		self.panel_run_server = RunServer(self.organizer, "Configure and Run Server")
		self.tabs : List[DefaultPanel] = [self.panel_intro, self.panel_install_tools, self.panel_build_software, self.panel_run_server]

		# Add the pages to the notebook with the label to show on the tab.
		for tab in self.tabs:
			self.organizer.AddPage(tab, text=tab.title)

		self.organizer.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_change, id=wx.ID_ANY)
		
		sizer_buttons = wx.BoxSizer(orient=wx.HORIZONTAL)
		
	#	self.button_refresh = wx.Button(self.top_panel, wx.ID_ANY, label="Recheck Components")
	#	self.button_refresh.SetFont(system_font)
		self.button_start = wx.Button(self.top_panel, wx.ID_ANY, label="Home")
		self.button_start.SetFont(system_font)
		self.button_prev = wx.Button(self.top_panel, wx.ID_ANY, label="Prev")
		self.button_prev.SetFont(system_font)
		self.button_next = wx.Button(self.top_panel, wx.ID_ANY, label="Next")
		self.button_next.SetFont(system_font)
		self.button_finish = wx.Button(self.top_panel, wx.ID_ANY, label="Save and Run Server")
		self.button_finish.SetFont(system_font)
		
		sizer_buttons.Add(self.button_start, 0, 0, 5)
		sizer_buttons.AddStretchSpacer()
		sizer_buttons.Add(self.button_prev, 0, 0, 5)
		sizer_buttons.Add(self.button_next, 0, 0, 5)
		sizer_buttons.Add(self.button_finish, 0, 0, 5)
		
	#	self.button_refresh.Bind(wx.EVT_BUTTON, self.on_refresh, id=wx.ID_ANY)
		self.button_start.Bind(wx.EVT_BUTTON, self.on_start, id=wx.ID_ANY)
		self.button_prev.Bind(wx.EVT_BUTTON, self.on_prev, id=wx.ID_ANY)
		self.button_next.Bind(wx.EVT_BUTTON, self.on_next, id=wx.ID_ANY)
		self.button_finish.Bind(wx.EVT_BUTTON, self.on_finish, id=wx.ID_ANY)

		# Finally, put the notebook in a sizer for the panel to manage the layout.
		sizer = wx.BoxSizer(orient=wx.VERTICAL)
		sizer.Add(self.organizer, 1, wx.EXPAND, border=5)
	#	sizer.Add(self.button_refresh, 0, wx.ALIGN_RIGHT, 5)
		sizer.Add(sizer_buttons, 0, wx.BOTTOM | wx.EXPAND, border=5)

		self.top_panel.SetSizer(sizer)

		sizer_buttons.Layout()
		sizer.Layout()

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.check_consistency, self.timer)
		self.timer.Start(2000)

		self.splitter.SplitVertically(self.top_panel, self.log_panel, 0)
		self.splitter.SetSashGravity(0.5)

		self.on_change()

	def on_change(self, event = None):
		self.currentTab = self.organizer.GetSelection()

		self.check_consistency()
	
	def on_refresh(self, event):
		self.currentTab = self.organizer.GetSelection()

		for tab in self.tabs:
			tab.print_status()

		self.check_consistency()

	def on_start(self, event):
		self.currentTab = 0
		self.organizer.ChangeSelection(self.currentTab)
		self.currentTab = self.organizer.GetSelection()

		self.on_change()

	def on_prev(self, event):
		self.currentTab = self.organizer.GetSelection()
		if self.currentTab > 0:
			self.currentTab -= 1
			self.organizer.ChangeSelection(self.currentTab)

		self.on_change()

	def on_next(self, event):
		self.currentTab = self.organizer.GetSelection()

		while self.currentTab < len(self.tabs) - 1:
			self.currentTab += 1
			self.organizer.ChangeSelection(self.currentTab)
			if not self.tabs[self.currentTab].is_complete():
				break

		self.on_change()

	def on_finish(self, event):
		self.currentTab = self.organizer.GetSelection()

		all_good : bool = True
		for tab in self.tabs:
			complete = tab.is_complete()
			all_good &= complete
		if all_good:
			self.panel_run_server.save_and_run(event)

		self.on_change()
	
	def check_consistency(self, event=None):
		if self.IsShown() is False:
			return

		if self.currentTab > 0:
			self.button_prev.Enable()
		else:
			self.button_prev.Disable()

		if self.tabs[self.currentTab].is_complete() and self.currentTab < len(self.tabs) - 1:
			self.button_next.Enable()
		else:
			self.button_next.Disable()

		all_good : bool = True
		for index, tab in enumerate(self.tabs):
			complete = tab.is_complete()
			# I wish this would change the tab colors and not the panel colors  (should investigate later, perhaps)
		#	if index == self.currentTab:
		#		tab.SetBackgroundColour(wx.Colour(67, 119, 250))
		#	elif complete:
		#		tab.SetBackgroundColour(wx.Colour(95, 250, 116))
		#	else:
		#		tab.SetBackgroundColour(wx.Colour(219, 37, 37))
			all_good &= complete
		if all_good and self.currentTab == len(self.tabs) - 1:
			self.button_finish.Enable()
		else:
			self.button_finish.Disable()
			
	def OnMinimize(self, event):
		if self.IsIconized() is True:
			self.Hide()

	def OnShowFrame(self, event):
		# Restore Frame if it is minimized.
		if self.IsIconized() is True:
			self.Restore()

			self.currentTab = self.organizer.GetSelection()

		# Show MainFrame if it is not shown already.
		if self.IsShown() is True:
			# Frame is already visible. Flash it.
			self.RequestUserAttention()
			self.SetFocus()
		else:
			self.Show()
			self.currentTab = self.organizer.GetSelection()

		self.Raise()

	def OnClose(self, event):
		if self.CloseToTaskbar:
			self.Hide()
		else:
			self.panel_run_server.stop_server()

			# Frame closed. Destroy taskbar icon
			event.Skip(True)
			self.taskBarIcon.Destroy()

	def OnQuit(self, event):
		self.panel_run_server.stop_server()
		self.CloseToTaskbar = False
		wx.CallAfter(self.Close)


class USMApp(wx.App):
	def __init__(self):
		wx.App.__init__(self, redirect=False, filename=None, useBestVisual=True)

	def OnInit(self):
		global system_font
		system_font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
	#	description_font = wx.Font(12, family=wx.FONTFAMILY_DECORATIVE, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_NORMAL)

		frame = MainWindow(None, "Ultimate Sensor Monitor")
		frame.SetClientSize(frame.FromDIP(wx.Size(1400, 960)))
		self.SetTopWindow(frame)
		frame.Show(True)

		return True


if __name__ == "__main__":
	signal.signal(signal.SIGINT, lambda _1, _2: signal.raise_signal(signal.SIGTERM))
	signal.signal(signal.SIGTERM, lambda _1, _2: os._exit(0))

	app = USMApp()
	app.MainLoop()
