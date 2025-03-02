from machine import Pin, ADC
import dht
from constant import *
from time import  sleep, localtime

# Data storage structure
class Data:
    def __init__(self,  soil_moisture=0, air_humidity=0, air_temperature=0, water=False):
        self.timestamp = f"{DAY[localtime()[6]]}/{localtime()[3]:02d}:{localtime()[4]:02d}:{localtime()[5]:02d}"
        self.soil_moisture = soil_moisture
        self.air_humidity = air_humidity
        self.air_temperature = air_temperature
        self.water = water
    def __repr__(self):
        return str(self)
    def __str__(self):
        return f"timestamp: {self.timestamp}, soil_moisture: {self.soil_moisture}, air_humidity: {self.air_humidity}, air_temperature: {self.air_temperature}"

# Class to manage sensors
class SensorManager:
    def __init__(self, dht_pin=DHT_PIN, soil_pin=SOIL_SENSOR_PIN):
        self.dht_sensor = dht.DHT11(Pin(dht_pin))
        self.soil_sensor = ADC(Pin(soil_pin))

    def read_sensors(self):
        self.dht_sensor.measure()
        return Data(self._map(self.soil_sensor.read_u16(), SOIL_SENSOR_DRY, SOIL_SENSOR_WET, 0, 100),
                    self.dht_sensor.humidity(), self.dht_sensor.temperature())

    def _map(self, value, in_min, in_max, out_min, out_max):
        return (value - in_min) * (out_max - out_min) // (in_max - in_min) + out_min
    
    
if __name__ == "__main__":
    print("Test SensorManager")
    sensor = SensorManager()
    relay = machine.Pin("GP22")
    
    while True:
        air_humidity, air_temperature, soil_humidity = sensor.read_sensors()
        print(air_humidity, air_temperature, soil_humidity)
        sleep(1)
        if soil_humidity<50:
            relay.value(1)
        else:
            relay.value(0)
            