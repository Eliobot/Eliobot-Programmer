Python script to flash the entire CircuitPython factory setup on Eliobot robots

## First setup

Install the required libraries :

``` pip3 install -r requirements.txt ```

## Run the script 

Run once :

``` python3 eliobot_programmer.py ```

Run forever :

``` python3 eliobot_programmer.py --repeat```

## Options

- `--nopull` : Do not pull ElioBot library automatically

if you have problems pulling the library, you can delete the `lib` folder and run the script again
