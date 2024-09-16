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
    os.makedirs(lib_path, exist_ok=True)

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
            if p.device == "/dev/cu.usbmodem01":
                serialFound = True
            else:
                print(".", end='', flush=True)
        time.sleep(1)
    print()
    print("Found!")

    os.system(
        'esptool.py -p /dev/cu.usbmodem01 erase_flash;' +
        ' esptool.py -p /dev/cu.usbmodem01 --after hard_reset write_flash 0x0 ' + (
            pathname) + '/firmware-mass-storage.bin')

    os.system('afplay /System/Library/Sounds/Funk.aiff')
    print()
    print("Waiting for reset")

    while not os.path.ismount("/Volumes/ELIOBOT"):
        print(".", end='', flush=True)
        time.sleep(1)
    print()

    print("Copying files, please wait ")

    os.system('rm -rf  /Volumes/ELIOBOT/sd')
    os.system('rm  /Volumes/ELIOBOT/code.py')
    os.system('cp -R ' + (pathname) + '/code/ /Volumes/ELIOBOT')

    os.system('diskutil unmount "ELIOBOT"')

    os.system('afplay /System/Library/Sounds/Glass.aiff')
    print()
    print("Job done !")
    print()

    if not args.repeat:
        break
