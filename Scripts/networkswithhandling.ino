#include <SoftwareSerial.h>
#include <AccelStepper.h>

#define Dir1 4
#define Pul1 5
#define Limit1 1000000  // Large number of steps for forward movement
#define Limit2 -1000000

AccelStepper Stepper1(1, Pul1, Dir1);
char ssid[] = "Cato";      // Your Wi-Fi SSID
char password[] = "12345678910";   // Your Wi-Fi Password
int x = 0;
// Server details (TCP server to connect to)
const char* server_ip = "192.168.238.21";  // Server IP address
const int server_port = 5001;  // Server port

const char* client_ip = "192.168.238.91";  
const int client_port = 27217;  // Server port

// Communication with ESP8266 using SoftwareSerial
SoftwareSerial espSerial(2, 3);  // RX, TX pins for communication with ESP8266 module

const int startButtonPin = 2;  // Pushbutton connected to digital pin 2
const int ir1Pin = A0;         // IR Sensor 1 connected to digital pin A0
const int ir2Pin = A1;         // IR Sensor 2 connected to digital pin A1
const int ledPin = 13;         // Example: LED to indicate system state

// Variables for state, timing, and counting
bool systemActive = false;         // Flag to track system state
int currentStage = 0;              // Tracks the stage of the cycle (0: waiting for IR1, 1: waiting for IR2)
int counter = 0;                   // Counter for successful detections
String status1 = "0";                    // Status variable to track IR sensor states
unsigned long intervalStartTime;   // Start time for the current interval
unsigned long intervalDuration;    // Duration of the current interval

////
    int lengthStart;
    int lengthEnd;
    int dataLength;

    // Extract the command
    int commandIndex;
    char command;
    int speed;  // Default to -1 if no speed is provided
    int speedStart;
      int speedEnd;
      String speedString;

////////////


// Function declarations
void sendACK(int dataLength, char command, String status, int speed = -1);
void sendError(String error_stat);
void sendMessageWithChecksum(const char* message, size_t messageLength);
uint16_t calculateChecksum(const uint8_t* data, size_t length);
void read_messaage();
void wait_for_ack();



void setup() {
  pinMode(9,OUTPUT);
    pinMode(10,OUTPUT);
    Stepper1.setMaxSpeed(400);  // Adjust this based on motor and driver capabilities
  Stepper1.setAcceleration(500);  // Set a reasonable acceleration

  // Set initial speed to maximize torque at lower speeds
  Stepper1.setSpeed(400);  // Max speed for the motor (can be adjusted for higher torque)
  Serial.begin(230400);  // For debugging in the Serial Monitor
  espSerial.begin(115200);  // Communication with ESP8266 module

  // Initialize ESP8266 and connect to Wi-Fi
  sendATCommand("AT+RST\r\n", 2000);  // Reset the ESP8266
  sendATCommand("AT+CWMODE=1\r\n", 2000);  // Set Wi-Fi mode to STA (Station)
  
  String connectCommand = "AT+CWJAP=\"" + String(ssid) + "\",\"" + String(password) + "\"\r\n";
  sendATCommand(connectCommand.c_str(), 5000);  // Connect to Wi-Fi
  delay(5000);  // Wait for connection
  
  // Check Wi-Fi connection status
  sendATCommand("AT+CWJAP?\r\n", 2000);  // Query Wi-Fi status

  // Initialize TCP connection manually (send raw TCP data)
  String tcpConnectCommand = "AT+CIPSTART=\"TCP\",\"" + String(server_ip) + "\"," + String(server_port) + "\r\n";
  sendATCommand(tcpConnectCommand.c_str(), 5000);  // Establish TCP connection with the server
  
    pinMode(startButtonPin, INPUT_PULLUP); // Configure pushbutton with internal pull-up
  pinMode(ir1Pin, INPUT);               // Configure IR Sensor 1 pin as input
  pinMode(ir2Pin, INPUT);               // Configure IR Sensor 2 pin as input
  pinMode(ledPin, OUTPUT);              // Set LED pin as output (for indication)
  int counter = 0;

   // sendError(error_stat);
    
  digitalWrite(9,0);
   analogWrite(10,0);
  
}

void read_messaage()
{
   char fin='!';
  // Check if there is data available to read
  if (espSerial.available()) {

     Serial.println("entered loop");
    String incomingData = "";  // Store incoming data

    // Check for the IPD prefix to know it's incoming data
    String header = "";
    while (espSerial.available()) {
      char c = espSerial.read();
      header += c;
      Serial.println(c);  // Print received data

      // If we detect the prefix "+IPD", it means data is coming
      if (c==fin) {
        break;
      }
    }

    // Extract the length of the message
    int lengthStart = header.indexOf(",") + 1;
    int lengthEnd = header.indexOf(":");
    int dataLength = header.substring(lengthStart, lengthEnd).toInt();

    // Extract the command
    int commandIndex = lengthEnd + 1;
    char command = header.charAt(commandIndex);
    Serial.print("command=");
    Serial.print(command);
    int speed = -1;  // Default to -1 if no speed is provided

    int speedStart = header.indexOf(",", commandIndex);
    if (speedStart != -1) {
      int speedEnd = header.indexOf("!", speedStart);
      String speedString = header.substring(speedStart + 1, speedEnd);  // Extract speed as a string
      speed = speedString.toInt();  // Convert speed to integer
    }

    // Extract checksum if present (i.e., if '|' exists)
String receivedChecksum = "";
int checksumIndex = header.indexOf("|");
if (checksumIndex != -1) {
  receivedChecksum = header.substring(checksumIndex + 1);  // Extract checksum from after '|'
}
  }
}

void wait_for_ack() {
    Serial.println("Waiting for data...");
    
    while (true) { // Infinite loop
        if (espSerial.available()) { // Check if buffer is not empty
            Serial.println("Data received!");
            break; // Exit the loop when data is available
        }
        // Optional: Add a small delay to avoid busy-waiting
        delay(10); 
    }
    
    Serial.println("Exiting loop.");
}


void loop() {
  char fin='!';
  // Check if there is data available to read
  if (espSerial.available()) {

    
    String incomingData = "";  // Store incoming data

    // Check for the IPD prefix to know it's incoming data
    String header = "";
    while (espSerial.available()) {
      char c = espSerial.read();
      header += c;
      Serial.println(c);  // Print received data

      // If we detect the prefix "+IPD", it means data is coming
      if (c==fin) {
        break;
      }
    }

    // Extract the length of the message
    int lengthStart = header.indexOf(",") + 1;
    int lengthEnd = header.indexOf(":");
    int dataLength = header.substring(lengthStart, lengthEnd).toInt();

    // Extract the command
    int commandIndex = lengthEnd + 1;
    char command = header.charAt(commandIndex);
    int speed = -1;  // Default to -1 if no speed is provided

    int speedStart = header.indexOf(",", commandIndex);
    if (speedStart != -1) {
      int speedEnd = header.indexOf("!", speedStart);
      String speedString = header.substring(speedStart + 1, speedEnd);  // Extract speed as a string
      speed = speedString.toInt();  // Convert speed to integer
    }

    // Extract checksum if present (i.e., if '|' exists)
String receivedChecksum = "";
int checksumIndex = header.indexOf("|");
if (checksumIndex != -1) {
  receivedChecksum = header.substring(checksumIndex + 1);  // Extract checksum from after '|'
}

    if(command=='S') {
      Serial.print("received command Start");
      sendACK(dataLength, command, "OK");
      sensingS();
   
      //sendError(error_stat);
    }
    if(command=='T') {
      analogWrite(9,0);
      Serial.print("received command Stop");
          sendACK(dataLength, command, "OK");
    }
    if(command=='A') {
      Serial.print("received command Adjust Speed");
      if (speed != -1) {  // If speed is provided
        Serial.print("Speed value: ");
        Serial.println(speed);
      } else {
        Serial.println("No speed value provided.");
      }

      sendACK(dataLength, command, "OK", speed);
      sensingA();
    }

    
  }
  counter ++;
}
void sendACK(int dataLength, char command, String status, int speed) {
  // Create the ACK message without the checksum
  String ackMessage = "ACK:" + String(client_ip) + ":" + String(client_port) + ":" + String(server_ip) + ":" + String(server_port) + ":" + "0" + "|";
  
  uint8_t data[ackMessage.length() + 1];  // +1 for null terminator
  ackMessage.toCharArray((char*)data, ackMessage.length() + 1);

  uint16_t checksum = calculateChecksum(data, ackMessage.length());

  // Convert checksum to string (in HEX format) and ensure 2 digits
  String checksumStr = String(checksum, HEX);
  if (checksum < 0x10) {
    checksumStr = "0" + checksumStr;  // Ensure two characters for checksum if it's a single digit
  }

  // Construct the message with "|" after the main message and checksum at the end
  String ackWithChecksum = ackMessage + "|" + checksumStr;

  // Send the AT command with the checksum in the message
  String sendDataCommand = "AT+CIPSEND=" + String(ackWithChecksum.length()) + "\r\n";
  sendATCommand(sendDataCommand.c_str(), 2000);
  sendATCommand(ackWithChecksum.c_str(), 2000);
  
  Serial.println("ACK sent to server: " + ackWithChecksum);
}




uint16_t calculateChecksum(const uint8_t* data, size_t length) {
  uint16_t checksum = 0;  // Initialize the checksum to 0

  // Perform XOR operation on each byte in the data
  for (size_t i = 0; i < length; i++) {
    checksum ^= data[i];
  }

  return checksum;  // Return the 16-bit checksum value
}

// Function to send a message with checksum
void sendMessageWithChecksum(const char* message, size_t messageLength) {
  // Calculate the checksum for the message
  uint16_t checksum = calculateChecksum((const uint8_t*)message, messageLength);

  // Split the 16-bit checksum into two bytes (big-endian format)
  uint8_t checksumBytes[2];
  checksumBytes[0] = (uint8_t)(checksum >> 8);  // Higher byte
  checksumBytes[1] = (uint8_t)(checksum & 0xFF);  // Lower byte

  // Send the message
  Serial.write((const uint8_t*)message, messageLength);

  // Append the checksum (big-endian format)
  Serial.write(checksumBytes, 2);
}
void sendError(String error_stat) {
  int errorStatLength = error_stat.length();
  String errorMessage = "ERROR:" + String(client_ip) + ":" + String(client_port) + ":" + String(server_ip) + ":" + String(server_port) + ":" +
                        String(errorStatLength) + "|" + error_stat;

  uint8_t data[errorMessage.length() + 1];
  errorMessage.toCharArray((char*)data, errorMessage.length() + 1);

  uint16_t checksum = calculateChecksum(data, errorMessage.length());

  String errorWithChecksum = errorMessage + "|";
  if (checksum < 0x10) {
    errorWithChecksum = errorMessage + "|0" + String(checksum, HEX);  // Ensure two characters for checksum
  } else {
    errorWithChecksum = errorMessage + "|" + String(checksum, HEX);
  }

  String sendDataCommand = "AT+CIPSEND=" + String(errorWithChecksum.length()) + "\r\n";
  sendATCommand(sendDataCommand.c_str(), 2000);
  sendATCommand(errorWithChecksum.c_str(), 2000);

  Serial.println("Error message sent: " + errorWithChecksum);
}

void sendATCommand(const char* command, unsigned long timeout) {
  String response = "";
  espSerial.println(command);
  unsigned long startTime = millis();

  // Wait for the response from ESP8266
  while (millis() - startTime < timeout) {
    if (espSerial.available()) {
      char c = espSerial.read();
      response += c;
    }
  }

  // Print the response for debugging
  Serial.print("Response: ");
  Serial.println(response);

  // Ensure that we have received the expected response
  if (response.indexOf("OK") == -1) {
    Serial.println("Error in AT command response.");
  }
}
void sensingS()
{
while(1){
if(x==1){
read_messaage();
if (command!="S" )
{
  Serial.print("t_received");
   sendACK(dataLength, command, "OK");
  break;
}
}
analogWrite(9,255);
  // Check if the button is pressed to activate the system
  if (!systemActive) {
    systemActive = true;               // Activate the system
    currentStage = 0;                  // Start with waiting for IR1
    intervalStartTime = millis();      // Start the interval timer
    intervalDuration = 5000;           // Set the first interval duration (5 seconds)
    Serial.println("System activated. Waiting for IR Sensor 1...");
    delay(300);                        // Debounce delay for the button
  }

  if (systemActive) {
    unsigned long currentTime = millis();

    if (currentStage == 0) { // Waiting for IR1 to detect or timeout
      int ir1Value = digitalRead(ir1Pin); // Read IR Sensor 1

      if (ir1Value == LOW) { // IR Sensor 1 detected
        Serial.println("IR Sensor 1 detected!");
        status1 = "1";          // Set status1 to 1
        currentStage = 1;    // Move to waiting for IR2
        intervalStartTime = currentTime; // Reset the interval timer
        intervalDuration = 5000;         // Set the next interval duration (5 seconds)
        Serial.println("Waiting for IR Sensor 2...");
      } else if (currentTime - intervalStartTime > intervalDuration) {
        Serial.println("Timeout! Moving to IR Sensor 2...");
        status1 = "0";
        currentStage = 2;     // Timeout occurred, move to IR2
        intervalStartTime = currentTime; // Reset the interval timer
        intervalDuration = 5000;         // Set the next interval duration (5 seconds)
        Serial.println("Waiting for IR Sensor 2...");
      }
    } else if (currentStage == 1) { // Waiting for IR2 to detect or timeout
      int ir2Value = digitalRead(ir2Pin); // Read IR Sensor 2

      if (ir2Value == LOW) { // IR Sensor 2 detected
        Serial.println("IR Sensor 2 detected!");
        status1 = "1";          // Set status1 to 1
        counter++;           // Increment the counter
        Serial.print("Counter incremented: ");
        Serial.println(counter);
        currentStage = 0;    // Move back to waiting for IR1
        intervalStartTime = currentTime; // Reset the interval timer
        intervalDuration = 10000;        // Set the next interval duration (10 seconds)
        Serial.println("Waiting for IR Sensor 1...");
        Serial.print("status1: ");       // Print status1 after both sensors are processed
        Serial.println(status1);
      } else if (currentTime - intervalStartTime > intervalDuration) {
        Serial.println("Timeout! Moving back to IR Sensor 1...");
        status1 = "2"; 
        currentStage = 0;     // Timeout occurred, move back to IR1
        intervalStartTime = currentTime; // Reset the interval timer
        intervalDuration = 10000;        // Set the next interval duration (10 seconds)
        Serial.println("Waiting for IR Sensor 1...");
        Serial.print("status1: ");       // Print status1 after both sensors are processed
        Serial.println(status1);
      }

    } else if (currentStage == 2) { // Extra state for handling IR2 explicitly
      int ir2Value = digitalRead(ir2Pin); // Read IR Sensor 2

      if (ir2Value == LOW) { // IR Sensor 2 detected
        Serial.println("IR Sensor 2 detected!");
        status1 =  "0";         // Set status1 to 2
        counter++;           // Increment the counter
        Serial.print("Counter incremented: ");
        Serial.println(counter);
        currentStage = 0;    // Move back to waiting for IR1
        intervalStartTime = currentTime; // Reset the interval timer
        intervalDuration = 10000;        // Set the next interval duration (10 seconds)
        Serial.println("Waiting for IR Sensor 1...");
        Serial.print("status1: ");       // Print status1 after both sensors are processed
        Serial.println(status1);
      } else if (currentTime - intervalStartTime > intervalDuration) {
        Serial.println("Timeout! Moving back to IR Sensor 1...");
        currentStage = 0;
         status1 =  "3"; // Timeout occurred, move back to IR1
        intervalStartTime = currentTime; // Reset the interval timer
        intervalDuration = 10000;        // Set the next interval duration (10 seconds)
        Serial.println("Waiting for IR Sensor 1...");
        Serial.print("status1: ");       // Print status1 after both sensors are processed
        Serial.println(status1);
      }
    }
    x=0;
    if (status1 != "1")
    {
      x=1;
      sendError(status1);
      wait_for_ack();
      break;

    }
    
    }
    
  }
  
  
}


void sensingA()
{
while(1){
if(x==1){
read_messaage();
if (command!="A" )
{
  Serial.print("A_STOPPED");
  break;
}
}
analogWrite(10,255);
  // Check if the button is pressed to activate the system
  if (!systemActive) {
    systemActive = true;               // Activate the system
    currentStage = 0;                  // Start with waiting for IR1
    intervalStartTime = millis();      // Start the interval timer
    intervalDuration = 5000;           // Set the first interval duration (5 seconds)
    Serial.println("System activated. Waiting for IR Sensor 1...");
    delay(300);                        // Debounce delay for the button
  }

  if (systemActive) {
    unsigned long currentTime = millis();

    if (currentStage == 0) { // Waiting for IR1 to detect or timeout
      int ir1Value = digitalRead(ir1Pin); // Read IR Sensor 1

      if (ir1Value == LOW) { // IR Sensor 1 detected
        Serial.println("IR Sensor 1 detected!");
        status1 = "1";          // Set status1 to 1
        currentStage = 1;    // Move to waiting for IR2
        intervalStartTime = currentTime; // Reset the interval timer
        intervalDuration = 5000;         // Set the next interval duration (5 seconds)
        Serial.println("Waiting for IR Sensor 2...");
      } else if (currentTime - intervalStartTime > intervalDuration) {
        Serial.println("Timeout! Moving to IR Sensor 2...");
        status1 = "0";
        currentStage = 2;     // Timeout occurred, move to IR2
        intervalStartTime = currentTime; // Reset the interval timer
        intervalDuration = 5000;         // Set the next interval duration (5 seconds)
        Serial.println("Waiting for IR Sensor 2...");
      }
    } else if (currentStage == 1) { // Waiting for IR2 to detect or timeout
      int ir2Value = digitalRead(ir2Pin); // Read IR Sensor 2

      if (ir2Value == LOW) { // IR Sensor 2 detected
        Serial.println("IR Sensor 2 detected!");
        status1 = "1";          // Set status1 to 1
        counter++;           // Increment the counter
        Serial.print("Counter incremented: ");
        Serial.println(counter);
        currentStage = 0;    // Move back to waiting for IR1
        intervalStartTime = currentTime; // Reset the interval timer
        intervalDuration = 10000;        // Set the next interval duration (10 seconds)
        Serial.println("Waiting for IR Sensor 1...");
        Serial.print("status1: ");       // Print status1 after both sensors are processed
        Serial.println(status1);
      } else if (currentTime - intervalStartTime > intervalDuration) {
        Serial.println("Timeout! Moving back to IR Sensor 1...");
        status1 = "2"; 
        currentStage = 0;     // Timeout occurred, move back to IR1
        intervalStartTime = currentTime; // Reset the interval timer
        intervalDuration = 10000;        // Set the next interval duration (10 seconds)
        Serial.println("Waiting for IR Sensor 1...");
        Serial.print("status1: ");       // Print status1 after both sensors are processed
        Serial.println(status1);
      }

    } else if (currentStage == 2) { // Extra state for handling IR2 explicitly
      int ir2Value = digitalRead(ir2Pin); // Read IR Sensor 2

      if (ir2Value == LOW) { // IR Sensor 2 detected
        Serial.println("IR Sensor 2 detected!");
        status1 =  "0";         // Set status1 to 2
        counter++;           // Increment the counter
        Serial.print("Counter incremented: ");
        Serial.println(counter);
        currentStage = 0;    // Move back to waiting for IR1
        intervalStartTime = currentTime; // Reset the interval timer
        intervalDuration = 10000;        // Set the next interval duration (10 seconds)
        Serial.println("Waiting for IR Sensor 1...");
        Serial.print("status1: ");       // Print status1 after both sensors are processed
        Serial.println(status1);
      } else if (currentTime - intervalStartTime > intervalDuration) {
        Serial.println("Timeout! Moving back to IR Sensor 1...");
        currentStage = 0;
         status1 =  "3"; // Timeout occurred, move back to IR1
        intervalStartTime = currentTime; // Reset the interval timer
        intervalDuration = 10000;        // Set the next interval duration (10 seconds)
        Serial.println("Waiting for IR Sensor 1...");
        Serial.print("status1: ");       // Print status1 after both sensors are processed
        Serial.println(status1);
      }
    }
    x=0;
    if (status1 != "1")
    {
      x=1;
      sendError(status1);
      wait_for_ack();
      break;
    }
    }
    
  }
  
  
}
