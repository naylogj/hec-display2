/*
 *  ESP8266 Programm to take output from a Resol BS/4 Solar Hot Water Pump Controller
 *  decode its output and publish its data using MQTT over WiFi for consumption
 *  Author: G. Naylor
 *  ----------------
 *  V001  - initial version to get WiFi working
 *  V001  - added MQTT pub-sub with dummy payload
 */

// dependencies 
// Arduino Libraries for the esp8266
// Adafruit MQTT Arduino libraries

#include <ESP8266WiFi.h>
#include "Adafruit_MQTT.h"
#include "Adafruit_MQTT_Client.h"

// settings for wifi
const char* ssid     = "yourNetworkSSID";
const char* password = "yourWiFiPassowrd";

// dummy MQTT payload defined below.  replace with your code in loop()
const uint8_t payload = 19;		// this is the MQTT payload (message)


// settings for mqtt

#define MQTT_SERVER      "192.168.x.y"		// replace with IP address of MQTT server
#define MQTT_SERVERPORT  1883                   // use 8883 for SSL
//#define MQTT_USERNAME    "user id"		// uncomment if needed
//#define MQTT_PW         "mqtt password"	// uncomment if needed


// Create an ESP8266 WiFiClient class to connect to the MQTT server.
WiFiClient client;

// Setup the MQTT client class by passing in the WiFi client and MQTT server and login details.
// Adafruit_MQTT_Client mqtt(&client, MQTT_SERVER, MQTT_SERVERPORT, MQTT_USERNAME, MQTT_PW);
Adafruit_MQTT_Client mqtt(&client, MQTT_SERVER, MQTT_SERVERPORT);

// Setup a feed called 'resol/temperature' for publishing.

#define FEED "resol/temperature"

Adafruit_MQTT_Publish ap = Adafruit_MQTT_Publish(&mqtt, FEED);


// Bug workaround for Arduino 1.6.6, it seems to need a function declaration
// for some reason (only affects ESP8266, likely an arduino-builder bug).
void MQTT_connect();

//----------------------------------- SETUP -----------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(100);

  // We start by connecting to a WiFi network

  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");  
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Netmask: ");
  Serial.println(WiFi.subnetMask());
  Serial.print("Gateway: ");
  Serial.println(WiFi.gatewayIP());
  
}

//------------------------------------------------- LOOP ---------------------------------------------------

void loop() {
  
  // Ensure the connection to the MQTT server is alive (this will make the first
  // connection and automatically reconnect when disconnected). 
  MQTT_connect(); 

  Serial.print("MQTT Connected");


 // put code here to read the sensor 
 // put the sensor value into the uint_t variable 'payload'

  
  delay(1000);

 // send the data via MQTT over WiFi
  if (! ap.publish(payload, sizeof(payload)))
        Serial.println(F("Publish Failed."));
      else {
        Serial.println(F("Publish Success!"));
        delay(500);
      }

      delay(10000);  // just a delay to ensure readings are not sent all the time.
  
  }
  

// --------------------------------------------- OTHER FUNCTIONS --------------------------------------------
// Function to connect and reconnect as necessary to the MQTT server.
// Should be called in the loop function and it will take care if connecting.

void MQTT_connect() {
  int8_t ret;

  // Stop if already connected.
  if (mqtt.connected()) {
    return;
  }

  Serial.print(F("Connecting to MQTT... "));

  uint8_t retries = 3;
  while ((ret = mqtt.connect()) != 0) { // connect will return 0 for connected
       Serial.println(mqtt.connectErrorString(ret));
       Serial.println(F("Retrying MQTT connection in 5 seconds..."));
       mqtt.disconnect();
       delay(5000);  // wait 5 seconds
       retries--;
       if (retries == 0) {
         // basically die and wait for WDT to reset me
         while (1);
         }
     }
}
