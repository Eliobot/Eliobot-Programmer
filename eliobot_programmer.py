import platform
import os
import time
import serial.tools.list_ports
import argparse
import subprocess

pathname = os.path.dirname(os.path.realpath(__file__))

# Create the parser
parser = argparse.ArgumentParser(description='Flash robot with latest firmware and optional library update.')

# Add an argument
parser.add_argument('--repeat', type=bool, required=False)
parser.add_argument('--pull', action='store_true', help='Pull the latest library updates from git repository before flashing.')

# Parse the argument
args = parser.parse_args()

if args.pull:
    print("Pulling latest updates from git repository...")
    subprocess.run(['git', '-C', 'code/lib', 'pull'])
    print("Update completed.")
    readme_path = os.path.join('code/lib', 'README.md')
    if os.path.exists(readme_path):
        os.remove(readme_path)
        print("README.md deleted successfully.")
    else:
        print("README.md not found.")

    gitignore_path = os.path.join('code/lib', '.gitignore')
    if os.path.exists(gitignore_path):
        os.remove(gitignore_path)
        print(".gitignore deleted successfully.")
    else:
        print(".gitignore not found.")


print(os.name)

print(platform.platform())


while True :
    print()
    print("Waiting for Serial")

    serialFound = False

    while not serialFound :
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if p.device == "/dev/cu.usbmodem01" :
                serialFound = True
            else :
                print(".", end='', flush=True)
        time.sleep(1)
    print()
    print("Found!")

    os.system('esptool.py -p /dev/cu.usbmodem01 erase_flash; esptool.py -p /dev/cu.usbmodem01 --after hard_reset write_flash 0x0 '+(pathname)+'/eliobot.bin')

    os.system('afplay /System/Library/Sounds/Funk.aiff')
    print()
    print("Waiting for reset")

    while not os.path.ismount("/Volumes/TINYS2BOOT") :
        print(".", end='', flush=True)
        time.sleep(1)
    print()

    os.system('cp '+(pathname)+'/firmware.uf2 /Volumes/TINYS2BOOT')
    print()
    print("Copying files, please wait ")

    while not os.path.ismount("/Volumes/CIRCUITPY") :
        print(".", end='', flush=True)
        time.sleep(1)
    print()

    os.system('diskutil rename "CIRCUITPY" "ELIOBOT"')
    print()

    while not os.path.ismount("/Volumes/ELIOBOT") :
        print("Waiting ELIOBOT")
        time.sleep(1)

    os.system('rm  /Volumes/ELIOBOT/code.py')
    os.system('cp -R '+(pathname)+'/code/ /Volumes/ELIOBOT')

    os.system('diskutil unmount "ELIOBOT"')

    os.system('afplay /System/Library/Sounds/Glass.aiff')
    print()
    print("Job done !")
    print()


    if not args.repeat :
        break
