import sacn
import time

# Define the universe and destination IP for WLED
universe = 1  # Make sure this matches the universe configured in WLED
destination_ip = "192.168.93.141"  # Replace "WLED_IP_ADDRESS" with the IP address of your ESP32 running WLED

# Create an sACN sender
sender = sacn.sACNsender()

sender.start()

# Add the WLED ESP32 as a target
sender.activate_output(universe)

# [1] is the first universe, we are using unicast for now
sender[1].destination = destination_ip

no_leds = 37
# Define the sACN data to send to control WLED
# data = [255, 0, 0] * 6  # Assuming a 512-channel DMX universe, set all channels to red
data = [0] * (no_leds * 3)
print(data)


for i in range(no_leds):
    
    # Calculate the starting index of channels for the current LED
    start_index = i * 3

    # Set the channels for the current LED to a custom color (r, g, b)
    # Assuming full brightness white color for RGB LEDs
    data[start_index:start_index+3] = [215, 50, 120]  
    print(data)
    # Send the sACN data
    sender.dmxis_multicast = False  # Set to True if using multicast
    sender[1].dmx_data = data
    
    # Delay to visualize each LED lighting up one at a time
    time.sleep(0.1)  # Adjust this delay as needed
    
    # Reset data to turn off the current LED before lighting up the next one
    data[start_index:start_index+3] = [0, 0, 0]
    print(data)
    sender[1].dmx_data = data

# Send the sACN data
# sender.dmxis_multicast = False  # Set to True if using multicast
# sender.manual_flush = True
# sender[1].dmx_data = data # First channels data?

# time.sleep(15)  # send the data for 15 seconds
# Close the sender when done
sender.stop()
