# import aiorepl
import asyncio
import json
import machine
import network
import rp2

from mqtt_as import config, MQTT_base as MQTTClient
from asyncpin import AsyncPinDb
from broker import Broker

network.hostname("Degraves")
network.USBNET().active(True)

#network.USBNET().ifconfig()


# Local configuration
# config['ssid'] = 'your_network_name'  # Optional on ESP8266
# config['wifi_pw'] = 'your_password'
# config['server'] = '192.168.0.10'  # Change to suit e.g. 'iot.eclipse.org'


async def wait_for_host_connection():
    """
    The host pc usb interface is assigned an ip by dhcp
    running in micropython. Once its assigned, the host ip
    address is set as the gateway on the micropython interface.
    """
    iface = network.USBNET()
    ipaddr = iface.ipconfig('addr4')[0]
    while (host_ip := iface.ipconfig('gw4')) == ipaddr:
        await asyncio.sleep_ms(100)

    if host_ip == "0.0.0.0":
        host_ip = "169.254.128.16"
    print(f"Connecting to host: {host_ip}")
    config['server'] = host_ip
    config["client_id"] = network.hostname()


async def monitor_hardware(client):
    # button = AsyncPinDb(machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_DOWN), machine.Pin.IRQ_RISING)
    current = 0
    while True:
        # await button.wait_edge()
        while rp2.bootsel_button() == current:
            await asyncio.sleep_ms(100)
        current = rp2.bootsel_button()

        client.publish(
            "button_topic", 
            json.dumps({
                "state": button.value()
            })
        )


async def handle_led(topic, msg):
    print(topic, msg)
    led_onboard = machine.Pin("LED", machine.Pin.OUT)
    led_onboard.toggle()


async def main():
    # try:
        client = None
        await wait_for_host_connection()
        
        client = MQTTClient(config)
        broker = Broker()

        await client.connect()

        asyncio.create_task(_reconnect(client))
        # asyncio.create_task(_messages(client, broker))
        
        asyncio.create_task(monitor_hardware(client))

        broker.subscribe("led_topic", handle_led)

        client.set_cb_on_event("msg", _messages, udata=broker)

        # while True:
        #     await client.up.wait()
        #     client.up.clear()
        #     print("mqtt connected")
        #     client.set_cb_on_event("msg", _messages)

        #     await client.subscribe('led_topic', 1)

        # asyncio.create_task(aiorepl.task())

        # asyncio.get_event_loop().run_forever()
            
        await client.up.wait()
        n = 0
        while True:
            await asyncio.sleep(5)
            print('publish', n)
            # If WiFi is down the following will pause for the duration.
            await client.publish('result_topic', '{}'.format(n), qos = 1)
            n += 1
    # finally:
    #     if client:
    #         client.close()  # Prevent LmacRxBlk:1 errors



async def _messages(topic, msg, retained, udata):  # Respond to incoming messages
    broker = udata
    print(topic.decode(), msg.decode(), retained)
    broker.publish(topic.decode(), msg.decode())


async def _reconnect(client):  # Respond to connectivity being (re)established
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
        # renew subscriptions
        # await client.subscribe('degraves_topic', 1)  
        print("Subscribing")
        await client.subscribe('led_topic', 1)
        # await client.disconnect()


# config["queue_len"] = 1  # Use event interface with default queue size
# config["quick"] = 1  # Fast startup as we're not waiting for wifi

# MQTTClient.DEBUG = True  # Optional: print diagnostic messages


asyncio.run(main())
