#include <Arduino.h>
#include <PCF8574.h>
#include <WiFi.h>
#include <WebSocketsServer.h>

PCF8574 board1(0x20, 21, 22);
PCF8574 board2(0x21, 21, 22);
PCF8574 board3(0x22, 21, 22);
const int single_pin = 18;  // GPIO 18 is the single pin

const char* ssid = "wifi_name";
const char* password = "wifi_password";
WebSocketsServer webSocket = WebSocketsServer(81);  // Websocket Server on port 81

void sendTouchInput()
{
  int sensorValues[19] = {
  board1.digitalRead(P0), board1.digitalRead(P1), board1.digitalRead(P2),
  board1.digitalRead(P3), board1.digitalRead(P4), 
  board2.digitalRead(P0), board2.digitalRead(P1), board2.digitalRead(P2), 
  board2.digitalRead(P3), board2.digitalRead(P4), board2.digitalRead(P5), 
  board2.digitalRead(P6), board2.digitalRead(P7), 
  board3.digitalRead(P0), board3.digitalRead(P1), board3.digitalRead(P2), 
  board3.digitalRead(P3), board3.digitalRead(P4),
  digitalRead(18)
  };
  
  // send the index of the activated touch sensor to python script
  for (int i = 0; i < 19; i++) 
  {
    if (sensorValues[i] == HIGH) 
    { 
      webSocket.broadcastTXT(("Touched Sensor: " + String(i)).c_str());
      break; // exit the loop after sending the activated sensor index
    }
  }
}

// called when receiving any WebSocket message
void onWebSocketEvent(uint8_t num, WStype_t type, uint8_t* payload, size_t length) 
{
  // a new client has connected
  if(type == WStype_CONNECTED) 
  {
    IPAddress ip = webSocket.remoteIP(num);
    Serial.printf("[%u] Connected. IP is: \n", num);
    Serial.println(ip.toString());
  } 
  
  // if the client has disconnected
  else if(type == WStype_DISCONNECTED) 
  {
    Serial.printf("[%u] Disconnected.\n", num);  // see what disconnected
  }

  // echo the text message back to the client
  else if(type == WStype_TEXT)
  {
    Serial.printf("[%u] Text: %s\n", num, payload);
    webSocket.sendTXT(num, payload);
  }
}

void setup() 
{
  Serial.begin(115200);

  // pin stuff
  board1.pinMode(P0,INPUT);
  board1.pinMode(P1,INPUT);
  board1.pinMode(P2,INPUT);
  board1.pinMode(P3,INPUT);
  board1.pinMode(P4,INPUT);

  board1.begin();

  board2.pinMode(P0,INPUT);
  board2.pinMode(P1,INPUT);
  board2.pinMode(P2,INPUT);
  board2.pinMode(P3,INPUT);
  board2.pinMode(P4,INPUT);
  board2.pinMode(P5,INPUT);
  board2.pinMode(P6,INPUT);
  board2.pinMode(P7,INPUT);

  board2.begin();

  board3.pinMode(P0,INPUT);
  board3.pinMode(P1,INPUT);
  board3.pinMode(P2,INPUT);
  board3.pinMode(P3,INPUT);
  board3.pinMode(P4,INPUT);

  board3.begin();

  pinMode(single_pin, INPUT);

  // wifi stuff
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) 
  {
    delay(500);
    Serial.println("Connecting to WiFi...");
  }
  Serial.print("Connected to WiFi with IP: ");
  Serial.println(WiFi.localIP());

  webSocket.begin();  // start the WebSocket server
  webSocket.onEvent(onWebSocketEvent);  // attach an event handler
}

void loop() 
{
  webSocket.loop();  // Constantly check for WebSocket communication

  sendTouchInput();
  delay(100);
}