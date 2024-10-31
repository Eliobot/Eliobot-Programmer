Python script to flash the entire CircuitPython factory setup on Eliobot robots

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
