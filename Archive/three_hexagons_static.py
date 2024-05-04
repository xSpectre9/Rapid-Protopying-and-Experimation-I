import sacn
import time
import threading

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
data = [0] * ((512) * (no_total_universes))

# this is for the receiving data
led = [[0]*3 for _ in range(no_leds)]


def send_to_hexagon(ip, start, end, n_leds):
    
    # this is the send calls stuff for WLED
    destination_ip = ip
    sender = sacn.sACNsender()
    sender.start()
    sender.dmxis_multicast = False
    
    # the sliced 1260 array gives the number of DMX channels to be sent
    no_DMX_channels = (end - start + 1) # this should be 1350 for 450 LEDs
    
    # no_leds = no_DMX_channels/3 # 450 LEDs again
    
    # this is the number of universes to be sent for the specific slice
    no_universes = no_DMX_channels//512 + 1 # 3 universes
    
    # this helps us determine which hexagon it is
    if(start > 0):
        hex = (start//512 + 1) 
    else:
        hex = 0
    
    # setup the link to send stuff to hexagons
    for universe in range(no_universes):
        
        sender.activate_output(universe+1)
        sender[universe + 1].destination = destination_ip
        
    # manipulate data from LED
    for universe in range(no_universes):
        
        # print(f"universe: {universe}")
        # these are the universe specific indexes
        start_index = (512 * (universe + hex)) # 0, 512, 1024 // 1536, 2048, 2560
        # print(f"start_index: {start_index}")
        
        end_index = (512 * (universe + hex + 1)) - 1 # 511, 1023, 1535 // 2047, 2559, 3071
        # print(f"end_index: {end_index}")
        
        # last universe case
        if(universe == no_universes - 1):
            
            last_index = start_index + no_DMX_channels - (universe * 510) - 1 # this will be 1353//2799//4246

            # writing data
            a = start_index 
            # r = n_leds - (universe * (510//3)) # the last bit of LEDs that need to be written into the last universe
            for i in range((start//3 + ((universe) * 510//3)), (end//3)):
                data[a:a+3] = led[i]
                a = a + 3
                
            # padding
            data[last_index+1:end_index+1] = [0] * (end_index - last_index)
        
        # normal universe case
        else:
            last_index = ((universe + hex + 1) * 512) - 1 - 2 # this will be 510 // 
            
            # writing data
            a = start_index
            for i in range((start//3 + (universe * 510//3)), (start//3 + ((universe + 1) * 510//3))):
                data[a:a+3] = led[i]
                # print(f"{data[a:a+3]} = {led[i]}")
                a = a + 3
            
            # padding
            data[last_index+1:end_index+1] = [0] * 2
            
        # print(data[start_index:end_index+1])
        # print(len(data[start_index:end_index+1]))
    
    while True:
        
        for universe in range(no_universes):  
            
            # print(f"Universe: {universe}")
            # print(f"Start: {start}, End: {end}")
            
            start_index = ((universe + hex) * 512)
            end_index = ((universe + hex + 1) * 512) - 1
            
            dta = data[start_index:end_index+1]
            # print(data[start_index:end_index+1])
            
            # print(len(dta))
            
            sender[universe + 1].dmx_data = dta
            # time.sleep(2)
    
def modify_array():
    
    # populate LED here 
    # left hexagon
    # for i in range(left_leds):
        
    #     led[i] = [255, 0, 0] # this is all red
    # # print(f"Left LED: {led[left_start//3:left_end//3]}")
    
    # # right hexagon
    # for i in range(left_leds, left_leds+right_leds):
        
    #     led[i] = [0, 255, 0] # this is all green
    # # print(f"Right LED: {led[right_start//3:right_end//3]}")
    
    # # top hexagon
    # for i in range(left_leds+right_leds, left_leds+right_leds+top_leds):
        
    #     led[i] = [0, 0, 255] # this is all blue
    # print(f"Top LED: {led[top_start//3:top_end//3]}")
    
    for i in range(1260):
        if(i%45<15): # first 15
            led[i] = [255, 105, 180]
        elif(i%45<30): # next 15
            led[i] = [255, 0, 0]
        else: # third 15
            led[i] = [0, 0, 255]
            
t_left = threading.Thread(target=send_to_hexagon, args=(left_ip, left_start, left_end, left_leds, ))
t_right = threading.Thread(target=send_to_hexagon, args=(right_ip, right_start, right_end, right_leds, ))
t_top = threading.Thread(target=send_to_hexagon, args=(top_ip, top_start, top_end, top_leds, ))

t4 = threading.Thread(target=modify_array)
t4.start()

t_left.start()
t_right.start()
t_top.start()