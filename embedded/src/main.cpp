#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h> 
#include <ArduinoJson.h>
#include "env.h"
#include <cstdlib>
#include <string>
#include <iostream>
#include <OneWire.h>
#include <DallasTemperature.h>

//need JSON objects to read the JSON coming from server for get
#define FanPin 22 
#define LampPin 23
#define temp_sensor 21
#define motion_sensor 20

float sunset;
OneWire oneWire(temp_sensor);
DallasTemperature sensors(&oneWire);


void setup() 
{ 
  pinMode (FanPin ,OUTPUT);
  pinMode(LampPin,OUTPUT);
  pinMode(motion_sensor,INPUT);
  pinMode(temp_sensor,INPUT);

  Serial.begin(115200);
  sensors.begin();
  WiFi.begin(WIFI_SSID, WIFI_PASS); // initiates connection
  Serial.println("Connecting");
  while (WiFi.status() != WL_CONNECTED){
    delay(500); 
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected with IP Address: ");
  Serial.println(WiFi.localIP());
}


void loop() {
if (WiFi.status() != WL_CONNECTED ){
//PUT

  String endpoint = "https://smart-hub-cipv.onrender.com/put"
  HTTPClient http;
  http.begin(endpoint);
  String http_response;
  http.addHeader("Content-Type", "application/json"); // look up what the request needs(if json, html or whatever) to know header type etc
  StaticJsonDocument<100> doc; // Empty JSONDocument
  char * httpRequestData;
  http.addHeader("Host",HOST);  //change to render domain after
  http.addHeader("Content-length","100");

  serializeJson(doc, httpRequestData); // serialize to go from string to JSON
  //youd have to hardcode the data if you dont do it this way

  int httpResponseCode = http.PUT(httpRequestData); // takes info from the document dynamically
  //if you want to get different sets of information you need to retrive from different vairables of the doc

  //after this is essentially the same as get request

  if (httpResponseCode>0){
    
    Serial.print("HTTP Response code: ");
    Serial.print(httpResponseCode);
    Serial.print("Server Response:");
    http_response = http.getString();
    Serial.print(http_response);
  }
  else{
    Serial.print("Error code:");
    Serial.print(httpResponseCode);
  }
  http.end();

  //GET

 
  String endpoint2 = "https://smart-hub-cipv.onrender.com/states";
   http.begin(endpoint2);       //start connection to api url
    httpResponseCode = http.GET();      //performs get request and receives status code response
    
    if (httpResponseCode>0) 
    {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);

      Serial.print("Response from server: ");
      http_response = http.getString();       //gets worded/verbose response
      Serial.println(http_response);
    }
    else 
    {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }
    http.end();

 StaticJsonDocument<150> doc;
  DeserializationError error = deserializeJson(doc,http_response);


  if (error){
    Serial.print("Deserialize failed: ");
    Serial.print(error.c_str());
    return;
  }
   
   sensors.requestTemperatures();
   float temp_reading = sensors.getTempCByIndex(0); //wait for digital read
   bool motion_reading = digitalRead(motion_sensor);
  //  if(motionValue == HIGH){
  //   return true;
  //  }
  //  else return false
   doc["presence"] = motion_reading; 
   doc["temperature"]= temp_reading;

   const bool fanState = doc["Fan"];
   const bool lightState = doc["light"];

   digitalWrite(FanPin,fanState);
   digitalWrite(LampPin,lightState);
   delay(1500);
}
else return;
  
  
}