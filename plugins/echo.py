#...........................................................
#. Echo Command Plugin
#. Author: Kevin C. Kurtz
#. Date: 2021-03-17
#. Version: 1
#. Intent: echo from the bot, to the reply channel or another channel
#...........................................................

#necessary local imports
import logging

#pull in some identifying variables
import config_file as cfg

#Logging setup
logger = logging.getLogger(__name__)

#create a non-existant client. We'll set this in init when we have a client.
client = None

#echo command
async def echo(message):
	if message.content.startswith('!echo'):
		try:
			#check you're an admin. Don't want rando's making the bot talk.
			if message.author.id == cfg.myID:
				#the -c switch can be used to specify a channel. This allows you to DM the bot and get it to echo in another location using the channel ID.
				if message.content.startswith('!echo -c'):
					#split the first 3 spaces. This will leave us '!echo' '-c' 'channelID' 'full_message_with_no_splitting'
					args = message.content.split(' ',3)
					channel = client.get_channel(int(args[2]))
					msg = args[3]
					await channel.send(msg)
				else:
					#normal echo. Remove the '!echo' and send the message back on the channel.
					msg = message.content.split(' ',1)[1]
					await message.channel.send(msg)
		except:
			logger.exception('echo command threw an exception')

if __name__ == "__main__":
	#if we aren't logged into discord, this plugin would be pretty useless
	print('This plugin currently has no capabilities standalone.')