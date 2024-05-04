import numpy as np

left_leds = 450
right_leds = 420
top_leds = 390
no_leds = 1260

no_edges = no_leds//15

led = np.zeros((no_leds, 3), dtype=np.uint8)

with open('led_text_file.txt', 'w') as f:
    d = 0
    for i in range(no_edges):
        
        led[d:d+15] = [255, 255, 255]
        led[d:d+3] = [255, 0, 0]
        
        print(f"{i}: {led.tolist()}")
        np.savetxt(f, led, fmt='%d')
        
        led[d:d+3] = [0, 255, 0]
        d = d+15  
        
# edge_num = 58
# i = 15 * edge_num
# led[i:i+15] = [255, 255, 255]
# # led[15:30] = [255, 0, 0]
# led[i:i+3] = [255, 0, 0]
# np.savetxt('led_text_file.txt', led, fmt='%d')