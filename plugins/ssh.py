#...........................................................
#. SSH Command Plugin
#. Author: Kevin C. Kurtz
#. Date: 2021-03-17
#. Version: 1
#. Intent: Open SSH ports on the server
#...........................................................

#necessary local imports
import subprocess
import logging

#pull in some identifying variables
import config_file as cfg

#Logging setup
logger = logging.getLogger(__name__)

#SSH command
async def ssh(message):
  if message.content.startswith('!ssh'):
    try:

      msg = 'Opening SSH for 10 seconds.'
      await message.channel.send(msg)

      #This is a restricted command. Check that the user is the owner before executing the script.
      if message.author.id == cfg.myID:
        #call a script on the server that opens the ports in UFW, waits, then closes them. 
        #It should executeable by your python user, and you should have nopasswd sudo enabled for that script and user in visudo
        cmd = ['sudo', cfg.sshScriptPath]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

      else:
        msg = 'Hey. Wait. You\'re not <@{}>. Get outta here. You can\'t do that.'.format(cfg.myID)
        await message.channel.send(msg)

    except:
      logger.exception('ssh plugin died.')


if __name__ == "__main__":
  #no reason we can't call this plugin on its own. Doesn't need the discord client or the web server.
  cmd = ['sudo', cfg.sshScriptPath]
  proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  print('Ran SSH script.')