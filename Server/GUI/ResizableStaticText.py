import wx
	
class ResizableStaticText(wx.StaticText):
	def __init__(self, parent, grandparent, label):
		wx.StaticText.__init__(self, parent, id=wx.ID_ANY, label=label)

		self._original_text = label
		self._parent = parent
		self._grandparent = grandparent
		self._grandparent.Bind(wx.EVT_SIZE, self.grandparent_resize, id=wx.ID_ANY)
	
	def grandparent_resize(self, event):
		self._grandparent.Freeze()
		self.SetLabelText(self._original_text)
		self.Wrap(self._grandparent.GetClientSize()[0]-self.GetPosition()[0]-20)
		self.SetSizeHints(minSize=self.GetSizeFromText(self._original_text), maxSize=(4096, 4096))
		self._grandparent.Thaw()
		event.Skip()
		