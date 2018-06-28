import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup
import time
import subprocess
from pprint import pprint
import pathlib
from hashcat import Hashcat
import os

TYPE_DICTIONARY = 0
TYPE_HASHFILES = 1
TYPE_OPTIONS = 2

class Chat:

	def __init__(self, chat_id, bot, hashcat):
		self.bot = bot
		self.chat_id = chat_id
		self.exec_command = ''
		self.hashcat = hashcat
		self.directory = ['wordlists/', 'documents/' + str(chat_id) + '/']
		self.potfile = 'potfile.pot'
		self.chooser = Chooser(chat_id, bot, self, self.potfile)
		for path in self.directory:
			os.makedirs(path, exist_ok=True)
		self.options = ['', '', '']

	def on_message_received(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg)
		if content_type == 'text':
			print('on_message_received: ', msg['text'])
			if 'entities' in msg:
				for entity in msg['entities']:
					if entity['type'] == 'bot_command':
						self.on_command_received(msg['text'][entity['offset']:])
			elif self.chooser.is_choosing():
				self.chooser.update_chooser(msg, is_callback=False)
		elif content_type == 'document':
			file_id = msg['document']['file_id']
			file_name = msg['document']['file_name']
			print('file_id =', file_id, 'fil_name =', file_name)
			if file_name.split('.')[-1] == 'txt':
				self.bot.download_file(file_id, self.directory[TYPE_DICTIONARY] + file_name)
				self.chooser.choose(file_name, TYPE_DICTIONARY, append_directory=True)
			else:
				self.bot.download_file(file_id, self.directory[TYPE_HASHFILES] + file_name)
				self.chooser.choose(file_name, TYPE_HASHFILES, append_directory=True)

	def on_callback_received(self, msg):
		command = msg['data'].split()[0]
		if self.chooser.is_choosing():
			self.chooser.update_chooser(msg)
		elif command == 'exec':
			self.on_command_received('/cmd ' + self.exec_command)
		elif command == '/status':
			self.on_command_received(msg['data'])
		elif command == 'cleanpotfile':
			#os.system('rm ' + self.directory[TYPE_HASHFILES] + self.potfile)
			open(self.directory[TYPE_HASHFILES] + self.potfile, 'w').close()
			self.bot.sendMessage(self.chat_id, 'Potfile has been deleted')

	def on_command_received(self, command):
		command = command.split(' ', 1)
		comm = command[0]
		if command[0] == '/start':
			self.bot.sendMessage(self.chat_id, 'Hello there, I\'m hashcat bot v0.2. Send /begin command or "/cmd hashcat [options]".' + \
				'All uploaded .txt files are in ' + self.directory[TYPE_DICTIONARY] + ' and other files are in ' + \
				self.directory[TYPE_HASHFILES])
		elif command[0] == '/begin':
			self.options = ['', '', '']
			self.chooser.send_chooser(TYPE_HASHFILES, self.directory[TYPE_HASHFILES])
		elif command[0] == '/status':
			if len(command) > 1:
				self.hashcat.send_keystroke(command[1])
				time.sleep(0.1)
			screnshot = 'terminal.png'
			if self.hashcat.save_screenshot(screnshot):
				buttons = ['s', 'p', 'r', 'b', 'c', 'q']
				keyboard = [[InlineKeyboardButton(text=button, callback_data='/status ' + button) for button in buttons]]
				self.bot.sendPhoto(self.chat_id, photo=open(screnshot, 'rb'), reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
			else:
				if self.hashcat.get_status():
					self.bot.sendMessage(self.chat_id, 'No terminal output yet')
				else:
					self.bot.sendMessage(self.chat_id, 'Hashcat is not running. Send /status or /potfile comands')
		elif command[0] == '/potfile':
			text = ''
			try:
				file = open(self.directory[TYPE_HASHFILES] + self.potfile, 'r')
				text = file.read()
			except:
				open(self.directory[TYPE_HASHFILES] + self.potfile, 'w')
			#text = subprocess.check_output('cat ' + self.directory[TYPE_HASHFILES] + self.potfile, shell=True).decode('utf-8')
			lines = text.splitlines()
			passwords = [' '.join(x.split(':')[3:5]) for x in lines]
			text = '\n'.join(passwords)
			if len(text) < 3:
				self.bot.sendMessage(self.chat_id, 'Potfile is empty')
			else:
				self.bot.sendMessage(self.chat_id, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=
					[[InlineKeyboardButton(text='clean', callback_data='cleanpotfile')]]
				))
		elif command[0] == '/cmd' and len(command) > 1:
			print('executing: ' + command[1])
			self.hashcat.add_to_queue(command[1], self.chat_id)
			self.bot.sendMessage(self.chat_id, 'Wait a couple of secs and then you can send /status or /potfile commands')
		else:
			self.bot.sendMessage(self.chat_id, 'unrecognized command')

	def on_choosen(self, data, type):
		print('on_choosen:', data, 'type:', type)
		self.options[type] = data
		for mType in range(3):
			if self.options[mType] == '':
				if mType == TYPE_OPTIONS:
					self.chooser.send_chooser(mType, None)
				else:
					self.chooser.send_chooser(mType, self.directory[mType])
				return
		self.exec_command = 'sudo hashcat ' + self.options[TYPE_OPTIONS] + ' --status-timer 1 --status --potfile-path="'
		self.exec_command += self.directory[TYPE_HASHFILES] + self.potfile + '" "'
		self.exec_command += self.options[TYPE_HASHFILES] + '" "' + self.options[TYPE_DICTIONARY] + '"'
		self.bot.sendMessage(self.chat_id, '<code>' + self.exec_command + '</code>', parse_mode='HTML',
			reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Execute', callback_data='exec')]]))

class Chooser:

	def __init__(self, chat_id, bot, chat, potfile):
		self.chat_id = chat_id
		self.bot = bot
		self.chat = chat
		self.set(TYPE_HASHFILES, None)
		self.choosing = False
		self.directory = None
		self.potfile = potfile

	def set(self, type, directory):
		print('set chooser type as:', type)
		self.directory = directory
		self.type = type
		self.choosing = True
		if type == TYPE_HASHFILES:
			self.text_primary = 'Choose available hashfiles or upload your own (up to 20MB)'
			self.text_secondary = 'Upload hashfile (up to 20MB)'
			self.text_choosen = 'Choosen hashfile: '
		elif type == TYPE_DICTIONARY:
			self.text_primary = 'Write password mask, choose dictionary or upload dictionary (up to 20MB)'
			self.text_secondary = 'Write password mask or upload dictionary (up to 20MB)'
			self.text_choosen = 'Choosen dictionary/mask: '

	def send_chooser(self, type, directory):
		print('send_chooser type: ' + str(type))
		self.set(type, directory)
		if type == TYPE_OPTIONS:
			self.bot.sendMessage(self.chat_id, 'Set options (ex: <code>--force -m 2500</code>)', parse_mode='HTML')
		elif not self.isEmpty(self.directory):
			file_list = self.show_files(self.directory)
			self.bot.sendMessage(self.chat_id, self.text_primary + file_list, parse_mode='HTML',
				reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
					InlineKeyboardButton(text='Choose', callback_data='Chooser')
			]]))
		else:
			self.bot.sendMessage(self.chat_id, self.text_secondary)

	def update_chooser(self, msg, is_callback=True):
		if is_callback:
			if msg['data'] == 'Chooser':
				file_list = subprocess.check_output('ls ' + self.directory + ' -I ' + self.potfile, shell=True).decode('utf-8').splitlines()
				print('file_list:', file_list)
				keyboard = [[InlineKeyboardButton(text=file, callback_data=file)] for file in file_list]
				self.bot.editMessageText((msg['message']['chat']['id'], msg['message']['message_id']),
					text=self.text_primary, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
			else:
				self.choose(msg['data'], self.type, append_directory=True)
		else:
			self.choose(msg['text'], self.type, quiet=True)

	def choose(self, data, type, quiet=False, append_directory=False):
		self.set(type, self.directory)
		self.choosing = False
		if append_directory:
			data = self.directory + data
		if not quiet:
			self.bot.sendMessage(self.chat_id, self.text_choosen + '<code>' + data + '</code>', parse_mode='HTML')
		self.chat.on_choosen(data, self.type)

	def is_choosing(self):
		return self.choosing

	def isEmpty(self, directory):
		txt = subprocess.check_output('ls ' + directory + ' -I ' + self.potfile, shell=True)
		print('Chooser.isEmpty: ', txt)
		if len(txt) < 3:
			return True
		return False

	def show_files(self, directory):
		file_names = subprocess.check_output('ls ' + directory + ' -I ' + self.potfile, shell=True).decode('utf-8').splitlines()
		file_sizes = subprocess.check_output('ls -lah ' + directory + ' -I ' + self.potfile +
			' | grep ^- | awk \'{print $5}\'\n', shell=True).decode('utf-8').splitlines()
		print('file_names:', file_names)
		print('file_sizes:', file_sizes)
		file_list = ''
		for i in range(len(file_names)):
			file_list += '{:5s} {}\n'.format(file_sizes[i], file_names[i])
		print('dir =',directory,'len(file_list):', len(file_list))
		if len(file_list) < 3:
			return None
		return '\n<pre>' + file_list + '</pre>'

class HashBot:

	def __init__(self, token):
		self.chats = {}
		self.bot = telepot.Bot(token)
		self.hashcat = Hashcat()
		print('Hashbot.__init__(): hashcat.update()')

	def handle_message(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg)
		if chat_id not in self.chats:
			self.chats[chat_id] = Chat(chat_id, self.bot, self.hashcat)
		self.chats[chat_id].on_message_received(msg)

	def handle_callback(self, msg):
		content_type, chat_type, chat_id = telepot.glance(msg['message'])
		if chat_id not in self.chats:
			self.chats[chat_id] = Chat(chat_id, self.bot, self.hashcat)
		self.chats[chat_id].on_callback_received(msg)
		
	def start(self):
		MessageLoop(self.bot, {'chat': self.handle_message, 'callback_query': self.handle_callback}).run_as_thread()
		while 1:
			self.hashcat.update()
			self.hashcat.get_status()
			time.sleep(5)

mybot = HashBot('536267386:AAGJUhuC1LQe6avvx79A2xlqpQLArQ_jumQ')
mybot.start()
