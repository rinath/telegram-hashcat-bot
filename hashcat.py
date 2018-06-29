import pexpect
import time
import traceback
from PIL import Image, ImageDraw, ImageFont

class Hashcat:

	STATUS_RUNNING = 0
	STATUS_STOPPED = 1
	STATUS_DIFFERENT_USER = 2

	def __init__(self):
		self.filename = 'queue.txt'
		self.process = None
		self.chat_id = None
		self.buffer = []
		try:
			open(self.filename, 'r')
		except:
			open(self.filename, 'w')

	def add_to_queue(self, cmd, chat_id):
		with open(self.filename, 'a') as f:
			f.write(str(chat_id) + ' ' + cmd + '\n')

	def update(self):
		if self.process is not None and self.process.isalive():
			while True:
				try:
					self.process.expect('\n')
					txt = self.process.before.decode('ascii', errors='ignore').rstrip()
					self.buffer.append(txt)
					print('>>>>' + txt)
					if len(self.buffer) > 200:
						self.buffer = self.buffer[100:]
				except pexpect.TIMEOUT:
					break
				except:
					break
		else:
			queries = self.parse_queue(True)
			if queries is not None:
				print('Hashcat.update: queries:' + str(queries))
				self.process = pexpect.spawn(queries[1], timeout=0.1)
				self.chat_id = int(queries[0])
				print('Hashcat.update: chat_id:', self.chat_id)

	def get_status(self, chat_id):
		if self.chat_id == chat_id:
			if self.process is not None and self.process.isalive():
				return self.STATUS_RUNNING
			else:
				return self.STATUS_STOPPED
		else:
			return self.STATUS_DIFFERENT_USER

	def get_queue_position(self, chat_id):
		if chat_id == self.chat_id:
			return (0, 0)
		else:
			with open(self.filename, 'r') as f:
				queries = f.read().splitlines()
				count = 0
				first = -1
				for i in range(len(queries)):
					if int(queries[i].split()[0]) == chat_id:
						count += 1
						if first == -1:
							first = i
				return (first, count)
			return (-1, 0)

	def parse_queue(self, remove_first=False):
		with open(self.filename, 'r+') as f:
			queries = f.read().splitlines()
			if len(queries) > 0:
				ans = [query.split(' ', 1) for query in queries]
				if remove_first:
					print('Hashcat.parse_queue: queries[1:] =', queries[1:])
					f.seek(0)
					f.write('\n'.join(queries[1:]))
					f.truncate()
					return ans[0]
				return ans
		return None

	def save_screenshot(self, filename):
		if self.process is None or not self.process.isalive():
			print('Hashcat.save_screenshot: hashcat is not running')
			return False
		rows = 26
		if len(self.buffer) >= rows:
			text = '\n'.join(self.buffer[-rows:])
			#print(self.buffer[-rows:])
		else:
			text = '\n'.join(self.buffer)
			#print(self.buffer)
		fnt = ImageFont.truetype('DejaVuSans.ttf', 15)
		tmp_img = Image.new('RGB', (1,1))
		d = ImageDraw.Draw(tmp_img)
		(width, height) = d.textsize(text, fnt)
		if width < 10 and height < 10:
			print('terminal screenshot cannot be saved, width and height is too small')
			return False
		if width > 600:
			width = 600
		text_size = (width + 20, height)
		img = Image.new('RGB', text_size, color='black')
		d = ImageDraw.Draw(img)
		d.text((10, 0), text, font=fnt, fill = 'white')
		img.save(filename)
		return True

	def send_keystroke(self, key):
		if self.process is not None and self.process.isalive():
			print('Hashcat.send_keystroke: ' + key)
			self.process.send(key)
			time.sleep(0.3)
