import RPi.GPIO as GPIO
import time


def rc_time(pin_to_circuit):
    count = 0

    # Output on the pin for
    GPIO.setup(pin_to_circuit, GPIO.OUT)
    GPIO.output(pin_to_circuit, GPIO.LOW)
    time.sleep(0.1)

    # Change the pin back to input
    GPIO.setup(pin_to_circuit, GPIO.IN)

    # Count until the pin goes high
    while GPIO.input(pin_to_circuit) == GPIO.LOW:
        count += 1

    return count


def ldr_sensor(pin):
    total = 0

    for x in range(0, 9):
        total += rc_time(int(pin))

    average = total / 10

    try:
        light = (1 / float(average)) * 10000
    except ZeroDivisionError:
        light = 10000

    if light > 10000:
        light = 10000

    return light

