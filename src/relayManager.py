from machine import Pin
from time import sleep
from constant import *

# Class to manage the irrigation relay
class RelayManager:
    def __init__(self, gpio=RELAY_PIN):
        self.relay = Pin(gpio,Pin.OUT)
        self.off()
    
    
    def on(self):
        self.relay.off()

    def off(self):
        self.relay.on()

if __name__ == "__main__":
    relay = RelayManager()
    led = machine.Pin("LED", Pin.OUT)
    
    while True:
        sleep(1)
        if led.value():
            relay.off()
            led.off()
        else:
            relay.on()
            led.on()