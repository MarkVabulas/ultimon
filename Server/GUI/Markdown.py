import wx
import wx.richtext as rt
import markdown
import bs4
import webbrowser
import urllib

from urllib.error import HTTPError, URLError

from io import BytesIO
from pathlib import Path

class ExtendedRichText(rt.RichTextCtrl):
	"""
	`RichTextCtrl` with some extra quality-of-life methods and functionality.
	"""

	def __init__(self, parent,
		files_directory: str = "",
		allow_download_images: bool = False,
		*args, **kwargs
	) -> None:

		super().__init__(parent, style=wx.TE_RICH2|wx.HSCROLL, *args, **kwargs)
		
		self.indentations = [0]
		self.ordered_list_indices = []
		
		self.files_directory = Path(files_directory)
		self.allow_download_images = allow_download_images

		self.Bind(wx.EVT_TEXT_URL, self.on_url)

	
	def on_url(self, event: rt.RichTextEvent) -> None:
		"""Open link in web browser."""
		webbrowser.open(event.GetString())


	def GetIndentation(self) -> int:
		"""
		Get current indentation.
		"""
		return int(sum(self.indentations))

	def GetStyle(self) -> rt.RichTextAttr:
		"""
		Get current style.
		"""
		style = rt.RichTextAttr()
		super().GetStyle(self.GetInsertionPoint(), style)
		return style

	def EnsureNewline(self) -> None:
		"""
		Ensure buffer ends in newline.
		"""
		if self.GetValue()[-1:] != '\n':
			self.Newline()

	def BeginIndentation(self, indentation: int) -> None:
		"""
		Begins an indentation.
		"""
		self.indentations.append(indentation)
		self.BeginLeftIndent(self.GetIndentation())

	def EndIndentation(self) -> None:
		"""
		Ends an indentation.
		"""
		self.EndLeftIndent()
		self.indentations.pop()


	def BeginParagraph(self) -> None:
		"""
		Begins paragraph.
		"""

	def EndParagraph(self) -> None:
		"""
		Ends paragraph.
		"""
		self.Newline()


	def BeginBlockquote(self) -> None:
		"""
		Begins blockquote.
		"""
		self.BeginIndentation(self.GetCharWidth() * 2)
		self.BeginTextColour('#FF8000')

	def EndBlockquote(self) -> None:
		"""
		Ends blockquote.
		"""
		self.EndTextColour()
		self.EndIndentation()


	def BeginCode(self) -> None:
		"""
		Begins code.
		"""
		font_info = self.GetStyle().GetFont()
		font_info.SetFamily(wx.FONTFAMILY_TELETYPE)
		font = wx.Font(font_info)
		self.BeginFont(font)

	def EndCode(self) -> None:
		"""
		Ends code.
		"""
		self.EndFont()


	def BeginHeading1(self) -> None:
		"""
		Begins heading 1.
		"""
		self.BeginFontSize(int(self.Font.GetPointSize() * 2.0))

	def EndHeading1(self) -> None:
		"""
		Ends heading 1.
		"""
		self.EndFontSize()
		self.Newline()

	def BeginHeading2(self) -> None:
		"""
		Begins heading 2.
		"""
		self.BeginFontSize(int(self.Font.GetPointSize() * 1.5))

	def EndHeading2(self) -> None:
		"""
		Ends heading 2.
		"""
		self.EndFontSize()
		self.Newline()

	def BeginHeading3(self) -> None:
		"""
		Begins heading 3.
		"""
		self.BeginFontSize(int(self.Font.GetPointSize() * 1.3))

	def EndHeading3(self) -> None:
		"""
		Ends heading 3.
		"""
		self.EndFontSize()
		self.Newline()

	def BeginHeading4(self) -> None:
		"""
		Begins heading 4.
		"""
		self.BeginFontSize(int(self.Font.GetPointSize() * 1.0))

	def EndHeading4(self) -> None:
		"""
		Ends heading 4.
		"""
		self.EndFontSize()
		self.Newline()

	def BeginHeading5(self) -> None:
		"""
		Begins heading 5.
		"""
		self.BeginFontSize(int(self.Font.GetPointSize() * 0.8))

	def EndHeading5(self) -> None:
		"""
		Ends heading 5.
		"""
		self.EndFontSize()
		self.Newline()

	def BeginHeading6(self) -> None:
		"""
		Begins heading 6.
		"""
		self.BeginFontSize(int(self.Font.GetPointSize() * 0.7))

	def EndHeading6(self) -> None:
		"""
		Ends heading 6.
		"""
		self.EndFontSize()
		self.Newline()


	def BeginLink(self, url: str) -> None:
		"""
		Begins link.
		"""
		self.BeginURL(url)
		self.BeginUnderline()
		self.BeginTextColour('#AAAAFF')
	
	def EndLink(self) -> None:
		"""
		Ends link.
		"""
		self.EndTextColour()
		self.EndUnderline()
		self.EndURL()


	def BeginUnorderedList(self) -> None:
		"""
		Begins unordered list.
		"""
		self.EnsureNewline()

	def EndUnorderedList(self) -> None:
		"""
		Ends unordered list.
		"""
		self.EnsureNewline()

	def BeginUnorderedListItem(self) -> None:
		"""
		Begins unordered list item.
		"""
	#	self.EnsureNewline()
		indent = self.GetIndentation()
		subindent = int(self.GetCharWidth() * 1.5)
		self.BeginStandardBullet('circle', indent, subindent)

	def EndUnorderedListItem(self) -> None:
		"""
		Ends unordered list item.
		"""
		self.EnsureNewline()
		self.EndStandardBullet()


	def BeginOrderedList(self) -> None:
		"""
		Begins ordered list.
		"""
		self.ordered_list_indices.append(0)
	#	self.EnsureNewline()


	def EndOrderedList(self) -> None:
		"""
		Ends ordered list.
		"""
	#	self.EnsureNewline()
		self.ordered_list_indices.pop()

	def BeginOrderedListItem(self) -> None:
		"""
		Begins ordered list item.
		"""

	#	self.EnsureNewline()

		# Increment counter and get current index
		self.ordered_list_indices[-1] += 1
		index = self.ordered_list_indices[-1]

		# Calculate the subindent from the width of the prefix
		digits = len(str(index))
		# TODO: Make this consistent.
		# This formula seems to align the text properly,
		# but it isn't rooted in anything mathematically sound.
		subindent = int(self.GetCharWidth() * 0.65 * (digits + 2))

		self.BeginNumberedBullet(index, self.GetIndentation(), subindent)

	def EndOrderedListItem(self) -> None:
		"""
		Ends ordered list item.
		"""
		self.EnsureNewline()
		self.EndStandardBullet()

	def WriteImage(self,
		source: str, alt_text: str = "",
		width: int = None, height: int = None
		) -> wx.Image:
		"""
		Write an image.
		"""
		
		try:
			# Download image
			if source.startswith('http://') or source.startswith('https://'):

				if not self.allow_download_images:
					raise PermissionError('Downloading images is disabled.')
					
				request = urllib.request.Request(source, headers={'User-Agent': 'Mozilla/5.0'})
				stream = BytesIO(urllib.request.urlopen(request).read())
				image = wx.Image(stream, wx.BITMAP_TYPE_ANY)
				
			# Use local image
			else:
				path = Path(source)
				if not path.exists() \
				or not path.is_file():
					raise FileNotFoundError(source)

				image = wx.Image(self.image_directory / path)

		except (FileNotFoundError, HTTPError, URLError, PermissionError):
			# If anything goes wrong
			# with finding and rendering the image,
			# render the alt text in stead.
			
			if alt_text:
				self.BeginTextColour('grey')
				self.BeginItalic()
				self.WriteText(alt_text)
				self.EndItalic()
				self.EndTextColour()

		else:
			# Scale image
			if width and height:
				# Resize to new width and height
				image.Rescale(int(width), int(height))

			elif width and height is None:
				# Maintain aspect ratio
				ratio = int(width) / image.GetWidth()
				height = image.GetHeight() * ratio
				# Resize to new width and matching height
				image.Rescale(int(width), int(height))

			elif width is None and height:
				# Maintain aspect ratio
				ratio = int(height) / image.GetHeight()
				width = image.GetWidth() * ratio
				# Resize to new height and matching width
				image.Rescale(int(width), int(height))

			# Render image
			super().WriteImage(image)
			

class Markdown(wx.Panel):
	"""
	`Markdown` is a panel that renders Markdown using Rich Text.
	"""

	def __init__(self, parent,
		files_directory: str = "",
		allow_download_images: bool = False,
		*args, **kwargs
	) -> None:

		super().__init__(parent, *args, **kwargs)
		
		self.opened_lists = [None]

		self.rtc = ExtendedRichText(self,
			files_directory=files_directory,
			allow_download_images=allow_download_images)
		self.rtc.SetEditable(False)  # Make it read-only
		
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(self.rtc, proportion=1, flag=wx.EXPAND)
		self.SetSizer(self.sizer)

		self.rtc.Bind(wx.EVT_TEXT_URL, self.handle_url)

		self.rtc.SetBackgroundColour((64, 64, 64, 255))
		self.rtc.SetForegroundColour((232, 232, 232, 255))

	def handle_url(self, event: rt.RichTextEvent) -> None:
		"""Open link in webbrowser."""
		webbrowser.open(event.GetString())
		
	def AddContent(self, text: str) -> None:
		"""
		Add Markdown content.
		"""

		# Set scale for spacing and such
		scale = self.rtc.GetCharHeight() // 3.5
		self.rtc.SetDimensionScale(scale)
		self.rtc.SetMargins(0, 0)
		
		if '\\.' in text:
			text = text.replace('\\.', '&bsol;.')

		# Parse Markdown into HTML
		html = markdown.markdown(text)
		html = html.replace('&amp;', '&')
		html = html.replace('&bsol;.', '\\.')
		html = html.replace('</li>\n', '</li>')
		soup = bs4.BeautifulSoup(html, 'html.parser')

		self.rtc.BeginTextColour(self.rtc.GetForegroundColour())
		self.rtc.BeginParagraphSpacing(before=0, after=0)
		# Generate Rich Text from HTML
		self._generate_richtext(soup)
		self.rtc.EndParagraphSpacing()
		self.rtc.EndTextColour()

	def _generate_richtext(self, tag: bs4.Tag | str) -> None:
		"""
		Generate Rich Text from HTML.
		
		Recursively iterate over HTML tree and perform
		Rich Text operations based on the discovered tags.
		"""

		if isinstance(tag, str):
			self.rtc.WriteText(str(tag))
		else:
			# Line break
			if tag.name == 'br' or tag.name == '<br />':
				self.rtc.LineBreak()
				return
			# Image
			if tag.name == 'img' and tag.has_attr('src'):
				self.rtc.WriteImage(
					tag['src'], tag.get('alt', ""),
					width=tag.get('width'),
					height=tag.get('height'))
				return
			
			
			# [OPEN TAG CONTEXT]

			# Bold text
			if tag.name == 'strong':
				self.rtc.BeginBold()
			# Italic text
			elif tag.name == 'em':
				self.rtc.BeginItalic()
			# Paragraph
			elif tag.name == 'p':
				self.rtc.BeginParagraph()
				pass
			# Blockquote
			elif tag.name == 'blockquote':
				self.rtc.BeginBlockquote()
			# Code
			elif tag.name == 'code':
				self.rtc.BeginCode()
			# Heading 1
			elif tag.name == 'h1':
				self.rtc.BeginHeading1()
			# Heading 2
			elif tag.name == 'h2':
				self.rtc.BeginHeading2()
			# Heading 3
			elif tag.name == 'h3':
				self.rtc.BeginHeading3()
			# Heading 4
			elif tag.name == 'h4':
				self.rtc.BeginHeading4()
			# Heading 5
			elif tag.name == 'h5':
				self.rtc.BeginHeading5()
			# Heading 6
			elif tag.name == 'h6':
				self.rtc.BeginHeading6()
			# Link
			elif tag.name == 'a' and tag.has_attr('href'):
				self.rtc.BeginLink(tag.attrs['href'])
			# Unordered list
			elif tag.name == 'ul':
				self.opened_lists.append(tag.name)
				self.rtc.BeginUnorderedList()
			# Ordered list
			elif tag.name == 'ol':
				self.opened_lists.append(tag.name)
				self.rtc.BeginOrderedList()
			# List item
			elif tag.name == 'li':
				if self.opened_lists[-1] == 'ul':
					self.rtc.BeginUnorderedListItem()
				elif self.opened_lists[-1] == 'ol':
					self.rtc.BeginOrderedListItem()


			# [RECUR INTO CHILDREN]
			for child in tag.children:
				self._generate_richtext(child)


			# [CLOSE TAG CONTEXT]

			# Bold text
			if tag.name == 'strong':
				self.rtc.EndBold()
			# Italic text
			elif tag.name == 'em':
				self.rtc.EndItalic()
			# Paragraph
			elif tag.name == 'p':
				self.rtc.EndParagraph()
				pass
			# Blockquote
			elif tag.name == 'blockquote':
				self.rtc.EndBlockquote()
			# Code
			elif tag.name == 'code':
				self.rtc.EndCode()
			# Heading 1
			elif tag.name == 'h1':
				self.rtc.EndHeading1()
			# Heading 2
			elif tag.name == 'h2':
				self.rtc.EndHeading2()
			# Heading 3
			elif tag.name == 'h3':
				self.rtc.EndHeading3()
			# Heading 4
			elif tag.name == 'h4':
				self.rtc.EndHeading4()
			# Heading 5
			elif tag.name == 'h5':
				self.rtc.EndHeading5()
			# Heading 6
			elif tag.name == 'h6':
				self.rtc.EndHeading6()
			# Link
			elif tag.name == 'a' and tag.has_attr('href'):
				self.rtc.EndLink()
			# Unordered list
			elif tag.name == 'ul':
				self.rtc.EndUnorderedList()
				self.opened_lists.pop()
			# Ordered list
			elif tag.name == 'ol':
				self.rtc.EndOrderedList()
				self.opened_lists.pop()
			# List item
			elif tag.name == 'li':
				if self.opened_lists[-1] == 'ul':
					self.rtc.EndUnorderedListItem()
				elif self.opened_lists[-1] == 'ol':
					self.rtc.EndOrderedListItem()


	def BeginBackgroundColour(self, colour: wx.Colour) -> None:
		"""
		Begins background colour.
		"""
		highlight_attr = rt.RichTextAttr()
		highlight_attr.SetBackgroundColour(colour)
		self.rtc.BeginStyle(highlight_attr)

	def EndBackgroundColour(self) -> None:
		"""
		Ends background colour.
		"""
		self.rtc.EndStyle()