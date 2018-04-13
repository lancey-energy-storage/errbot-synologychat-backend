# Synology Chat backend for ErrBot

## Features

- Supports chatbot conversations as well as trigger words from channels
- Verifies that received requests contain the token to avoid unauthorized commands

## How it works

Most chats allow websocket connections to have a real time bidirectionnal communication, but Synology Chat doesn't. It only uses webhooks, to send and receives messages. Hence, this backend opens up a HTTP server to receive requests from Chat.

## How to use

- Clone or download the project
- Add an integration to your Synology Chat app (read more about it [here](https://www.synology.com/en-global/knowledgebase/DSM/help/Chat/chat_integration))
- Read config_example.py to see how to configure ErrBot
