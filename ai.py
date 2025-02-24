import serial
import time
import json
import re
import pyaudio
import pyttsx3
import subprocess
import threading
from vosk import Model, KaldiRecognizer

# --- Global Variables ---
call_mode = False
call_active = False   # Indicates whether a call is currently active
phone_number = ""     # To store the 9 digits of the phone number
engine = None         # Global TTS engine

# --- SIM800L Serial Configuration ---
SERIAL_PORT = '/dev/ttyS0'  # Update as needed
BAUD_RATE = 9600

# Mapping for converting spoken words to digits
digit_mapping = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9"
}

def convert_words_to_digits(text):
    """
    Convert spoken words (e.g., 'five') to digits.
    """
    result = ""
    for word in text.split():
        word_clean = re.sub(r'[^\w\s]', '', word)
        if word_clean in digit_mapping:
            result += digit_mapping[word_clean]
        elif word_clean.isdigit():
            result += word_clean
    return result

def init_tts():
    """
    Initialize the global TTS engine.
    """
    global engine
    if engine is None:
        engine = pyttsx3.init('espeak')
        engine.setProperty('rate', 125)
        engine.setProperty('volume', 1.0)

def speak(text):
    """
    Speak the provided text using pyttsx3.
    """
    init_tts()
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("TTS error:", e)
    time.sleep(0.5)

def send_at_command(ser, command, delay=1):
    """
    Send an AT command to the SIM800L and log the response.
    """
    full_command = command + "\r\n"
    print(f"Sending command: {full_command.strip()}")
    ser.write(full_command.encode())
    time.sleep(delay)
    response = ser.read_all().decode().strip()
    print(f"Received response: {response}")
    return response

def init_serial():
    """
    Initialize the serial connection.
    """
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(1)
        print("Serial connection established.")
        response = send_at_command(ser, "AT")
        if "OK" in response:
            return ser
        else:
            print("SIM800L did not respond correctly.")
            return None
    except Exception as e:
        print("Serial connection error:", e)
        return None

def switch_audio_routing():
    """
    Switch audio routing by loading the required loopback modules.
    """
    try:
        cmd1 = ("pactl load-module module-loopback "
                "source=bluez_input.9F_DA_07_42_18_F4.0 "
                "sink=alsa_output.usb-C-Media_Electronics_Inc._USB_Audio_Device-00.analog-stereo "
                "latency_msec=30")
        cmd2 = ("pactl load-module module-loopback "
                "source=alsa_input.usb-C-Media_Electronics_Inc._USB_Audio_Device-00.mono-fallback "
                "sink=bluez_output.9F_DA_07_42_18_F4.1 "
                "latency_msec=30")
        subprocess.run(cmd1, shell=True, check=True)
        subprocess.run(cmd2, shell=True, check=True)
        print("Audio routing switched successfully.")
    except subprocess.CalledProcessError as e:
        print("Error switching audio routing:", e)

def delete_all_routings():
    """
    Delete all loopback routings by unloading modules containing 'module-loopback'.
    """
    try:
        cmd1 = ("for mod in $(pactl list short modules | grep loopback | awk '{print $1}'); "
                "do pactl unload-module $mod; done")
        subprocess.run(cmd1, shell=True, check=True)
        print("Deleted all loopback routings.")
    except subprocess.CalledProcessError as e:
        print("Error deleting all routings:", e)

def dial_number(ser, full_phone_number):
    """
    Dial the given phone number via the SIM800L.
    Runs in its own thread so that voice commands (e.g., 'hang up')
    can be processed concurrently.
    """
    global call_active
    print("Preparing to dial...")
    switch_audio_routing()
    dial_command = "ATD" + full_phone_number + ";"
    print(f"Dialing: {full_phone_number}")
    response = send_at_command(ser, dial_command, delay=2)
    
    # Check if the response indicates the call is progressing
    if "OK" in response or "CONNECT" in response:
        print("Call initiated successfully.")
    else:
        print("Call initiation may have failed. Check SIM800L and connection.")
    
    # Mark the call as active
    call_active = True

    # Instead of a fixed sleep, check every second for up to 30 seconds
    for i in range(30):
        if not call_active:
            # Call was terminated via voice command
            break
        time.sleep(1)
    
    # If the call is still active, hang up
    if call_active:
        send_at_command(ser, "ATH", delay=2)
        print("Call ended automatically after timeout.")
    else:
        print("Call was hung up by voice command.")
    
    delete_all_routings()
    call_active = False

def list_audio_devices(p):
    """
    List available audio input devices.
    """
    print("Available audio devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info.get("maxInputChannels") > 0:
            print(f"  Device {i}: {info.get('name')} (Channels: {info.get('maxInputChannels')})")

def voice_recognition_loop(ser):
    """
    Main loop for voice recognition.
    """
    global call_mode, phone_number, call_active

    p = pyaudio.PyAudio()
    list_audio_devices(p)
    
    # Use a valid device index from the printed list (try 1 or 2)
    device_index = 2
    print(f"Using audio device index: {device_index}")
    
    model_path = "/home/pi/Desktop/vosk-model-small-en-us-0.15"  # Update as needed
    try:
        model = Model(model_path)
    except Exception as e:
        print(f"Error loading model from {model_path}: {e}")
        return

    recognizer = KaldiRecognizer(model, 16000)
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=8000
        )
    except Exception as e:
        print(f"Error opening audio stream: {e}")
        return

    stream.start_stream()
    print("Listening... Press Ctrl+C to stop.")

    try:
        while True:
            data = stream.read(4000, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()
                if text:
                    print("You said:", text)
                    
                    # Check for initiating a call
                    if "call" in text:
                        call_mode = True
                        phone_number = ""
                        speak("tell me number")
                        continue

                    # If in call mode, accumulate digits
                    if call_mode:
                        digits = convert_words_to_digits(text)
                        if digits:
                            phone_number += digits
                            print(f"Accumulated digits: {phone_number}")
                            
                            if len(phone_number) >= 9:
                                phone_number = phone_number[:9]
                                full_phone_number = "+995" + phone_number
                                print(f"Final phone number: {full_phone_number}")
                                speak("Calling number " + " ".join(phone_number))
                                # Start the call in a separate thread so we can listen for hang up
                                threading.Thread(target=dial_number, args=(ser, full_phone_number)).start()
                                call_mode = False
                                phone_number = ""
                        continue

                    # Check for hang up command during an active call
                    if "hang up" in text:
                        if call_active:
                            send_at_command(ser, "ATH", delay=2)
                            delete_all_routings()
                            speak("Call ended")
                            call_active = False
                        else:
                            speak("No active call to hang up")
    except KeyboardInterrupt:
        print("Exiting voice recognition loop...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

def main():
    ser = init_serial()
    if ser is None:
        print("Unable to initialize serial connection. Exiting.")
        return

    try:
        voice_recognition_loop(ser)
    except Exception as e:
        print("An error occurred in the main loop:", e)
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Serial connection closed.")

if __name__ == "__main__":
    main()
