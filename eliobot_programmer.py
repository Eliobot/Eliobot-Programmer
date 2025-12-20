import platform
import os
import shutil
import time
import serial.tools.list_ports
import argparse
import subprocess

pathname = os.path.dirname(os.path.realpath(__file__))

# Create the parser
parser = argparse.ArgumentParser(description='Flash robot with latest firmware and optional library update.')

# Add an argument
parser.add_argument('--repeat', action='store_true', required=False)
parser.add_argument('--nopull', action='store_true',
                    help='Pull the latest library updates from git repository before flashing.')

# Parse the argument
args = parser.parse_args()


def update_library_repo(lib_path, git_url, branch='dev'):
    # Remove the directory if it exists
    shutil.rmtree(lib_path, ignore_errors=True)

    # Clone the specific branch if the directory is empty
    subprocess.run(['git', 'clone', '--branch', branch, git_url, lib_path], check=True)
    os.chdir(lib_path)

    # Remove unnecessary files
    for filename in ['README.md', '.gitignore', '.git']:
        try:
            # Check if it's a directory
            if os.path.isdir(filename):
                shutil.rmtree(filename)  # Remove directory
                print(f"{filename} directory deleted.")
            else:
                os.remove(filename)  # Remove file
                print(f"{filename} file deleted.")
        except FileNotFoundError:
            print(f"{filename} not found")
        except PermissionError:
            print(f"Permission denied while trying to delete {filename}")


if not args.nopull:
    lib_directory = 'code/lib'
    repository_url = 'https://github.com/Eliobot/Eliobot-Python-Library.git'
    update_library_repo(lib_directory, repository_url)

print(os.name)

print(platform.platform())

while True:
    print()
    print("Waiting for Serial")

    serialFound = False

    while not serialFound:
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if p.device.startswith("/dev/cu.usbmodem"):
                serialFound = True
            else:
                print(".", end='', flush=True)
        time.sleep(1)
    print()
    print("Found!")

    print("Erasing flash...")
    # Erase flash and capture output to determine chip type
    result = subprocess.run(['esptool', 'erase-flash'], capture_output=True, text=True)
    print(result.stdout)  # Print the erase-flash output

    # Parse chip type from output
    chip_type = None
    for line in result.stdout.split('\n'):
        if 'Chip type:' in line:
            chip_type = line.split('Chip type:')[1].strip()  # e.g., "ESP32-S3"
            break

    # Choose firmware based on chip type
    if chip_type and 'ESP32-S3' in chip_type:
        firmware_file = 'Eliobot_S3/fw_eliobot_s3_noREPL.bin'
        code_dir = 'Eliobot_S3/code-S3'
    elif chip_type and 'ESP32-S2' in chip_type:
        firmware_file = 'Eliobot_S2/fw_eliobot_s2_noREPL.bin'
        code_dir = 'Eliobot_S2/code-S2'
    else:
        firmware_file = 'fw_eliobot_s3_noREPL.bin'  # Default fallback
        code_dir = 'Eliobot_S3/code-S3'  # Default fallback

    print(f"Detected chip: {chip_type}, using firmware: {firmware_file} and code dir: {code_dir}")


    print()
    print("Waiting for Serial")

    serialFound = False

    while not serialFound:
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if p.device.startswith("/dev/cu.usbmodem"):
                serialFound = True
            else:
                print(".", end='', flush=True)
        time.sleep(1)
    print()
    print("Found!")
    
    # Write flash with the chosen firmware
    subprocess.run(['esptool', '--after', 'hard-reset', 'write-flash', '0x0', os.path.join(pathname, firmware_file)])

    os.system('afplay /System/Library/Sounds/Funk.aiff')
    print()
    print("Waiting for reset")

    while not os.path.ismount("/Volumes/ELIOBOT"):
        print(".", end='', flush=True)
        time.sleep(1)
    print()

    print("Copying files, please wait ")

    os.system('cp -R ' + (pathname) + '/' + code_dir + '/ /Volumes/ELIOBOT')

    os.system('diskutil unmount "ELIOBOT"')

    os.system('afplay /System/Library/Sounds/Glass.aiff')
    print()
    print("Job done !")
    print()

    if not args.repeat:
        break
