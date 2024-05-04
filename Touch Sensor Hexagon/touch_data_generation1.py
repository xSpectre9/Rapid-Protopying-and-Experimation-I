import numpy as np

no_leds = 450

decay = []
# write r,g,b values into a small function that decay for the first 5 array
for i in range(1, 16):
    r = 255*(i*0.0666)
    g = 255*(i*0.0666)
    b = 255*(i*0.0666)
    decay.append([r,g,b])
    
decay_np = np.array(decay, dtype=np.uint8)
led = np.zeros((no_leds, 3), dtype=np.uint8)

led[0:15] = decay_np
led[0] = [0, 0, 0]

with open('dta_text_file.txt', 'w') as f:
    for i in range(0, 450-15):
        
        for j in range(i+15-1, i-1, -1):
            
            led[j+1] = led[j]
            
            np.savetxt(f, led, fmt='%d')