#init file for the plugins module
#comment out any plugins you don't want. They typically don't depend on each other. There's some code in main that requires watchdog. and strava/webserver are connected.

#a dictionary to hold all our commands. This makes it easy for the bot to send messages to every command without cluttering our code.
commands = {}

#import for valheim plugin. imports the plugin file and then saves the main command to the commands dictionary
import plugins.valheim
commands['valheim'] = plugins.valheim.valheim

#import for ssh plugin. imports the plugin file and then saves the main command to the commands dictionary
import plugins.ssh
commands['ssh'] = plugins.ssh.ssh

#import for echo plugin. imports the plugin file and then saves the main command to the commands dictionary
import plugins.echo
commands['echo'] = plugins.echo.echo

#import for test plugin. imports the plugin file and then saves the main command to the commands dictionary
import plugins.strava
commands['strava'] = plugins.strava.strava

#import for webserver plugin. Imports the plugin file for the web server. 
import plugins.webserver

#import for watchdog plugin. Import and start the watchdog program
import plugins.watchdog
plugins.watchdog.start()



#give the client to whoever needs it
def client(client):
	plugins.echo.client = client
	plugins.strava.client = client