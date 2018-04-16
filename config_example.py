import logging
import os

# This is a minimal configuration to get you started with the Synology backend.
# Check out the complete config-template.py here:
# https://raw.githubusercontent.com/errbotio/errbot/master/errbot/config-template.py

#########################

# ErrBot basics (see ErrBot doc)

BOT_DATA_DIR = r'...'
BOT_EXTRA_PLUGIN_DIR = r'...'

BOT_LOG_FILE = r'...'
BOT_LOG_LEVEL = logging.DEBUG

#########################

# Set backend
BOT_EXTRA_BACKEND_DIR = r'...' # path to synologychat backend folder
BACKEND = 'SynologyChat'

# Set connection to Chat
BOT_IDENTITY = {
	# url for incoming messages (incoming into Chat), do not paste the token parameter (stop at version=2)
    'url': 'https://hostname:port/webapi/entry.cgi?api=SYNO.Chat.External&method=chatbot&version=2', # example for a chatbot
    # tokens to authorize requests
    # the incoming token is the one given with the previous url
    # the outoging token is generated by synology when you setup an outgoing webhook from a channel
    # note: in case of a chat bot, the two tokens will be the same, but you must specify them anyway
    'token-incoming': '...', # or os.environ['TOKEN-IN'] if you prefer to use environment variables for safety reasons
    'token-outgoing': '...' # or os.environ['TOKEN-OUT']
}

# Set bot prefix
# If you use the bot from a chatbot conversation, you can just type in commands with the "!" prefix (eg: !tryme) and you don't need this BOT_ALT_PREFIXES parameter. However, if you use your bot in a channel, you need a trigger word to make Synology Chat send the message to the outgoing webhook (eg "bot tryme"). Enter your trigger word into BOT_ALT_PREFIXES.
BOT_ALT_PREFIXES = ('bot',) # should be the same as the trigger word if used in channel

# Admins
# If you need to allow some commands to a group of people only, add their username with a '@' before it and configure access controls accordingly.
BOT_ADMINS = ('@me', )
ACCESS_CONTROLS = {'tryme': {'allowusers': BOT_ADMINS}}

