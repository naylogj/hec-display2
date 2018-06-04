#!/usr/bin/python2

# python script to recieve data from OWl Intuition
# via multicast 
# V1 working
# V2 ammend to send data over MQTT
# V3 ammend to send data to thingsboard over MQTT

from twisted.internet.protocol import DatagramProtocol
from decimal import Decimal
import socket
import re
import os, sys, time, json
import paho.mqtt.publish as publish

# set debug to 1 for extra messages
debug=0
mqtt_ON = True	# send MQTT packets if true
thingsboard = True # if true send data to things_board
ACCESS_TOKEN = "your-access-token"		# token for HEC2 device

# Configuration Variables
_mqtt_host = "192.xx.yy.zz"						# IP address of MQTT Broker
_mqtt_topic = "owl/prod/single"				# Topic 
_message = ""									# string for holding message
_buffer = []									# list for holding data


# output data path
datadir="/home/pi/owl/data/"
soutfile=datadir + "solar-data"
eoutfile=datadir + "elec-data"

# setup network constants
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
MCAST_ADDR = '224.192.32.19'	# fixed by owl
MCAST_PORT = 22600 # fixed by owl


class OwlMessage(object):
	def __init__(self, datagram):
		
		# check what datagram we have got electricity or solar
		# a datagram pair is sent approx every 10 seconds
		
		if re.search('electricity', str(datagram)):
			DgramType="E"
			if debug: print(".. Got an Electricity datagram ..")
		else:
			if debug: print(".. Got an Solar datagram ..")
			DgramType="S"
			
			
		# extract values (remove everything that is not a "." or a number)
		v=re.sub(r'[^(\.|\-|0-9|\s)]',"", str(datagram))
		# remove duplicate whitespace and replace " " with "," to give a CSV row.
		r=",".join(v.split())	
		
		if debug: print(r)
		
		if DgramType=="E":
			# r now contains the following data, separated by comma (no spaces)
			# mac,	rssi, 	lqi,	batt level,	0,	watt0,	whday0,	1,	watt1, 	whday1,	2,	watt2,	whday2	
			# 0		1		2			3		4		5		6	7		8		9	10		11		12
			# we only want to use items [3] , [5], [6], [8], [9], [channel 2 is not used in my house]
			#
			vals = re.split(",", r)
			if len(vals)==13:
				if debug:
					print("================================")
					print(" Battery level: %s%%"  % vals[3])
					print(" Current Watts Chan0 is: %s" % vals[5])
					print(" kWH Chan0 so far today is: %s" % vals[6])
					print(" Current Watts Chan1 is: %s" % vals[8])
					print(" kWH Chan1 so far today is: %s" % vals[9])
					print("================================")
					print
				self.data = "E,"+str(vals[3])+","+str(vals[5])+","+str(vals[6])+","+"0.0"
			else:
				if debug: print("Rubbish Elec Data")
				self.data="Rubbish"
								
		elif DgramType=="S":
			# r now contains the following data, separated by comma (no spaces)
			# mac,	watt0,	exportw,	whday,	whexported
			# 0		1		2			3			4
			# we only want to use items [1] , [2], [3], [4]
			#
			vals = re.split(",", r)
			if len(vals)==5:
				if debug:
					print("=======================================")
					print(" Current Watts GEN is: %s" % vals[1])
					print(" Current Watts Exported is: %s" % vals[2])
					print(" kWH GEN so far today is: %s" % vals[3])
					print(" kWH Exported so far today is: %s" % vals[4])
					print("=======================================")
					print
				self.data = "S,"+str(vals[1])+","+str(vals[2])+","+str(vals[3])+","+str(vals[4])
			else:
				if debug: print("Rubbish Solar Data")
				self.data="Rubbish"
				
	def __str__(self):
		result = self.data
		return result


class OwlIntuitionProtocol(DatagramProtocol):
	def __init__(self, iface=''):
		"""
		Protocol for Owl Intution (Network Owl) multicast UDP.
	 
		:param iface: Name of the interface to use to communicate with the Network Owl.  If not specified, uses the default network connection on the cost.
		:type iface: str
		"""
		self.iface = iface

	def startProtocol(self):
		self.transport.joinGroup(MCAST_ADDR, self.iface)

	def datagramReceived(self, datagram, address):
		msg = OwlMessage(datagram)
		self.owlReceived(address, msg)

	def owlReceived(self, address, msg):
                global thingsboard
		global ACCESS_TOKEN
		if debug: print('%s' % (msg))
		# write solar data to one file
		if re.match('^S',str(msg)):
			_S = True
			f = open(soutfile, 'w')
			f.write(str(msg))
			f.close()
		# write elec data to another file
		elif re.match('^E',str(msg)):
			_S = False
			f = open(eoutfile, 'w')
			f.write(str(msg))
			f.close()
		
		# now send mqtt packet
		if mqtt_ON:
			publish.single(_mqtt_topic,str(msg), hostname=_mqtt_host)
		if debug:
			print("MQTT Packet Sent")

                if thingsboard and _S:
		    _vals = re.split(",", str(msg))
                    _tbhost = "demo.thingsboard.io"
                    # form the payload in key value pairs [{"key1":"value1"}, {"key2":"value2"}]
                    _payload = [ {"Gen":_vals[1]}, 
                                 {"Export":_vals[2]},
                                 {"kWH Today":_vals[3]},
                                 {"kWH Export Today":_vals[4]} ]

                    # send mqtt packet using the thingsboard preferences and token
                    # "v1/devices/me/telemetry" and using the access token as the user
                    # syntax for authorisation
                    try:
                        publish.single("v1/devices/me/telemetry", json.dumps(_payload), hostname=_tbhost, auth = {'username':ACCESS_TOKEN} )
                        if debug: 
                            print("Payload sent to thingsboard")
                    except:
                        pass

		# else rubbish data and do nothing
				
		
if __name__ == '__main__':
	from twisted.internet import reactor
	from argparse import ArgumentParser
	parser = ArgumentParser()
	parser.add_argument('-i', '--iface', dest='iface', default='', help='Network interface to use for getting data.')
	options = parser.parse_args()

	protocol = OwlIntuitionProtocol(iface=options.iface)
	reactor.listenMulticast(MCAST_PORT, protocol, listenMultiple=True)
	reactor.run()
