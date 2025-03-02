from machine import Pin, I2C
import ssd1306
from sensorManager import Data
from time import sleep, localtime
from constant import *

# Class for managing the SSD1306 screen
class DisplayManager:
    def __init__(self, scl=I2C_SCL_PIN, sda=I2C_SDA_PIN):
        i2c = I2C(0, scl=Pin(scl), sda=Pin(sda))
        self.display = ssd1306.SSD1306_I2C(128, 64, i2c)
        
    def show_message(self, message:str):
        self.display.fill(0)
        lines = [message[i:i+16] for i in range(0, len(message), 16)]
        for i, line in enumerate(lines):
            self.display.text(line, 0, i*10)
        self.display.show()
            
    def show_data(self, data:Data, last_water:str="", water_week=[0]*7):
        self.display.fill(0)
        self.display.text(f"Dirt:{data.dirt_humidity:.2f}%", 0, 0)
        self.display.text(f"Air :{data.air_humidity:.2f}%", 0, 10)
        self.display.text(f"Temp:{data.air_temperature:.2f}C", 0, 20)
        self.display.text(f"DT:{data.timestamp}", 0, 30)
        self.display.text(f"LT:{last_water}", 0, 40)
        self.display.text(f"{','.join(map(str, water_week))}", 0, 50)
        self.display.show()
        
if __name__ == "__main__":
    print("Test DisplayManager")
    display = DisplayManager()
    for i in range(20):
        display.show_data(Data(i, i*2, i*4)) 
        sleep(2)
        
    display.show_message("This device reads the temperature and humidity, depending on whether it waters or not.")