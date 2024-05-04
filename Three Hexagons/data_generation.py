# generate the numpy double array LED
# output it to a file (.txt)
# read that file in send_to_esps
# it will run, close and generate all the data to the .txt
# it wont be running in parallel to send_to_esps

import numpy as np
left_leds = 450
right_leds = 420
top_leds = 390
no_leds = 1260

# led = np.zeros((no_leds, 3), dtype=np.uint8)

trail = 15
offset_fade = 0.2
decay = []
# write r,g,b values into a small function that decay for the first 5 array
for i in range(1, 16):
    r = 255*(i*0.0666)
    g = 255*(i*0.0666)
    b = 255*(i*0.0666)
    decay.append([r,g,b])
    
print(decay)

decay_np = np.array(decay, dtype=np.uint8)
led = np.zeros((no_leds, 3), dtype=np.uint8)

# write this array into main led
led[0:15] = decay_np
led[0] = [0, 0, 0]
# outer for loop runs from 0 to 1260-5
# inner for runs from i+5-1 to i-1, -1
# copy j into j+1

with open('led_text_file.txt', 'w') as f:
    for i in range(0, 1260-15):
        
        for j in range(i+15-1, i-1, -1):
            
            led[j+1] = led[j]
            
            np.savetxt(f, led, fmt='%d')
            
# inner for runs from i+5-1 to i-1, -1
# copy j into j+1

# Initialize the file to write the configurations
# with open('led_text_file.txt', 'w') as f:
    
    # led = np.zeros((no_leds, 3), dtype=np.uint8)

    # for i in range(no_leds):
        
        # led[i] = [255, 255, 255]
        # # turn off the LED that is now not in trail
        
        # if i >= trail:
        #     # led[i - trail] = np.uint8(led[i - trail] * offset_fade)
        #     led[i - trail] = [0, 0, 0] 
        
    # for i in range(left_leds):

    #     if i <= left_leds:
    #         led[0 : i] = [255, 0, 0] 
        
    #     if i <= left_leds+right_leds:
    #         led[left_leds : i+left_leds] = [0, 255, 0]
        
    #     if i <= left_leds+right_leds+top_leds:            
    #         led[left_leds+right_leds : i+left_leds+right_leds] = [0, 0, 255]
            
    #     np.savetxt(f, led, fmt='%d')
        
# led[:left_leds] = [255, 0, 0]
# led[left_leds:left_leds+right_leds] = [0, 255, 0]
# led[left_leds+right_leds:] = [0, 0, 255]

# np.savetxt('led_text_file.txt', led, fmt='%d')
