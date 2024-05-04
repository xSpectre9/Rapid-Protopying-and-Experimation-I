import sacn
import threading
import numpy as np

import time
import pandas as pd

timing_data = []
timing_for_modify_array = []

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

# this is for the sending padded data
data = np.zeros((512 * no_total_universes,), dtype=np.uint8)

# this reads the entire text file or effect 
led_mega = np.loadtxt('led_text_file.txt', dtype=np.uint8)
# print(led_mega)
# print(len(led_mega))

# this is the number of different LED configurations generated
no_configs = len(led_mega)//(no_leds)

# reshape the array to have rgb tuples
led_mega = led_mega.reshape(no_configs, no_leds, 3)
# print(led_mega)
# print(led_mega.shape)

# this is the global led variable that iterates through led_mega
led = np.zeros((no_leds, 3), dtype=np.uint8)
# print(led)

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
def fill_data(universe, no_universes, hex, start, end, no_DMX_channels):
    
    # time test
    start_time = time.time()
    
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
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    timing_data.append({'Function': 'fill_array', 'Universe': universe, 'Thread': hex, 'Time': elapsed_time})
    # print(f"Time: fill_data() in universe {universe} by thread {hex} = {elapsed_time} seconds")
    # print("")
    
# send the universes from data to WLED       
def send_data(universe, hex, sender):
    
    start_time = time.time()
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
    # time.sleep()
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    timing_data.append({'Function': 'send_array', 'Universe': universe, 'Thread': hex, 'Time': elapsed_time})
    # print(f"Time: send_data() in universe {universe} by thread {hex} = {elapsed_time} seconds")
    # print("")
    
def send_to_hexagon(ip, start, end):
    
    sender = initialize_sender()
    
    # the sliced 1260 array gives the number of DMX channels to be sent
    no_DMX_channels = (end - start + 1) # this should be 1350 for 450 LEDs
    
    # this is the number of universes to be sent for the specific slice
    no_universes = (no_DMX_channels+511)//512 # 3 universes
    
    hex = determine_hexagon(start)
    setup_sender(ip, no_universes, sender)
    
    timer = 0
    while True:
        
        for universe in range(no_universes):
            
            # fill values from led into data
            fill_data(universe, no_universes, hex, start, end, no_DMX_channels)
            # send this data to esp
            send_data(universe, hex, sender)
            timer = timer+1

# make led iterate through led_mega
def modify_array():
    
    global led 
    timer = 0
    
    while True:
        
        for i in range(no_configs):
            
            start_time = time.time()
            
            # update the global 'led' array with the current configuration
            led = led_mega[i, :, :].copy()
            
            # delay for effects
            # time.sleep(0.001)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            timing_for_modify_array.append({'Function': 'modify_array', 'Time': elapsed_time})
            # print(f"Time taken by modify_data() = {elapsed_time} seconds")
            # print("")
            timer = timer + 1
        


def analyze_timing_data():
    
    # Convert the timing data to a DataFrame
    df = pd.DataFrame(timing_data)
    df_m = pd.DataFrame(timing_for_modify_array)
    
    # Group by function, universe, and thread, then describe the times
    result = df.groupby(['Function', 'Universe', 'Thread']).Time.describe()
    result_m = df_m.groupby(['Function']).Time.describe()
    
    # Print the full summary stats
    print(result)
    print(result_m)
    
    # You might want to save the result to a CSV file for further analysis
    result.to_csv("timing_analysis.csv")
    result_m.to_csv("timing_analysis_m.csv")
    
def main():
    
    t_left = threading.Thread(target=send_to_hexagon, args=(left_ip, left_start, left_end, ))
    t_right = threading.Thread(target=send_to_hexagon, args=(right_ip, right_start, right_end, ))
    t_top = threading.Thread(target=send_to_hexagon, args=(top_ip, top_start, top_end, ))

    t4 = threading.Thread(target=modify_array)
    t4.start()

    t_left.start()
    t_right.start()
    t_top.start()
    
    t4.join()
    t_left.join()
    t_right.join()
    t_top.join()
    
    # analyze_timing_data()
    
main()