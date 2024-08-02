from elio import Eliobot
import board
import time
import digitalio
import analogio
import pwmio
import neopixel

vBatt_pin = analogio.AnalogIn(board.BATTERY)

obstacleInput = [analogio.AnalogIn(pin) for pin in
                 (board.IO4, board.IO5, board.IO6, board.IO7)]

lineCmd = digitalio.DigitalInOut(board.IO33)
lineCmd.direction = digitalio.Direction.OUTPUT

lineInput = [analogio.AnalogIn(pin) for pin in
             (board.IO10, board.IO11, board.IO12, board.IO13, board.IO14)]

AIN1 = pwmio.PWMOut(board.IO36)
AIN2 = pwmio.PWMOut(board.IO38)
BIN1 = pwmio.PWMOut(board.IO35)
BIN2 = pwmio.PWMOut(board.IO37)

buzzer = pwmio.PWMOut(board.IO17, variable_frequency=True)

elio = Eliobot(AIN1, AIN2, BIN1, BIN2, vBatt_pin, obstacleInput, buzzer, lineInput, lineCmd)

# Built in Neopixel declaration
pixels = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2, auto_write=False, pixel_order=neopixel.GRB)

speed = 100


while True:
    if elio.get_obstacle(1):
        pixels.fill((255, 0, 0))
        pixels.show()
        for i in range(1):
            elio.move_one_step("backward",4)

        elio.turn_one_step("left", 30)

        elio.turn_one_step("right", 30)

        elio.turn_one_step("left", 30)

        elio.turn_one_step("right", 30)

        elio.turn_one_step("left", 30)

        elio.turn_one_step("right", 120)

    else:
        pixels.fill((51, 204, 0))
        pixels.show()
        elio.move_forward(speed)
