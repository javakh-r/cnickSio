import pexpect
import time

def get_device_info(child, device_mac):
    """
    Sends the 'info' command to bluetoothctl and returns the output.
    """
    child.sendline("info " + device_mac)
    child.expect("#", timeout=20)
    return child.before

def scan_for_device(child, device_mac, scan_duration=10):
    """
    Scans for the device with the given MAC address.
    
    Args:
        child (pexpect.spawn): The bluetoothctl session.
        device_mac (str): The MAC address to search for.
        scan_duration (int): How long to scan (in seconds).
    
    Returns:
        bool: True if the device was found, False otherwise.
    """
    print(f"Scanning for device {device_mac}...")
    child.sendline("scan on")
    found = False
    start_time = time.time()
    
    # Continuously read output for a certain duration
    while time.time() - start_time < scan_duration:
        try:
            index = child.expect([device_mac, pexpect.TIMEOUT], timeout=2)
            if index == 0:
                print(f"Device {device_mac} found during scan!")
                found = True
                break
        except pexpect.EOF:
            break

    child.sendline("scan off")
    # Wait a moment for scan to actually stop
    time.sleep(1)
    return found

def pair_and_connect_device(device_mac):
    """
    Checks the device's status, scans if necessary, and if needed:
      - Pairs the device (if not already paired),
      - Connects if not connected,
      - Prints status if already paired and connected.
    
    Args:
        device_mac (str): The MAC address of the device.
    
    Returns:
        bool: True if the device is paired and connected (or already connected),
              False otherwise.
    """
    print(f"Processing device: {device_mac}")
    # Start an interactive bluetoothctl session.
    child = pexpect.spawn('bluetoothctl', encoding='utf-8', timeout=30)
    child.expect("#")
    
    # Enable agent and set as default.
    child.sendline("agent on")
    child.expect("#")
    child.sendline("default-agent")
    child.expect("#")
    
    # Check if the device is already listed.
    child.sendline("devices")
    child.expect("#")
    devices_output = child.before
    if device_mac not in devices_output:
        print(f"Device {device_mac} not found in devices list. Starting scan.")
        if not scan_for_device(child, device_mac):
            print("Device not found after scanning. Exiting.")
            child.sendline("exit")
            child.close()
            return False
    else:
        print(f"Device {device_mac} is already listed in devices.")
    
    # Get device info.
    info_output = get_device_info(child, device_mac)
    print("Initial device info:")
    print(info_output)
    
    is_paired = "Paired: yes" in info_output
    is_connected = "Connected: yes" in info_output

    # If device is already paired and connected, print status and exit.
    if is_paired and is_connected:
        print("Device is already paired and connected.")
        child.sendline("exit")
        child.close()
        return True

    # If not paired, attempt to pair.
    if not is_paired:
        print("Device is not paired. Attempting to pair...")
        child.sendline("pair " + device_mac)
        try:
            index = child.expect([
                "Pairing successful",
                "Failed to pair",
                "Confirm passkey",
                pexpect.TIMEOUT
            ], timeout=30)

            if index == 0:
                print("Pairing successful!")
            elif index == 2:
                print("Passkey confirmation requested. Sending confirmation.")
                child.sendline("yes")
                child.expect("Pairing successful", timeout=30)
                print("Pairing successful after confirmation!")
            elif index == 1:
                # Pairing failed; check if device is already paired.
                print("Pairing failed. Checking device info...")
                info_output = get_device_info(child, device_mac)
                if "Paired: yes" in info_output:
                    print("Device appears to be already paired. Proceeding to connection.")
                else:
                    print("Device is not paired. Cannot proceed.")
                    child.sendline("exit")
                    child.close()
                    return False
            else:
                print("Timeout occurred during pairing.")
                child.sendline("exit")
                child.close()
                return False

        except pexpect.EOF:
            print("Unexpected end of session during pairing.")
            child.close()
            return False
    else:
        print("Device is already paired. Skipping pairing step.")

    # Attempt to connect.
    print("Attempting to connect...")
    child.sendline("connect " + device_mac)
    try:
        index = child.expect([
            "Connection successful",
            "Failed to connect",
            "Already connected",
            pexpect.TIMEOUT
        ], timeout=30)
        if index == 0:
            print("Connection successful!")
        elif index == 2:
            print("Device is already connected.")
        elif index == 1:
            print("Failed to connect.")
            print("Output:", child.before)
            child.sendline("exit")
            child.close()
            return False
        else:
            print("Timeout occurred during connection.")
            child.sendline("exit")
            child.close()
            return False
    except pexpect.TIMEOUT:
        print("Timeout occurred during connection.")
        child.sendline("exit")
        child.close()
        return False

    child.sendline("exit")
    child.close()
    return True

if __name__ == "__main__":
    device_mac = "9F:DA:07:42:18:F4"
    print(f"Processing device: {device_mac}")
    if pair_and_connect_device(device_mac):
        print("Device is paired and connected.")
    else:
        print("Failed to pair and/or connect to the device.")
