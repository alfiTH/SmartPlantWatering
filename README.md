# SmartPlantWatering
SmartPlantWatering is an automated plant care system using a Raspberry Pi Pico. It monitors soil moisture and waters plants as needed. The web interface allows users to view historical data and adjust settings like humidity, watering time, and more, ensuring efficient plant care with minimal effort.

## Features
This system has three main features:

- **Automated watering** – Set the desired humidity level and watering duration for automatic irrigation.
- **Data display** – The SSD1306 screen shows the latest measurements, last watering timestamp, and weekly statistics.
- **Web interface** – A built-in web server provides historical data, weekly statistics, and configurable settings.

## Hardware Requirements
List of hardware
- Raspberry Pi Pico 2W
- DHT11 sensor
- Soil moisture sensor
- Relay module
- SDD1306 display
- 5V 2.5A power supply
- Peristaltic pump

## Software Requirements
You need to install MicroPython on the Raspberry Pi Pico. Follow the official [MicroPython tutorial](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html#what-is-micropython) for setup instructions.

## Installation
### Pin Connections:
![pico2w-pinout](https://www.raspberrypi.com/documentation/microcontrollers/images/pico2w-pinout.svg)

The following GPIO pins are used:
- **DHT11** -> `GP21`
- **Soil moisture sensor** -> `GP28`
- **Relay module** -> `GP20`
- **SCL (SSD1306)** -> `GP17`
- **SDA (SSD1306)** -> `GP16`

These configurations can be found in the [constants file](src/constant.py).
The **DHT11**, **SSD1306**, and **soil moisture sensor** are powered by 3V3(OUT), while the relay module is connected to VBUS.
The DHT11, SDD1306 and Dirt humidity sensor positive are connected to `3V3(OUT)`, menwile de module relay is conected to `VBUS`