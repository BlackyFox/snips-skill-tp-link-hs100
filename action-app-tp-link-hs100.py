#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from snipsTools import SnipsConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io
import socket
from struct import pack

CONFIG_INI = "config.ini"

# If this skill is supposed to run on the satellite,
# please get this mqtt connection info from <config.ini>
# Hint: MQTT server is always running on the master device
MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

IP = ""
PORT = ""

commands = {'info'     : '{"system":{"get_sysinfo":{}}}',
			'on'       : '{"system":{"set_relay_state":{"state":1}}}',
			'off'      : '{"system":{"set_relay_state":{"state":0}}}',
			'cloudinfo': '{"cnCloud":{"get_info":{}}}',
			'wlanscan' : '{"netif":{"get_scaninfo":{"refresh":0}}}',
			'time'     : '{"time":{"get_time":{}}}',
			'schedule' : '{"schedule":{"get_rules":{}}}',
			'countdown': '{"count_down":{"get_rules":{}}}',
			'antitheft': '{"anti_theft":{"get_rules":{}}}',
			'reboot'   : '{"system":{"reboot":{"delay":1}}}',
			'reset'    : '{"system":{"reset":{"delay":1}}}',
			'energy'   : '{"emeter":{"get_realtime":{}}}'
}


class Skill_TPL_HS100(object):
    """Class used to wrap action code with mqtt connection

        Please change the name refering to your application
    """

    def __init__(self):
        # get the configuration if needed
        try:
            config = SnipsConfigParser.read_configuration_file(CONFIG_INI)
        except :
            config = None
        ip = None
        port = None

        if config and config.get('secret', None) is not None:
            if config.get('secret').get('ip', None) is not None:
                ip = config.get('secret').get('ip')
                if ip == "":
                    ip = None
            if config.get('secret').get('port', None) is not None:
                port = config.get('secret').get('port')
                if port == "":
                    port = None
        IP = ip
        PORT = port
        # start listening to MQTT
        self.start_blocking()

    # --> Sub callback function, one per intent
    def turnOnHS100(self, hermes, intent_message):
        print("Allumer la prise, recu!")
        retmsg = ""
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.connect((ip, int(port)))
            sock_tcp.send(self.hs100encrypt('on'))
            data = sock_tcp.recv(2048)
            sock_tcp.close()
            retmsg = self.hs100decrypt(data[4:])
        except:
            retmsg = ("Could not connect to host %s:%s" %(str(ip), str(port)))

        hermes.publish_start_session_notification(intent_message.site_id, "Prise ON", "TP-Link-HS100")
        # terminate the session first if not continue
        hermes.publish_end_session(intent_message.session_id, "")

    def turnOffHS100(self, hermes, intent_message):
        print("Eteindre la prise, recu!")
        retmsg = ""
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.connect((ip, int(port)))
            sock_tcp.send(self.hs100encrypt('off'))
            data = sock_tcp.recv(2048)
            sock_tcp.close()
            retmsg = self.hs100decrypt(data[4:])
        except:
            retmsg = ("Could not connect to host %s:%s" %(str(ip), str(port)))
        # terminate the session first if not continue
        hermes.publish_end_session(intent_message.session_id, "")


    # More callback function goes here...

    # --> Master callback function, triggered everytime an intent is recognized
    def master_intent_callback(self,hermes, intent_message):
        coming_intent = intent_message.intent.intent_name
        if coming_intent == 'HS100On':
            self.turnOnHS100(hermes, intent_message)
        if coming_intent == 'HS100Off':
            self.turnOffHS100(hermes, intent_message)

        # more callback and if condition goes here...

    # --> Register callback function and start MQTT
    def start_blocking(self):
        with Hermes(MQTT_ADDR) as h:
            h.subscribe_intents(self.master_intent_callback).start()

    def hs100encrypt(string):
    	key = 171
    	result = pack('>I', len(string))
	for i in string:
		a = key ^ ord(i)
		key = a
		result += chr(a)
	return result

    def hs100decrypt(string):
	key = 171
	result = ""
	for i in string:
		a = key ^ ord(i)
		key = ord(i)
		result += chr(a)
	return result

if __name__ == "__main__":
    Skill_TPL_HS100()
