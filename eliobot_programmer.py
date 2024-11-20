import os
import platform
import time
import serial.tools.list_ports
import argparse
import shutil
import subprocess


# Détection du répertoire courant
pathname = os.path.dirname(os.path.realpath(__file__))

# Parser les arguments
parser = argparse.ArgumentParser(description='Flash robot with latest firmware and optional library update.')
parser.add_argument('--repeat', action='store_true', required=False, help='Repeat the process after finishing.')
parser.add_argument('--nopull', action='store_true', required=False, help='Skip pulling the library updates.')
args = parser.parse_args()


# Mettre à jour la bibliothèque via Git
def update_library_repo(lib_path, git_url, branch='dev'):
    # Supprimer le dossier existant
    shutil.rmtree(lib_path, ignore_errors=True)

    # Cloner le dépôt
    subprocess.run(['git', 'clone', '--branch', branch, git_url, lib_path], check=True)

    # Nettoyer les fichiers inutiles
    clean_repo(lib_path, ['README.md', '.gitignore', '.git'])


# Nettoyer les fichiers inutiles
def clean_repo(lib_path, files_to_remove):
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


# Détection du port série
def find_serial_device():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if os.name == 'nt':  # Windows
            if "COM" in p.device:
                return p.device
        else:  # macOS/Linux
            if p.device == "/dev/cu.usbmodem01":
                return p.device
    return None


# Flashage du microcontrôleur
def flash_device(port, firmware_path):
    erase_command = f"esptool.py -p {port} erase_flash"
    write_command = f"esptool.py -p {port} --after hard_reset write_flash 0x0 {firmware_path}"
    os.system(erase_command)
    os.system(write_command)


# Lecture de sons
def play_sound(sound_name):
    if os.name == 'nt':  # Windows
        import winsound
        if sound_name == "Funk":
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        elif sound_name == "Glass":
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
    else:  # macOS/Linux
        sound_file = f"/System/Library/Sounds/{sound_name}.aiff"
        os.system(f'afplay {sound_file}')


# Vérification si le volume est monté
def is_volume_mounted(volume_name):
    if os.name == 'nt':  # Windows
        drive_letters = [f"{chr(letter)}:\\" for letter in range(65, 91)]
        for drive in drive_letters:
            if os.path.exists(drive) and volume_name in drive:
                return True
        return False
    else:  # macOS/Linux
        return os.path.ismount(f"/Volumes/{volume_name}")


# Copie des fichiers sur le volume
def copy_files_to_volume(source_path, volume_name):
    if os.name == 'nt':  # Windows
        destination_path = f"{volume_name}:\\"
    else:  # macOS/Linux
        destination_path = f"/Volumes/{volume_name}/"

    # Supprimer l'ancien code et copier les nouveaux fichiers
    code_py_path = os.path.join(destination_path, "code.py")
    os.remove(code_py_path)
    shutil.rmtree(os.path.join(destination_path, "sd"), ignore_errors=True)
    shutil.copytree(source_path, destination_path, dirs_exist_ok=True)


# Fonction principale
if __name__ == "__main__":
    # Mise à jour des bibliothèques si l'option `--nopull` n'est pas utilisée
    if not args.nopull:
        update_library_repo('code/lib', 'https://github.com/Eliobot/Eliobot-Python-Library.git')

    # Boucle principale (si `--repeat` est utilisé)
    while True:
        print("\nWaiting for Serial")
        port = None

        # Attendre que le périphérique série soit détecté
        while not port:
            port = find_serial_device()
            print(".", end='', flush=True)
            time.sleep(1)

        print(f"\nFound serial device at {port}")

        # Flashage du firmware
        flash_device(port, os.path.join(pathname, "firmware-mass-storage.bin"))
        play_sound("Funk")

        # Attente du montage du volume
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

        # Quitter la boucle si `--repeat` n'est pas utilisé
        if not args.repeat:
            break
