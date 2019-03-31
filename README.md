# telegram-hashcat-bot
A telegram bot which is an interface for hashcat, hash cracking program.
This bot was written during internship in "ЦАРКА, Центр Анализа и Расследования Кибер Атак" in 2018
# commands
There are two ways of sending commands:  
/begin - Easy gui version  
Or  
/cmd hashcat [options]... files...  
Uploaded .txt files are stored in wordlists/ and all other files are in documents/<chat_id>/  
  
/potfile - to see potfile  
/status - to get execution status  
# Installing
```
pip3 install telepot
pip3 install pillow
pip3 install pexpect
```
# Runing
```
sudo python3 bot.py
```
