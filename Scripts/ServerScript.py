#!/usr/bin/env python3

"""# OUR TCP CUSTOM PROTOCOL"""
"""#
# Custom TCP Protocol:
# Format:  HEADER|PAYLOAD|CHECKSUM
#
# Header Structure:
#   TYPE:SENDER_IP:SENDER_PORT:DEST_IP:DEST_PORT:PAYLOAD_SIZE
#
#   - TYPE: Specifies the type of message (COMMAND, ACK, ERROR, STATUS).
#     Examples:
#       - COMMAND: Instruction for the conveyor (e.g., START, STOP).
#       - ACK: Acknowledgment of a command or status.
#       - ERROR: Error message (e.g., invalid command, sensor failure).
#       - STATUS: Status updates (e.g., motor running, sensor active).
#   - SENDER_IP: The IP address of the sender (e.g., Raspberry Pi, PC).
#   - SENDER_PORT: The port number used by the sender.
#   - DEST_IP: The destination IP address (e.g., Arduino, Raspberry Pi).
#   - DEST_PORT: The port number used by the recipient.
#   - PAYLOAD_SIZE: Size of the payload in bytes (excluding the header or checksum).
#
# Payload Structure:
#   The payload contains the actual data being communicated.
#   Examples of commands in the payload:
#     - START: Start the conveyor belt.
#     - STOP: Stop the conveyor belt.
#     - SPEED:<value>: Adjust the conveyor belt speed to <value>.
#
# Checksum:
#   - CHECKSUM: A 2-byte binary checksum for data integrity verification.
#       - The checksum is calculated using a simple 16-bit checksum method: sum of all byte values, modulo 65536 (0xFFFF).
#       - The checksum is appended to the message to ensure no transmission errors.
#       - The checksum is **transmitted as raw binary data** (not human-readable text).
#       - Example checksum (in binary): b'\x1a\x2b' (2-byte checksum).
#
# Full Message Example:
#   Command from PC to Raspberry Pi:
#       HEADER: COMMAND:192.168.1.10:5000:192.168.1.20:5001:5
#       PAYLOAD: START
#       CHECKSUM: b'\x1a\x2b'  # 2-byte binary checksum
#
#   Full Message (in human-readable text + binary):
#   b'COMMAND:192.168.1.10:5000:192.168.1.20:5001:5|START|b'\x1a\x2b''
#
"""


import socket
import select
import time


############################################# FUNCTIONS ###########################################

# Example of a parsed message structure
def ParseMessage(message):
    print("Start Parsing")
    try:
        parts = message.split(b'|')
        
        # Ensure the message has exactly 3 parts: header, payload, and checksum
        if len(parts) != 3:
            raise ValueError(f"Invalid message format: expected 3 parts, got {len(parts)}")
        print("Done Splitting")
        # Extract the header, payload, and checksum
        header_bytes, payload_bytes, checksum_bytes = parts
        header = header_bytes.decode('utf-8')
        payload = payload_bytes.decode('utf-8')
        # Assuming the checksum is 2 bytes long
        received_checksum = checksum_bytes[:2]
        
        # Now verify checksum
        if not VerifyChecksum(header_bytes + b'|' + payload_bytes, received_checksum):
            print(f"Checksum verification failed for header: {header_bytes}, payload: {payload}")
            ACKNACK = "NACK"
         
        else:
            print(f"Checksum verified successfully for header: {header_bytes}, payload: {payload}")
            ACKNACK ="ACK"
        
        if IPAddress == AddressPC:
            AckMessage = construct_message(
                                        ACKNACK,
                                        None,
                                        dest_ip=AddressPC[0],
                                        dest_port=AddressPC[1],
                                        sender_port=PC_PORT,
                                        )
            ConnectionPC.sendall(AckMessage) 
        else:
            AckMessage = construct_message(
                                        ACKNACK,
                                        None,
                                        dest_ip=AddressArduino[0],
                                        dest_port=AddressArduino[1],
                                        sender_port=ARDUINO_PORT,
                                        )
            ConnectionPC.sendall(AckMessage) 
        
        # Extract the message type from the header (which is the first part before the first ':')
        message_type = header.split(':')[0]  # Decode it to string for comparison
        
        # Use the dictionary to handle the message based on its type
        handle_message(message_type, payload)  # Call the appropriate handler for the payload

        return   
        
    except Exception as e:
        print(f"Error parsing message: {e}")
        return 


####################################### Calculating Checksum #######################
def CalculateChecksum(data):
    # Initialize the checksum to 0
    checksum = 0    
    # Perform XOR operation on each byte in the data
    for byte in data:
        checksum ^= byte  # XOR each byte with the current checksum value
    # Ensure the checksum is 2 bytes (16 bits), you can return the lower byte if needed
    return checksum.to_bytes(2, byteorder='big')  # bytes([checksum >> 8, checksum & 0xFF])

# Real checksum verification function using XOR checksum
def VerifyChecksum(data, ReceivedChecksum):
    # Calculate checksum (using XOR method)
    CalculatedChecksum = CalculateChecksum(data)

    print(f"Calculated checksum: {CalculatedChecksum}, Received checksum: {ReceivedChecksum}")
    if int.from_bytes(CalculatedChecksum, 'big') != int.from_bytes(ReceivedChecksum, 'big'):
        flag = 0
    else:
        flag = 1
    
    # Compare the received checksum with the calculated one
    return flag

# Function to log and handle errors
def handle_error(message):
    print(f"Error: {message}")

    # Function to construct the message


#################################### Handlers #########################################################
def HandleACK(payload):
    """Handle ACK messages."""
    print("ACK Received")


def HandleError(payload):
    """Handle error messages."""
    Message = construct_message("ERROR", payload , AddressPC[0], AddressPC[1], PC_PORT)
    ConnectionPC.sendall(Message)
    print("Sent error to PC")
    # Wait for acknowledgment or response from the client
    while True:
        # Set timeout duration for the socket operation
        try:
            # Wait for acknowledgment or response from the client
            response = ConnectionPC.recv(1024)
            print(f"Received from PC: {response.decode('utf-8')}")
            print("Acknowledgment received.")
            break  # Exit the loop if acknowledgment is received
        except socket.timeout:
            print(f"Error: Acknowledgment not received within {timeout} seconds.")
            print("Resending command...")
            ConnectionPC.sendall(Message)  # Resend the command

    #Our own implementation:
    """
    While True:
        response = ConnectionPC.recv(1024)
        print(f"Received from PC: {response.decode('utf-8')}")

        # Wait for acknowledgment
        print("Waiting for acknowledgment...")

        # Set timeout duration
        timeout = 5
        start_time = time.time()

        # Check if acknowledgment is received within the timeout period
        while time.time() - start_time < timeout:
            if response:
                print("Acknowledgment received.")
                break
        else:
            print("Error: Acknowledgment not received within 5 seconds.")
            ConnectionPC.sendall(Message.encode('utf-8'))  # Resend the command
    """


    
def HandleCommand(payload):
    """Process a command like START, STOP, SPEED, etc."""
    CommandParts = payload.split(':')
    Command = CommandParts[0]
    ToArduino = None

    if Command == 'START':
        # Start the conveyor belt
        ToArduino = "S"
        print("Starting conveyor belt...")
    elif Command == 'STOP':
        # Stop the conveyor belt
        ToArduino = "T"
        print("Stopping conveyor belt...")
    elif Command.startswith('SPEED'):
        # Adjust speed
        SpeedValue = int(CommandParts[1])
        ToArduino = "A"
        print(f"Adjusting speed to {SpeedValue}")
    else:
        print("Unknown command")
    
    if ToArduino == "A":
        FullCommand = f"{ToArduino},{SpeedValue}!"
    else:
        FullCommand = f"{ToArduino}!"

    ConnectionArduino.sendall(FullCommand.encode('utf-8'))
    # Wait for acknowledgment or response from the client
    while True:
        # Set timeout duration for the socket operation
        try:
            # Wait for acknowledgment or response from the client
            response = ConnectionArduino.recv(1024)
            print(f"Received from Arduino: {response.decode('utf-8')}")
            print("Acknowledgment received.")
            break  # Exit the loop if acknowledgment is received
        except socket.timeout:
            print(f"Error: Acknowledgment not received within {timeout} seconds.")
            print("Resending command...")
            ConnectionArduino.sendall(FullCommand.encode('utf-8'))  # Resend the command

    #Our own implementation
    """
    While True:
        response = ConnectionArduino.recv(1024)
        print(f"Received from Arduino: {response.decode('utf-8')}")

        # Wait for acknowledgment
        print("Waiting for acknowledgment...")

        # Set timeout duration
        timeout = 5
        start_time = time.time()

        # Check if acknowledgment is received within the timeout period
        while time.time() - start_time < timeout:
            if response:
                print("Acknowledgment received.")
                break
        else:
            print("Error: Acknowledgment not received within 5 seconds.")
            ConnectionArduino.sendall(Message.encode('utf-8'))  # Resend the command
    """
    print(f"Received from Arduino: {response.decode('utf-8')}")


MessageHandlers = {
    "COMMAND": HandleCommand,
    "ERROR": HandleError,
    "ACK" : HandleACK,
}


def handle_message(message_type, payload):
    # Get the appropriate function from the dictionary, or a default function for unknown types
    handler = MessageHandlers.get(message_type, None)
    
    if handler:
        handler(payload)  # Call the corresponding handler function
    else:
        print(f"Unknown message type: {message_type}")

def reconnect(server_socket, device_name):
    global ConnectionArduino, ConnectionPC, AddressArduino, AddressPC

    print(f"{device_name} disconnected. Attempting to reconnect...")
    while True:
        try:
            if device_name == "PC":
                port = PC_PORT
            else:
                port = ARDUINO_PORT

            connection, address = server_socket.accept()
            print(f"Reconnected to {device_name} at {address}")
            SendACK(
                connection=connection,
                dest_ip=address[0],
                dest_port=address[1],
                sender_port=port,
            )
            
            return connection, address
        except Exception as e:
            print(f"Reconnection attempt failed: {e}")
            time.sleep(5)  # Wait 5 seconds before retrying


# Constants for the server
HOST = '0.0.0.0' 
PC_PORT = 5000  
ARDUINO_PORT = 5001 

# Knowing my IP Address
MYIPAddress = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
MYIPAddress.connect(("8.8.8.8", 80))
MYIPAddress = MYIPAddress.getsockname()[0]
print(f"My IP address is: {MYIPAddress}")

def SendACK(connection, dest_ip, dest_port , sender_port , sender_ip = MYIPAddress):
    # Construct the header
    header = f"ACK:{sender_ip}:{sender_port}:{dest_ip}:{dest_port}:0"  # No payload, so size is 0
    Full_message= header + "|"
    # Calculate the checksum for the header
    checksum = CalculateChecksum(Full_message.encode('utf-8'))

    # Construct the full message: header + delimiter + empty payload + delimiter + checksum
    FullMessage = f"{header}||".encode('utf-8')  + checksum

    # Send the acknowledgment
    print(FullMessage)
    connection.sendall(FullMessage)

def construct_message(message_type, payload, dest_ip, dest_port , sender_port , sender_ip = MYIPAddress):
    try:
        if payload == None :
            payload_size = 0
            payload_bytes = b''
        else:
            payload_size = len(payload.encode('utf-8'))
            payload_bytes = payload.encode('utf-8')
        
        header = f"{message_type}:{sender_ip}:{sender_port}:{dest_ip}:{dest_port}:{payload_size}"
        header_bytes = header.encode('utf-8')
            
        full_message = header_bytes + b'|' + payload_bytes
        checksum = CalculateChecksum(full_message)
        print(f"Constructed checksum: {checksum}")
        return full_message + b'|' + checksum
    except Exception as e:
        handle_error(f"Error constructing message: {e}")
        return b''


# Set up the server socket to listen for incoming connections from the PC
PC_ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PC_ServerSocket.bind((HOST, PC_PORT))
PC_ServerSocket.listen(1)  # Accept one client (PC) at a time

print(f"Server listening on {HOST}:{PC_PORT}")


# Accept the connection from the PC (client)
ConnectionPC, AddressPC = PC_ServerSocket.accept() #AddressPC[0] = IP Adresss , #AddressPC[1] = PortNumber
print(f"Connected to PC at {AddressPC}")


# Set up the socket to connect to the Arduino
# Set up the server socket to listen for incoming connections from the Arduino
Arduino_ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
Arduino_ServerSocket.bind((HOST, ARDUINO_PORT))
Arduino_ServerSocket.listen(1)  # Accept one Arduino at a time

print(f"Waiting for connection from Arduino on {HOST}:{ARDUINO_PORT}")

ConnectionArduino, AddressArduino = Arduino_ServerSocket.accept()
print(f"Connected to Arduino at {AddressArduino}")

# Send acknowledgment to the PC
SendACK(
    connection=ConnectionPC,
    dest_ip=AddressPC[0],
    dest_port=AddressPC[1],
    sender_port=PC_PORT,
)

# Send acknowledgment to the Arduino
ConnectionArduino.sendall(b"ACK:CONNECTION:SUCCESS\n")

timeout = 5  # Timeout in seconds
ConnectionPC.settimeout(timeout)
ConnectionArduino.settimeout(timeout)

try:
    while True:
        readable, _, _ = select.select([ConnectionPC, ConnectionArduino], [], [])

        for connection in readable:
            if connection == ConnectionPC:
                try:
                    # Receive a message from the PC
                    data = ConnectionPC.recv(1024)
                    if data:
                        print(f"Received message from PC: {data.decode()}")
                        IPAddress = AddressPC
                        ParseMessage(data)  # Process the message
                    else:
                        print("PC disconnected.")
                        ConnectionPC.close()
                        ConnectionPC, AddressPC = reconnect(PC_ServerSocket, "PC")  # Reconnect to PC
                except Exception as e:
                    print(f"Error with PC connection: {e}")
                    ConnectionPC.close()
                    ConnectionPC, AddressPC = reconnect(PC_ServerSocket, "PC")  # Reconnect to PC

            elif connection == ConnectionArduino:
                try:
                    # Receive a message from the Arduino
                    data = ConnectionArduino.recv(1024)
                    if data:
                        print(f"Received message from Arduino: {data.decode()}")
                        IPAddress = AddressArduino
                        print("Parsing ard")
                        ParseMessage(data)  # Process the message
                    else:
                        print("Arduino disconnected.")
                        ConnectionArduino.close()
                        ConnectionArduino, AddressArduino = reconnect(Arduino_ServerSocket, "Arduino")  # Reconnect to Arduino
                except Exception as e:
                    print(f"Error with Arduino connection: {e}")
                    ConnectionArduino.close()
                    ConnectionArduino, AddressArduino = reconnect(Arduino_ServerSocket, "Arduino")  # Reconnect to Arduino

        


except KeyboardInterrupt:
    print("Shutting down server...")
    
except Exception as e:
    print(f"Error: {e}")

finally:
    # Close the connections
    ConnectionPC.close()
    ConnectionArduino.close()
    Arduino_ServerSocket.close()
    PC_ServerSocket.close()
    print("Connections closed.")

