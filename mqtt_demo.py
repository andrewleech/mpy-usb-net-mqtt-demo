import aiorepl
import asyncio
import machine
import network
import rp2
import sys

sys.path.insert(0, "micropython-mqtt")
from mqtt_as import MQTTClient, config
# from asyncpin import AsyncPinDb
from broker import Broker

network.hostname("Degraves")
network.USBNET().active(True)


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
        print(f"button: {current}")
        await client.publish('button_topic', str(current))


async def handle_led(topic, msg):
    print(topic, msg)
    led_onboard = machine.Pin("LED", machine.Pin.OUT)
    led_onboard.toggle()


async def main():
    try:
        client = None
        await wait_for_host_connection()
        
        client = MQTTClient(config)
        broker = Broker()

        await client.connect()
        
        print(f"Connectd.")

        asyncio.create_task(_reconnect(client))
        asyncio.create_task(_messages(client, broker))
        
        asyncio.create_task(monitor_hardware(client))

        broker.subscribe("led_topic", handle_led)
        await client.subscribe('led_topic', 1)

        asyncio.create_task(aiorepl.task())

        asyncio.get_event_loop().run_forever()
            
    finally:
        if client:
            client.close()  # Prevent LmacRxBlk:1 errors

async def _messages(client, broker):  # Respond to incoming messages
    async for topic, msg, retained in client.queue:
        # print(topic.decode(), msg.decode(), retained)
        broker.publish(topic.decode(), msg.decode())

async def _reconnect(client):  # Respond to connectivity being (re)established
    initial = True
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
        # renew subscriptions
        print("Subscribing" if initial else "Reconnecting")
        initial = False
        await client.subscribe('led_topic', 1)

config["queue_len"] = 1  # Use event interface with default queue size
config["quick"] = 1  # Fast startup as we're not waiting for wifi

#MQTTClient.DEBUG = True  # Optional: print diagnostic messages

asyncio.run(main())
