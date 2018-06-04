#!/usr/bin/python3
# -------------------------------------------------------------------
# Python programme for sending a test payload over MQTT
# for the RESOL BS/4 (Deltasol BS 2009)
# 
#
# Author G. Naylor May 2018
# V001 first version
# 
# 
# Version 1

import os, sys, serial
#import numpy as np
import paho.mqtt.publish as publish


debug = 1	# debug if True
mqtt_ON = True	# send MQTT packets if true


# Configuration Variables

_mqtt_host = "192.168.x.y"			# IP address of MQTT Broker
_mqtt_topic = "resol/test/single"	# Topic 


# --------------------- construct payload ------------------------------
# formatoutput data in the following format
# hh:mm,S1Temp,S2Temp,PumpSpeed%, TotalHrsPumped, Error Status, 
# Example "18:07,8.3,34.5,0,8104,0"

Hours = 19
Minutes = 17
S1_Temp = 80.5
S2_Temp = 45.7
PumpSpeed = 60
HoursPumped = 3
Error = 0

# format output correctly into _payload string

payload = "{:02}:{:02},{:.1f},{:.1f},{},{},{}".format(Hours, Minutes, S1_Temp, S2_Temp, PumpSpeed, HoursPumped, Error)


if debug:
	print(payload)


# send via MQTT
if mqtt_ON:
	publish.single(_mqtt_topic,payload, hostname=_mqtt_host)
	if debug:
		print("MQTT Packet Sent")



sys.exit(0)
