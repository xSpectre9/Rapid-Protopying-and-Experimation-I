import sacn
import time
import threading

# SINGLE STRIP ESP32
no_leds = 38
data = [0] * (no_leds * 3)

def send_to_wled():
    
    universe = 1
    destination_ip = "192.168.93.141"
    sender = sacn.sACNsender()
    sender.start()
    sender.activate_output(universe)
    sender.dmxis_multicast = False
    
    while True:
        
        sender[1].destination = destination_ip
        dta = data
        sender[1].dmx_data = dta
        
        
def modify_array():
    
    for i in range(no_leds):
    
        start_index = i * 3
        data[start_index:start_index+3] = [0, 255, 0]
        time.sleep(0.1) 
        data[start_index:start_index+3] = [255, 0, 0]
        time.sleep(0.1) 
        data[start_index:start_index+3] = [0, 0, 255]
        time.sleep(0.1) 
        data[start_index:start_index+3] = [0, 0, 0]

t1 = threading.Thread(target=send_to_wled)
t2 = threading.Thread(target=modify_array)
t1.start()
t2.start()