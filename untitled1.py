import serial
import time

def send_command(ser, command, wait=1):
    """Send an AT command to the SIM800L and print the response."""
    full_command = command + "\r\n"
    print("Sending:", command)
    ser.write(full_command.encode())
    time.sleep(wait)
    while ser.in_waiting:
        response = ser.readline().decode().strip()
        if response:
            print("Response:", response)

def main():
    serial_port = '/dev/ttyS0'  # Adjust to your correct serial port
    baud_rate = 9600  # Or use the baud rate your module requires

    try:
        ser = serial.Serial(serial_port, baud_rate, timeout=1)
        time.sleep(2)  # Allow module initialization

        # Test communication
        send_command(ser, "AT")

        # *** Ensure you are in an active call before sending DTMF ***
        print("Please make or answer a call on the SIM800L now...")
        time.sleep(10)  # Wait 10 seconds for a call to be active

        # Try sending DTMF without quotes
        send_command(ser, 'AT+VTS=1')

        # Alternatively, if your module expects quotes, try this:
        # send_command(ser, 'AT+VTS="1"')

        ser.close()

    except serial.SerialException as e:
        print("Serial error:", e)
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
