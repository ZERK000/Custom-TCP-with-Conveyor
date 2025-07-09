# Custom-TCP-with-Conveyor
This project's goal was to automate a conveyor belt using our custom TCP protocol 
The conveyor belt had stepper motor and 2 IR sensors to serve our application which was counting
We developed our custom message format for the protocol and included a fault-handling mechanism for motor and sensor faliures

### This custom TCP protocol was implemented on the three main devices of the system, the PC, the Raspberry Pi and the arduino where:
  1- The Raspberry Pi acts as the server, where it forwards the commands from the PC (client) to Arduino or from the Arduino to the PC "Python script"
  
  2- Arduino acts as a Client who controls the conveyor based on the commands received, and returns ACKs or Error states ".ino file (C++)"
  
  3- The PC acts as the other client which sends commands to through the server and then to the Arduino to control the conveyor "Python script"

Our custom TCP had more features like connection retry, data acknowledgment , and timeout handling in the protocol logic

## Wireshark Analysis
 1- Analyzed latency and packet structure of the custom TCP, including ACKs timings.
 
 2- Measured the time between sending control commands from sending command to the Raspberry Pi ad Receiving Acks from the Arduino.
 
 3- Simulated network congestion and Monitored the effect of packet loss and retransmission of command execution.

