from time import sleep
import network

def connect(ssid, password):
    # Turn off AP
    network.WLAN(network.AP_IF).active(False)

    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    count = 0
    while not wlan.isconnected():
        count += 1
        print(f'Connecting to {ssid}... {count}')
        if count > 5:
            print(f'Retrying.')
            count = 0
            wlan.disconnect()
            wlan.active(True)
            wlan.connect(ssid, password)
        sleep(1)
    print(f'Connected.')
    print(wlan.ifconfig())
    return wlan.ifconfig()[0]
