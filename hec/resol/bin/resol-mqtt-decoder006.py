#!/usr/bin/python3
# -------------------------------------------------------------------
# Python programme for digesting adata via serial port
# and decoding binary file produced by the RESOL BS/4 (Deltasol BS 2009)
# and transmitting processed data via mqtt
#
# Author G. Naylor May 2018 
# V001 first version
# V002 added MQTT functionality and serial port listening functionality
# V003 changed serial port handling to not use a local file
# V004 debuging completed, now using bytearray - removed some functions
# V005 production version, added print to standard out for hecpi
# V006 Solved problem when S1 Panel Temp is below zero.  Now correctly reports negative temps.
# 
# Version 6

import os, sys, serial
import numpy as np
import paho.mqtt.publish as publish


debug = 0	# debug if True
mqtt_ON = True	# send MQTT packets if True
#mqtt_ON = False	# dont send MQTT packets if False

# Configuration Variables
_mqtt_host = "0.0.0.0"			# IP address of your MQTT Broker
_mqtt_topic = "resol/prod/single"	# Topic 

#------------------- functions -----------------------------------------
def _septett(frame_array):
	# function to extract the septett byte and reset the necessary
	# MSB's of the bytes passed in array
	# array is always 6 bytes (the frame) 
	# the septett byte is 5, checksum is 6 we only consider first 4 bytes
	# note array index goes from 0 - 5 
	septett = (frame_array[4])
	# work through the first nibble of septett byte
	for bit in range(0,4):
			if (septett & 2**bit):
				# need to flip the MSB
				value = (frame_array[bit])
				frame_array[bit]=(int(np.bitwise_or(value, 128)))
	return frame_array

def process_frame(frame_num, all_frames):
	frame_start=startpos+10+((frame_num-1)*6)
	frame_data=all_frames[frame_start:frame_start+6]
	frame_data2 = _septett(frame_data) # reset the MSB's as per septett
	return frame_data2
	

#-------------------- functions end ------------------------------------

#-------------------- main program -------------------------------------
# try to open serial port, serial0 on a Raspberry Pi Zero with the overlay for using the hw uart
try:
	ser = serial.Serial(port='/dev/serial0',baudrate=9600,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,timeout=3)
	if debug: 
		print("Port Opened .... listening")
	data=[]
	cnt=0
	LOOP=190
                    
except:
		print("Error opening serial port.  Exiting")
		sys.exit(1)

# create a buffer string for storing data in.
# needs to be a binary data buffer
buffer = bytearray()	# create a byte array to hold binary data

# read serial port data and write to a file	
while cnt < LOOP:
	w = ser.inWaiting()  	# for pyserial > V2.7
	if w > 0:
		data = ser.read(w)
		buffer.extend(data)
		cnt = cnt + w
		if debug: print("Got %s bytes" % cnt)

ser.close()	# close the serial port

if debug:
       print("Buffer contains:\n")
       print(buffer)
       print("Buffer length: %s " % len(buffer))

# now read all bytes and look for \xAA (170) sync byte
_syncs=[]

for d in range(0,len(buffer)-1):
        if ( buffer[d] == 170):
            _syncs.append(d)
            if debug: print("Postion: %s" % d)
            if debug: print("Syncs are: %s" % _syncs)

# For each sync found check the destination address, we are only interested in destination addresses
# that have the value 0x10 (16).  
# Destination address LSB is at sync + 1 byte offset
syncs=[]
for i in _syncs:
	if (buffer[i+1] == 16):
		if debug: print("Data at sync is: %s" % buffer[i+1])
		syncs.append(i)

# debug
if debug: print("Got %s correct messages" % len(syncs))

# check we have got at least one correct message type, if not exit
if len(syncs) == 0:
	print("Error : No corect message types found in file to process!")
	print()
	sys.exit(1)
	
# Now to decode the number of frames, just take the first message
startpos=syncs[0]

# number of frames is in offset + 8
frames = buffer[startpos + 8]

output=""

# ----------------------------------------------------------------------
# FRAME 1 [ bytes 0-3 ]
# 0 temperature sensor S1 LSB
# 1 temperature sensor S1 MSB
# 2 temperatire sensot S2 LSB
# 3 temperature sensor S2 MSB
frame_bytes=process_frame(1,buffer)
S1_Temp = (256*(frame_bytes[1]))+(frame_bytes[0]) # Panel Temp 
S2_Temp = ((256*(frame_bytes[3]))+(frame_bytes[2]))*0.1 # Water Temp

# Test value below for testing -negative temp handling
# S1_Temp = 65525

# Check is S1 Temp is below freezing (Value will have wrapped around 16 bit number)
if S1_Temp > 1800:			# > 180 C
	S1_Temp = -(65535 - S1_Temp)

# Scale S1_Temp correctly
S1_Temp = S1_Temp * 0.1
	

if debug: print()
if debug: print("Temperature Sensor 1 is: %0.1f C" % S1_Temp)
if debug: print("Temperature Sensor 2 is: %0.1f C" % S2_Temp)

# ----------------------------------------------------------------------
# FRAME 2 [ bytes 4 - 7 ]
# 4 temperature sensor S3/s4 4 bytes
#         ignored 
# ----------------------------------------------------------------------
# FRAME 3 [ bytes 8,9,10,11 ]
# 8  Pump Speed 1 (percentge)
# 9  not used
# 10 Pump 1 Operating Hours LSB
# 11 Pump 1 Operating Hours MSB
frame_bytes=process_frame(3,buffer)
PumpSpeed = (frame_bytes[0])
HoursPumped = ((256*(frame_bytes[3]))+(frame_bytes[2]))

if debug: print("Pump Speed is %s percent" % PumpSpeed)
if debug: print("Hours Pumped is %s Hours" % HoursPumped)

# ----------------------------------------------------------------------
# FRAME 4 [ bytes 12-15 ]
# 12 Pump Speed 2 - etc ignored
# ----------------------------------------------------------------------
# FRAME 6 [ bytes 20 - 23 ]
# 20 Error Mask
# 13 Error Mask
# 14 System Time LSB
# 15 System Time MSB
frame_bytes=process_frame(6,buffer)
Error = ((256*(frame_bytes[1]))+(frame_bytes[0]))
UnitTime = (256*((frame_bytes[3]))+(frame_bytes[2]))
Hours = int(UnitTime / 60)
Minutes = int(UnitTime % 60)
if debug: print("System Time is %s:%s" % (Hours, Minutes))
if debug: print("Error Mask %s" % Error)

# --------------------- end of frames ----------------------------------
# formatoutput data in the following format
# hh:mm,S1Temp,S2Temp,PumpSpeed%, TotalHrsPumped, Error Status, 
# Example "18:07,8.3,34.5,0,8104,0"

# format output correctly into _payload string
payload = "{:02}:{:02},{:.1f},{:.1f},{},{},{}".format(Hours, Minutes, S1_Temp, S2_Temp, PumpSpeed, HoursPumped, Error)
if debug:
	print(payload)

# send via MQTT
if mqtt_ON:
	publish.single(_mqtt_topic,payload, hostname=_mqtt_host)
	if debug:
		print("MQTT Packet Sent")

# print out data to standard output
# required for hecpi but no longer used
#print(payload+",")

# Exit
sys.exit(0)
