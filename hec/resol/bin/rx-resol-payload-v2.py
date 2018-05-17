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
# V002 modified to calculate max temp gain in the day and hours pumped
# V002.1 Bugfix for hours
# 
# Version 2.1

import os, sys, time
import paho.mqtt.subscribe as subscribe

debug = 0	# debug if True

# Configuration Variables
_mqtt_host = "192.x.y.z"						# IP address of MQTT Broker
_mqtt_topic = "resol/prod/single"				# Topic 
_datafile = "/home/pi/resol/www/hwinst.json"	# 
_message = ""									# string for holding message
_buffer = []									# list for holding data

# set global variables for temp max and temp min
tmax=float(0)
tmin=float(150)
# samples a global boolean flag for if we have more that one dataset
# after program has been started
samples = False		

st_hours_pumped = float(8377)	# random initial setting

# incoming message format is
#    0         1            2           3            4             5
# hh:mm , panel temp , water temp , pump%speed , hrs pumped , error status

# ---------------------- functions ------------------------------------
def got_msg(client, userdata, message):
    
    global tmax , tmin , samples , st_hours_pumped
    _message = message.payload.decode('ascii')
    _buffer = _message.split(",")
    if debug:
        print("%s : %s" % (message.topic, message.payload))
        # put payload into _buffer
        print("_message contains:")
        print(_message)
        print("_buffer contains:")
        print(_buffer)
        
	# now calculate max temp gain
    wtemp=float(_buffer[2])
    if debug: print("Water Temp is %s degress" % wtemp)
    if wtemp > tmax:
        tmax = wtemp
    elif wtemp < tmin:
        tmin = wtemp
    
    if debug: print("tmax is now: %s degress" % tmax)
    if debug: print("tmin is now: %s degress" % tmin)

    if wtemp > tmin:
        tgain=round(tmax-tmin,1)
    else: 
        tgain=round(tmin-tmax,1)   
		
    # now calculate number of hours pumped.
    # assume no generation before 05:00am - so capture the number of hours pumped
    # at start of day and reset the temp min and max for the day to current temp
    # changed for v2.1 this line had a bug --> hours = int(time.strftime("%H").lstrip('0'))
    hours = int(time.strftime("%H"))
    if hours < 5:
        st_hours_pumped = float(_buffer[4])
        tmax = wtemp
        tmin = wtemp
        
    # now calculate hours_pumped
    hrs_pumped = float(_buffer[4]) - st_hours_pumped
    
    # check if this is the first time this program has run
    # if it is then we do not know any info about temp gain
    # or hours pumped, so set them both to 0 but then
    # set samples flag to True so next time around we get data
   
    if not samples:
        hrs_pumped = float(0)
        tgain = float(0)
        tmin = wtemp	# this is first time running today, so set min temp to current
        samples = True	# flip the flag
	
	# debugging lets see what we have
    if debug: print("Temp gain is %s degress" % tgain)
    if debug: print("Hours Pumped %s" % hrs_pumped)
   
    # put the new data in to the buffer as strings
    _buffer.append(str(tgain))
    _buffer.append(str(hrs_pumped))

    if debug:
        print("_buffer now contains:")
        print(_buffer)
	 
    # so we now have some data so store it in a file
    # for the HEC-code to pick up
    # ensure we can write a file
    try:
        f=open(_datafile,"w+")		# open the file for non binary write
        f.write(','.join(_buffer))	# write the buffer as a CSV string
        f.close()					# close the file
    except:
        print("Error writing to %s " % _datafile)
        f.close()					# ensure file handle is closed
	
# ---------------------- main -----------------------------------------

# Setup connection to MQTT queue and wait for a message.
# when a message arrives call funcion got_msg
#

# line below will sit and wait for a message and then run got_msg()
subscribe.callback(got_msg, _mqtt_topic, hostname=_mqtt_host)



sys.exit(0)
