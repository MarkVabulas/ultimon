
import aiohttp
import aiohttp_cors
import asyncio
import ssl
import json

from pathlib import Path
from typing import Any, AsyncIterator, Coroutine, Union, Callable, List, Dict

from aiohttp import web, WSMsgType
from aiohttp_index import IndexMiddleware

from Server.ServerSettings import ServerSettings
from Server.WebSocketClientManager import WebSocketClientManager
from Server.ServerLogger import logger, logging

DISCONNECT_DELAY_S = 1
INACTIVE_DELAY_S = 5
PING_INTERVAL_S = 10

# coroutine that will start another coroutine after a delay in seconds  (from https://superfastpython.com/asyncio-delayed-task/)
async def delay(coro, seconds):
    # suspend for a time limit in seconds
    await asyncio.sleep(seconds)
    # execute the other coroutine
    await coro
		
@web.middleware
async def cors_middleware(request, handler) -> web.StreamResponse:
	try:
		response = await handler(request)
		response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
		response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
		response.headers['Cross-Origin-Resource-Policy'] = 'cross-origin'
		return response
	except:
		return web.StreamResponse()
	
class ServerModule:
	def __init__(self, settings : ServerSettings):
		try:

			self.event_lookup : Dict[str, Callable] = {
				'connect': self.handle_connection
			}

			self.settings = settings
			self.web_socket_client_manager = WebSocketClientManager()
			middlewares_list = [IndexMiddleware(), cors_middleware]
			self.app = web.Application(middlewares=middlewares_list)

			self.should_update_users = False
			self.current_user_data = {}
			asyncio.create_task(self.load_user_data())
			
			# Configure default CORS settings.
			self.cors = aiohttp_cors.setup(self.app, defaults={
				"*": aiohttp_cors.ResourceOptions(
						allow_credentials=False,
						expose_headers="*",
						allow_headers="*",
						max_age=3600,
					)
			})
			
			# Create route to get iceservers
			self.app.add_routes([ web.get('/sensor_data', self.web_socket_handler) ])
			if hasattr(self.settings, 'static_folder') and self.settings.static_folder is not None and self.settings.static_folder.is_dir():
				self.app.router.add_static('/', path=str(self.settings.static_folder))
			
			# Configure CORS on all routes.
			for route in list(self.app.router.routes()):
				self.cors.add(route)

			# Create static route if required
		#	if self.settings.static_folder is not None:
		#		self.app.add_routes([web.static('/', )])
		except Exception as ex:
			print('An exception of type {0} occurred. Arguments:\n\t{1!r}'.format(type(ex).__name__, ex.args))

	async def load_user_data(self):
		old_data = self.current_user_data
		with open('user_data.json') as f:
			d = json.load(f)
			self.current_user_data = d
		
		if old_data != self.current_user_data:
			self.should_update_users = True
		await delay(self.load_user_data(), 30)
	
	async def authorized(self, client_id : str, data) -> bool:
		#check authorization password
		if not self.isAuthorized(data['password'] if 'password' in data else ''):
			asyncio.create_task(self.disconnect_delayed(client_id))
			return False
		# we're good
		return True
		
	def isAuthorized(self, user_password):
		return self.settings.password is None or user_password == self.settings.password
	
	def run_webserver(self):
		# Run app
		if self.settings.using_tls:
			assert(self.settings.certificate is not None)
			assert(self.settings.key is not None)

			ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
			ssl_context.verify_mode = ssl.CERT_NONE
			ssl_context.load_cert_chain(certfile=self.settings.certificate, keyfile=self.settings.key)
			web.run_app(self.app, port=self.settings.port, ssl_context=ssl_context) # add access_log=logger for more debugging
		else:
			web.run_app(self.app, port=self.settings.port) # add access_log=logger for more debugging
			
	async def web_socket_handler(self, request):
		ws = web.WebSocketResponse()
		await ws.prepare(request)

		client_id = await self.web_socket_client_manager.add_ws(ws)
		logger.info('connect %s', client_id)
		self._asyncio_context = asyncio.get_running_loop()
		asyncio.create_task(self.web_socket_ping_task(ws))

		try:
			async for msg in ws:
				if msg.type == WSMsgType.TEXT:
					try:
						data = json.loads(msg.data)
						await self.handle_web_socket_message(client_id, data)
					except Exception as e:
						logger.error('Message error (%s): %s', client_id, str(e))
						if (len(msg.data) < 255):
							logger.error('\tMessage error (continued): msg.data=%s', msg.data)

			logger.info('disconnect %s', client_id)
			
			await self.web_socket_client_manager.close(client_id)
			
		except:
			pass

		return ws

	async def web_socket_ping_task(self, ws):
		while not ws.closed:
			try:
				await asyncio.sleep(PING_INTERVAL_S)
				await ws.ping()
			except:
				pass

	async def handle_web_socket_message(self, client_id : str, encapsulated_data):
		if 'event' not in encapsulated_data:
			logger.error('Invalid message (%s): %s', client_id, str(encapsulated_data))
			return

		event = encapsulated_data['event']
		if 'data' in encapsulated_data:
			data = encapsulated_data['data']
		else:
			data = {}

	#	logger.error('handle_web_socket_message (%s): %s {%s}', client_id, event, data)

		if (event in self.event_lookup):
			await self.event_lookup.get(event, lambda: 'Invalid')(client_id, data)
		else:
			logger.error('Not handled message (%s): %s: %s', client_id, event, str(data))

	def event_to_message(self, event, data=None):
		if data is None:
			message = {'event': event}
		else:
			message = {'event': event, 'data': data}

	#	logger.info('event_to_message: %s', json.dumps(message)[:60])
		return json.dumps(message)


	async def handle_connection(self, client_id : str, data):
	#	logger.info('handle_connection %s (%s)', client_id, data)

		# check authorization
		if not await self.authorized(client_id, data):
			return
		
		# notify that the user is welcome
		await self.web_socket_client_manager.send_to(self.event_to_message('welcome', { 'id': client_id }), client_id)
		await self.web_socket_client_manager.send_to(self.event_to_message('user-data', self.current_user_data), client_id)
		
	async def disconnect_delayed(self, client_id : str):
		await asyncio.sleep(DISCONNECT_DELAY_S)
		await self.web_socket_client_manager.close(client_id)
		
	async def send_sensor_update(self, data):
		# send the sensor data to everyone
	#	logger.info('current: send_sensor_update to all')
		await self.web_socket_client_manager.send_to_all(self.event_to_message('sensor-data', data))
		if self.should_update_users:
			self.should_update_users = False
			await self.web_socket_client_manager.send_to_all(self.event_to_message('user-data', self.current_user_data))
		
	async def send_sensor_update_targeted(self, data, client_id):
		# send the sensor data to everyone
		logger.info('current: send_sensor_update to %s', client_id)
		await self.web_socket_client_manager.send_to(self.event_to_message('sensor-data', data), client_id)

	async def send_suggest_refresh(self):
		# send the suggest refresh to everyone
		logger.info('current: suggest-refresh to all')
		await self.web_socket_client_manager.send_to_all(self.event_to_message('suggest-refresh', data={}))
