import platform
import os
import shutil
import time
import serial.tools.list_ports
import argparse
import subprocess
import sys

pathname = os.path.dirname(os.path.realpath(__file__))

# Create the parser
parser = argparse.ArgumentParser(description='Flash robot with latest firmware and optional library update.')

# Add arguments
parser.add_argument('--repeat', action='store_true', required=False)
parser.add_argument('--nopull', action='store_true',
                    help='Skip pulling the latest library updates from git repository before flashing.')
parser.add_argument(
    '--chip',
    choices=['s2', 's3'],
    default=None,
    help='Forcer le chip: s2 ou s3 (détection automatique par défaut).'
)

# Parse the arguments
args = parser.parse_args()


def update_library_repo(lib_path, git_url, branch='dev'):
    # Clone into a temp dir first — if clone fails, existing lib is preserved
    tmp_path = lib_path + '_tmp'
    shutil.rmtree(tmp_path, ignore_errors=True)

    try:
        subprocess.run(
            ['git', 'clone', '--branch', branch, git_url, tmp_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        shutil.rmtree(tmp_path, ignore_errors=True)
        raise RuntimeError(f"Git clone failed: {e}") from e

    # Remove unnecessary files from the clone
    for filename in ['README.md', '.gitignore', '.git']:
        target = os.path.join(tmp_path, filename)
        try:
            if os.path.isdir(target):
                shutil.rmtree(target)
                print(f"{filename} directory deleted.")
            else:
                os.remove(target)
                print(f"{filename} file deleted.")
        except FileNotFoundError:
            print(f"{filename} not found")
        except PermissionError:
            print(f"Permission denied while trying to delete {filename}")

    # Replace old directory with new one only after successful clone
    shutil.rmtree(lib_path, ignore_errors=True)
    shutil.move(tmp_path, lib_path)


def detect_chip(serial_port):
    """Detect the ESP32 chip type from a serial port using esptool chip_id.
    Returns 's2' or 's3', or raises RuntimeError if detection fails.
    """
    result = subprocess.run(
        ['esptool', '-p', serial_port, 'chip_id'],
        capture_output=True,
        text=True,
        check=False
    )
    output = result.stdout + result.stderr
    if 'ESP32-S3' in output:
        return 's3'
    elif 'ESP32-S2' in output:
        return 's2'
    else:
        raise RuntimeError(
            f"Chip non reconnu. Sortie esptool:\n{output}\n"
            "Utilise --chip s2 ou --chip s3 pour forcer."
        )


def find_serial_port(vid, pid=None):
    """Scan for a serial port by USB VID (and optionally PID)."""
    for p in serial.tools.list_ports.comports():
        if p.vid == vid and (pid is None or p.pid == pid):
            return p.device
    return None


def get_volume_path(volume_name):
    """Return the mount path for a named volume."""
    system = platform.system()
    if system == 'Darwin':
        return f'/Volumes/{volume_name}'
    elif system == 'Linux':
        user = os.getenv('USER', '')
        candidates = [
            f'/media/{user}/{volume_name}',
            f'/media/{volume_name}',
            f'/mnt/{volume_name}',
        ]
        for path in candidates:
            if os.path.ismount(path):
                return path
        # Return the most likely path even if not yet mounted
        return candidates[0]
    else:
        raise RuntimeError(f"OS non supporté: {system}")


def play_sound(sound):
    """Play a system sound (macOS only, silent on Linux)."""
    if platform.system() == 'Darwin':
        sounds = {
            'flash': '/System/Library/Sounds/Funk.aiff',
            'success': '/System/Library/Sounds/Glass.aiff',
        }
        path = sounds.get(sound)
        if path:
            subprocess.run(['afplay', path], check=False)


def eject_volume(volume_name):
    """Unmount a volume by name."""
    system = platform.system()
    if system == 'Darwin':
        subprocess.run(['diskutil', 'unmount', volume_name], check=True)
    elif system == 'Linux':
        vol_path = get_volume_path(volume_name)
        subprocess.run(['umount', vol_path], check=True)
    else:
        raise RuntimeError(f"OS non supporté: {system}")


if not args.nopull:
    lib_directory = os.path.join(pathname, 'code', 'lib')
    repository_url = 'https://github.com/Eliobot/Eliobot-Python-Library.git'
    update_library_repo(lib_directory, repository_url)

print(f"OS: {os.name} / {platform.platform()}")

chip_cfg = {
    's2': {
        # Espressif VID — set pid to the specific S2 PID if multiple chips are connected
        'vid': 0x303A,
        'pid': None,
        'firmware': os.path.join(pathname, 'Eliobot_S2', 'fw_eliobot_s2_noREPL.bin'),
        'code_dir': os.path.join(pathname, 'code'),
        'volume': 'ELIOBOT',
    },
    's3': {
        # Espressif VID — set pid to the specific S3 PID if multiple chips are connected
        'vid': 0x303A,
        'pid': None,
        'firmware': os.path.join(pathname, 'Eliobot_S3', 'fw_eliobot_s3_noREPL.bin'),
        'code_dir': os.path.join(pathname, 'code'),
        'volume': 'ELIOBOT',
    }
}

while True:
    print()
    print("Waiting for Serial...")

    # Scan for any Espressif chip (VID=0x303A), both S2 and S3 share the same VID
    serial_port = None
    while serial_port is None:
        serial_port = find_serial_port(vid=0x303A)
        if serial_port is None:
            print(".", end='', flush=True)
            time.sleep(1)
    print()
    print(f"Found on {serial_port}!")

    # Determine chip type: use --chip override, or auto-detect
    if args.chip:
        chip = args.chip
        print(f"Chip forcé: {chip.upper()}")
    else:
        try:
            chip = detect_chip(serial_port)
            print(f"Chip détecté: ESP32-{chip.upper()}")
        except RuntimeError as e:
            print(e)
            if not args.repeat:
                sys.exit(1)
            continue

    cfg = chip_cfg[chip]

    # Check firmware exists
    if not os.path.isfile(cfg['firmware']):
        print(f"ERROR: Firmware introuvable: {cfg['firmware']}")
        if not args.repeat:
            sys.exit(1)
        continue

    # Erase flash
    result = subprocess.run(
        ['esptool', '-p', serial_port, 'erase-flash'],
        check=False
    )
    if result.returncode != 0:
        print("ERROR: Échec de l'effacement du flash.")
        play_sound('flash')
        if not args.repeat:
            sys.exit(1)
        continue

    # Write firmware
    result = subprocess.run(
        ['esptool', '-p', serial_port, '--after', 'hard-reset',
         'write-flash', '0x0', cfg['firmware']],
        check=False
    )
    if result.returncode != 0:
        print("ERROR: Échec du flash du firmware.")
        play_sound('flash')
        if not args.repeat:
            sys.exit(1)
        continue

    play_sound('flash')
    print()
    print("Waiting for reset...")

    volume_name = cfg['volume']
    volume_path = get_volume_path(volume_name)
    while not os.path.ismount(volume_path):
        print(".", end='', flush=True)
        time.sleep(1)
        volume_path = get_volume_path(volume_name)
    print()

    print("Copying files, please wait...")

    # Copy code directory contents onto the volume
    for item in os.listdir(cfg['code_dir']):
        src = os.path.join(cfg['code_dir'], item)
        dst = os.path.join(volume_path, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    eject_volume(volume_name)

    play_sound('success')
    print()
    print("Job done!")
    print()

    if not args.repeat:
        break
