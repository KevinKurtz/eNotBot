#...........................................................
#. Global configuration variables and settings
#. Author: Kevin C. Kurtz
#. Date: 2021-03-17
#. Version: 1
#. Intent: Store all our secrets
#...........................................................
#  every module can/should import this

#run command
#source /path/to/bot/botenv/bin/activate && /path/to/bot/eNotBot.py 1>>/path/to/bot/log.log 2>&1 &

#path to program
botPath = '/path/to/bot'

#discord API token. Essentially our apps password
discordToken = ''

#myID is the owner's discord ID. Lets you check for admin privs and get pinged when it breaks
myID = 12345678910

#path string to a script that turns SSH on and back off by timer.
sshScriptPath = '/home/user/scripts/ssh.sh'

#url of the mongo server
mongoServer = 'mongodb://user:pass@localhost:27017/'

#strava
stravaSecret = ''
stravaID = 12345
stravaRedirectURI = 'https://website.com/bot/strava/auth'
stravaSubURL = 'https://website.com/bot/strava/sub'

#Channels to ignore
ignoredChannels = [12345678910,1230456793882]

#webserver configuration
webserverIP = '127.0.0.1'
webserverPort = '1234

#Valheim
valheimServer = 'website.com'
valheimPassword = 'Password'
valheimWorld = 'WorldName'
valheimDownload = 'website.com'