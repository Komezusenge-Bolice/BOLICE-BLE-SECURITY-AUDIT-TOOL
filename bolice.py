import sys
import time
import subprocess 
from bluepy.btle import Scanner, DefaultDelegate, Peripheral, BTLEException

# --- Global Configuration ---
ADAPTER_INDEX = 0 
TIMEOUT_SCAN = 300  # 5 minutes
TIMEOUT_CONN = 5
HCI_DEVICE = f"hci{ADAPTER_INDEX}" 

# --- System & Setup Function ---
def reset_adapter(device):
    """
    Performs the CRITICAL system reset command to clear the adapter's corrupted state.
    This fixes the 'Rejected' error by killing the locking process.
    """
    print(f"\n[SYSTEM] Attempting ultimate reset on {device}...")
    
    # NOTE: Since the main script is run with 'sudo', we remove 'sudo' from the subprocess calls.
    # This prevents the nested privilege issue that causes command rejection.
    try:
        # 1. Stop Bluetooth service to release the adapter lock
        subprocess.run(['systemctl', 'stop', 'bluetooth'], check=False, capture_output=True)
        print(" [INFO] Bluetooth service stopped.")
        
        # 2. **CRITICAL FIX:** Kill any residual BlueZ processes holding the lock (Code 11: Rejected)
        subprocess.run(['killall', '-9', 'bluetoothd'], check=False, capture_output=True)
        print(" [INFO] Residual bluetoothd processes killed.")
        
        # 3. Final hardware reset
        result = subprocess.run(['hciconfig', device, 'reset'], check=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f" [SUCCESS] {device} reset successful.")
        else:
            print(f" [WARNING] hciconfig reset failed (Code: {result.returncode}). Continuing...")
    except subprocess.CalledProcessError as e:
        print(f" [ERROR] Could not execute adapter reset command: {e}")
    except FileNotFoundError:
        print(" [ERROR] Core commands ('systemctl', 'killall', 'hciconfig') not found. Check system PATH.")
        
# --- 1. Delegate Class for Scanning ---
class ScanDelegate(DefaultDelegate):
    """Handles discovery events during scanning."""
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.devices = {}

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            # Store device by MAC address
            self.devices[dev.addr.upper()] = dev

# --- 2. Core Scanning Function ---
def discover_devices(adapter_index):
    """Scans for nearby BLE devices and prompts user for selection."""
    print("\n--- 1. Device Discovery ---")
    
    # CRITICAL FIX: Run the ultimate reset before scanning
    reset_adapter(HCI_DEVICE)
    time.sleep(1) # Give the adapter a moment to re-initialize

    try:
        # Final Syntax Fix: Use positional argument for index, and withDelegate() method
        scanner = Scanner(adapter_index)
        delegate = ScanDelegate()
        scanner.withDelegate(delegate) 
        
        print(f" [+] Scanning for {TIMEOUT_SCAN} seconds on hci{adapter_index}...")
        devices = scanner.scan(TIMEOUT_SCAN)
        
    except BTLEException as e:
        print(f"\n[CRITICAL ERROR] Scanner failed: {e}")
        return None

    if not delegate.devices:
        print(" [INFO] No devices found.")
        return None

    print("\n--- Discovered Devices ---")
    device_list = sorted(delegate.devices.values(), key=lambda d: d.addr)
    for i, dev in enumerate(device_list):
        name = dev.getValueText(9) if dev.getValueText(9) else "N/A"
        print(f" {i+1}. MAC: {dev.addr.upper()} | Name: {name} | RSSI: {dev.rssi} dB")

    while True:
        try:
            choice = input("\nSelect device number to test (e.g., 1) or 'q' to quit: ")
            if choice.lower() == 'q':
                return None
            
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(device_list):
                selected_device = device_list[choice_index]
                print(f" [SELECTED] Testing device: {selected_device.addr.upper()}")
                return selected_device.addr.upper()
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number or 'q'.")

# --- 3. Full Security Audit Test ---
def run_security_audit(target_mac, adapter_index):
    """Performs the full connection and enumeration test."""
    print("\n--- 2. Connection and Enumeration Test ---")
    
    try:
        # Connect to the target device using the specified interface
        p = Peripheral(target_mac, iface=adapter_index) 
        print(" [PASS] Successfully connected to device.")
        
        # Test 2a: Service Enumeration
        services = p.getServices()
        print(f" [INFO] Enumerated {len(services)} services:")
        
        # Test 2b: Characteristic Read/Write Test 
        for svc in services:
            print(f"\n  [Service] UUID: {svc.uuid}")
            characteristics = svc.getCharacteristics()

            for char in characteristics:
                props = char.propertiesToString()
                char_info = f"    [Char] UUID: {char.uuid}, Props: {props}"
                
                # Test READ permissions
                if 'READ' in props:
                    try:
                        value = char.read()
                        print(f"{char_info} -> READ SUCCESS: {value.hex()}")
                    except BTLEException:
                        print(f"{char_info} -> READ FAIL (Auth needed?)")

                # Test WRITE permissions
                if 'WRITE' in props or 'WRITE NO RESPONSE' in props:
                    try:
                        char.write(b'\x01', withResponse='WRITE' in props)
                        print(f"{char_info} -> WRITE SUCCESS (CRITICAL VULNERABILITY!)")
                    except BTLEException:
                        print(f"{char_info} -> WRITE FAIL (Good: Requires authentication.)")
                        
        p.disconnect()
        print("\n [INFO] Disconnected successfully.")
        
    except BTLEException as e:
        if "Failed to connect" in str(e):
             print(f" [FAIL] Failed to connect. (Good: Device requires bonding/pairing.)")
        else:
            print(f" [ERROR] Connection/Enumeration Test failed: {e}")

# --- 4. Main Execution and Menu ---
def main():
    """Handles the user interface and test flow."""
    print("\n==============================================")
    print("  BOLICE: BLE SECURITY AUDIT TOOL")
    print("==============================================")
    print("Pre-flight Checklist (CRITICAL):")
    print(f"1. **Execute as Root:** Use `sudo /home/voidghost/venv/bin/python3 bolice.py`")
    print(f"2. **Adapter Interface:** Using {HCI_DEVICE} (Index {ADAPTER_INDEX}).")

    target_mac = None

    while True:
        print("\n==============================================")
        print("  BOLICE MENU")
        print("==============================================")
        print("1. Scan for devices (Resets adapter and kills processes)")
        print("2. Run Full Security Audit (Connect & Enumerate)")
        print("3. Exit")
        
        choice = input("Enter your choice (1, 2, or 3): ")

        if choice == '1':
            target_mac = discover_devices(ADAPTER_INDEX)
        
        elif choice == '2':
            if target_mac is None:
                print("\nPlease scan for devices first (Option 1) and select a target.")
            else:
                print(f"\n## Starting Security Audit for: {target_mac} ##")
                run_security_audit(target_mac, ADAPTER_INDEX)

        elif choice == '3':
            print("Exiting audit tool. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please select 1, 2, or 3.")

# --- Run the Script ---
if __name__ == "__main__":
    main()