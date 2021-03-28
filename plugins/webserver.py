#...........................................................
#. Webserver Endpoint Plugin
#. Author: Kevin C. Kurtz
#. Date: 2021-03-19
#. Version: 1
#. Intent: Operate as the bots web interface. Input and Output if possible.
#...........................................................

#my assumption is this plugin will have to import other plugins (strava, whatever else needs routing from web) to call whatever commands or functions it needs to route data where it needs to go
#I don't want to, but it may have to import main and call an alexa function, to send intents to commands if I cant think of a smarter way
#I DO NOT WANT THE COMMANDS ARRAY IN HERE! This plugin shouldn't be importing all of the others. It should somehow send to main with an import worst case scenario.

#The whole bot runs in a single thread. This is typically a bad idea for a web server component. Flask is blocking. I've gone with Quart to by async compatible. We won't be doing enough
#CPU intensive requests to ever need another process in my use case and it makes communication about the APP super easy (no pipes or queues).
#If you have more traffic, you can bundle uvicorn (ASGI) inside the app for worker threads, but you'll have to figure out the communication between the discord loop and the other processes.
#I've already set up a non-blocking webframework that can handle the 10 requests a week the app will recieve. (nonblocking as in co-routine with discord)

#necessary local imports
import quart
import json
import logging
import asyncio

#set up our logging configuration
logger = logging.getLogger(__name__)

#my libraries
from plugins.strava import authorize as stravaAuthorize, activity as stravaActivity

app = quart.Quart(__name__)

@app.route('/')
async def default():
	#eventually, there will be some sort of templated page here. Until then. Why don't we just sent some simple text.
	return 'e-Not Bot'

@app.route('/strava')
async def strava():
	#eventually, there will be some sort of templated page here. Until then. Why don't we just sent some simple text.
	return 'strava'

@app.route('/strava/sub', methods=['GET', 'POST'])
async def strava_sub():
	try:
		#These were debugging. they'll print the args, post, and json values of all requests.
		#logger.info(f'Request values on /strava/sub: {await quart.request.values}')
		#logger.info(f'Request json on /strava/sub: {await quart.request.json}')

		#The only time we should get a GET request is when we are subscribing. Which should never happen again after the original
		if quart.request.method == "GET":
			#recieve GET https://mycallbackurl.com?hub.verify_token=STRAVA&hub.challenge=15f7d1a91c1f40f8a748fd134752feb3&hub.mode=subscribe
			#respond with { “hub.challenge”:”15f7d1a91c1f40f8a748fd134752feb3” }
			if quart.request.args.get('hub.challenge') != None and quart.request.args.get('hub.verify_token') == 'STRAVA':
				challenge = quart.request.args.get('hub.challenge')
				logger.info(f'New subscription request initiated? Strava subscription hub.challenge: {challenge}')
				return json.dumps({'hub.challenge':challenge}), 200
			
			#This means it wasn't a subscription request, or the verify token was wrong so it didn't come from our request. Either way, just ack we got it and disregard. Maybe we sent a GET request for debugging or something.
			else:
				return 'ok', 200

		#We should only get a POST when the subscription is giving us an event
		elif quart.request.method == "POST":
			#this log command is excessive. Lots of data for each rename, etc. We'll post a short one in the strava plugin. This is useful for debugging, but no reason for it to be on.
			#logger.info(f'POST subscription Activity: {await quart.request.json}')

			#We have 2 seconds. literally. to respond to the strava API that we got the event. We want to post process, but let's do that that asyncronously in the strava plugin. We don't need the webserver for that.
			task = asyncio.create_task(stravaActivity(await quart.request.json))
			#This should respond pretty quick since we are doing all the other stuff in another task that hasn't been awaited.
			return 'ok', 200

		#We should never ever get here.
		else:
			logger.info('Strava sub request wasn\'t GET or POST. Should not get here ever. Should return 405 instead.')
			return 'Not good', 500

	except:
		logger.exception('A request on /strava/sub broke')
		return 'A request broke', 500

#path for the auth callback when you send someone the authroization link
@app.route('/strava/auth')
async def strava_auth():
	try:
		#returns the code that strava sent after the users authorizes. We have to send to strava to confirm. Also get the discordID we shoved in the auth link
		code = quart.request.args.get('code')
		discordID = int(quart.request.args.get('discordID')) #to be useful in discord, this should not be a string and it is by default from args. (this will make it a numberlong in the database)
		confirmation = await stravaAuthorize(discordID,code)
		logger.info(f'Strava auth confirmation: {confirmation}')
		return confirmation
	except:
		logger.exception('A request on /strava/auth broke')
		return 'The request broke', 500

@app.errorhandler()
async def page_not_found(e):
	#eventually, there will be some sort of templated page here. Until then. Why don't we just sent some simple text.
	return 'You have encountered an error, because of something you did, not me. I\'m perfect. If you think you SHOULDN\'T be seeing this page, contact me at pretty_much_anything at thisdomain.com'

if __name__ == '__main__':
	#not available publically. Only loop back. You should reverse proxy from apache2 or some other real web server that can handle requests properly and then internally route.
	app.run('127.0.0.1','8888')

