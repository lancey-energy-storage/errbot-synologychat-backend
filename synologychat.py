import asyncio
import json
import logging
import requests
import sys

from errbot.backends.base import Message, Person, ONLINE
from errbot.core import ErrBot

log = logging.getLogger('errbot.backends.synologychat')

class SynologyChatUser(Person):
    """
    This class inherits from backends.Person, it is used to represent a chat user.
    """
    
    def __init__(self, user_id, user_name):
        """
        :param user_id: 
            The Synology Chat integer representing the user.
        :param user_name:
            The Synology Chat string representing the user.
        """
        self.id   = str(user_id)
        self.name = user_name

    @property
    def person(self) -> str:
        """
        :return: a backend specific unique identifier representing the person you are talking to.
        """
        return "@{}".format(self.name)

    @property
    def fullname(self) -> str:
        """
        Some backends have the full name of a user.
        :return: the fullname of this user if available.
        """
        return self.person

    @property
    def nick(self) -> str:
        """
        :return: a backend specific nick returning the nickname of this person if available.
        """
        return self.person

    @property
    def aclattr(self) -> str:
        """
        :return: returns the unique identifier that will be used for ACL matches.
        """
        return self.person # not using self.id allows you to use user names in BOT_ADMINS

    @property
    def client(self) -> str:
        """
        :return: a backend specific unique identifier representing the device or client the person is using to talk.
        """
        pass

class SynologyChatBackend(ErrBot):
    """
    This class inherits from ErrBot, it is the main class handling interactions with Synology Chat.
    """

    def __init__(self, config):
        super().__init__(config)
        identity = config.BOT_IDENTITY
        # verify params
        if not identity.get('url'):
            log.critical("Missing 'url' parameter in BOT_IDENTITY")
            sys.exit(2)
        if not identity.get('token-incoming'):
            log.critical("Missing 'token-incoming' parameter in BOT_IDENTITY")
            sys.exit(2)
        if not identity.get('token-outgoing'):
            log.critical("Missing 'token-outgoing' parameter in BOT_IDENTITY")
            sys.exit(2)
        # parse params
        self.token_in = identity.get('token-incoming')
        self.token_out = identity.get('token-outgoing')
        self.incoming_url = identity.get('url') + "&token=%22" + self.token_in + "%22"
        self.bot_identifier = SynologyChatUser(0, "bot") # default name (not very important it seems)
        self.ip = identity.get('ip', '0.0.0.0')
        self.port = identity.get('port', 8080)
        # log
        log.info("initialized Synology Chat backend with url {}".format(identity.get('url')))

    def build_identifier(self, txtrep):
        """
        Recognize references to users, such as @chatuser.
        
        This first implementation only accepts @user references and returns an identifier with user_id=0.
        The next implementation will user the user_list command with bots and will cache user ids from incoming requests for channels.
        """
        # TODO: implement cached user list
        if txtrep[0] == '@':
            return SynologyChatUser(0, txtrep[1:])
        raise Exception("Invalid Synology Chat identifier: {}".format(txtrep))

    def build_reply(self, message, text=None, private=False, threaded=False):
        """
        Prepare arguments for incoming message.
        """
        # debug
        log.debug("building reply '{0}' to '{1}'".format(text, message.frm))
        # replace markdown with Synology Chat specifics
        text = text.replace("**", "*") # bold
        text = text.replace("\n- ", "\n* ") # lists 
        if text[0:2] == "- ": # if message begins with list
            text[0] = '*'
        # setup fields
        response     = self.build_message(text)
        response.frm = self.bot_identifier
        response.to  = message.frm
        # no support for private or threaded arguments
        return response
        
    def send_message(self, message):
        """
        Send message to Synology Chat a user in a bot conversation or to a channel.
        """
        super().send_message(message)
        # build request body
        payload = {
            "text"     : str(message)
        }
        if int(message.to.id) != 0:
            payload["user_ids"] = [int(message.to.id)]
        data = "payload="+json.dumps(payload)
        log.debug("incoming message payload: {}".format(data))
        # build url
        url = self.incoming_url
        # send
        r = requests.post(url, data=data)
        # debug response
        if not json.loads(r.text)["success"]:
            log.warning("cannot send message to Chat: {}".format(json.loads(r.text)["error"]["errors"]))
        
    def change_presence(self, status: str=ONLINE, message: str=''):
        """
        Change user status (active or away).
        """
        pass  # can't do
        
    @property
    def mode(self):
        return 'synologychat' # to tell plugins which backend is loaded
        
    def query_room(self, room):
        """ 
        Room can either be a name or a channelid 
        """
        pass # not supported
        
    def rooms(self):
        """
        Return public and private channels, but no direct channels
        """
        pass # not supported
        
    def serve_once(self):
        """
        Create the HTTP server which will handle outgoing messages.
        """
        #############
        # FLASK SETUP
        from flask import Flask, request
        app = Flask(__name__)

        # This is where we receive requests from Synology Chat
        @app.route("/", methods=['POST'])
        def receive_from_chat():
            # Debug
            log.debug("received message | args:{0} | form:{1}".format(request.args, request.form))
            # Verify that the request contains the token, otherwise it's an unauthorized request
            if not request.form or not request.form['token'] or request.form['token'] != self.token_out:
                ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                log.warning("unauthorized request: wrong or missing token | ip:{0} | args:{1} | form:{2}".format(ip, request.args, request.form))
                return "Unauthorized\n", 401 
            # Send to ErrBot
            msg = Message(body = request.form['text'],
                          frm  = SynologyChatUser(request.form['user_id'], request.form['username']),
                          to   = self.bot_identifier)
            self.callback_message(msg)
            # Send an empty reply to Synology Chat
            return "", 200
        #############
        
        # Start HTTP server
        self.connect_callback() # tell ErrBot we're up so it can load commands
        try:
            log.info("running http server on host {0}:{1}".format(self.ip, self.port))
            app.run(host=self.ip, port=self.port) # fire the server
            # TODO: maybe find more production-suites ways to run flask
        except KeyboardInterrupt:
            log.info("Interrupt received, shutting down..")
            return True
        except Exception:
            log.exception("HTTP server error:")
        finally:
            log.debug("Triggering disconnect callback")
            self.disconnect_callback() # tell ErrBot we're down in case of error
          
