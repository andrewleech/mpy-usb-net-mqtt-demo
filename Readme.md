# Micropython MQTT over USB_Net Demo

This demo app is intended to show basic usage of mqtt communication over a USB Network
interface from PC to Micropython, currently running on a Raspberry Pi Pico.

This usilises the USB Network endpoint provided in the PR: [shared/tinyusb: Add support for USB Network (NCM) interface.](https://github.com/micropython/micropython/pull/)16459

It has been tested with the Mosquitto mqtt broker on Windows 11.

## Installation
1. Install Mosquitto: https://mosquitto.org/download/

1. Update the Mosquitto config file to enable access from other devices. 
    1. Open `C:\Program Files\mosquitto\mosquitto.conf` in notepad or similar, Administrator privs are needed to save.
    1. Find the section with:
    ```
    # listener port-number [ip address/host name/unix socket path]
    #listener
    ```
    and add the line below:
    ```
    # listener port-number [ip address/host name/unix socket path]
    #listener
    listener 1883 0.0.0.0
    ```
    1. Find the section with:
    ```
    #allow_anonymous false
    ``` 
    and add below:
    ```
    #allow_anonymous false
    allow_anonymous true
    ```
    1. Note: This is **insecure** and should only be used for local testing in a local / protected environment.
    More appropriate security settings should be used for any kind of production use.

1. Go to Windows Services (Win+R keys, run `services.msc`), then restart the `mosquitto` service.

1. Install MQTT Explorer: https://mqtt-explorer.com/ and open it, connect to `localhost` on port `1883` (tls disabled)

1. In a local clone of micropython, apply the PR linked above: `gh pr checkout 16459`

1. Build micropython for RPI_PICO with USB_NET variant: `mpbuild build RPI_PICO USB_NET`

1. Plug the rpi pico into USB with the BOOTSEL pushbutton held down. Then copy the firmware to the USB drive that pops up, eg.  
   `copy micropython\ports\rp2\build-RPI_PICO-USB_NET\firmware.uf2 E:\`

1. Once copied, the pico should reboot automatically and be detected as both a USB Serial device _and_ a USB Network interface.

1. In a terminal, open to this repo, run `mpremote mount . repl --inject-code "import mqtt_demo\n"`

1. The repl should appear, at which point you can jit `Ctrl-J` to run the application.
```
PS mqtt_demo\> mpremote mount . repl --inject-code "import mqtt_demo\n"
Local directory . is mounted at /remote
Connected to MicroPython at COM33
Use Ctrl-] or Ctrl-x to exit this shell
Use Ctrl-J to inject b'import mqtt_demo\r\n'
>
MicroPython v1.25.0-preview.342.g89f246acb7.dirty on 2025-03-03; Raspberry Pi Pico with RP2040
Type "help()" for more information.
>>> import mqtt_demo
Connecting to host: 169.254.128.16
Connectd.
Subscribing
Starting asyncio REPL...
--> 
```
1. Try pressing the button on the pico, it should be reported on the repl
1. You should also see it pop up in MQTT Explorer!

1. In Mqtt Explorer try publishing any text to the topic: `led_topic`, you should 
see it pop up in the repl! and the led on the pico should toggle!