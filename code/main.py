import board
import elio
import time
import neopixel

# Built in Neopixel declaration
pixels = neopixel.NeoPixel(
    board.NEOPIXEL, 1, brightness=0.2, auto_write=False, pixel_order=neopixel.GRB)

# Create a colour wheel index int
color_index = 0

speed = 100


while True:
    if elio.getObstacle(1):
        pixels.fill((255, 0, 0))
        pixels.show()
        elio.moveBackward(speed)

        time.sleep(0.2)

        elio.turnRight(speed)

        time.sleep(0.45)

        elio.motorStop()

        time.sleep(0.2)

    else:
        pixels.fill((0, 255, 0))
        pixels.show()
        
        elio.moveForward(speed)
