import math
import struct
import keyboard
import time
from socket import *

SERVER_IP = '127.0.0.1'
SERVER_PORT = 6501
ARRAY_SIZE = 20
PACK_FORMAT = '20d'

class SimulationClient:
    def __init__(self):
        self.udp_socket = socket(family=AF_INET, type=SOCK_DGRAM)
        self.server_address = (SERVER_IP, SERVER_PORT)

    def send_params(self, array):
        bts = struct.pack(PACK_FORMAT, *array)
        self.udp_socket.sendto(bts, self.server_address)

class CarController:
    def __init__(self):
        self.x, self.z = 0.0, 0.0
        self.angle = 0.0
        self.speed = 0.0
        self.wheel_turn = 0.0      # Угол поворота руля (лево/право)
        self.wheel_rotation = 0.0  # Вращение самих колес (кручение диска)
        self.headlights_angle = 0.0

    def update(self):
        # 1. ПЛАВНЫЙ ПОВОРОТ КОЛЕС (РУЛЯ)
        if keyboard.is_pressed('left'):
            self.wheel_turn = min(self.wheel_turn + 1.5, 25.0)
        elif keyboard.is_pressed('right'):
            self.wheel_turn = max(self.wheel_turn - 1.5, -25.0)
        else:
            self.wheel_turn *= 0.85

        # 2. ПОВОРОТ КОРПУСА МАШИНЫ
        self.angle += (self.speed * 25) * (self.wheel_turn / 25.0)

        # 3. ДВИЖЕНИЕ
        rad = math.radians(self.angle)
        if keyboard.is_pressed('up'):
            self.speed = min(self.speed + 0.001, 0.05)
        elif keyboard.is_pressed('down'):
            self.speed = max(self.speed - 0.001, -0.05)
        else:
            self.speed *= 0.97 # Трение

        self.x += self.speed * math.sin(rad)
        self.z += self.speed * math.cos(rad)

           # ... (код выше без изменений)

        # 4. ВРАЩЕНИЕ КОЛЕС (КРУЧЕНИЕ ВОКРУГ ОСИ Х/Z)
        # Если колеса крутятся "как юла", значит индекс 12-15 в симуляторе 
        # ожидает другой тип данных. Попробуем разделить вращение и поворот.
        self.wheel_rotation += self.speed * 8000 

        # 5. ФОРМИРОВАНИЕ МАССИВА
        sendArray = [0.0] * ARRAY_SIZE
        
        sendArray[6] = self.x                   
        sendArray[16] = self.z                  
        sendArray[8] = self.angle                        
        sendArray[2] = abs(self.speed * 2000)

        # ФАРЫ
        if keyboard.is_pressed('h'):
            self.headlights_angle = min(self.headlights_angle + 2, 90)
        else:
            self.headlights_angle = max(self.headlights_angle - 2, 0)
        sendArray[3] = self.headlights_angle 

        # --- ИСПРАВЛЕНИЕ ОСЕЙ ---
        # Если индексы 12-15 — это вращение колеса (Spin), 
        # а 17-18 — это поворот руля (Steer), убедитесь, что они не конфликтуют.
        
        # Вращение всех колес (вперед-назад)
        for i in [12, 13, 14, 15]:
            sendArray[i] = self.wheel_rotation

        # Поворот передних колес (влево-вправо)
        sendArray[17] = self.wheel_turn
        sendArray[18] = self.wheel_turn

        return sendArray


if __name__ == "__main__":
    client = SimulationClient()
    car = CarController()
    print("Управление: Стрелки - движение, H - фары. Esc - выход.")

    try:
        while not keyboard.is_pressed('esc'):
            data = car.update()
            client.send_params(data)
            time.sleep(0.01) # Небольшая пауза, чтобы не перегружать процессор
    except KeyboardInterrupt:
        pass
