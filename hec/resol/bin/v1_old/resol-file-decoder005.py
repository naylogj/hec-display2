#!/usr/bin/python3
# -------------------------------------------------------------------
# Python programme for digesting and decoding binary file produced by the RESOL BS/4 (Deltasol BS 2009)
# Author G. Naylor March 2018
# V001 first version
# V002 fixed calculation bug for High Order bytes
# V003 functional - reports all data
# V004 functionalise code
# V005 Strip code to bare minimum.

import os, sys
import numpy as np

# debug if True
debug = 0

# source data
datafile = "/tmp/datafile"


#------------------- functions -----------------------------------------
def get_dec(value):
	# take a byte and return the decimal
	value_d = int.from_bytes(value, byteorder=sys.byteorder)
	return value_d

def to_bytes(value):
	# take a decimal value and return the byte
	value_d = value.to_bytes(1, byteorder=sys.byteorder)
	return value_d

def _septett(frame_array):
	# function to extract the septett byte and reset the necessary
	# MSB's of the bytes passed in array
	# array is always 6 bytes (the frame) 
	# the septett byte is 5, checksum is 6 we only consider first 4 bytes
	# note array index goes from 0 - 5 
	septett = get_dec(frame_array[4])
	# work through the first nibble of septett byte
	for bit in range(0,4):
			if (septett & 2**bit):
				# need to flip the MSB
				value = get_dec(frame_array[bit])
				frame_array[bit]=to_bytes(int(np.bitwise_or(value, 128)))
	return frame_array

def process_frame(frame_num, all_frames):
	frame_start=startpos+10+((frame_num-1)*6)
	frame_data=all_frames[frame_start:frame_start+6]
	frame_data2 = _septett(frame_data) # reset the MSB's as per septett
	return frame_data2
	

#-------------------- functions end ------------------------------------

# first task open a file
try:
		f = open(datafile, "rb")
		
except:
		print("File not found or cannot be opened error")
		sys.exit(1)
		
# now read all bytes into the file.
pos=0
_syncs=[]

byte = f.read(1)
i=get_dec(byte)
bb = bin(i)
buffer = [byte]
if (byte == b'\xaa'):
	_syncs.append(pos)

while byte:
	pos = pos +1
	byte = f.read(1)
	buffer.append(byte)
	if (byte == b'\xaa'):
		_syncs.append(pos)
f.close()

# For each sync found check the destination address, we are only interested in destination addresses
# that have the value 0x0010.  
# Destination address LSB is at sync + 1 byte offset
syncs=[]
for i in _syncs:
	if (buffer[i+1] == b'\x10'):
		# not destination 0x10 therefore drop from syncs
		syncs.append(i)

# check we have got at least one correct message type, if not exit
if len(syncs) == 0:
	print("Error : No corect message types found in file to process!")
	print()
	sys.exit(1)
	
# Now to decode the number of frames, just take the first message
startpos=syncs[0]

# number of frames is in offset + 8
frames = get_dec(buffer[startpos + 8])

output=""

# ----------------------------------------------------------------------
# FRAME 1 [ bytes 0-3 ]
# 0 temperature sensor S1 LSB
# 1 temperature sensor S1 MSB
# 2 temperatire sensot S2 LSB
# 3 temperature sensor S2 MSB
frame_bytes=process_frame(1,buffer)
S1_Temp = ((256*get_dec(frame_bytes[1]))+get_dec(frame_bytes[0]))*0.1
S2_Temp = ((256*get_dec(frame_bytes[3]))+get_dec(frame_bytes[2]))*0.1

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
PumpSpeed = get_dec(frame_bytes[0])
HoursPumped = ((256*get_dec(frame_bytes[3]))+get_dec(frame_bytes[2]))

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
Error = ((256*get_dec(frame_bytes[1]))+get_dec(frame_bytes[0]))
UnitTime = (256*(get_dec(frame_bytes[3]))+get_dec(frame_bytes[2]))
Hours = int(UnitTime / 60)
Minutes = UnitTime % 60
if debug: print("System Time is %s:%s" % (Hours, Minutes))
if debug: print("Error Mask %s" % Error)

# --------------------- end of frames ----------------------------------
# echo data out of standard output in the following format
# hh:mm,S1Temp,S2Temp,PumpSpeed%, TotalHrsPumped, Error Status, 
# 18:07,8.3,34.5,0,8104,0,

print("{}:{},{:.1f},{:.1f},{},{},{},".format(Hours, Minutes, S1_Temp, S2_Temp, PumpSpeed, HoursPumped, Error))

sys.exit(0)
