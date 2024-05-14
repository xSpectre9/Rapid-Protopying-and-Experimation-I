import sacn
import time

# universe and destination IP for WLED
universe = 1 
destination_ip = "192.168.93.141" 

# create an sACN sender
sender = sacn.sACNsender()

sender.start()

# add the WLED ESP32 as a target
sender.activate_output(universe)

# [1] is the first universe, we are using unicast for now
sender[1].destination = destination_ip

no_leds = 37
# define the sACN data to send to control WLED
# data = [255, 0, 0] * 6  # Assuming a 512-channel DMX universe, set all channels to red
data = [0] * (no_leds * 3)
print(data)

for i in range(no_leds):
    
    # calculate the starting index of channels
    start_index = i * 3
    
    data[start_index:start_index+3] = [215, 50, 120]  
    print(data)
    # Send the sACN data
    sender.dmxis_multicast = False  # Set to True if using multicast
    sender[1].dmx_data = data
    
    # delay for animation
    time.sleep(0.1)
    
    # reset data to turn off the current LED before lighting up the next one
    data[start_index:start_index+3] = [0, 0, 0]
    # print(data)
    sender[1].dmx_data = data

sender.stop()
