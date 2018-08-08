import requests
import re
import json
import datetime
import time, os, sys
import telebot
from telebot import types
import cherrypy

os.chdir(os.path.dirname(sys.argv[0]))

class WebhookServer(object):
	@cherrypy.expose
	def index(self):
		if 'content-length' in cherrypy.request.headers and \
				'content-type' in cherrypy.request.headers and \
				cherrypy.request.headers['content-type'] == 'application/json':
			length = int(cherrypy.request.headers['content-length'])
			json_string = cherrypy.request.body.read(length)
			update = telebot.types.Update.de_json(json_string)
			bot.process_new_updates([update])
			return ''
		else:
			raise cherrypy.HTTPError(403)


TOKEN = 'TOKEN'

WEBHOOK_HOST = 'IP'
WEBHOOK_PORT = 8443
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = 'webhook_cert.pem'
WEBHOOK_SSL_PRIV = 'webhook_pkey.pem'

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (TOKEN)

bot = telebot.TeleBot(TOKEN)

knownUsers = []  # todo: save these in a file,
userStep = {}  # so they won't reset every time the bot restarts

commands = {  # command description used in the "help" command
              'teamrating': 'team rating in ctftime',
	      'top': 'top 10 teams',
              #'ctfonline': 'now running ctf',
              'ctfnext': 'next 3 ctf',
              'help': 'extended help for bot commands'
}

#time decoder
def decode_time(time):
	tm = time[:-6]
	tm = re.sub("T", ' ', tm)
	tim_r = datetime.datetime.strptime(tim_t, '%Y-%m-%d %H:%M:%S')
	tm = time.mktime(tim_r.timetuple())
	return tm


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        knownUsers.append(uid)
        userStep[uid] = 0
        print "New user detected, who hasn't used \"/start\" yet"
        return 0


# only used for console output now
def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text


# handle the "/start" command
@bot.message_handler(commands=['start'])
def command_start(m):
    cid = m.chat.id
    if cid not in knownUsers:  # if user hasn't used the "/start" command yet:
        knownUsers.append(cid)  # save user id, so you could brodcast messages to all users of this bot later
        userStep[cid] = 0  # save user id and his current "command level", so he can use the "/getImage" command
        bot.send_message(cid, "Hello, stranger, let me scan you...")
        bot.send_message(cid, "Scanning complete, I know you now \n")
        command_help(m)  # show the new user the help page
    else:
        bot.send_message(cid, "I already know you, no need for me to scan you again!")
        
# help page
@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    help_text = "You can control me by sending these commands: \n\n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + " - "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page

# teamrating page
@bot.message_handler(commands=['teamrating'])
def command_teamrating(m):
    cid = m.chat.id
    # connect to ctftime
    url = 'https://ctftime.org/api/v1/teams/4292/'
    r = requests.get(url)
    jsont = json.loads(r.text)
    teamname = jsont['name']
    res_place = jsont['rating'][0]['2016']['rating_place']
    res_b = jsont['rating'][0]['2016']['rating_points']
    
    help_text = "Team " + teamname + ":\n"
    help_text += "Overall rating place: " + str(res_place) + " with " + str(res_b) + " pts in 2016"
    bot.send_message(cid, help_text) 

#top 10 teams
@bot.message_handler(commands=['top'])
def command_top(m):
	cid = m.chat.id
	url = 'https://ctftime.org/api/v1/top/'
	r = requests.get(url)
	jsont = json.loads(r.text)
	print jsont['2016'][0]['team_name']
	e_text = " "
	r = 0
	n = 1
	for i in jsont['2016']:
		text = n + i[r]['team_name'] + "(" + i[r]['points']  + ")" + "\n"
		e_text = e_text + text
		r = r + 1
		n = n + 1
	bot.send_message(cid, e_text)	


# ctfonline page
#@bot.message_handler(commands=['ctfonline'])
def command_ctfonline(m):
    cid = m.chat.id
    # connect to ctftime
    now = datetime.datetime.now()
    day14 = now - datetime.timedelta(days=14)
    tsnow = time.mktime(now.timetuple())
    tsday14 = time.mktime(day14.timetuple())
    url = 'https://ctftime.org/api/v1/events/?limit=100&start=' + str(tsday14) + '&finish=' + str(tsnow)
    r = requests.get(url)
    jsont = json.loads(r.text)
    r = 1
    for i in jsont:
	    help_text = "Name: " + i['title'] + "\n"
	    help_text += "Date:\n"
	    help_text += " - Start: " + i['start'] + "\n"
	    help_text += " - Finish: " + i['finish'] + "\n"
	    help_text += "Format: " + i['format'] + "\n"
	    if i['onsite'] == True:
	    	help_text += "Location: " + i['location'] + "\n"
	    if i['onsite'] == False:
	    	help_text += "Location: On-line \n"
	    help_text += "============= \n"
	    r = r + 1
	    bot.send_message(cid, help_text)

# ctfnext page
@bot.message_handler(commands=['ctfnext'])
def command_ctfnext(m):
    cid = m.chat.id
    # connect to ctftime
    url = 'https://ctftime.org/api/v1/events/?limit=3'
    r = requests.get(url)
    jsont = json.loads(r.text)
    r = 1
    for i in jsont:
	    help_text = "Name: " + i['title'] + "\n"
	    help_text += "Date:\n"
	    help_text += " - Start: " + i['start'] + "\n"
	    help_text += " - Finish: " + i['finish'] + "\n"
	    help_text += "Format: " + i['format'] + "\n"
	    if i['onsite'] == True:
	    	help_text += "Location: " + i['location'] + "\n"
	    if i['onsite'] == False:
	    	help_text += "Location: On-line \n"
	    help_text += "Url: " + i['url'] + "\n"
	    help_text += "============= \n"
	    r = r + 1
	    bot.send_message(cid, help_text)

# default handler for every other text
@bot.message_handler(func=lambda message: True, content_types=['text'])
def command_default(m):
    # this is the standard reply to a normal message
    bot.send_message(m.chat.id, "I don't understand \"" + m.text + "\"\nMaybe try the help page at /help")

#bot.polling()

bot.remove_webhook()

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH, certificate=open(WEBHOOK_SSL_CERT, 'r'))

cherrypy.config.update({
	'server.socket_host': WEBHOOK_LISTEN,
	'server.socket_port': WEBHOOK_PORT,
	'server.ssl_module': 'builtin',
	'server.ssl_certificate': WEBHOOK_SSL_CERT,
	'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})


