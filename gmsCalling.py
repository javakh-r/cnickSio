import serial
import time

# Configure serial connection (update SERIAL_PORT as needed)
SERIAL_PORT = '/dev/ttyS0'  # or '/dev/serial0'
BAUD_RATE = 9600

def send_at_command(ser, command, delay=1):
    """
    Sends an AT command to the SIM800L and returns the response.
    """
    full_command = command + "\r\n"
    ser.write(full_command.encode())
    time.sleep(delay)
    response = ser.read_all().decode()
    return response

def main():
    try:
        # Open serial connection to the SIM800L module
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(1)  # Allow time for module initialization

        # Test communication with the module
        response = send_at_command(ser, "AT")
        print("Response to 'AT':", response)

        # Optional: Check SIM card status
        response = send_at_command(ser, "AT+CPIN?")
        print("Response to 'AT+CPIN?':", response)

        # Dial a number (replace with the actual phone number)
        phone_number = "+995557598200"
        dial_command = "ATD" + phone_number + ";"  # Note the semicolon to indicate voice call
        print("Dialing:", phone_number)
        response = send_at_command(ser, dial_command)
        print("Response to Dial command:", response)

        # Keep the call active for 30 seconds (adjust as necessary)
        time.sleep(30)

        # Hang up the call using the ATH command
        response = send_at_command(ser, "ATH")
        print("Response to Hang-up command:", response)

    except Exception as e:
        print("An error occurred:", e)
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial connection closed.")

if __name__ == "__main__":
    main()
