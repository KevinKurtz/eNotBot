
#...........................................................
#. Valheim Command Plugin
#. Author: Kevin C. Kurtz
#. Date: 2021-03-17
#. Version: 1
#. Intent: Control the server's Valheim dedicated server
#...........................................................
#This requires that your valheim server runs in its own systemctl and that you have it running under the username steam in most linux distros.
#Your bot account also needs sudo privledges for these commands (I give it for just these commands in visudo)
#This plugin is more 'me' specific than most.

#necessary local imports
import socket
import subprocess
import asyncio
import logging

#pull in some identifying variables
import config_file as cfg

#Logging setup
logger = logging.getLogger(__name__)

#Valheim plugin
async def valheim(message):
	if message.content == '!valheim':
		#pull the IP of the server
		msg = f'The Valheim server is {cfg.valheimServer} or {socket.gethostbyname(cfg.valheimServer)}'
		await message.channel.send(msg)
		try:
			#We are going to attempt to see if the server is running and what it's name is. I don't know what any of this "does" so to say. I used wireshark to analyze the connection packets from steam
			#so I could pretend to be a client connecting and get the info. It works. I send this byte string and it spits back the servername and responds if its online. Hacky, but works.
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
			s.settimeout(2)
			s.sendto(bytes.fromhex('ff ff ff ff 54 53 6f 75 72 63 65 20 45 6e 67 69 6e 65 20 51 75 65 72 79 00'), (cfg.valheimServer, 2457))
			data, address = s.recvfrom(4096)
			if data:
				data = data.decode('cp437')
				data = data[6:]
				data = data.split('\x00')
				data = data[0]
				msg = f'It is ONLINE and the server name is \'{data}\'. The password is \'{cfg.valheimPassword}\'.'
			else:
				msg = 'It is OFFLINE. (Probably. No data.)'
		except:
			msg = 'It is OFFLINE. (Probably. Timeout on ping.)'
			logger.exception('Valheim server didn\'t respond to ping')
		await message.channel.send(msg)

  #call all the sub commands in this module and let them sort out their own messages/switches
	await update(message)
	await restart(message)
	await start(message)
	await world(message)

async def update(message):
	if message.content == '!valheim update':
		#pretty self explanatory. Shuts down the server. Updates it. then starts it again.
		try:
			msg = 'Attempting to update server. Please wait.'
			await message.channel.send(msg)
			cmd = ['sudo', 'systemctl', 'stop', 'valheimserver']
			proc = subprocess.Popen(cmd)
			proc.wait()
			cmd = ['sudo', '/home/steam/steamcmd', '+login', 'anonymous', '+force_install_dir', '/home/steam/valheimserver', '+app_update', '896660', 'validate', '+exit']
			proc = subprocess.Popen(cmd)
			proc.wait()
			cmd = ['sudo', 'systemctl', 'start', 'valheimserver']
			proc = subprocess.Popen(cmd)
			msg = 'Server updated and restarted. (takes ~15 more seconds to boot)'
		except:
			msg = f'Something exploded. <@{cfg.myid}> HELP!'
			logger.exception('failed to update valheim')
		await message.channel.send(msg)

async def restart(message):
	if message.content == '!valheim restart':
		try:
			msg = 'Attempting to restart server. Please wait.'
			await message.channel.send(msg)
			cmd = ['sudo', 'systemctl', 'stop', 'valheimserver']
			proc = subprocess.Popen(cmd)
			proc.wait()
			cmd = ['sudo', 'systemctl', 'start', 'valheimserver']
			proc = subprocess.Popen(cmd)
			msg = 'Server restarted. (takes ~15 more seconds to boot)'
		except:
			msg = f'Something exploded. <@{cfg.myid}> HELP!'
			logger.exception('failed to restart valheim')
		await message.channel.send(msg)

async def start(message):
	if message.content == '!valheim start':
		try:
			msg = 'Attempting to start server. Please wait.'
			await message.channel.send(msg)
			cmd = ['sudo', 'systemctl', 'start', 'valheimserver']
			proc = subprocess.Popen(cmd)
			msg = 'Server started. (takes ~15 more seconds to boot if it wasn\'t already running)'
		except:
			msg = f'Something exploded. <@{cfg.myid}> HELP!'
			logger.exception('failed to start valheim')
		await message.channel.send(msg)

async def world(message):
	if message.content == '!valheim world':
		#This command actually zips up the world files and moves them over to the webhost for someone to download and backup.
		try:
			msg = 'Packaging up the whole wide world.'
			await message.channel.send(msg)
			cmd = ['zip', '-j', '/var/www/html/valheim_world.zip', f'/home/steam/.config/unity3d/IronGate/Valheim/worlds/{cfg.valheimWorld}.fwl', f'/home/steam/.config/unity3d/IronGate/Valheim/worlds/{cfg.valheimWorld}.db']
			proc = subprocess.Popen(cmd)
			proc.wait()
			msg = f'{message.author.mention} can temporarily download the world at http://{cfg.valheimDownload}/valheim_world.zip'
			await message.channel.send(msg)
			#we don't want this download to be available forever. So let's sleep (non-blocking) for 3min then delete the file.
			await asyncio.sleep(180)
			cmd = ['rm', '/var/www/html/valheim_world.zip']
			proc = subprocess.Popen(cmd)
		except:
			msg = f'Something exploded. <@{cfg.myid}> HELP!'
			await message.channel.send(msg)
			logger.exception('Something broke in Valheim world download command.')

if __name__ == "__main__":
	#It should. Maybe. But this stuff is pretty easy to do from command line... so why? Maybe for the world file, but it relies on discord i/o
	print('This plugin currently has no capabilities standalone.')