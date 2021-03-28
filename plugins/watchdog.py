#!/usr/bin/env python3
#...........................................................
#. e-Not Bot Watchdog Plugin
#. Author: Kevin C. Kurtz - kevinckurtz.com
#. Date: 2021-03-24
#. Version: 1
#. Intent: Make sure that e-Not Bot is running
#...........................................................

import psutil
import logging
import time
import subprocess
import sys
from setproctitle import setproctitle

#This is the normal setup. If we are main we have to import and log a little differently. WE also have to check again later because some things need definitions at the beginning and omse at the end.
if __name__ != '__main__':
	#Logging setup
	logger = logging.getLogger(__name__)
	#pull in some identifying variables
	from config_file import botPath

else: ##This means the program is main.
	#we don't want the logger name to be __main__. Looks bad in the logs.
	logger = logging.getLogger('Watchdog')
	logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

	#get path to eNotBot. Can't pull from cfg because its a directory up. Best to just pass it in. Relative imports don't work if you can't run as a package, etc.
	#we could do this with path variables, or with getting the current working directory, but those can be overridden or messed up. arguments are easy and pretty full-proof for dist.
	#"Why not just take the calling command, sys.argvp[0]. The path is in there by removing watchdog.py". It is. the way I'm calling it that would work. What if someone wants to 
	#start the watchdog from somewhere else and doesn't use the full path to call it. Or changes its name! Thinking ahead, this is the more universal solution. Stop trying to shoot holes in my methods.
	if len(sys.argv) > 1:
		botPath = sys.argv[1]
	else:
		logger.info('A bot path wasn\'t specified. Shutting down.')
		exit() #if we don't have a path to use to open eNotBot, we really don't need to be running.



def main():
	while True:
		try:
			#Better to wait a few minutes even if the program is stopped. If it failed to run we don't want to be in an infinite short loop.
			time.sleep(300)

			running = False
			#logger.info('Started running watchdog loop.')

			#Iterate over the all the running process
			for proc in psutil.process_iter():
					#logger.info(f'Checking {proc.name()}')
					# Check if process name contains the given name string. This fails a lot.
					try:
						if proc.name() == 'enotbot':
								running = True
								#logger.info('eNotBot is currently running.')
								break #no reason to check the rest, is there? Restart loop
					except: #expect this a lot, probably best to ignore this.
						#logger.info('Checking process name failed.')
						pass

			if running == False:
				#start the program because its not running
				cmd = [f'{botPath}/eNotBot.py 1>>{botPath}/log.log 2>&1']
				proc = subprocess.Popen(cmd, shell=True)
				logger.info('Watchdog has started eNotBot. It was not running.')
									
		except:
			logger.exception('Error checking for process running or restarting process.')

def start():
	try:
			running = False

			#Iterate over the all the running process
			for proc in psutil.process_iter():
							# Check if process name contains the given name string.
							try:
								if proc.name() == 'enotbot_wd':
										running = True
										logger.info('eNotBot init attempted to start Watchdog, but it is already running.')
							except:
								#logger.info('Checking process name failed in start.')
								pass

			if running == False:
				#start the watchdog as its own process because its not running. We don't want it to run as part of the base program or it'll crash with it.
				cmd = [f'{botPath}/plugins/watchdog.py {botPath} 1>>{botPath}/log.log 2>&1']
				proc = subprocess.Popen(cmd, shell=True)
				#logger.info('Watchdog started from eNotBot init')

	except:
		logger.exception('Error starting the watchdog from init.')

#Have to check again here if we are main. Can't call main before, because we haven't defined all our functions yet.
#And can't do the imports later because there's a chance we need some of that info to get here (we didn't when I wrote this, but that changes)
if __name__ == "__main__":
	setproctitle('enotbot_wd')
	logger.info('Watchdog started in it\'s own process.')
	main()