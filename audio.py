import subprocess

import asyncio
import time
from decouple import config

import matrix_functions as mx
import functions as func


async def main():
    server = config('MATRIX_SERVER')
    user = config('MATRIX_USER')
    password = config('MATRIX_PASSWORD')
    device_id = config('MATRIX_DEVICE_ID')
    room = config('MATRIX_ROOM_NAME_SPEAKER')
    lang_room = config('MATRIX_ROOM_NAME_LANGUAGE')
    alarm_room = config('MATRIX_ROOM_NAME_ALARM')
    
    client_task = asyncio.create_task(
        mx.matrix_login(server, user, password, device_id))
    client = await client_task

    room_id_task1 = asyncio.create_task(
        mx.matrix_get_room_id(client, room))
    room_id = await room_id_task1

    lang_id_task = asyncio.create_task(mx.matrix_get_room_id(client, lang_room))
    lang_id = await lang_id_task

    alarm_id_task = asyncio.create_task(mx.matrix_get_room_id(client, alarm_room))
    alarm_id = await alarm_id_task

    proc = subprocess.Popen(['true'])
    last_msg_ids = set()
    messages = []
    langu = ""
    alarm_msg = ""
    last_time_lang = 0
    last_time_alarm = 0
    while True:
        time.sleep(1)
        msg = ''
        room_msg_task = asyncio.create_task(
            mx.matrix_get_messages(client, room_id, limit=10))
        room_msgs = await room_msg_task

        #alarm
        alarm_task = asyncio.create_task(mx.matrix_get_messages(client, alarm_id))
        alarm = await alarm_task

        lang_room_task = asyncio.create_task(
            mx.matrix_get_messages(client, lang_id))
        if (func.has_time_passed(last_time_lang, 10)):
            langu = await lang_room_task
            if langu:
                langu = langu[0][0]
                last_time_lang = time.time()

        if (func.has_time_passed(last_time_alarm, 2)):
            alarm_msg = await alarm_task
            if alarm_msg:
                alarm_msg = alarm_msg[0][0]
                last_time_alarm = time.time()

        if room_msgs:
            for room_msg in room_msgs:
                msg, timestamp, msg_id = room_msg
                if not (msg_id in last_msg_ids or func.has_time_passed(timestamp, 20)):
                    msgs = msg.split('\n')
                    
                    last_msg_ids.add(msg_id)
                    messages += msgs
                    #messages = messages[0].split()
        messages.append(alarm_msg)
        for name in messages:
            name = alarm_msg if alarm_msg == 'ALARM' else name
            command = f'aplay ./Audio/{langu}/{name}.wav' 
            if name == 'STOP':
                break
            print(command)

            try:
                proc = subprocess.Popen(command.split())
                proc.wait()

                while alarm_msg == 'ALARM':
                    alarm_task = asyncio.create_task(mx.matrix_get_messages(client, alarm_id))
                    alarm_msg = await alarm_task
                    if alarm_msg:
                        alarm_msg = alarm_msg[0][0]
                        last_time_alarm = time.time()
                    proc = subprocess.Popen(command.split())
                    proc.wait()
            except Exception as e:
                print(e)

        messages.clear()

        # for _, event_id in room_msgs:
        #     last_room_msg_event_ids.insert(0, event_id)

        # last_room_msg_event_ids = last_room_msg_event_ids[:10]

if __name__ == '__main__':
    asyncio.run(main())
