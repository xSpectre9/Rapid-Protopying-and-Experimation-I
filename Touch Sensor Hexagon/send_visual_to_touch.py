# This is the main file I am running. It connects to led-graph-mono's docker
import sacn
import time
import threading
import numpy as np
import os
import socket
import json

# get data from socket
# convert to text file

# touch sensor hexagon = 450 LEDs
led_ip = "192.168.40.8"
no_leds = 450
led_start = 0
led_end = (no_leds * 3) - 1

no_total_universes = (no_leds * 3)//512 + 1

# edit this variable based on what delay you want
# timer_var = 0.5

# this is the global led variable that iterates through led_mega
led = np.zeros((no_leds, 3), dtype=np.uint8)

t_led = None
t = None
stop_threads = False


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

# this is to setup the universe-specific sender
def setup_sender(destination_ip, no_universes, sender):
    
    for universe in range(no_universes):
        
        sender.activate_output(universe + 1)
        sender[universe + 1].destination = destination_ip
        
# core logic of the code, this fits LED into DATA universe by universe     
def fill_data(universe, start, no_DMX_channels, data):
    
    # print(f"universe: {universe}")
    
    # these are the universe specific indexes
    start_index = (512 * (universe)) # 0, 512, 1024
    # print(f"start_index: {start_index}")

    end_index = (512 * (universe + 1)) - 1 # 511, 1023, 1535
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
    
def send_data(universe, data, sender):
 
    start_index = ((universe) * 512)
    end_index = ((universe + 1) * 512) - 1
    
    # need to convert it back to a list or it doesnt get sent
    dta = data[start_index:end_index+1].tolist()
    
    sender[universe + 1].dmx_data = dta
    
def send_to_hexagon(ip, start, end, data):
    
    sender = initialize_sender()
    
    # the sliced 1260 array gives the number of DMX channels to be sent
    no_DMX_channels = (end - start + 1) # this should be 1350 for 450 LEDs
    
    # this is the number of universes to be sent for the specific slice
    no_universes = (no_DMX_channels+511)//512 # 3 universes

    setup_sender(ip, no_universes, sender)
    
    while not stop_threads:  # Check the stop flag in the main loop
        for universe in range(no_universes):
            if stop_threads:  # Check stop condition again before proceeding
                break
            
            # fill values from led into data
            fill_data(universe, start, no_DMX_channels, data)
            
            # send this data to esp
            send_data(universe, data, sender)
            
# make led iterate through led_mega
def modify_array(no_frames, led_mega):
    
    global led 
    
    while not stop_threads:  # Continue until told to stop
        for i in range(no_frames):
            if stop_threads:  # Check stop condition again inside the loop
                break
            # update the global 'led' array with the current configuration
            led = led_mega[i, :, :].copy()
            
            # delay for effects
            time.sleep(0.7)

def stop_existing_threads():
    global stop_threads, t, t_led
    stop_threads = True  # Signal threads to stop

    # Wait for threads to finish
    if t and t.is_alive():
        t.join()
    
    if t_led and t_led.is_alive():
        t_led.join()

    # Reset the stop flag for potential future thread reinitialization
    stop_threads = False
  
def write_to_hardware(data):

    global t, t_led

    # Stop existing threads if they are running
    stop_existing_threads()

    create_txt_file(data)
    
    # led_mega loads the entire text file into an array
    led_mega, no_frames = load_file('dta_text_file.txt')
    
    # this is for the sending padded data
    data = np.zeros((512 * no_total_universes,), dtype=np.uint8)
    
    t_led = threading.Thread(target=send_to_hexagon, args=(led_ip, led_start, led_end, data))

    t = threading.Thread(target=modify_array, args=(no_frames, led_mega))
    t.start()

    t_led.start()

    t.join()
    t_led.join()

def map_indv_arr(inp_arr):
    '''
    Mapping each individual array from visualizer to hardware indices
    '''
    finalarr = [269, 268, 267, 266, 265, 264, 263, 262, 261, 260, 259, 258, 257, 256, 255, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 149, 148, 147, 146, 145, 144, 143, 142, 141, 140, 139, 138, 137, 136, 135, 179, 178, 177, 176, 175, 174, 173, 172, 171, 170, 169, 168, 167, 166, 165, 419, 418, 417, 416, 415, 414, 413, 412, 411, 410, 409, 408, 407, 406, 405, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 239, 238, 237, 236, 235, 234, 233, 232, 231, 230, 229, 228, 227, 226, 225, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 209, 208, 207, 206, 205, 204, 203, 202, 201, 200, 199, 198, 197, 196, 195, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 449, 448, 447, 446, 445, 444, 443, 442, 441, 440, 439, 438, 437, 436, 435, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389]
    newarr = [0 for i in range(450)]
    
    for i in range(450):
        newarr[finalarr[i]] = inp_arr[i]
    
    return newarr

def flatten_json(json_data):
    '''
    Converting json from visualizer format to one large array with mapped data
    Arguments:
    - json_data: dict, a JSON-like dictionary where each key is a string representing the index
      and each value is a list of numbers.
    
    Returns:
    - List[int], a single flattened list containing all mapped arrays concatenated together.
    '''

    # Initialize an empty list to store the concatenated results
    flattened_list = []

    # Iterate over each key in the sorted order of keys to maintain consistent order
    for key in sorted(json_data.keys(), key=int):
        # Get the array associated with the current key
        current_array = json_data[key]
        # Map the current array using the predefined mapping function
        mapped_array = map_indv_arr(current_array)
        # Extend the flattened list with the mapped array
        flattened_list.extend(mapped_array)
    
    return flattened_list

def create_txt_file(json_dict):
    # Use the provided function to flatten the JSON data
    flattened_list = flatten_json(json_dict)
    # print(flattened_list)

    # File path for the text file
    file_path = 'dta_text_file.txt'

    # Remove the file if it already exists
    if os.path.exists(file_path):
        os.remove(file_path)

    # Open a new text file in write mode
    with open(file_path, 'w') as file:
        # Iterate over each value in the flattened list
        for hex_value in flattened_list:
            # Check if the hex value is in the format "#ccc"
            if len(hex_value) == 4:  # e.g., "#ccc"
                # Expand the shorthand to full form
                r, g, b = hex_value[1]*2, hex_value[2]*2, hex_value[3]*2
            else:  # Full six-digit hex format, e.g., "#cccccc"
                r, g, b = hex_value[1:3], hex_value[3:5], hex_value[5:7]

            # Convert hex values to decimal and format the string
            rgb_str = f"{int(r, 16)} {int(g, 16)} {int(b, 16)}"

            # Write the formatted string to the file followed by a newline
            file.write(rgb_str + '\n')

def client_thread(conn, addr):
    print(f"Connected by {addr}")
    data = ''
    try:
        while True:
            part = conn.recv(1024).decode('utf-8')
            if not part:
                break
            data += part
            if data.endswith('\n'):  # '\n' is the delimiter
                break

        if data:
            processed_data = json.loads(data.strip())
            print("Received data")
            stop_existing_threads()
            write_to_hardware(processed_data)

    except json.JSONDecodeError as e:
        print("Received data that was not valid JSON:", data)
    except Exception as e:
        print("An error occurred:", e)
    finally:
        print("Closing connection")
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 8444))
    server.listen(5)
    print("Listening on port 8444")

    try:
        while True:
            conn, addr = server.accept()
            print(f"Connected by {addr}")
            # Start a new thread for each client
            threading.Thread(target=client_thread, args=(conn, addr)).start()

    except KeyboardInterrupt:
        print("Server is shutting down.")

if __name__ == "__main__" :
    t_socket = threading.Thread(target=start_server)
    t_socket.start()
    t_socket.join()
