import board
from digitalio import DigitalInOut, Direction, Pull
import elio
import time
from analogio import AnalogIn
import neopixel

# Button declaration
buttonPin = DigitalInOut(board.IO39)
buttonPin.direction = Direction.INPUT

# Built in Neopixel declaration
pixels = neopixel.NeoPixel(
    board.NEOPIXEL, 1, brightness=0.2, auto_write=False, pixel_order=neopixel.GRB)

# Create a colour wheel index int
color_index = 0


motorAIN1 = DigitalInOut(board.IO36)
motorAIN2 = DigitalInOut(board.IO38)
motorBIN1 = DigitalInOut(board.IO35)
motorBIN2 = DigitalInOut(board.IO37)
motorAIN1.direction = Direction.OUTPUT
motorAIN2.direction = Direction.OUTPUT
motorBIN1.direction = Direction.OUTPUT
motorBIN2.direction = Direction.OUTPUT


while buttonPin.value == True:
    # Get the R,G,B values of the next colour
    r, g, b = elio.rgb_color_wheel(color_index)
    # Set the colour on the NeoPixel
    pixels[0] = (r, g, b, 0.5)
    pixels.show()
    # Increase the wheel index
    color_index += 1

    # Sleep for 15ms so the colour cycle isn't too fast
    time.sleep(0.015)



while True:
    if elio.get_obstacle(1):
        pixels.fill((255, 0, 0))
        pixels.show()
        motorAIN1.value = True
        motorAIN2.value = False
        motorBIN1.value = True
        motorBIN2.value = False

        time.sleep(0.2)

        motorAIN1.value = True
        motorAIN2.value = False
        motorBIN1.value = False
        motorBIN2.value = True

        time.sleep(0.45)

        motorAIN1.value = True
        motorAIN2.value = True
        motorBIN1.value = True
        motorBIN2.value = True

        time.sleep(0.2)

    else:
        pixels.fill((0, 255, 0))
        pixels.show()
        motorAIN1.value = False
        motorAIN2.value = True
        motorBIN1.value = False
        motorBIN2.value = True
