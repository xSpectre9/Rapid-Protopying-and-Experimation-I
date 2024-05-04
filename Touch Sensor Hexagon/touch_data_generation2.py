import numpy as np

no_leds = 450

no_edges = no_leds//15

led = np.zeros((no_leds, 3), dtype=np.uint8)

with open('dta_text_file.txt', 'w') as f:
    d = 0
    for i in range(no_edges):
        
        led[d:d+15] = [255, 255, 255]
        led[d:d+3] = [255, 0, 0]
        
        print(f"{i}: {led.tolist()}")
        np.savetxt(f, led, fmt='%d')
        
        led[d:d+3] = [0, 255, 0]
        d = d+15