import json
from typing import Dict, List

from html.parser import HTMLParser
from multiprocessing import shared_memory

from Sources.BaseSourceInterface import BaseSourceInterface

class SourceAida64(HTMLParser, BaseSourceInterface):
	def __init__(self):
		super(SourceAida64, self).__init__()

		# Ensure our connection to the shared memory from Aida64
		self._aida64Memory = shared_memory.SharedMemory(name='AIDA64_SensorValues', create=False)

		# Initialize our variables
		self._changedValues : Dict[str, Dict[str, str]] = {} 
		self._keyValues : Dict[str, Dict[str, str]] = {}
		self._tagStack : List[str] = []
		self._currentId : str = ''

	def __del__(self):
		# DON'T FORGET TO CLEANUP the Shared Memory
		self._aida64Memory.close()
	
	def source_once(self):
		# Ensure that we have reset the tag stack and the currentId after a parse has finished, so we don't get confused between runs
		self._tagStack = []
		self._currentId = ''

		self._changedValues = {}

		# Perform one iteration of the process, where we grab the data
		if self._aida64Memory:
			self.feed(bytes(self._aida64Memory.buf[:64*1024]).decode(encoding='utf-8'))

		#print(json.dumps(self._changedValues))
		
	def handle_starttag(self, tag, attrs):
		# Start a tag, so we can keep track of where we are in the parse tree
		self._tagStack.append(tag)
		
	def handle_endtag(self, tag):
		# End the tag, but make sure we're not at root depth (Aida64 loves to have extraneous end-tags)
		if len(self._tagStack) == 0:
			return
		
		# Lets pop the stack, and reset the currentId if we're at root
		self._tagStack.pop()
		if len(self._tagStack) == 0:
			self._currentId = ''
			
	def handle_data(self, data):
		# Ensure that we are still inside a tag somewhere
		if len(self._tagStack) == 0:
			#if len(data) > 0: print('ignoring bad data: "' + data + '"')
			return
		
		# Get the current tag from the top of the stack
		currentTag = self._tagStack[-1]
		if currentTag == '' and self._currentId != '':
			# This should never happen, abandon this call
			return
		elif currentTag == 'id':
			# Lets save which data ID we're going to be saving into for the next while, until we pop out of this stack
			self._currentId = data
			# Ensure the data exists
			if self._keyValues is None or self._currentId not in self._keyValues:
				self._keyValues[self._currentId] = {}
				self._keyValues[self._currentId]['type'] = self._tagStack[0]
				self._changedValues[self._currentId] = {}
		else:
			# Since the tag isn't an ID, we should store the tag+data into our key/value pairs for lookup later
			if self._currentId in self._keyValues:
				if currentTag not in self._keyValues[self._currentId]:
					self._keyValues[self._currentId][currentTag] = ''
				if self._keyValues[self._currentId][currentTag] != data:
					if self._currentId not in self._changedValues:
						self._changedValues[self._currentId] = {}
						self._changedValues[self._currentId]['type'] = self._tagStack[0]
					if currentTag not in self._changedValues[self._currentId]:
						self._changedValues[self._currentId][currentTag] = ''
					self._changedValues[self._currentId][currentTag] = data
				self._keyValues[self._currentId][currentTag] = data
	
	def can_loop(self):
		return True

	def get_values(self) -> Dict[str, Dict[str, str]]:
		# Let the caller get the updated info from us
		return self._changedValues

	def get_all_values(self) -> Dict[str, Dict[str, str]]:
		# Let the caller get the complete info from us
		return self._keyValues
	