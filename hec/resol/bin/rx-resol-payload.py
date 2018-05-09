#!/usr/bin/python3
# -------------------------------------------------------------------
# Python programme for reciving a test payload over MQTT
# for the RESOL BS/4 (Deltasol BS 2009)
# and writing the values to "/home/pi/resol/www/hwinst.json"
# so that the hecpi/bin/nook-web-hecdisplay-v303.py file can
# read the data and display it
#
# Author G. Naylor May 2018
# V001 first version
# 
# 
# Version 1

import os, sys, serial
import paho.mqtt.subscribe as subscribe

debug = 1	# debug if True

# Configuration Variables
_mqtt_host = "192.168.x.y"
_mqtt_topic = "resol/test/single"				# Topic 
_datafile = "/home/pi/resol/www/hwinst.json"	# its not json!

# ---------------------- functions ------------------------------------
def got_msg(client, userdata, message):
    
    if debug:
        print("%s : %s" % (message.topic, message.payload))

    # so we now have some data so store it in a file
    # for the HEC-code to pick up
    # esure we can write a file
    try:
        f=open(_datafile,"w")		# open the file
        f.write(message.payload.decode('ascii'))	# write the payload (convert from bin)
        f.close()					# close the file
    except:
        print("Error writing to {} ", _datafile)
        f.close()					# ensure file handle is closed
	
# ---------------------- main -----------------------------------------

# Setup connection to MQTT queue and wait for a message.
# when a message arrives call funcion got_msg
#
subscribe.callback(got_msg, _mqtt_topic, hostname=_mqtt_host)



sys.exit(0)
