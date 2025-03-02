from machine import Pin, reset
from time import sleep, time, localtime
from collections import deque
import uasyncio as asyncio
import ntptime

from relayManager import RelayManager
from sensorManager import Data, SensorManager
from webServer import WebServer
from displayManager import DisplayManager
from constant import *


class Main:
    def __init__(self):
        self.display_manager = DisplayManager()
        self.display_manager.show_message("Creating objet")
        self.sensor_manager = SensorManager()
        self.relay_manager = RelayManager()
        self.display_manager.show_message("Generaring webServer")
        self.web_server = WebServer()
        ntptime.settime()
        self.display_manager.show_message(f"Web in ip:       {self.web_server.get_IP()}")
        self.last_reading_time = time()


    async def sensors(self):
        while True:
            try:
                current_time = time()
                if current_time - self.last_reading_time >= self.web_server.reading_interval:
                    data = self.sensor_manager.read_sensors()
                    
                    if data.soil_moisture < self.web_server.needed_soil_moisture:  
                        finish_ban_seconds = self.web_server.time_to_seconds(self.web_server.finish_ban_time)
                        start_ban_seconds = self.web_server.time_to_seconds(self.web_server.start_ban_time)
                        if finish_ban_seconds <  current_time % 86400 < start_ban_seconds:
                            self.relay_manager.on()
                            await asyncio.sleep(self.web_server.time_water)
                            self.relay_manager.off()
                            self.web_server.last_water = f"{DAY[localtime()[6]]}/{localtime()[3]:02d}:{localtime()[4]:02d}:{localtime()[5]:02d}"
                            data.water = True
                        
                    self.web_server.add_reading(data)
                    self.display_manager.show_data(data, self.web_server.last_water, self.web_server.get_water_week())
                    
                    self.last_reading_time = current_time
                await asyncio.sleep(4)
            except Exception as e:
                self.display_manager.show_message(str(e))
                sleep(5)
                reset()

    async def handle_web_server(self):
        while True:
            try:
                client, addr = self.web_server.server.accept()
                print(f"Client connected from: {addr}")
                self.web_server.handle_request(client)
            except OSError:
                await asyncio.sleep(0.1)
            except Exception as e:
                self.display_manager.show_message(str(e))
                sleep(5)
                reset()
        
    async def run(self):
        await asyncio.gather(
            self.handle_web_server(),
            self.sensors()
        )

# Ejecutar el programa
if __name__ == "__main__":
    main = Main()
    asyncio.run(main.run())
    
    

