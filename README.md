# BOLICE-BLE-SECURITY-AUDIT-TOOL
BOLICE (Bluetooth Low Energy Security Audit Tool) is a Python utility designed to help security professionals and developers assess the security posture of target Bluetooth Low Energy (BLE) devices.

This tool automates the process of discovering nearby BLE devices, performing unauthenticated connection attempts, and enumerating services and characteristics to identify potential vulnerabilities like unauthorized data access (read) or device control (write).

✨ Features
Interactive Menu: Easy command-line interface for selecting scan and audit actions.

Target Selection: Scans for devices and allows the user to select a specific MAC address for testing.

Ultimate Stability: Includes a built-in, low-level adapter reset sequence (using systemctl, killall, and hciconfig) to clear common BlueZ driver conflicts (like "Rejected" or "Invalid Parameters" errors) that frequently occur during raw BLE access on Kali Linux.

Vulnerability Testing: Attempts unauthorized reads and writes on exposed characteristics.

Customizable Scan Time: Configurable scan period (currently 5 minutes/300 seconds).

🚀 Getting Started
Prerequisites
This tool requires raw access to the Bluetooth hardware, which means specific configurations on Linux (like Kali or Debian/Ubuntu) are necessary.

Operating System: Kali Linux (Recommended) or any Debian-based distribution.

Required System Tools: Ensure the BlueZ tools and management utilities are installed:

Bash

sudo apt update
sudo apt install bluetooth bluez bluez-tools
Python Environment: Python 3.x with a dedicated virtual environment is highly recommended.

Bash

python3 -m venv venv
source venv/bin/activate
Installation
Install the required Python library (bluepy) within your virtual environment:

Bash

pip install bluepy
Critical Setup Steps (Required for Low-Level Access)
Since BOLICE needs raw access to the Bluetooth adapter, the bluepy-helper binary must have special capabilities set. This is mandatory and often the reason for permission errors.

Locate the Helper: Find the path to the installed bluepy-helper within your virtual environment.

Bash

HELPER_PATH=$(find /home/voidghost/venv -name "bluepy-helper" 2>/dev/null)
echo $HELPER_PATH
Set Capabilities: Run the following command using the path found above.

Bash

sudo setcap 'cap_net_raw+eip' $HELPER_PATH
⚙️ How to Run the Tool
Due to the raw hardware access requirements, you must run the script using the explicit path to the virtual environment's Python interpreter and with sudo.

Run the script:

Bash

sudo /home/voidghost/venv/bin/python3 bolice.py
Follow the Menu:

Option 1 (Scan): Select this first. The script will automatically stop the main bluetooth service, kill any lingering bluetoothd processes, and hard reset the hci0 adapter before scanning to ensure a clean state.

Select Target: Choose the device you wish to audit by entering its corresponding number.

Option 2 (Audit): Runs the full security test on the selected MAC address.

🆘 Getting Help & Troubleshooting
If you encounter the [CRITICAL ERROR] Scanner failed message, it means the low-level adapter reset sequence failed.

Final Manual Fix: Even with the built-in reset, residual processes can sometimes hold a lock. Run these manual commands and try the script again:

Bash

sudo systemctl stop bluetooth
sudo killall -9 bluetoothd
sudo hciconfig hci0 reset
Unplug/Replug: If the error persists, the hardware state might be completely corrupted. Unplug and replug your USB Bluetooth adapter (if using one).

Check Capabilities: Double-check that the setcap command (under Critical Setup Steps) was executed successfully.
