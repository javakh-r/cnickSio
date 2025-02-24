import serial
import time
import os
import sys

def require_root():
    """Relaunch the script with sudo if not running as root."""
    if os.geteuid() != 0:
        print("This script requires root privileges. Relaunching with sudo...")
        # Build the command: sudo python3 script_name.py arg1 arg2 ...
        try:
            os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
        except Exception as e:
            print("Failed to elevate privileges:", e)
            sys.exit(1)

require_root()
def send_at_command(ser, command, delay=1):
    """
    Sends an AT command to the SIM800L module and prints its immediate response.
    
    Args:
        ser (serial.Serial): The open serial port connection.
        command (str): The AT command to send.
        delay (float): Delay in seconds to wait after sending the command.
    """
    full_command = command + "\r\n"
    print(f"\n>> Sending: {command}")
    ser.write(full_command.encode())
    time.sleep(delay)
    # Print any immediate response data from the SIM800L
    if ser.inWaiting():
        response = ser.read(ser.inWaiting()).decode('utf-8', errors='ignore')
        print("<< Response:", response.strip())

def listen_for_responses(ser, duration=10):
    """
    Continuously listens to the serial port and prints any data coming from SIM800L.
    
    Args:
        ser (serial.Serial): The open serial port connection.
        duration (int): Number of seconds to listen for responses.
    """
    print(f"\nListening for responses for {duration} seconds...")
    start_time = time.time()
    while time.time() - start_time < duration:
        if ser.inWaiting():
            response = ser.read(ser.inWaiting()).decode('utf-8', errors='ignore')
            print("<< SIM800L:", response.strip())
        time.sleep(0.2)

def send_sms(ser, phone_number, message):
    """
    Sends an SMS message using the SIM800L AT command set.
    
    Args:
        ser (serial.Serial): The open serial port connection.
        phone_number (str): Recipient's phone number (include country code if required).
        message (str): The text message to send.
    """
    # Test communication with the module
    send_at_command(ser, "AT", delay=1)
    
       # Set SMS text mode
    send_at_command(ser, "AT+CMGF=1", delay=1)
    
    # Start SMS command by specifying the recipient's number
    send_at_command(ser, f'AT+CMGS="{phone_number}"', delay=2)
    
    # Send the message text followed by Ctrl+Z (ASCII 26) to signal message end.
    print(">> Sending SMS text...")
    ser.write(message.encode() + b"\r\n")
    ser.write(bytes([26]))
    
    # Wait a few seconds for the module to process the SMS command.
    time.sleep(3)
    
    # Read and print any response after sending the SMS.
    if ser.inWaiting():
        response = ser.read(ser.inWaiting()).decode('utf-8', errors='ignore')
        print("<< Response:", response.strip())

def main():
    # Open the UART serial port. /dev/serial0 is typically the Pi's primary UART.
    serial_port = "/dev/ttyS0"  # Adjust if necessary (/dev/ttyAMA0 or /dev/ttyS0)
    baud_rate = 9600             # The common baud rate for SIM800L modules
    try:
        ser = serial.Serial(serial_port, baud_rate, timeout=1)
        print(f"Opened serial port {serial_port} at {baud_rate} baud.")
    except Exception as e:
        print(f"Error opening serial port {serial_port}: {e}")
        return

    # Allow time for the SIM800L to initialize after power-up.
    time.sleep(2)

    # Replace with the recipient's phone number (include country code if needed)
    phone_number = "+995557598200"
    # Replace with your SMS text message.
    message = "Hello, this is a test SMS sent from the SIM800L via Raspberry Pi UART!"

    # Send the SMS message
    send_sms(ser, phone_number, message)
    
    # Close the serial port
    ser.close()
    print("Serial port closed.")

if __name__ == "__main__":
    main()
