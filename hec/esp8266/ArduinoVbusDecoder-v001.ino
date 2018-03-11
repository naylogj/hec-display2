/* VBUS decoder sketch to MQTT for ESP8266 
 * Author : G. Naylor 
 * Version 001
 * 
 * Version History
 * Version 001 - strip out not needed code, make specific for BS/4 (DeltaSol 2009)
 *             - send decoded values to serial port
 * Version 002 - [todo]connect to Wifi, Connect to MQTT, send values via MQTT
 * Version 003 - [todo]production  
 * 
 * Modified from and credit acknowledged to below:
 * 
 * VBus decoder to Domoticz sketch for Arduino
 * * 
 * Version 1.1 - August 2017 - Added Joule / Resol Deltasol C (credits: Fatbeard)
 * Version 1.0 - January 2016
 * 
 * Copyright (c) 2016 - 'bbqkees' @ www.domoticz.com/forum
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software
 * and associated documentation files (the "Software"), to deal in the Software without restriction,
 * including without limitation the rights to use, copy, modify, merge, publish, distribute,
 * sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
 * TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 * 
 * Legal Notices
 * RESOL, VBus, VBus.net and others are trademarks or registered trademarks of RESOL - Elektronische Regelungen GmbH.
 * All other trademarks are the property of their respective owners.
 * 
 * 
 * * What does it do?
 * This sketch reads the VBus data and depending on the format of the controller decodes
 * the data and puts in in variables.
 * You can then send the values via HTTP GET requests to Domoticz.
 * 
 * In this sketch the VBus data is read out continously and send periodically to Domoticz
 * If the VBus is read out periodically, it sometimes reads nothing and you get all zero's.
 * 
 * * Currently supports the following controllers:
 * -Resol DeltaTherm FK (a.k.a. Oranier Aquacontrol III) 
 * -Conergy DT5
 * -Joule / Resol Deltasol C
 * If it does not find any of the supported controllers,
 * it will try to decode the first 2 frames which usually contain Temp 1 to 4.
 * 
 * * My controller is not in your list, how can I add it?
 * Go to http://danielwippermann.github.io/resol-vbus/vbus-packets.html
 * and find your controller. In the list you can see which information the controller sends.
 * You need the controller ID and offset, bitsize and names of all the variables.
 * Now use the examples for the DT5 and FK in VBusRead()
 * to create a new entry for your own controller.
 * 
 * Sketch is based on VBus library from 'Willie' from the Mbed community.
 *  
 */

long intervalvbus = 30000;   // interval at which to send data (milliseconds)

// Settings for the VBus decoding
#define Sync  0xAA  // Synchronisation bytes
#define FLength 6   // Framelength
#define FOffset 10  // Offset start of Frames
#define FSeptet 4   // Septet byte in Frame
#define ResolAddress 0x427B  //   BS/4 (DeltaSol BS 2009) Controller ID

// BS DeltaSol 2009 Specific Variables
float Sensor1_temp;
float Sensor2_temp;
char PumpSpeed1;  // in  %
char RelayMask;
char ErrorMask;
uint16_t OperatingHoursRelay1;
uint16_t Version;
uint16_t OperatingHoursRelay1Today;
uint16_t SystemToalTime;
uint16_t SystemHours;
uint16_t SystemMinutes;

unsigned char Buffer[80];
volatile unsigned char Bufferlength;

unsigned int Destination_address;
unsigned int Source_address;
unsigned char ProtocolVersion;
unsigned int Command;
unsigned char Framecnt;
unsigned char Septet;
unsigned char Checksum;

long lastTimeTimer;
long timerInterval;
bool all;

// Set to "1" when debugging 
// If enabled, the ESP8266 sends the decoded values over the Serial port.
// If enabled it also prints the source address in case you do not
// know what controller(s) you have.
#define DEBUG 0


void setup() {
Serial1.begin(9600);
#if DEBUG
Serial.begin(9600);
Serial.println("ESP8266 debugging started");
#endif

// for V2+ add code to setup and connect to Wifi here
// add code to setup payload and MQTT connection here


all=false;
} // end void setup()

void loop() {

if (VBusRead()){
  #if DEBUG
        Serial.println("------Decoded VBus data------");
        Serial.print("Destination: ");
        Serial.println(Destination_address, HEX);
        Serial.print("Source: ");
        Serial.println(Source_address, HEX);
        Serial.print("Protocol Version: ");
        Serial.println(ProtocolVersion);
        Serial.print("Command: ");
        Serial.println(Command, HEX);
        Serial.print("Framecount: ");
        Serial.println(Framecnt);
        Serial.print("Checksum: ");
        Serial.println(Checksum);
        Serial.println("------Values------");
        Serial.print("Sensor 1: ");
        Serial.println(Sensor1_temp);
        Serial.print("Sensor 2: ");
        Serial.println(Sensor2_temp);
        Serial.print("Relay 1: ");
        Serial.println(Relay1, DEC);
        Serial.println("------END------");
#endif
} //end VBusRead

  // loop for VBus readout
  // This loop is executed every intervalvbus milliseconds.
  if(millis() - lastTimevbus > intervalvbus) {
    lastTimevbus = millis(); 


// The following is needed for decoding the data
void  InjectSeptet(unsigned char *Buffer, int Offset, int Length) {
    for (unsigned int i = 0; i < Length; i++) {
        if (Septet & (1 << i)) {
            Buffer [Offset + i] |= 0x80;
        }
    }
}


// The following function reads the data from the bus and converts it all
// depending on the used VBus controller.
bool VBusRead() {
    int F;
    char c;
    bool start,stop,quit;

    start = true;
    stop = false;
    quit = false;
    Bufferlength=0;
    lastTimeTimer = 0;
    lastTimeTimer = millis();

    while ((!stop) and (!quit))  {
          if (Serial1.available()) {
              c=Serial1.read();
            
char sync1 = 0xAA;
            if (c == sync1) {

#if DEBUG
           // Serial.println("Sync found");
#endif
              
                if (start) {
                    start=false;
                    Bufferlength=0;
//#if DEBUG
//#endif
                } else {
                    if (Bufferlength<20) {
                       lastTimeTimer = 0;
                       lastTimeTimer = millis();
                        Bufferlength=0;
                    } else
                        stop=true;
                }
            }
#if DEBUG
           // Serial.println(c, HEX);
#endif
            if ((!start) and (!stop)) {
                Buffer[Bufferlength]=c;
                Bufferlength++;
            }
        }
        if ((timerInterval > 0) &&  (millis() - lastTimeTimer > timerInterval )  ) {
            quit=true;
#if DEBUG
         //   Serial.print("Timeout: ");
         //   Serial.println(lastTimeTimer);
#endif
        }
    }

   lastTimeTimer = 0;

    if (!quit) {
        Destination_address = Buffer[2] << 8;
        Destination_address |= Buffer[1];
        Source_address = Buffer[4] << 8;
        Source_address |= Buffer[3];
        ProtocolVersion = (Buffer[5]>>4) + (Buffer[5] &(1<<15));

        Command = Buffer[7] << 8;
        Command |= Buffer[6];
        Framecnt = Buffer[8];
        Checksum = Buffer[9];  //TODO check if Checksum is OK
#if DEBUG
        Serial.println("---------------");
        Serial.print("Destination: ");
        Serial.println(Destination_address, HEX);
        Serial.print("Source: ");
        Serial.println(Source_address, HEX);
        Serial.print("Protocol Version: ");
        Serial.println(ProtocolVersion);
        Serial.print("Command: ");
        Serial.println(Command, HEX);
        Serial.print("Framecount: ");
        Serial.println(Framecnt);
        Serial.print("Checksum: ");
        Serial.println(Checksum);
        Serial.println("---------------");
#endif
        // Only analyse Commands 0x100 = Packet Contains data for slave
        // with correct length = 10 bytes for HEADER and 6 Bytes  for each frame

        if ((Command==0x0100) and (Bufferlength==10+Framecnt*6)) {

          //Only decode the data from the correct source address
          //(There might be other VBus devices on the same bus).
          
          if (Source_address ==0x427B){
#if DEBUG
        Serial.println("---------------");
        Serial.println("Now decoding for 0x427B");
        Serial.println("---------------");  
#endif

            // Frame info for the Resol Deltasol BS 2009 (BS4)
            // check VBusprotocol specification for other products
            
            //Off FR  Size    Mask    Name                    Factor  Unit
            //0   F1  2               Temperature sensor 1    0.1     &#65533;C
            //2   F1  2               Temperature sensor 2    0.1     &#65533;C 
            //4   F2  2               Temperature sensor 3    0.1     &#65533;C
            //6   F2  2               Temperature sensor 4    0.1     &#65533;C
            //8   F3  1               Pump speed relay 1      1       %
            //12  F3  1				  Pump speed relay 2      1       %
            //10  F3  2               Operating hours relay 1 1       h
            //14  F4  2               Operating hours relay 2 1       h
            //16  F4  1               Unit Type               1
            //17  F4  1               System                  1
            //20  F5  2               Error mask              1
            //20  F5  1       1       Sensor 1 defective      1       bit
            //20  F5  1       2       Sensor 2 defective      1       bit
            //20  F5  1       4       Sensor 3 defective      1       bit
            //20  F5  1       8       Sensor 4 defective      1       bit
            //22  F5  2               System Time             1       minutes
            //24  F6  4               Status Mask             1
            //28  F7  4               Heat quantity           1       Wh
            //32  F8  2               SV Version              0.01
            //34  F8  2               Variant                 1
            //
            // Each frame has 6 bytes
            // byte 1 to 4 are data bytes -> MSB of each bytes
            // byte 5 is a septet and contains MSB of bytes 1 to 4
            // byte 6 is a checksum
            //
            //*******************  Frame 1  *******************
            F=FOffset;
            Septet=Buffer[F+FSeptet];
            InjectSeptet(Buffer,F,4);

            // 'collector1' Temperatur Sensor 1, 15 bits, factor 0.1 in C
            Sensor1_temp =CalcTemp(Buffer[F+1], Buffer[F]);
            // 'store1' Temperature sensor 2, 15 bits, factor 0.1 in C
            Sensor2_temp =CalcTemp(Buffer[F+3], Buffer[F+2]);

            //*******************  Frame 2  *******************
            // not needed
            
            //*******************  Frame 3  *******************
            F=FOffset+FLength*2;
            Septet=Buffer[F+FSeptet];
            InjectSeptet(Buffer,F,4);

            PumpSpeed1 = (Buffer[F] & 0X7F);
            OperatingHoursRelay1=Buffer[F+3] << 8| Buffer[F+2];
      
            //*******************  Frame 4  *******************
            // not needed

            //*******************  Frame 5  *******************
            F=FOffset+FLength*4;
            Septet=Buffer[F+FSeptet];
            InjectSeptet(Buffer,F,4);
 
            ErrorMask  = Buffer[F];
            SystemTotalTime = Buffer[F+3] << 8| Buffer[F+2];
            SystemMinutes = SystemTotalTime % 60;
            SystemHours = int(SystemTotalTime/60);

            //*******************  Frame 6  *******************
            // not needed          

            //*******************  Frame 7  *******************
            F=FOffset+FLength*6;
            Septet=Buffer[F+FSeptet];
            InjectSeptet(Buffer,F,4);

            HeatQuantity=(Buffer[F+1] << 8 | Buffer[F])+(Buffer[F+3] << 8| Buffer[F+2])*1000;
            
           //*******************  Frame 8  *******************
            F=FOffset+FLength*7;
            Septet=Buffer[F+FSeptet];
            InjectSeptet(Buffer,F,4);
            
            Version=Buffer[F+3] << 8| Buffer[F+2];

            ///******************* End of frames ****************

           }// end 0x427B Deltasol BS 2009        
        } // end if command 0x0100
    } // end !quit

    return !quit;
} // end VBusRead()


// This function converts 2 data bytes to a temperature value.
float CalcTemp(int Byte1, int Byte2) {
   int v;
    v = Byte1 << 8 | Byte2; //bit shift 8 to left, bitwise OR

    if (Byte1 == 0x00){
    v= v & 0xFF;  
    }

    if (Byte1 == 0xFF)
        v = v - 0x10000;

    if (v==SENSORNOTCONNECTED)
        v=0;

    return (float)((float) v * 0.1);
    }    

