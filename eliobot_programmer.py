import platform
import RPi.GPIO as GPIO
import neopixel
import board
import os
import shutil
import time
import serial.tools.list_ports
import argparse
import subprocess


pathname = os.path.dirname(os.path.realpath(__file__))

state=0
erreur=0
GPIO.setmode(GPIO.BCM)

#Initialize of RGB_LED WS2812B with PWM
Pin_LED = board.D12#LED RGB
NUM_PIXELS = 1 # Nombre de leds
BRIGHTNESS = 0.1  # Luminosité (0.0 à 1.0)
ORDER= neopixel.GRB
pixels = neopixel.NeoPixel(Pin_LED, NUM_PIXELS, brightness=BRIGHTNESS, auto_write=False, pixel_order=ORDER)

#Initialize of IN/OUT
BReset = 18 #EN/Reset TP1
BBoot = 24 #IO/Button TP5
BDebug = 17 #Debug Button

GPIO.setup(BReset, GPIO.OUT) #to simulate RESET
GPIO.setup(BBoot, GPIO.OUT) #to simulate BOOT
GPIO.setup(BDebug, GPIO.IN,  pull_up_down=GPIO.PUD_UP) #BUTTON of bench


#############
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

#########################################################################################################################################
#########################################################################################################################################
#Start of code
try:
    while True:

        if state==0: #Initial state, BOOT state

            GPIO.output(BBoot, GPIO.HIGH) #stop simulation of boot button
            pixels.fill((0, 0, 255))  # Blue color (R, G, B)
            pixels.show()
            time.sleep(2)
            if GPIO.input(BDebug)== GPIO.LOW: #Press button just one time
                time.sleep(1)
                
                state=1

        elif state==1: #SEARCH state

            erreur=0
            
            time.sleep(1)
            GPIO.output(BBoot, GPIO.LOW) #Simulation of boot button
            pixels.fill((0, 78, 255))   # Cyan color (R, G, B)
            pixels.show()
            time.sleep(3)
            print()
            print("reset")
            GPIO.output(BReset, GPIO.LOW) #Simulation of reset button
            state=2

        elif state==404: #ERROR state
            pixels.fill((255, 0, 0))  # Red color (R, G, B)
            pixels.show()

            print("En attente que le bouton soit pressé pendant 5 secondes...")
            if GPIO.input(BDebug) == GPIO.LOW:
                start_time = time.time()  
                while GPIO.input(BDebug) == GPIO.LOW:
                    elapsed_time = time.time() - start_time  
                    if elapsed_time >= 5:  
                        state=0
                        break
                    time.sleep(0.1)
                if elapsed_time < 5:
                    print("Le bouton a été relâché avant 5 secondes. Recommence...")
            time.sleep(0.1)

        while state==2:  # flash and program state

            pixels.fill((255, 0, 255))   # Purple color (R, G, B)
            pixels.show()
            time.sleep(2)
            GPIO.output(BReset, GPIO.HIGH) #Stop simulation of reset button

            time.sleep(5)
            GPIO.output(BBoot, GPIO.HIGH) #Stop simulation of boot button
            
            print()
            print("Waiting for Serial")

            serialFound = False

            while not serialFound:
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    # Check type of connection(like /dev/ttyUSB0 or /dev/ttyACM0)
                    if p.device.startswith('/dev/ttyUSB') or p.device.startswith('/dev/ttyACM'):
                        serialFound = True
                        serial_device = p.device
                        break
                print(".", end='', flush=True)
                time.sleep(1)
            print()
            print(f"Found {serial_device}!")

            pixels.fill((0, 120, 255))   # Cyan color (R, G, B)
            pixels.show()
            # Flash card with esptool
            os.system(f'sudo esptool.py -p {serial_device} erase_flash; '
                    f'sudo esptool.py -p {serial_device} --after no_reset write_flash 0x0 /home/ELIO/Documents/Eliobot-Programmer/firmware-mass-storage.bin') 
            #sudo esptool because we use the native environment which is already on Raspberry Pi at the first run.



            print()
            print("Waiting for reset")

            pixels.fill((255, 255, 0)) # Yellow color (R, G, B)
            pixels.show()
            time.sleep(1)
            GPIO.output(BReset, GPIO.LOW) #Simulation of reset button
            time.sleep(5)
            GPIO.output(BReset, GPIO.HIGH) #Stop simulation of reset button

            mount_point = '/media/ELIO/ELIOBOT'  # Ajust if it's neccessary

            while not os.path.ismount(mount_point):
                print(".", end='', flush=True)
                time.sleep(1)
            print()
            print("Copying files, please wait ")
            pixels.fill((255, 64,0 )) # Orange color (R, G, B)
            pixels.show()

            os.system(f'rm -rf {mount_point}/sd')
            os.system(f'rm {mount_point}/code.py')
            os.system(f'cp -R /home/ELIO/Documents/Eliobot-Programmer/code/* {mount_point}')

            print()

            time.sleep(2)

            direct_path = "/media/ELIO/ELIOBOT/"
            file_name = "boot.py"
            file_path = "/media/ELIO/ELIOBOT/boot.py"

            # Read repertorie content
            contents = os.listdir(direct_path)

            # Check if the boot.py file is present
            if file_name in contents:
                print(f"Le fichier {file_name} est présent dans le répertoire {direct_path}.")
                with open(file_path, 'r') as file:
                # Read all lines of directory
                    lines = file.readlines()

                # Check if the specific line is present
                if any("storage.remount(\"/\", False)" in line for line in lines):
                    print("The line 'storage.remount(\"/\", False)' is not found.")
                else:
                    print("The line 'storage.remount(\"/\", False)' is not found.")
                    state=404
                    break
                    print(f"État défini à {state}.")
            else:
                print(f"The file {file_name} is not present in the directory {direct_path}.")
                state=404
                break

            # delete montage point
            os.system(f'umount {mount_point}')

            print("Job done !")
            print()
            print("Take your card!")
            print()


            time.sleep(3)

            state=0
        
except KeyboardInterrupt:
    #Stop led
    pixels.fill((0, 0, 0))
    pixels.show()
    GPIO.cleanup()
    print("\nInterrupt programm.")
    
