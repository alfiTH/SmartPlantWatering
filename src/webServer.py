import network
import socket
import json
from constant import *
from wifi import *
from sensorManager import Data
from time import sleep, time, localtime
from machine import reset
from collections import deque
import gc

# Class for managing the web server
class WebServer:
    def __init__(self):
        self.__max_reading = MAX_READINGS
        self.__readings = deque([], self.max_reading)
        self.__needed_soil_moisture = NEEDED_SOIL_MOISTURE
        self.__reading_interval = READING_INTERVAL
        self.__time_water = TIME_WATER
        self.__last_water = ""
        self.__finish_ban_time = FINISH_BAN_TIME
        self.__start_ban_time = START_BAN_TIME

        # Connect to WiFi
        self.__wlan = network.WLAN(network.STA_IF)
        self.__wlan.active(True)
        print("Connect to WiFi...")
        self.__wlan.connect(SSID, PASSWORD)
        
        attempts = 0
        while not self.__wlan.isconnected():
            print("Trying to connect...")
            sleep(1)
            attempts += 1
    
        if attempts >= MAX_ATTEMPTS:
            print("Unable to connect. Rebooting...")
            machine.reset()
            
        print("Connected to WiFi:", self.__wlan.ifconfig())

        # Start server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server.bind(('0.0.0.0', 80))
            self.server.listen(5)
            self.server.settimeout(0.5)
            #self.server.setblocking(False)
            print("Web server started on http://{}".format(self.__wlan.ifconfig()[0]))
        except OSError as e:
            print("Error while starting the server:", e)
            self.server.close()
            reset()

    def __del__(self):
        self.server.close()
        
        
###########################GETTERS/SETTERS###################
    @property
    def readings(self):
        return self.__readings
    
    @property
    def max_reading(self):
        return self.__max_reading
    @max_reading.setter
    def max_reading(self, value):
        if isinstance(value, (int)) and value > 0:
            if  self.max_reading != value and MIN_MAX_READINGS <= value <= MAX_MAX_READINGS:
                self.__max_reading = value
                self.__readings = deque(self.__readings, self.__max_reading)
        
    @property
    def last_water(self):
        return self.__last_water
    @last_water.setter
    def last_water(self, value:str):
        self.__last_water = value
        
    @property
    def needed_soil_moisture(self):
        return self.__needed_soil_moisture
    @needed_soil_moisture.setter
    def needed_soil_moisture(self, value):
        if isinstance(value, (int, float)) and MIN_NEEDED_SOIL_MOISTURE <= value <= MAX_NEEDED_SOIL_MOISTURE:
            self.__needed_soil_moisture = value
        
    @property
    def finish_ban_time(self):
        return self.__finish_ban_time
    @finish_ban_time.setter
    def finish_ban_time(self, value):
         if isinstance(value, str):
            time_parts = value.split(":")
            if len(time_parts) == 2 and 0 <= int(time_parts[0]) <= 23 and 0 <= int(time_parts[1]) <= 59:
                self.__finish_ban_time = value
        
    @property
    def start_ban_time(self):
        return self.__start_ban_time
    @start_ban_time.setter
    def start_ban_time(self, value):
         if isinstance(value, str):
            time_parts = value.split(":")
            if len(time_parts) == 2 and 0 <= int(time_parts[0]) <= 23 and 0 <= int(time_parts[1]) <= 59:
                self.__start_ban_time = value

    @property
    def reading_interval(self):
        return self.__reading_interval
    @reading_interval.setter
    def reading_interval(self, value):
        if isinstance(value, (int, float)) and MIN_READING_INTERVAL <= value <= MAX_READING_INTERVAL:
            self.__reading_interval = value


    @property
    def time_water(self):
        return self.__time_water

    @time_water.setter
    def time_water(self, value):
        if isinstance(value, (int, float)) and MIN_TIME_WATER <= value <= MAX_TIME_WATER:
            self.__time_water = value

########################################################################################
            
    def get_IP(self):
        return self.__wlan.ifconfig()[0]

    def add_reading(self, reading:Data):
        self.__readings.append(reading)
        
    def get_water_week(self):
        water_week = [0]*7
        for read in self.readings:
            if read.water:
                water_week[DAY.index(read.timestamp[0:3])]+=1
        return water_week
        
    def get_query_params(self, request):
        """Extract URL parameters (query string)"""
        params = {}
        if '?' in request:
            # Split the parameters
            query_string = request.split('?')[1].split(' ')[0].split('\r')[0]
            for param in query_string.split('&'):
                # Save into diccionary
                if '=' in param:
                    key, value = param.split('=')
                    params[key] = value
        return params
    
    def convert_seconds_to_time(self, seconds):
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return "{:02d}:{:02d}:{:02d}:{:02d}".format(days, hours, minutes, seconds)
    
    def time_to_seconds(self, time_str):
        hours, minutes = map(int, time_str.split(":"))
        return hours * 3600 + minutes * 60

############################WEB THINGS##############################
    def handle_request(self, client):
        print("Client connected")
        request = client.recv(1024).decode("utf-8")
        print("Request received:", request)

        if "GET /get_data" in request:
            # AJAX handle
            self.handle_ajax_request(client)
        else:
            params = self.get_query_params(request)

            humidity = params.get('humidity')
            if humidity is not None and humidity.isdigit():
                self.needed_soil_moisture = int(humidity)
                
            period = params.get('period')
            if period is not None and period.isdigit():
                self.reading_interval = int(period)

            time_water = params.get('time_water')
            if time_water is not None and time_water.isdigit():
                self.time_water = int(time_water)

            max_reading = params.get('max_reading')
            if max_reading is not None and max_reading.isdigit():
                self.max_reading = int(max_reading)

            finish_ban_time = params.get('finish_ban_time')
            if finish_ban_time is not None:
                self.finish_ban_time = finish_ban_time.replace("%3A",":")

            start_ban_time = params.get('start_ban_time')
            if start_ban_time is not None:
                self.start_ban_time = start_ban_time.replace("%3A",":")
                   
            self.handle_html_response(client)

    def handle_html_response(self, client):
        gc.collect()
        #Data
        if len(self.readings) == 0:
            timestamps, soil_moisture, air_humidity, air_temperature = 0,0,0,0
        else:
            timestamps = f'"{self.readings[0].timestamp}"'
            soil_moisture = str(self.readings[0].soil_moisture) 
            air_humidity = str(self.readings[0].air_humidity) 
            air_temperature = str(self.readings[0].air_temperature)
        water_week = self.get_water_week()
        
        #HTML Response
        response =  f"""
HTTP/1.1 200 OK
Content-Type: text/html\r\n
<html>
    <head>
        <meta charset='utf-8'>
        <script src='https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js'></script>
        <script src='https://code.jquery.com/jquery-3.6.0.min.js'></script>
        <style>
            {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                background-color: #f4f4f9;
                color: #333;
                padding: 20px;
            }}

            h1, h2, h3 {{
                color: #4CAF50;
                text-align: center;
            }}

            h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
            }}

            h2 {{
                font-size: 1.5em;
                margin-bottom: 20px;
            }}

            form {{
                background: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                max-width: 600px;
                margin: 0 auto 20px;
            }}

            form label {{
                display: block;
                font-size: 1em;
                margin-bottom: 8px;
            }}

            form input[type="number"],
            form input[type="time"] {{
                width: calc(100% - 20px);
                padding: 10px;
                margin-bottom: 15px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }}

            form input[type="submit"] {{
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
            }}

            form input[type="submit"]:hover {{
                background-color: #45a049;
            }}


            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 30px 0;
            }}

            th, td {{
                padding: 12px 15px;
                text-align: center;
                border: 1px solid #ddd;
            }}

            th {{
                background-color: #4CAF50;
                color: white;
            }}

            tbody tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}

            tbody tr:hover {{
                background-color: #f1f1f1;
            }}

            @media (max-width: 768px) {{
                h1 {{
                    font-size: 2em;
                }}

                h2 {{
                    font-size: 1.2em;
                }}

                form {{
                    width: 100%;
                    padding: 15px;
                }}

                table {{
                    font-size: 14px;
                }}
            }}
        </style>
    </head>
    <body>
        <h1>SmartPlantWatering</h1>
        <h2>Maximum duration of the history: {self.convert_seconds_to_time(self.reading_interval * self.max_reading)}</h2>
        
         <!------------------------------------ Form ------------------------------>
        <form method='GET' action=''>
            <label for='humidity'>Required soli moisture %:</label>
            <input type='number' id='humidity' name='humidity' min='{MIN_NEEDED_SOIL_MOISTURE}' max='{MAX_NEEDED_SOIL_MOISTURE}' required value='{self.needed_soil_moisture}'>
            
            <label for='period'>Sampling period in seconds:</label>
            <input type='number' id='period' name='period' min='{MIN_READING_INTERVAL}' max='{MAX_READING_INTERVAL}' required value='{self.reading_interval}'>
            
            <label for='time_water'>Watering time seconds:</label>
            <input type='number' id='time_water' name='time_water' min='{MIN_TIME_WATER}' max='{MAX_TIME_WATER}' required value='{self.time_water}'>
            
            <label for='max_reading'>Maximum readings:</label>
            <input type='number' id='max_reading' name='max_reading' min='{MIN_MAX_READINGS}' max='{MAX_MAX_READINGS}' required value='{self.max_reading}'><br>
            
            <label for="start_ban_time">Beginning of restricted time:</label>
            <input type="time" id="start_ban_time" name="start_ban_time" required value='{self.start_ban_time}'>

            <label for="finish_ban_time">End of restricted time:</label>
            <input type="time" id="finish_ban_time" name="finish_ban_time" required value='{self.finish_ban_time}'>
            
            <input type='submit' value='Actualizar'>
        </form>
        
        <!------------------------------------ Weekly watering data table ------------------------------>
        <h3>Watering by Day of the Week</h3>
        <table id='waterTable' border='1'>
            <thead>
                <tr>
                    <th>Monday</th>
                    <th>Tuesday</th>
                    <th>Wednesday</th>
                    <th>Thursday</th>
                    <th>Friday</th>
                    <th>Saturday</th>
                    <th>Sunday</th>
                    <th>Last Watering</th> 
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{water_week[0]}</td>
                    <td>{water_week[1]}</td>
                    <td>{water_week[2]}</td>
                    <td>{water_week[3]}</td>
                    <td>{water_week[4]}</td>
                    <td>{water_week[5]}</td>
                    <td>{water_week[6]}</td>
                    <td>{self.last_water}</td>
                </tr>
            </tbody>
        </table>
        
        <!------------------------------------------- Graphic -------------------------->
        <canvas id='myChart' style='width:100%; height:500px;'></canvas>
        <script>
            var ctx = document.getElementById('myChart').getContext('2d');
            var myChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: ['{timestamps}'],
                    datasets: [
                        {{
                            label: 'Dirt Humidity (%)',
                            data: [{soil_moisture}],
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'Air Humidity (%)',
                            data: [{air_humidity}],
                            borderColor: 'rgba(153, 102, 255, 1)',
                            borderWidth: 1
                        }},
                        {{
                            label: 'Air Temperature (°C)',
                            data: [{air_temperature}],
                            borderColor: 'rgba(255, 159, 64, 1)',
                            borderWidth: 1
                        }}
                    ]
                }},
                options: {{
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
            }});

            
            function updateChart() {{
                $.get('/get_data', function(data) {{
                    myChart.data.labels = data.timestamps;
                    myChart.data.datasets[0].data = data.soil_moisture;
                    myChart.data.datasets[1].data = data.air_humidity;
                    myChart.data.datasets[2].data = data.air_temperature;
                    myChart.update();
                    
                    var waterWeekHtml = '';
                    for (var i = 0; i < 7; i++) {{
                        waterWeekHtml += '<td>' + data.water_week[i] + '</td>';
                    }}
                    waterWeekHtml += '<td>' + data.last_water + '</td>';
                    
                    $('#waterTable tbody').html('<tr>' + waterWeekHtml + '</tr>');
                    
                }});
            }}
            setInterval(updateChart, 3000);
        </script>
    </body>
</html>
"""
        
        chunk_size = 512  
        for i in range(0, len(response), CHUNK_SIZE):
            client.send(response[i:i+CHUNK_SIZE].encode("utf-8"))

        #client.send(response.encode("utf-8"))
        client.close()
        print("HTML response sent")
        del response
        gc.collect()

    def handle_ajax_request(self, client):
        gc.collect()
        print("AJAX request received")
        data = {
            "timestamps": [reading.timestamp for reading in self.readings],
            "soil_moisture": [reading.soil_moisture for reading in self.readings],
            "air_humidity": [reading.air_humidity for reading in self.readings],
            "air_temperature": [reading.air_temperature for reading in self.readings],
            "water_week": self.get_water_week(),
            "last_water": self.last_water
        }
        
        response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" + json.dumps(data)
        
        for i in range(0, len(response), CHUNK_SIZE):
            client.send(response[i:i+CHUNK_SIZE].encode("utf-8"))
        client.close()
        print("response JSON sent")
        
        del response
        gc.collect()


if __name__ == "__main__":
    print("Test WebServer")
    

    web_server = WebServer()
    for i in range(20):
        web_server.add_reading(Data(i, i*2, i*4))
        
    print("Web server created and waiting for connections...")

    while True:
        try:
            client, addr = web_server.server.accept()
            print("Client connected from:", addr)
            web_server.handle_request(client)
            web_server.add_reading(Data(web_server.needed_soil_moisture, web_server.reading_interval, web_server.time_water))
        except OSError:
            sleep(1)
        except Exception as e:
            print("Server error:", e)
            web_server.__del__()
            raise
        
