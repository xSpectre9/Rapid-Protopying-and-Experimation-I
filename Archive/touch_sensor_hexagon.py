import sacn
import time
import threading

# TOUCH HEXAGON
# One universe has 512 DMX channels
# 3 DMX channels represent the (R, G, B) on one pixel
# 512/3 == 170.67 == 170 LEDs controlled by 1 universe
# 510 DMX channels need to be set to R,G,B values, while 2 need to be padded
# in the last universe, more DMX channels need to be padded

no_leds = 450
no_DMX_channels = no_leds * 3 # this should be 450*3 = 1350
no_universes = no_DMX_channels//512 + 1
no_dmx_per_universe = 510 # this is as 510 is divisible by 3

data = [0] * (512 * no_universes)

def send_to_wled():
    
    # universe = 1
    destination_ip = "192.168.40.5"
    sender = sacn.sACNsender()
    sender.start()
    # sender.activate_output(universe)
    sender.dmxis_multicast = False
    
    for universe in range(no_universes):
        sender.activate_output(universe+1)
        sender[universe + 1].destination = destination_ip
    
    while True:
        
        for universe in range(no_universes):  
            
            # print(f"Universe: {universe}")
            
            start_index = (universe * 512)
            end_index = ((universe+1) * 512) - 1
            
            dta = data[start_index:end_index+1]
            
            # print(dta)
            # print(len(dta))
            
            sender[universe + 1].dmx_data = dta
            # time.sleep(2)

def modify_array():
    
    # generate the super array ONCE
    # send that to the send function
    # slice it there
        
        for universe in range(no_universes):

            start_index = (512 * universe) # 0, 512, 1024
            end_index = (512 * (universe + 1)) - 1 # 511, 1023, 1535
            
            
            # data filling and padding
            
            # last universe case
            if(universe == no_universes-1): 
            
                last_index = (512 * universe) + (no_DMX_channels - (universe * no_dmx_per_universe)) - 1

                # writing data
                data[start_index:last_index+1] = [255, 0, 0] * ((last_index - start_index + 1)//3)
                
                # padding
                data[last_index+1:end_index+1] = [0] * (end_index - last_index)
                
            # normal universe case    
            else: 
                
                last_index = ((universe + 1) * 512) - 1 - 2 
                
                # writing data
                data[start_index:last_index+1] = [255, 0, 0] * (no_dmx_per_universe//3) 
                
                # padding
                data[last_index+1:end_index+1] = [0] * 2
        
t1 = threading.Thread(target=send_to_wled)
t2 = threading.Thread(target=modify_array)
t1.start()
t2.start()