# e-Not Bot

*Author:* Kevin C. Kurtz kevinckurtz.com magnetengineer.com
*Language:* Python3
*Summary:* e-Not Bot (e-Notifications Bot) was created to automate and anticipate my needs across the web. Focused primarily on Discord, the bot also features web services, Alexa skills, and general script running. It is my interface to interact with the world and my server. Planned integrations for more services.

## Installation

GIT this folder. You don't need a virtual environment, but you should create one, as python dependencies are a nightmare.
Use the built in configuration file example to set up the bot. Use \__init__.py in plugins to turn the plugins on/off by commenting them out.

## Usage

```
source /path/to/bot/env/bin/activate && /path/to/bot/eNotBot.py 1>>/path/to/bot/log.log 2>&1 &'
```
You will NEED a config_file.py file, that looks like the example. It should include your API keys for discord and strava, if you'd like to use that plugin. It has other settings and secrets that are for your server configuration only.

There's other helpful running hints (including cron, which has a bash/sh problem with source) in some of the comments, espeically in eNotBot.py. Comments are fairly thorough and explain my thought process through many of the decisions.

This looks portable, because Python, but it's pretty linux (maybe even Ubuntu) specific at times. (process naming, sh launching with Popen, logging output) I have not tested this anywhere but my venv on ubuntu 2020.4 LTS.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. This is a personal bot to automate my life, but if it helps you or you have changes, great!

## License
[MIT](https://choosealicense.com/licenses/mit/)

Give me credit, of course, and please. But do what you want/can. [Better yet, pay me to help you.]