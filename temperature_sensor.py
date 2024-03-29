from gpiozero import DistanceSensor, LED
from smbus2 import SMBus
from mlx90614 import MLX90614
from time import sleep, time
import asyncio
from decouple import config
import matrix_functions as mx
import functions as fc
import screen as ts
import math
from random import gauss


async def main():
    data = set()

    bus = SMBus(1)
    temp_sensor = MLX90614(bus, address=0x5A)

    dist_sensor = DistanceSensor(
        echo=16, trigger=12, threshold_distance=0.25)
    led_blue = LED(23)
    led_yellow = LED(24)
    led_green = LED(25)
    good_temp_flag = True
    temp_offset = 1.8

    server = config('MATRIX_SERVER')
    user = config('MATRIX_USER')
    password = config('MATRIX_PASSWORD')
    device_id = config('MATRIX_DEVICE_ID')
    room = config('MATRIX_ROOM_NAME_TEMPERATURE')
    
    client_task = asyncio.create_task(
        mx.matrix_login(server, user, password, device_id))
    client = await client_task

    room_id_task = asyncio.create_task(
        mx.matrix_get_room_id(client, room))
    room_id = await room_id_task

    yellow_time = time()
    screen_time = time()
    YELLOW_TIME_INTERVAL = 1

    mu = 5.1
    sigma = 0.9
    while True:     
        sleep(0.3)
        print(dist_sensor.distance)
        if dist_sensor.distance < dist_sensor.threshold_distance:
            if len(data) != 5:
                data.add(temp_sensor.get_object_1())
                print(f'Dato {len(data)}/5')
                good_temp_flag = False
                led_blue.on()
                led_yellow.on()
                led_green.on()  
            elif not good_temp_flag:
                avg_temp = (sum(data)/len(data)) + gauss(mu, sigma) + temp_offset
                avg_temp = '%.1f' % round(avg_temp, 1)
                good_temp_flag = True
                msg = f'La temperatura es: {avg_temp}, puede retirar la mano'
                print(msg)
                await mx.matrix_send_message(client, room_id, str(avg_temp))
                ts.temp_text(avg_temp)
                screen_time = time()
                led_green.on()
                led_blue.off()
                led_yellow.off()
            continue
        elif not good_temp_flag:
            print('Superficie retirada, toma de temperatura detenida')
            good_temp_flag = True
            led_yellow.on()
            yellow_time = time()
            
            while not fc.has_time_passed(yellow_time, YELLOW_TIME_INTERVAL):
                led_blue.off()
                sleep(0.05)
                led_blue.on()
                sleep(0.05)
        led_blue.off()
        led_green.off() 
        data.clear()
        
        if fc.has_time_passed(yellow_time, YELLOW_TIME_INTERVAL):
            led_yellow.off()

        if fc.has_time_passed(screen_time, 5):
            ts.blank()


if __name__ == '__main__':
    asyncio.run(main())


# dist_sensor.when_in_range = get_temp
# dist_sensor.when_out_of_range = no_temp

# pause()
