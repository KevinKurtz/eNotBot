#...........................................................
#. Strava Command Plugin
#. Author: Kevin C. Kurtz
#. Date: 2021-03-18
#. Version: 1
#. Intent: Strava authorization, subscriptions, posting about new activities
#. Strava and the webserver plugin are linked. Most strava doesn't work without being able to receive push
#...........................................................

#necessary local imports
import pymongo
import requests
import json
import aiohttp
import asyncio
import logging
import time
import datetime

#set up our logging configuration
logger = logging.getLogger(__name__)

#pull in some identifying variables
import config_file as cfg

#create a non-existant client. We'll set this in init when we have a client.
client = None

#connect to mongoDB
try:
	mongo_connection = pymongo.MongoClient(cfg.mongoServer) #server
	strava_database = mongo_connection['strava'] #database
	users_collection = strava_database['users'] #collection
	activities_collection = strava_database['activities'] #collection
except:
	logger.exception('Connection to Mongo failed in Strava Plugin')


#strava default command. Called from whereve the commands dict from init is used.
async def strava(message):
	if message.content == '!strava auth':
		try:
			#Check and see if the user trying to get authroization is already authorized.
			if users_collection.count_documents({'discordID': message.author.id}) > 0:
				await message.channel.send('You are already authorized. If you NEED to re-auth use the DM from last time or contact a mod.')
				logger.warning(f'{message.author.name} is already authorized and tried the strava auth command')
			
			#if they are not yet authorized
			else:
				#get their user class so we can send them a DM. Create a custom authroization link. Then let them know to check their messages.
				user = await client.fetch_user(message.author.id)
				await user.send(f'Use this link to authorize the bot. You\'ll be asked to log in to Strava and accept the permissions for the bot. \n https://www.strava.com/oauth/authorize?client_id={cfg.stravaID}&response_type=code&redirect_uri={cfg.stravaRedirectURI}?discordID={message.author.id}&approval_prompt=force&scope=profile:read_all,activity:read_all')
				await message.channel.send('I\'ve sent you a DM with an authorization link.')
				logger.info(f'{message.author.name} was sent a DM with a Strava authorization link.')
		except:
			logger.exception('strava auth command failed')

	#functions for the strava api subscription
	if message.content.startswith('!strava subscribe'):
		#Sign the bot up (in the Strava API) to be notified of activity updates. Hopefully, this is only done once.
		if message.content == '!strava subscribe init':
			try:
				#make sure it is the admin doing this, or bad things can happen
				if message.author.id == cfg.myID:
					msg = await subscribe()
					await message.channel.send(msg)
					logger.info(msg)
				else:
					await message.channel.send(f'This is a restricted command. You can not use it. I\'m tattling. <@{cfg.myID}>')
					logger.warning(f'{message.author.name} attempted to initialize the Strava subscription')
			except:
				logger.exception('strava subscribe init function (subscribe()) broke')

		#command to view strava subscription API for the bot (gets the subscription ID and makes sure its valid)
		elif message.content == '!strava subscribe view':
			try:
				#make sure it is the admin doing this, or bad things can happen
				if message.author.id == cfg.myID:
					msg = await view_subscribe()
					await message.channel.send(msg)
					logger.info(msg)
				else:
					await message.channel.send(f'This is a restricted command. You can not use it. I\'m tattling. <@{cfg.myID}>')
					logger.warning(f'{message.author.name} attempted to view the Strava subscription')
			except:
				logger.exception('strava subscribe view function (view_subscribe()) broke')

		#command to delete strava subscription in the API for the bot
		elif message.content == '!strava subscribe delete':
			try:
				#make sure it is the admin doing this, or bad things can happen
				if message.author.id == cfg.myID:
					msg = await del_subscribe()
					await message.channel.send(msg)
					logger.info(msg)
				else:
					await message.channel.send(f'This is a restricted command. You can not use it. I\'m tattling. <@{cfg.myID}>')
					logger.warning(f'{message.author.name} attempted to delete the Strava subscription')
			except:
				logger.exception('strava subscribe delete function (del_subscribe()) broke')

		#if they said !strava subscribe but didn't use the right following keyword they might be trying to authorize		
		else:
			await message.channel.send('You might be looking for !strava auth')



#I slammed my head on the keyboard repeatedly to create some of these auth codes and secrets/tokens. They aren't real. Just wanted to document the API
#Send someone this: https://www.strava.com/oauth/authorize?client_id=xxxxx&response_type=code&redirect_uri=https://xxxx.com?discordID=12345&approval_prompt=force&scope=profile:read,activity:read
#Get this back: http://xxxx.com/exchange_token?state=&code=56e756754675e6tuft6778r58r56&scope=read,activity:read,profile:read
#send: response = requests.post(url = 'https://www.strava.com/oauth/token',data = {'client_id': xxxxx,'client_secret': '4235asertsdrtsertse4tse4te','grant_type': 'authorization_code','code':'56e756754675e6tuft6778r58r56'})
#get this back: {'token_type': 'Bearer', 'expires_at': 1616151633, 'expires_in': 21600, 'refresh_token': 'ew457e4r57e457yedrthdrtyhdrydr45y', 'access_token': 'ddrthdr65red67u576567567d567', 'athlete': {Well.... assume there's a whole lot of confidential information in there}}
#tokens last six hours. So assume we are going to refresh them a lot.
#send: response = requests.post(url = 'https://www.strava.com/oauth/token',data = {'client_id': xxxxx,'client_secret': '4235asertsdrtsertse4tse4te','grant_type': 'refresh_token','refresh_token':'ew457e4r57e457yedrthdrtyhdrydr45y'})
#get this back: {'token_type': 'Bearer', 'access_token': 'w46wsredfyte4d56we45yrsdeb5rydrty', 'expires_at': 1616151633, 'expires_in': 21094, 'refresh_token': 'ew457e4r57e457yedrthdrtyhdrydr45y'}

#A warning from the discord python library peeps that know async programming way better tham me. It actually saved me in the subscribe function so I'm going to leave the note.
# # bad
# r = requests.get('http://aws.random.cat/meow')
# if r.status_code == 200:
#     js = r.json()
#     await channel.send(js['file'])

# # good
# async with aiohttp.ClientSession() as session:
#     async with session.get('http://aws.random.cat/meow') as r:
#         if r.status == 200:
#             js = await r.json()
#             await channel.send(js['file'])

#authorize is only called from the webserver when it gets an auth callback. That means someone clicked an authorization link (sent by DM from the bot with the !strava auth command)
async def authorize(discordID,code):
	try:
		#This works, but should be asyncronous. Stop use requests
		#If the webserver gets an auth response, we have to send back an acknowledgement with our secret and the auth code
		response = requests.post(url = 'https://www.strava.com/oauth/token',data = {'client_id': cfg.stravaID,'client_secret': cfg.stravaSecret,'grant_type': 'authorization_code','code':code})
		#this dictionary contains the refresh_token, access_token and a whole lot of secret athlete data
		data = response.json()
		#shove the discordID we shoved in the auth URL into the dictionary that was returned.
		data['discordID'] = discordID
		#Put all that data in Mongo, we'll need some of it later. set with the "upsert" option, that true at the end. It will update if it exists, or create it if it doesnt.
		users_collection.update({'athlete.id':data['athlete']['id']}, data, True)
		logger.info(f'Successful authorization of discordID {discordID}. AKA {data["athlete"]["firstname"]} {data["athlete"]["lastname"]}. StravaID {data["athlete"]["id"]}')
		#This return will literally write this in their browser window in text after they have clicked that auth link we DM'd.
		return f'SUCCESS! Thank you, {data["athlete"]["firstname"]}. You\'ve authorized e-Not Bot to subscribe to your Strava account.'
	except:
		logger.exception('Strava authorization broke (authorize) after it got past the webserver to our strava functions')



#activity should only be called from the subscription in the web server, unless we are creating a fake activity in the database I guess. It recieves the activity or update from the subscription feed.
async def activity(activity_json):
	try:
		#We don't know if this is a new activity or an update. We should figure that out. Let's see if it already matches an activity in the database.
		#This is a real concern, we are going to wait a while in this function, we could get an update that will process asyncronously while we are waiting. We don't
		#want two copies of the same activity in the database. Let's pop it in now and ignore any updates (this is just for the feed, we'll grab the real activity after the wait, so it'll be updated!)

		#Activity sub feed looks something like this:
		#{'aspect_type': 'create', 'event_time': 1616366057, 'object_id': 123456767876, 'object_type': 'activity', 'owner_id': 123455678, 'subscription_id': 1234567, 'updates': {}}
		#if this object ID matches one already in the DB, then ignore (it would likely have aspect_type update if that were the case, but either way, they will have a unique object id for each activity)
		if activities_collection.count_documents({'id': activity_json['object_id']}) == 0:
			#do work here. Meat and potatoes, baby!
			#add the activity to the database and we'll update it more thoroughly later.
			activity = {'id': activity_json['object_id'], 'event_time': activity_json['event_time'], 'owner_id': activity_json['owner_id']}
			activities_collection.insert_one(activity)
			logger.info(f'Added strava activity to database: {activity}')

			#sleep 5min (asyncronously, non-blocking)
			await asyncio.sleep(300)

			#refresh our tokens for the given user, if necessary (likely, they only last 6 hours)
			#find the user information from the owner of the activity
			users = users_collection.find({'athlete.id': activity['owner_id']})
			#if the user doesn't exist, this users thing won't have any values so it'll skip this loop. That means the user for some reason isn't "authorized" despite being subscribed. Maybe they got wiped from our DB somehow.
			for user in users:
				#if the token is expired
				if user['expires_at'] <= int(time.time()):
					#refresh token
					#send: response = requests.post(url = 'https://www.strava.com/oauth/token',data = {'client_id': xxxxx,'client_secret': '4235asertsdrtsertse4tse4te','grant_type': 'refresh_token','refresh_token':'ew457e4r57e457yedrthdrtyhdrydr45y'})
					#get this back: {'token_type': 'Bearer', 'access_token': 'w46wsredfyte4d56we45yrsdeb5rydrty', 'expires_at': 1616151633, 'expires_in': 21094, 'refresh_token': 'ew457e4r57e457yedrthdrtyhdrydr45y'}
					async with aiohttp.ClientSession() as session:
						async with session.post('https://www.strava.com/oauth/token', data = {'client_id': cfg.stravaID,'client_secret': cfg.stravaSecret,'grant_type': 'refresh_token', 'refresh_token': user['refresh_token']}) as response:
							response_dict = await response.json()
							#update the tokens, expire time, etc for the given user in the database
							users_collection.update({'athlete.id':user['athlete']['id']}, {'$set':response_dict}, True)
							user['access_token'] = response_dict['access_token']
							logger.info(f'Update user token for {user["athlete"]["id"]}: {response_dict}')

				#Token is either still good, or we refreshed it to get here. Let's pull the activity and throw it in the database
				#send: GET "https://www.strava.com/api/v3/activities/{id}?include_all_efforts=" "Authorization: Bearer [[token]]"
				async with aiohttp.ClientSession() as session:
					async with session.get(f'https://www.strava.com/api/v3/activities/{activity["id"]}?include_all_efforts=false&access_token={user["access_token"]}') as response:
						if response.status == 200:
								activity = await response.json()
								#update, since it should already exist just with a lot less params, the activity
								activities_collection.update({'id':activity['id']}, activity)
								#This is a lot of data to log. Helpful for debug, but not normally needed. We noted earlier we created the activity and we'll find out below if we processed it.
								#logger.info(f'Logged final activity for {activity["id"]}: {activity}')

								#This does have the caveate that if they update an old activity that we haven't seen before it'll get posted. We don't want to filter for just create's though either
								#Because what if they imported from an old system to strava with back dates. This is where "start_date":"2021-03-21T21:40:01Z" might be handy. If imported, hopefully it'll keep the old date stamps.
								#let's only import if it started in the last day.
								#It gives us a funky format, but at least it looks like UTC, which is handy. no timezones. Let's make a datetime object, then a unix timestamp and then we can just subtract the seconds from current time.
								datetime_activity_start = datetime.datetime.strptime(activity['start_date'], '%Y-%m-%dT%H:%M:%SZ')
								unixtime_activity_start = datetime_activity_start.replace(tzinfo=datetime.timezone.utc).timestamp()
								if int(time.time())-int(unixtime_activity_start) < 86400:
									#If we are good to post, let's format it properly per activity type
									msg = await format_activity(user,activity)

									# #sending in dm right now, until we get this down
									# user = await client.fetch_user(user['discordID'])
									# await user.send(msg)
									
									#send in #general for now
									channel = client.get_channel(187598008874041355)
									await channel.send(msg)
									logger.info(f'Activity Report: {msg}')
						else:
							logger.info(f'Activity request returned something other than 200 (token didnt get refreshed?): User: {user} - Activity: {activity}')

	except:
		logger.exception('Strava activity broke (activity) after it got past the webserver to our strava functions')



async def subscribe():
	try:
		#this should only have to be done once ever. It tells strava API to push new activities at us through a post interfacte I think.
		#send POST https://www.strava.com/api/v3/push_subscriptions?client_id=5&client_secret=7b2946535949ae70f015d696d8ac602830ece412&callback_url=http://a-valid.com/url&verify_token=STRAVA
		#recieve GET https://mycallbackurl.com?hub.verify_token=STRAVA&hub.challenge=15f7d1a91c1f40f8a748fd134752feb3&hub.mode=subscribe
		#respond with { “hub.challenge”:”15f7d1a91c1f40f8a748fd134752feb3” }
		#this does step one, the rest is done in the webserver to acknowledge

		#this gives an error because it times out, because its blocking and we don't reciieve our responses until after. They get buffered. Stop using requests.
		#response = requests.post(url = 'https://www.strava.com/api/v3/push_subscriptions',data = {'client_id': cfg.stravaID,'client_secret': cfg.stravaSecret,'callback_url': cfg.stravaSubURL,'verify_token': 'STRAVA'})
		#print(response.json())

		#This works correctly and asyncronously. This is how we should be doing all GET/POST/DELETE requests
		async with aiohttp.ClientSession() as session:
			async with session.post('https://www.strava.com/api/v3/push_subscriptions', data = {'client_id': cfg.stravaID,'client_secret': cfg.stravaSecret,'callback_url': cfg.stravaSubURL,'verify_token': 'STRAVA'}) as response:
				response_dict = await response.json()
				#this should give us the subscription ID (after the web server gets down acknoledging on the callback_url. It will have to send the hub.challenge back
				logger.info(f'Strava subscription API response: {response_dict}')
				if response_dict.get('id') != None:
					logger.info(f'Strava subscription succesful. Subscription ID: {response_dict["id"]}')
					return f'Subscription succesful. Subscription ID: {response_dict["id"]}'
				else:
					logger.info('Strava subscription failed.')
					return 'Subscription failed.'
	except:
		logger.exception('Strava subscribe broke (subscribe)')
		return 'Error subscribing to the Strava feed'

async def view_subscribe():
	try:
		#this works but should be asyncronous. Stop using requests.
		response = requests.get(url = 'https://www.strava.com/api/v3/push_subscriptions',data = {'client_id': cfg.stravaID,'client_secret': cfg.stravaSecret})
		logger.info(f'Strava view subscription response:{response.json()}')
		return response.json()
	except:
		logger.exception('Strava view subscriptions broke (view_subscribe)')
		return 'Error viewing the subcription from Strava'

async def del_subscribe():
	try:
		#this function deletes our API request for subscriptions. We should hopefully never use it.

		#this works but should be asyncronous. Stop using requests.
		response = requests.get(url = 'https://www.strava.com/api/v3/push_subscriptions',data = {'client_id': cfg.stravaID,'client_secret': cfg.stravaSecret})
		logger.info(f'Strava view (within delete) response:{response.json()}')

		#We need the subscription ID as a string. It's in a list the contains a dictionary (if we get a response. If we don't have a sub we'll through an exception because there is no list to index)
		if len(response.json()) > 0:
			strID = str(response.json()[0]['id'])
			response = requests.delete(url = f'https://www.strava.com/api/v3/push_subscriptions/{strID}',data = {'client_id': cfg.stravaID,'client_secret': cfg.stravaSecret})
			logger.info(f'Strava delete subscription response (204 is success): {response}')
		else: #This likely means we don't have a subscription
			logger.info('Strava delete subscrption failed, likely because we don\'t have one')
			return 'Error finding the subscription to delete. Do we have one?'
		
		#a response of 204-no content means success.
		if response.status_code == 204:
			logger.info('Strava subscription was successfully deleted')
			return 'Strava subscription was successfully deleted' 
	except:
		logger.exception('del_subscribe has an exception when deleting the subscription from Strava')
		return 'Error deleting the subscription from Strava.'


async def format_activity(user, activity):
	try:
		#This function takes in a new activity to be posted and formats the message the bot will send specific to the activity itself.
		msg = f'<@{user["discordID"]}> just recorded a {activity["type"]}.\n\n__**Name:** {activity["name"]}__'

		#If it is a walk or a run it will follow this pattern
		if activity['type'] == 'Run' or activity['type'] == "Walk":
			msg = msg + f'\n**Distance:** {round(activity.get("distance")*0.00062137, 2)} miles\t**Time:** {str(datetime.timedelta(seconds=activity.get("moving_time")))}\n**Pace:** {str(datetime.timedelta(seconds=int(1609.344/(activity.get("distance")/activity.get("moving_time")))))[2:]} min/mile'
		
		#if it is a bike ride, do this
		if activity['type'] == 'Ride':
			msg = msg + f'\n**Distance:** {round(activity.get("distance")*0.00062137, 2)} miles\t**Time:** {str(datetime.timedelta(seconds=activity.get("moving_time")))}\n**Speed:** {round(2.23694*activity.get("distance")/activity.get("moving_time"),1)} mph'

		#Every activity likely has these.
		if activity.get('calories') != '':
			msg = msg + f'\t**Calores:** {int(activity.get("calories"))}'
		if activity['has_heartrate'] == True:
			msg = msg + f'\n**Average HR:** {int(activity.get("average_heartrate"))}\t**Max HR:** {int(activity.get("max_heartrate"))}'
		if activity.get('description') != '':
			msg = msg + f'\n**Description:** _{activity.get("description")}_'


		return msg
	except:
		logger.exception('format_activity somehow broke')
		return 'Error formating the activity'

if __name__ == "__main__":
	#REALLY need the build in webserver component. This is just here for the occasional fake message testing.
	pass