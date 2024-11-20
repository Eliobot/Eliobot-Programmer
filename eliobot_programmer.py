import os
import time
import esptool
import serial.tools.list_ports
import argparse
import shutil
import subprocess

# Detect current directory
pathname = os.path.dirname(os.path.realpath(__file__))

# Parse arguments
parser = argparse.ArgumentParser(description='Flash robot with latest firmware and optional library update.')
parser.add_argument('--repeat', action='store_true', required=False, help='Repeat the process after finishing.')
parser.add_argument('--nopull', action='store_true', required=False, help='Skip pulling the library updates.')
args = parser.parse_args()


def update_library_repo(lib_path, git_url, branch='dev'):
    """
    Update the library repository by cloning the specified branch.

    Args:
        lib_path (str): Path to the library folder.
        git_url (str): URL of the Git repository.
        branch (str): Branch to clone (default: 'dev').

    Returns:
        None
    """
    shutil.rmtree(lib_path, ignore_errors=True)
    subprocess.run(['git', 'clone', '--branch', branch, git_url, lib_path], check=True)
    clean_repo(lib_path, ['README.md', '.gitignore', '.git'])


def clean_repo(lib_path, files_to_remove):
    """
    Remove unnecessary files or directories from the library path.

    Args:
        lib_path (str): Path to the library folder.
        files_to_remove (list): List of filenames or directories to remove.

    Returns:
        None
    """
    for filename in files_to_remove:
        full_path = os.path.join(lib_path, filename)
        try:
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
                print(f"Directory '{filename}' deleted.")
            elif os.path.isfile(full_path):
                os.remove(full_path)
                print(f"File '{filename}' deleted.")
            else:
                print(f"'{filename}' does not exist or is not a file/directory.")
        except FileNotFoundError:
            print(f"'{filename}' not found.")
        except PermissionError:
            print(f"Permission denied while trying to delete '{filename}'.")
        except Exception as e:
            print(f"Unexpected error while deleting '{filename}': {e}")


def find_serial_device():
    """
    Detect and return the serial port of the connected device.

    Returns:
        str: Serial port of the device if found, None otherwise.
    """
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if os.name == 'nt':  # Windows
            if "COM" in p.device:
                return p.device
        else:  # macOS/Linux
            if p.device == "/dev/cu.usbmodem01":
                return p.device
    return None


def flash_device(port, firmware_path):
    """
    Flash the device by erasing the flash memory and writing the firmware.

    Args:
        port (str): Serial port of the device.
        firmware_path (str): Path to the firmware binary.

    Returns:
        None
    """
    try:
        erase_args = ["--chip", "esp32s2", "--port", port, "--after", "no_reset", "erase_flash"]
        print(f"Erasing flash on port {port}...")
        esptool.main(erase_args)
        time.sleep(1)

        write_args = ["--chip", "esp32s2", "--port", port, "--after", "no_reset", "write_flash", "0x0", firmware_path]
        print(f"Writing firmware to {port} from {firmware_path}...")
        esptool.main(write_args)
    except Exception as e:
        print(f"An error occurred during flashing: {e}")


def play_sound(sound_name):
    """
    Play a system sound based on the specified name.

    Args:
        sound_name (str): Name of the sound to play (e.g., "Funk", "Glass").

    Returns:
        None
    """
    if os.name == 'nt':  # Windows
        import winsound
        if sound_name == "Funk":
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        elif sound_name == "Glass":
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
    else:  # macOS/Linux
        sound_file = f"/System/Library/Sounds/{sound_name}.aiff"
        os.system(f'afplay {sound_file}')


def is_volume_mounted(volume_name):
    """
    Check if a volume with the specified name is mounted.

    Args:
        volume_name (str): Name of the volume to check.

    Returns:
        bool: True if the volume is mounted, False otherwise.
    """
    if os.name == 'nt':  # Windows
        drive_letters = [f"{chr(letter)}:\\" for letter in range(65, 91)]
        for drive in drive_letters:
            if os.path.exists(drive) and volume_name in drive:
                return True
        return False
    else:  # macOS/Linux
        return os.path.ismount(f"/Volumes/{volume_name}")


def copy_files_to_volume(source_path, volume_name):
    """
    Copy files from the source path to the mounted volume.

    Args:
        source_path (str): Path to the source files.
        volume_name (str): Name of the mounted volume.

    Returns:
        None
    """
    if os.name == 'nt':  # Windows
        destination_path = f"{volume_name}:\\"
    else:  # macOS/Linux
        destination_path = f"/Volumes/{volume_name}/"

    code_py_path = os.path.join(destination_path, "code.py")
    os.remove(code_py_path)
    shutil.rmtree(os.path.join(destination_path, "sd"), ignore_errors=True)
    shutil.copytree(source_path, destination_path, dirs_exist_ok=True)


# Main function
if __name__ == "__main__":
    """
    Main function to flash the device and manage library updates.

    If the `--repeat` flag is used, the process will run in a loop.
    If the `--nopull` flag is used, library updates are skipped.
    """
    if not args.nopull:
        update_library_repo('code/lib', 'https://github.com/Eliobot/Eliobot-Python-Library.git')

    while True:
        print("\nWaiting for Serial")
        port = None

        while not port:
            port = find_serial_device()
            print(".", end='', flush=True)
            time.sleep(1)

        print(f"\nFound serial device at {port}")

        flash_device(port, os.path.join(pathname, "firmware-mass-storage.bin"))
        play_sound("Funk")

        print("\nWaiting for reset")
        while not is_volume_mounted("ELIOBOT"):
            print(".", end='', flush=True)
            time.sleep(1)

        print("\nCopying files, please wait")
        copy_files_to_volume(os.path.join(pathname, "code"), "ELIOBOT")

        print("Unmounting volume...")
        if os.name == 'nt':  # Windows
            os.system(f"powershell -Command \"Remove-PartitionAccessPath -DiskNumber 0 -AccessPath ELIOBOT:\\\"")
        else:  # macOS/Linux
            os.system('diskutil unmount "ELIOBOT"')

        play_sound("Glass")
        print("\nJob done!")

        if not args.repeat:
            break
