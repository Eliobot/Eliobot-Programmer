Python script to flash the entire CircuitPython 9.1.2 factory setup on Eliobot robots

## First setup

If not already installed, you will need [esptool](https://docs.espressif.com/projects/esptool/) to run the script

Install with pip :

```pip install esptool```

Install with brew :

``` brew install esptool ```

## Run the script 

Run once :

``` python3 eliobot_programmer.py ```

Run forever :

``` python3 eliobot_programmer.py --repeat```

## Options

- `--nopull` : Do not pull ElioBot library automatically

if you have problems pulling the library, you can delete the `lib` folder and run the script again


## Raspberry Pi setup

### First install

Create Python Environment :

``` python -m venv esptoolenv ```

Activate the environment :

``` source esptoolenv/bin/activate ```

Install esptool :

``` pip install esptool ```


### Running the script

Don't forget to reactivate the environment at each new session : 

``` source esptoolenv/bin/activate ```

Then you can erase the flash :

``` esptool.py erase_flash ```

Or write a binary :

``` esptool.py write_flash 0x0 firmware-mass-storage.bin ```


