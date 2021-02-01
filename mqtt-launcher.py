#!/usr/bin/env python

# Copyright (c) 2014 Jan-Piet Mens <jpmens()gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of mosquitto nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

__author__    = 'Jan-Piet Mens <jpmens()gmail.com>'
__copyright__ = 'Copyright 2014 Jan-Piet Mens'

import os
import sys
import subprocess
import logging
import paho.mqtt.client as paho   # pip install paho-mqtt
import time
import socket
import string
from hashlib import sha1

qos=2
CONFIG=os.getenv('MQTTLAUNCHERCONFIG', 'launcher.conf')

class Config(object):
    def __init__(self, filename=CONFIG):
        self.config = {}
        exec(compile(open(filename, "rb").read(), filename, 'exec'), self.config)

    def get(self, key, default=None):
        return self.config.get(key, default)

try:
    cf = Config()
except Exception as e:
    print("Cannot load configuration from file %s: %s" % (CONFIG, str(e)))
    sys.exit(2)

LOGFILE = cf.get('logfile', 'logfile')
LOGFORMAT = '%(asctime)-15s %(message)s'
DEBUG=True

if DEBUG:
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG, format=LOGFORMAT)
else:
    logging.basicConfig(filename=LOGFILE, level=logging.INFO, format=LOGFORMAT)

logging.info("Starting")
logging.debug("DEBUG MODE")

def runprog(msg_topic, param=None):

    strip_pref = "%s/" % topic_prefix
    topic = msg_topic[msg_topic[:len(strip_pref)].index(strip_pref) + len(strip_pref):]
    print (topic)

    topic_report = "%s/report" % msg_topic

    if param is not None and all(c in string.printable for c in param) == False:
        logging.debug("Param for topic %s is not printable; skipping" % (topic))
        return

    if not topic in topiclist:
        logging.info("Topic %s isn't configured" % msg_topic)
        return

    if param is not None and param in topiclist[topic]:
        cmd = topiclist[topic].get(param)
    else:
        if None in topiclist[topic]: ### and topiclist[topic][None] is not None:
            cmd = [p.replace('@!@', param) for p in topiclist[topic][None]]
        else:
            logging.info("No matching param (%s) for %s" % (param, msg_topic))
            return

    logging.debug("Running t=%s: %s" % (msg_topic, cmd))

    try:
        res = subprocess.check_output(cmd, stdin=None, stderr=subprocess.STDOUT, shell=False, universal_newlines=True, cwd='/tmp')
    except Exception as e:
        res = "*****> %s" % str(e)

    payload = res.rstrip('\n')
    (res, mid) =  mqttc.publish(topic_report, payload, qos=qos, retain=False)


def on_message(mosq, userdata, msg):
    logging.debug(msg.topic+" "+str(msg.qos)+" "+msg.payload.decode('utf-8'))
    runprog(msg.topic, msg.payload.decode('utf-8'))

def on_connect(mosq, userdata, flags, result_code):
    status_payload_running = cf.get('status_payload_running', 'running')
    mqttc.publish(
        status_topic, status_payload_running, qos=1, retain=True
    )
    logging.info("Current status set on %r as %r.", status_topic, status_payload_running)

    logging.debug("Connected to MQTT broker (client id: %s), subscribing to topics...", client_id)
    for topic in topiclist:
        msg_topic = "%s/%s" % (topic_prefix, topic)
        mqttc.subscribe(msg_topic, qos)
        logging.info("Subscribed to topic: %r", msg_topic)

    logging.info("Waiting for subscribed topic messages.")

def on_disconnect(mosq, userdata, rc):
    logging.info("Disconnected from MQTT broker.")

if __name__ == '__main__':

    userdata = {
    }
    topiclist = cf.get('topiclist')

    if topiclist is None:
        logging.info("No topic list. Aborting")
        sys.exit(2)

    topic_prefix = cf.get('topic_prefix', 'mqtt-launcher')
    client_id = cf.get('mqtt_clientid', 'mqtt-launcher-%s' % sha1(topic_prefix.encode("utf8")).hexdigest())
    
    # initialise MQTT broker connection
    mqttc = paho.Client(client_id, clean_session=False)
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_disconnect = on_disconnect
    
    # Set last will and testament (LWT)
    status_topic = "%s/%s" % (topic_prefix, cf.get('status_topic', 'status'))
    status_payload_dead = cf.get('status_payload_dead', 'dead')
    mqttc.will_set(
        status_topic, payload=status_payload_dead, qos=1, retain=True
    )
    logging.info("Last will set on %r as %r.", status_topic, status_payload_dead)

    # Delays will be: 3, 6, 12, 24, 30, 30, ...
    #mqttc.reconnect_delay_set(delay=3, delay_max=30, exponential_backoff=True)

    if cf.get('mqtt_username') is not None:
        mqttc.username_pw_set(cf.get('mqtt_username'), cf.get('mqtt_password'))

    if cf.get('mqtt_tls') is not None:
        mqttc.tls_set()

    mqttc.connect(cf.get('mqtt_broker', 'localhost'), int(cf.get('mqtt_port', '1883')), 60)

    try:
        while True:
            mqttc.loop_forever()
    except socket.error:
        time.sleep(5)
    except KeyboardInterrupt:
        mqttc.publish(
            status_topic, cf.get('status_payload_stopped', 'stopped'), qos=1, retain=True
        )

        mqttc.loop_stop()
        mqttc.disconnect()
        mqttc.loop_forever()
        
        logging.debug("Exiting")
