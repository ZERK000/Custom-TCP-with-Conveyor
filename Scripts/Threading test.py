import socket
import threading
import queue
import time

# Client setup
server_ip = "192.168.238.21"  # Replace with the Raspberry Pi's IP address
server_port = 5000  # The port the server is listening on
buffer_size = 1024  # Buffer size for receiving data

# Thread-safe queue for communication between threads
response_queue = queue.Queue()
send_event = threading.Event()

next_command = "NULL"

# Function to calculate the checksum
def CalculateChecksum(data):
    # Initialize the checksum to 0
    checksum = 0
    # Perform XOR operation on each byte in the data
    for byte in data:
        checksum ^= byte  # XOR each byte with the current checksum value
    # Print the checksum
    print(f"Calculated checksum: {checksum}")
    # Ensure the checksum is 2 bytes (16 bits), you can return the lower byte if needed
    return checksum.to_bytes(2, byteorder='big')  # bytes([checksum >> 8, checksum & 0xFF])

# Function to construct the message
def construct_message(message_type, payload, dest_ip, dest_port , sender_port , sender_ip ):
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

# Function to parse the server's response
def parse_message(message):
    print(f"Message in parse message: {message.decode('utf-8')}")
    try:
        parts = message.split(b'|')
        if len(parts) == 3:
            print(f"Full message received")
            header_bytes, payload_bytes, checksum_bytes = parts
        elif len(parts) == 2:
            print(f"ACK message received")
            header_bytes, checksum_bytes = parts
            payload = None
        else:
            handle_error("Invalid message received")

        header = header_bytes.decode('utf-8')
        payload = payload_bytes.decode('utf-8')

        # Calculate and verify checksum
        full_message = header_bytes + b'|' + payload_bytes
        calculated_checksum = CalculateChecksum(full_message)
        print(f"Checksum with payload: {calculated_checksum}")
        
        if calculated_checksum != checksum_bytes:
            handle_error("Checksum mismatch")
            # return None, None
        if int.from_bytes(calculated_checksum, 'big') != int.from_bytes(checksum_bytes, 'big'):
            handle_error("Checksum mismatch")
            # return None, None

        # Parse header
        header_parts = header.split(':')
        message_type = header_parts[0]
        return message_type, payload
    except Exception as e:
        handle_error(f"Error parsing message: {e}")
        return None, None

## Global variables
next_command = "NULL"
last_command = None  # To store the last sent command for NACK handling

# Function to handle server commands
def handle_received_message(message_type, payload):
    global next_command, last_command
    try:
        if message_type == "ACK":
            print("Acknowledgment received from server.")
            next_command = "NULL"  # Reset the global variable
            response_queue.put("ACK")  # Notify the sender thread
            send_event.set()  # Signal ACK received
        elif message_type == "ERROR":
            message = construct_message("ACK", "0", client_ip, client_port, server_ip, server_port)
            client_socket.sendall(message)
            print(f"Sent: {message.decode('utf-8', errors='replace')}")
            print(f"Error from server: {payload}")
            if payload == "0":
                print("Error 1: Problem in IR sensor 1 reading, sending adjust speed to 20 command")
                speed = 20
                next_command = f"SPEED:{speed}"
            elif payload == "1":
                print("No error")
                next_command = "NULL"
            elif payload == "2":
                print("Error 2: IR sensor 2 did not read, sending stop command")
                next_command = "STOP"
            elif payload == "3":
                print("Error 3: Problem in motor, sending stop command")
                next_command = "STOP"
            else:
                print("Unknown error")
        elif message_type == "COMMAND":
            print("Cannot receive a command message!")
        elif message_type == "NACK":
            print("NACK received from server. Resending last command...")
            if last_command:
                client_socket.sendall(last_command)
                print(f"Resent: {last_command.decode('utf-8', errors='replace')}")
                if not send_event.wait(timeout=5):
                    print("Error: Acknowledgment not received within 3 seconds.")
                else:
                    print("Acknowledgment received.")
                    send_event.clear()  # Reset the event for the next command
            else:
                print("No last command to resend.")
        else:
            print(f"Unknown message type: {message_type}")
    except Exception as e:
        handle_error(f"Error handling server command: {e}")

# Function to listen to the server
def listen_to_server(client_socket):
    while True:
        try:
            response = client_socket.recv(buffer_size)
            if response:
                print(f"Received from server: {response.decode('utf-8')}")
                message_type, payload = parse_message(response)
                handle_received_message(message_type, payload)  # Pass to handler
            else:
                print("Server closed the connection.")
                break
        except Exception as e:
            print(f"Error in server listener: {e}")
            break

# Function to get user input
def get_user_input():
    print("Please choose one of the following options:")
    print("1. Start")
    print("2. Stop")
    print("3. Adjust Speed")

    while True:
        try:
            choice = int(input("Enter your choice (1, 2, or 3): "))
            if choice in [1, 2]:
                return "COMMAND", "START" if choice == 1 else "STOP"
            elif choice == 3:
                speed = int(input("Enter speed: "))
                return "COMMAND", f"SPEED:{speed}"
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except ValueError:
            print("Invalid input. Please enter a number (1, 2, or 3).")

# Function to send commands
def send_commands(client_socket, client_ip, client_port):
    global next_command, last_command
    while True:
        try:
            # Determine the next command
            if next_command == "NULL":
                print("Next command is NULL. Waiting for user input...")
                message_type, payload = get_user_input()
            else:
                print("Next command exists. Using next command...")
                message_type, payload = "COMMAND", next_command
                # next_command = "NULL"  # Reset the global variable

            # Construct and send the message
            message = construct_message(message_type, payload, client_ip, client_port, server_ip, server_port)
            last_command = message  # Store the last sent command for NACK handling
            client_socket.sendall(message)
            print(f"Sent: {message.decode('utf-8', errors='replace')}")

            # Wait for acknowledgment
            print("Waiting for acknowledgment...")
            if not send_event.wait(timeout=5):
                print("Error: Acknowledgment not received within 5 seconds.")
            else:
                print("Acknowledgment received.")
                send_event.clear()  # Reset the event for the next command

        except Exception as e:
            print(f"Error in send commands: {e}")
            break


# Function to log and handle errors
def handle_error(message):
    print(f"Error: {message}")
    
def listen_to_server(client_socket):
    while True:
        try:
            response = client_socket.recv(buffer_size)
            if response:
                print(f"Received from server: {response.decode('utf-8')}")
                message_type, payload = parse_message(response)
                
                # Immediately pass the message to handle_received_message function
                handle_received_message(message_type, payload)
            else:
                # If the response is empty, it means the server has closed the connection
                print("Server closed the connection.")
                break
        except Exception as e:
            print(f"Error in server listener: {e}")
            break



def get_user_input():
    print("Please choose one of the following options:")
    print("1. Start")
    print("2. Stop")
    print("3. Adjust Speed")

    while True:
        try:
            choice = int(input("Enter your choice (1, 2, or 3): "))
            if choice in [1, 2]:
                # if next_command != "NULL":
                return "COMMAND", "START" if choice == 1 else "STOP"
            elif choice == 3:
                speed = int(input("Enter speed: "))
                # if next_command != "NULL":
                return "COMMAND", f"SPEED:{speed}"
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except ValueError:
            print("Invalid input. Please enter a number (1, 2, or 3).")

def send_commands(client_socket, client_ip, client_port):
    global next_command
    while True:
        try:
            # Check for a command from the global variable
            if next_command == "NULL":
                # Get user input
                print("Next command null")
                message_type, payload = get_user_input()
            else:
                print("Next command exists")
                message_type, payload = "COMMAND", next_command

            if next_command == "NULL":
                print("Next command still null")
            else:
                print("Next command bow exists")
                message_type, payload = "COMMAND", next_command
                next_command = "NULL"  # Reset the global variable

            # Construct and send the message
            message = construct_message(message_type, payload, client_ip, client_port, server_ip, server_port)
            client_socket.sendall(message)
            print(f"Sent: {message.decode('utf-8', errors='replace')}")

            # Wait for acknowledgment
            print("Waiting for acknowledgment...")
            if not send_event.wait(timeout=5):
                print("Error: Acknowledgment not received within 3 seconds.")
            else:
                print("Acknowledgment received.")
                send_event.clear()  # Reset the event for the next command

        except Exception as e:
            print(f"Error in send commands: {e}")
            break



client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    # Connect to the server
    client_socket.connect((server_ip, server_port))
    client_ip, client_port = client_socket.getsockname()
    print(f"Connected to server at {server_ip}:{server_port}")
    print(f"Client IP and port: {client_ip}:{client_port}")
    response = client_socket.recv(buffer_size)
    if response:
        print(f"Received from server: {response.decode('utf-8')}")
    # Start the server listener thread
    listener_thread = threading.Thread(target=listen_to_server, args=(client_socket,), daemon=True)
    listener_thread.start()

    # Start the command sender thread
    send_thread = threading.Thread(target=send_commands, args=(client_socket, client_ip, client_port), daemon=True)
    send_thread.start()

    # Keep the main thread alive
    listener_thread.join()
    send_thread.join()

except KeyboardInterrupt:
    print("\nShutting down client...")
except Exception as e:
    print(f"Error: {e}")
finally:
    client_socket.close()