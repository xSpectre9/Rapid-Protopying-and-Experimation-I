import sacn
import time
import threading
import numpy as np

# get data from socket
# convert to text file

# declare global variables
# left hexagon = 450 LEDs
left_ip = "192.168.40.5"
left_leds = 450
left_start = 0
left_end = (left_leds * 3) - 1

# right hexagon = 420 LEDs
right_ip = "192.168.40.6"
right_leds = 420
right_start = left_end + 1
right_end = right_start + (right_leds * 3) - 1

# top hexagon = 390 LEDs
top_ip = "192.168.40.7"
top_leds = 390
top_start = right_end + 1
top_end = top_start + (top_leds * 3) - 1

no_leds = left_leds + right_leds + top_leds
no_total_universes = (left_leds * 3)//512 + 1 + (right_leds * 3)//512 + 1 + (top_leds * 3)//512 + 1

# this is the global led variable that iterates through led_mega
led = np.zeros((no_leds, 3), dtype=np.uint8)

# call(text file path)
def load_file(filepath):
    
    # load text file into mega array
    led_mega = np.loadtxt(filepath, dtype=np.uint8)
    
    # the number of frames being generated
    no_frames = len(led_mega)//(no_leds)
    led_mega = led_mega.reshape(no_frames, no_leds, 3)
    
    return led_mega, no_frames

# this inititializes the send calls for WLED
def initialize_sender():
    
    sender = sacn.sACNsender()
    sender.start()
    sender.dmxis_multicast = False
    
    return sender

# need to determine which hexagon it is to slice the data array accordingly
def determine_hexagon(start):
    
    # returns 3 and 6 as multipliers for the second and third slices
    if start > 0:
        hex = start//512 + 1
    
    # returns 0 as a multiplier for the first slice
    else:
        hex = 0
    
    return hex

# this is to setup the universe-specific sender
def setup_sender(destination_ip, no_universes, sender):
    
    for universe in range(no_universes):
        
        sender.activate_output(universe + 1)
        sender[universe + 1].destination = destination_ip
        
# core logic of the code, this fits LED into DATA universe by universe     
def fill_data(universe, hex, start, no_DMX_channels, data):
    
    # print(f"universe: {universe}")
    
    # these are the universe specific indexes
    start_index = (512 * (universe + hex)) # 0, 512, 1024 // 1536, 2048, 2560; etc
    # print(f"start_index: {start_index}")

    end_index = (512 * (universe + hex + 1)) - 1 # 511, 1023, 1535 // 2047, 2559, 3071; etc
    # print(f"end_index: {end_index}")

    # determine the number of DMX channels to be filled in this universe
    DMX_channels_this_universe = min(510, no_DMX_channels - universe * 510)  # 510 channels or 330 for last universe
    
    led_start = start//3 + (universe * 510//3) # 450, 450+170, 450+170+170
    led_end = led_start + DMX_channels_this_universe//3 # 450+170, 450+170+170, 450+170+170+80
    # print(led_start, led_end)
    
    # this is the number of LEDs needed to be added for the particular universe
    n_leds_in_universe = led_end - led_start
    
    # main data writing logic from led into data
    data[start_index:start_index + (n_leds_in_universe*3)] = led[led_start:led_end].flatten()

    # padding
    last_index = start_index + (n_leds_in_universe*3) - 1
    data[last_index + 1:end_index + 1] = 0
    
    # return data
    
# send the universes from data to WLED       
def send_data(universe, hex, data, sender):
    
    # print(f"Universe: {universe}")
    # print(f"Start: {start}, End: {end}")
    start_index = ((universe + hex) * 512)
    end_index = ((universe + hex + 1) * 512) - 1
    
    # need to convert it back to a list or it doesnt get sent
    dta = data[start_index:end_index+1].tolist()
    # print(data[start_index:end_index+1])
    # print(dta)
    # print(len(dta))
    
    sender[universe + 1].dmx_data = dta
    # time.sleep(2)

# caller function that calls all the other functions except modify array           
def send_to_hexagon(ip, start, end, data):
    
    sender = initialize_sender()
    
    # the sliced 1260 array gives the number of DMX channels to be sent
    no_DMX_channels = (end - start + 1) # this should be 1350 for 450 LEDs
    
    # this is the number of universes to be sent for the specific slice
    no_universes = (no_DMX_channels+511)//512 # 3 universes
    
    hex = determine_hexagon(start)
    setup_sender(ip, no_universes, sender)
    
    while True:
        
        for universe in range(no_universes):
            
            # fill values from led into data
            fill_data(universe, hex, start, no_DMX_channels, data)
            
            # send this data to esp
            send_data(universe, hex, data, sender)

# make led iterate through led_mega
def modify_array(no_frames, led_mega):
    
    global led 
    
    while True:
        
        for i in range(no_frames):
            
            # update the global 'led' array with the current configuration
            led = led_mega[i, :, :].copy()
            
            # delay for effects
            time.sleep(0.1)

def main():
    
    # led_mega loads the entire text file into an array
    led_mega, no_frames = load_file('led_text_file.txt')
    
    # this is for the sending padded data
    data = np.zeros((512 * no_total_universes,), dtype=np.uint8)
    
    t_left = threading.Thread(target=send_to_hexagon, args=(left_ip, left_start, left_end, data))
    t_right = threading.Thread(target=send_to_hexagon, args=(right_ip, right_start, right_end, data))
    t_top = threading.Thread(target=send_to_hexagon, args=(top_ip, top_start, top_end, data))

    t4 = threading.Thread(target=modify_array, args=(no_frames, led_mega))
    t4.start()

    t_left.start()
    t_right.start()
    t_top.start()
    
    t4.join()
    t_left.join()
    t_right.join()
    t_top.join()

if __name__ == "__main__" :
    main()