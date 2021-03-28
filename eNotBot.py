#!/usr/bin/env python3
#  #...........................................................
#. e-Not Bot
#. Author: Kevin C. Kurtz - kevinckurtz.com
#. Date: 2018-11-09
#. Version: 1
#. Intent: automate communication on several platforms
#...........................................................

#It is HIGHLY advised you run this in a virtual environment.
#command 'source /path/to/bot/env/bin/activate && /path/to/bot/eNotBot.py 1>>/path/to/bot/log.log 2>&1 &'
#I run this in a cron job on boot. It can be a hassle.
#I activate my virtual environement first, but since that only works in bash and not sh, and I don't
#want to force all my crons into bash, I just call from the bash command.
#/usr/bin/env bash -c 'source /path/to/bot/env/bin/activate && /path/to/bot/eNotBot.py 1>>/path/to/bot/log.log 2>&1'

import discord
import asyncio
import logging
import subprocess
import signal
from setproctitle import setproctitle


#Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

#pull in some identifying variables
import config_file as cfg

#import our commands and other capabilities to the bot
import plugins

#our interface for the discord API. Client contains all our settings and connection
client = discord.Client()
#gives the client to all the plugins who need it
plugins.client(client)

@client.event
async def on_message(message):
	#save some time. Not processing messages without the switch. Otherwise this check happens on every message in the server I believe.
	if message.content.startswith('!') == False:
		return
	# we do not want the bot to reply to itself
	if message.author == client.user:
		return
	#this is a channel ignore list, if its in one of these channels we don't even think about processing it
	for ignoredChannel in cfg.ignoredChannels:
		if message.channel.id == ignoredChannel:
			return

	#bot test, let's not put this in a plugin. Should always be accessible.
	if message.content.startswith('!hello'):
		msg = f'Hello, {message.author.mention}'
		await message.channel.send(msg)

	if message.content.startswith('!help'):
		msg = '!hello tests the bot. \n!valheim shows you the domian/ip and login info for the dedicated server. \n\'!valheim update\' and \'!valheim world\' should be used with caution\n\nPlease check out https://vps2.kevinckurtz.com/bot-faq.html for a full explanation of all commands.'
		await message.channel.send(msg)

	if message.content.startswith('!shutdown'):
		msg = f'{message.author.mention} has instructed us to shutdown. Logging off...'
		await message.channel.send(msg)
		if message.author.id == cfg.myID:
			#This means we want to kill the watchdog or other processes too if they are running
			if message.content == '!shutdown full': 
				proc = subprocess.Popen(['pkill','notbot_wd','-KILL'])
				logger.info('Watchdog killed by shutdown full.')

			logger.info('Client shutdown by admin commmand.')
			await client.logout()
		else:
			msg = f'Hey. Wait. You\'re not <@{cfg.myID}>. Get outta here. You can\'t do that.'
			await message.channel.send(msg)
			logger.info(f'{message.author.name} tried to shut down the bot.')


	#send the message to every command
	for command in plugins.commands.values():
		await command(message)



#catch for login event
@client.event
async def on_ready():
	logger.info(f'Logged into Discord as: {client.user.name}')
	#send the admin a DM letting them know we are logged in (so they are alerted on an accidental restart or other problem)
	user = await client.fetch_user(cfg.myID)
	await user.send('bot booted and logged in.')
	

if __name__ == "__main__":
	#set the name of the process. We need this if we are using Watchdog.
	setproctitle('enotbot')
	logger = logging.getLogger('eNotBot') #__main__ is a really ugly title in the logs.
	logger.info('Bot stated as main. Process named enotbot. Booting...')

	#I never run this as blocking on my command line, but found that if I do, Ctrl-c didn't work for some reason
	#Keyboard interrupt was completely ignored
	#This restores the default Ctrl+C signal handler, which just kills the process (doesn't work...)
	#signal.signal(signal.SIGINT, signal.SIG_DFL)
	
	#The app is single threaded and uses Asyncio.
	#The async webframework I've chosen doesn't need enough CPU time to bother with multiprocessing or threading and it makes communication easy. No need for hypercorn.
	#for clarity, discord is called from run and not start. We are using it's built in event loop through asyncio and just awaiting the webserver and other async function
	#we add the webserver as a separate coroutine in that loop using run_task instead of run. It is asyncronous start without an event loop. We shove it in the default
	#loop with create_task and then start the dicord client with the loop function as well. Haven't tested if we can just call client.run or if that makes its own loop.
	#discord also has a client.loop.something that I think will let you add a task before you run it. This worked, so I kept it. There's a few options for asyncio co-routines.

	#Get the default event loop for asyncio. Since we don't have one running yet, my current understanding is we should get one (create one) and then add tasks to it. Later, asyncio.create_task will just throw it in the running loop.
	loop = asyncio.get_event_loop()
	#add a task in the loop for the quart server, using run_task instead of run. Run creates its own loop
	loop.create_task(plugins.webserver.app.run_task(cfg.webserverIP,cfg.webserverPort))
	#add the discord stak and run it until it stops. This should kill the webserver also on shutdown command. We should find a way to do that cleanly later.
	loop.run_until_complete(client.start(cfg.discordToken))


