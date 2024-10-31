import board
import neopixel
from elio import Motors, Buzzer, ObstacleSensor, LineSensor, WiFiConnectivity, IRRemote
import time
import analogio
import digitalio
import pwmio
import ir_signals
import pulseio

# Flag for IR/obstacle pin initialization
obstacle_pin_initialized = False
ir_pin_initialized = False

isObstacleInitialized = False
isIRInitialized = False

prog = None

# IR Receiver and decoder
ir_receiver = None
decoder = None

# Built in Neopixel declaration
pixels = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2, auto_write=False, pixel_order=neopixel.GRB)

obstacleInput = None
obstacleSensor = None

# Button declaration
buttonPin = digitalio.DigitalInOut(board.IO0)
buttonPin.direction = digitalio.Direction.INPUT

vBatt_pin = analogio.AnalogIn(board.BATTERY)

AIN1 = pwmio.PWMOut(board.IO36)
AIN2 = pwmio.PWMOut(board.IO38)
BIN1 = pwmio.PWMOut(board.IO35)
BIN2 = pwmio.PWMOut(board.IO37)

motors = Motors(AIN1, AIN2, BIN1, BIN2, vBatt_pin)

lineCmd = digitalio.DigitalInOut(board.IO33)
lineCmd.direction = digitalio.Direction.OUTPUT

lineInput = [analogio.AnalogIn(pin) for pin in
             (board.IO10, board.IO11, board.IO12, board.IO13, board.IO14)]

lineSensor = LineSensor(lineInput, lineCmd, motors)

speed = 100
distance = 20
prog = 1


# Function to initialize the IR/obstacle pin
def init_ir_pin():
    global ir_pin_initialized, obstacle_pin_initialized, ir_receiver, decoder, obstacleInput, obstacleSensor
    if not obstacle_pin_initialized:
        ir_receiver = pulseio.PulseIn(board.IO4, maxlen=200, idle_state=True)
        decoder = IRRemote(ir_receiver)
        ir_pin_initialized = True
    else:
        for pin in obstacleInput:
            pin.deinit()
        ir_receiver = pulseio.PulseIn(board.IO4, maxlen=200, idle_state=True)
        decoder = IRRemote(ir_receiver)
        ir_pin_initialized = True


def init_obstacle_pin():
    global ir_pin_initialized, obstacle_pin_initialized, ir_receiver, decoder, obstacleInput, obstacleSensor
    if not ir_pin_initialized:
        obstacleInput = [analogio.AnalogIn(pin) for pin in
                         (board.IO4, board.IO5, board.IO6, board.IO7)]

        obstacleSensor = ObstacleSensor(obstacleInput)
        obstacle_pin_initialized = True
    else:
        ir_receiver.deinit()
        obstacleInput = [analogio.AnalogIn(pin) for pin in
                         (board.IO4, board.IO5, board.IO6, board.IO7)]

        obstacleSensor = ObstacleSensor(obstacleInput)
        obstacle_pin_initialized = True


def obstacle():
    global prog, isObstacleInitialized, isIRInitialized
    if not isObstacleInitialized:
        init_obstacle_pin()
        isObstacleInitialized = True
        isIRInitialized = False
    pixels.fill((255, 0, 0))
    pixels.show()
    if obstacleSensor.get_obstacle(1) and not buttonPin.value == False:
        motors.turn_one_step("left", 180)

    elif obstacleSensor.get_obstacle(2) and not buttonPin.value == False:
        motors.turn_one_step("left", 90)

    elif obstacleSensor.get_obstacle(0) and not buttonPin.value == False:
        motors.turn_one_step("right", 90)

    else:
        motors.move_forward(speed)


def followHand():
    global prog, isObstacleInitialized, isIRInitialized
    if not isObstacleInitialized:
        init_obstacle_pin()
        isObstacleInitialized = True
        isIRInitialized = False
    pixels.fill((0, 0, 255))
    pixels.show()
    if obstacleSensor.get_obstacle(1):
        motors.move_forward(speed)

    elif obstacleSensor.get_obstacle(3):
        motors.move_backward(speed)

    elif obstacleSensor.get_obstacle(2):
        motors.turn_right(speed)

    elif obstacleSensor.get_obstacle(0):
        motors.turn_left(speed)

    else:
        motors.motor_stop()


def doNotFall():
    global prog
    pixels.fill((128, 0, 128))
    pixels.show()
    if (lineSensor.get_line(2) < 10000 or lineSensor.get_line(0) < 10000 or lineSensor.get_line(
            4) < 10000) and not buttonPin.value == False:
        motors.move_backward(speed)

        time.sleep(0.5)
        motors.motor_stop()

        motors.turn_one_step("right", 180)

    else:
        motors.move_forward(speed)


def irRemote():
    global prog, isIRInitialized, isObstacleInitialized
    if not isIRInitialized:
        init_ir_pin()
        isIRInitialized = True
        isObstacleInitialized = False
    code = decoder.decode_signal()

    pixels.fill((255, 255, 0))
    pixels.show()

    if code == ir_signals.signal_up:
        for i in range(1):
            motors.move_one_step("forward", distance)

    elif code == ir_signals.signal_left:
        motors.turn_one_step("left", 90)

    elif code == ir_signals.signal_right:
        motors.turn_one_step("right", 90)

    elif code == ir_signals.signal_down:
        for i in range(1):
            motors.move_one_step("backward", distance)

    elif code == ir_signals.signal_ok:
        motors.turn_one_step("right", 180)

    else:
        motors.motor_stop()


try:
    with open("config.json", "r") as f:
        calibration = json.load(f)
    seuil = calibration["line_threshold"]
except:
    seuil = 15000

while True:
    if buttonPin.value == False:
        if prog == 5:
            prog = 1
        else:
            prog = prog + 1
        time.sleep(0.5)

    else:
        if prog == 1:
            pixels.fill((0, 255, 0))
            pixels.show()
            if lineSensor.get_line(2) < seuil:
                pixels.fill((51, 255, 51))
                pixels.show()
                motors.move_forward(speed)

            elif lineSensor.get_line(0) < seuil:
                motors.motor_stop()

                pixels.fill((255, 255, 0))
                pixels.show()
                motors.spin_right_wheel_forward(speed)

                time.sleep(0.1)

            elif lineSensor.get_line(4) < seuil:
                motors.motor_stop()

                pixels.fill((204, 51, 204))
                pixels.show()
                motors.spin_left_wheel_forward(speed)

            elif lineSensor.get_line(1) < seuil:
                motors.motor_stop()

                pixels.fill((255, 255, 0))
                pixels.show()
                motors.spin_right_wheel_forward(speed)

            elif lineSensor.get_line(3) < seuil:
                motors.motor_stop()

                pixels.fill((204, 51, 204))
                pixels.show()
                motors.spin_left_wheel_forward(speed)

                time.sleep(0.1)

            else:
                motors.motor_stop()

                pixels.fill((255, 0, 0))
                pixels.show()
        elif prog == 2:
            obstacle()
        elif prog == 3:
            followHand()
        elif prog == 4:
            doNotFall()
        elif prog == 5:
            irRemote()
