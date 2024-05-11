import time
import socket
import json
import sacn
import threading
import numpy as np
import os

# get data from socket
# convert to text file

t_left = None
t_right = None
t_top = None
t4 = None
stop_threads = False

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

# caller function for socket
def write_to_hardware(data):

    global t_left, t_right, t_top, t4

    create_txt_file(data)

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

def temp_function():
    # Define the path to the JSON file
    file_path = 'socket/test_pattern.json'

    # Open the JSON file and load it into a Python dictionary
    with open(file_path, 'r') as file:
        json_data = json.load(file)

    # Pass the loaded data to the function that writes to hardware
    write_to_hardware(json_data)

def stop_existing_threads():
    global stop_threads, t_left, t_right, t_top, t_4
    stop_threads = True  # Signal threads to stop

    # Wait for threads to finish
    if t_right and t_right.is_alive():
        t_right.join()
    
    if t_left and t_left.is_alive():
        t_left.join()

    if t_top and t_top.is_alive():
        t_top.join()

    if t4 and t4.is_alive():
        t4.join()

    # Reset the stop flag for potential future thread reinitialization
    stop_threads = False

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
    server.bind(('0.0.0.0', 8333))
    server.listen(5)
    print("Listening on port 8333")

    try:
        while True:
            conn, addr = server.accept()
            print(f"Connected by {addr}")
            # Start a new thread for each client
            threading.Thread(target=client_thread, args=(conn, addr)).start()

    except KeyboardInterrupt:
        print("Server is shutting down.")

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
    
    return data
    
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
    
    while not stop_threads:  # Check the stop flag in the main loop
        for universe in range(no_universes):
            if stop_threads:  # Check stop condition again before proceeding
                break

            # fill values from led into data
            data = fill_data(universe, hex, start, no_DMX_channels, data)
            
            # send this data to esp
            send_data(universe, hex, data, sender)

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
            time.sleep(0.1)

def map_indv_arr(inp_arr):
    '''
    Mapping each individual array from visualizer to hardware indices
    '''
    finalarr = [359, 358, 357, 356, 355, 354, 353, 352, 351, 350, 349, 348, 347, 346, 345, 344, 343, 342, 341, 340, 339, 338, 337, 336, 335, 334, 333, 332, 331, 330, 329, 328, 327, 326, 325, 324, 323, 322, 321, 320, 319, 318, 317, 316, 315, 314, 313, 312, 311, 310, 309, 308, 307, 306, 305, 304, 303, 302, 301, 300, 299, 298, 297, 296, 295, 294, 293, 292, 291, 290, 289, 288, 287, 286, 285, 74, 73, 72, 71, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 404, 403, 402, 401, 400, 399, 398, 397, 396, 395, 394, 393, 392, 391, 390, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 389, 388, 387, 386, 385, 384, 383, 382, 381, 380, 379, 378, 377, 376, 375, 374, 373, 372, 371, 370, 369, 368, 367, 366, 365, 364, 363, 362, 361, 360, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 434, 433, 432, 431, 430, 429, 428, 427, 426, 425, 424, 423, 422, 421, 420, 419, 418, 417, 416, 415, 414, 413, 412, 411, 410, 409, 408, 407, 406, 405, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 194, 193, 192, 191, 190, 189, 188, 187, 186, 185, 184, 183, 182, 181, 180, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 179, 178, 177, 176, 175, 174, 173, 172, 171, 170, 169, 168, 167, 166, 165, 164, 163, 162, 161, 160, 159, 158, 157, 156, 155, 154, 153, 152, 151, 150, 149, 148, 147, 146, 145, 144, 143, 142, 141, 140, 139, 138, 137, 136, 135, 134, 133, 132, 131, 130, 129, 128, 127, 126, 125, 124, 123, 122, 121, 120, 269, 268, 267, 266, 265, 264, 263, 262, 261, 260, 259, 258, 257, 256, 255, 254, 253, 252, 251, 250, 249, 248, 247, 246, 245, 244, 243, 242, 241, 240, 779, 778, 777, 776, 775, 774, 773, 772, 771, 770, 769, 768, 767, 766, 765, 764, 763, 762, 761, 760, 759, 758, 757, 756, 755, 754, 753, 752, 751, 750, 749, 748, 747, 746, 745, 744, 743, 742, 741, 740, 739, 738, 737, 736, 735, 524, 523, 522, 521, 520, 519, 518, 517, 516, 515, 514, 513, 512, 511, 510, 479, 478, 477, 476, 475, 474, 473, 472, 471, 470, 469, 468, 467, 466, 465, 824, 823, 822, 821, 820, 819, 818, 817, 816, 815, 814, 813, 812, 811, 810, 509, 508, 507, 506, 505, 504, 503, 502, 501, 500, 499, 498, 497, 496, 495, 494, 493, 492, 491, 490, 489, 488, 487, 486, 485, 484, 483, 482, 481, 480, 809, 808, 807, 806, 805, 804, 803, 802, 801, 800, 799, 798, 797, 796, 795, 794, 793, 792, 791, 790, 789, 788, 787, 786, 785, 784, 783, 782, 781, 780, 645, 646, 647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689, 720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 854, 853, 852, 851, 850, 849, 848, 847, 846, 845, 844, 843, 842, 841, 840, 839, 838, 837, 836, 835, 834, 833, 832, 831, 830, 829, 828, 827, 826, 825, 464, 463, 462, 461, 460, 459, 458, 457, 456, 455, 454, 453, 452, 451, 450, 569, 568, 567, 566, 565, 564, 563, 562, 561, 560, 559, 558, 557, 556, 555, 855, 856, 857, 858, 859, 860, 861, 862, 863, 864, 865, 866, 867, 868, 869, 644, 643, 642, 641, 640, 639, 638, 637, 636, 635, 634, 633, 632, 631, 630, 539, 538, 537, 536, 535, 534, 533, 532, 531, 530, 529, 528, 527, 526, 525, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 629, 628, 627, 626, 625, 624, 623, 622, 621, 620, 619, 618, 617, 616, 615, 614, 613, 612, 611, 610, 609, 608, 607, 606, 605, 604, 603, 602, 601, 600, 599, 598, 597, 596, 595, 594, 593, 592, 591, 590, 589, 588, 587, 586, 585, 584, 583, 582, 581, 580, 579, 578, 577, 576, 575, 574, 573, 572, 571, 570, 719, 718, 717, 716, 715, 714, 713, 712, 711, 710, 709, 708, 707, 706, 705, 704, 703, 702, 701, 700, 699, 698, 697, 696, 695, 694, 693, 692, 691, 690, 1169, 1168, 1167, 1166, 1165, 1164, 1163, 1162, 1161, 1160, 1159, 1158, 1157, 1156, 1155, 1154, 1153, 1152, 1151, 1150, 1149, 1148, 1147, 1146, 1145, 1144, 1143, 1142, 1141, 1140, 1139, 1138, 1137, 1136, 1135, 1134, 1133, 1132, 1131, 1130, 1129, 1128, 1127, 1126, 1125, 1124, 1123, 1122, 1121, 1120, 1119, 1118, 1117, 1116, 1115, 1114, 1113, 1112, 1111, 1110, 899, 898, 897, 896, 895, 894, 893, 892, 891, 890, 889, 888, 887, 886, 885, 1214, 1213, 1212, 1211, 1210, 1209, 1208, 1207, 1206, 1205, 1204, 1203, 1202, 1201, 1200, 1199, 1198, 1197, 1196, 1195, 1194, 1193, 1192, 1191, 1190, 1189, 1188, 1187, 1186, 1185, 1184, 1183, 1182, 1181, 1180, 1179, 1178, 1177, 1176, 1175, 1174, 1173, 1172, 1171, 1170, 1020, 1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030, 1031, 1032, 1033, 1034, 1035, 1036, 1037, 1038, 1039, 1040, 1041, 1042, 1043, 1044, 1045, 1046, 1047, 1048, 1049, 1050, 1051, 1052, 1053, 1054, 1055, 1056, 1057, 1058, 1059, 1060, 1061, 1062, 1063, 1064, 1095, 1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1109, 1244, 1243, 1242, 1241, 1240, 1239, 1238, 1237, 1236, 1235, 1234, 1233, 1232, 1231, 1230, 1229, 1228, 1227, 1226, 1225, 1224, 1223, 1222, 1221, 1220, 1219, 1218, 1217, 1216, 1215, 884, 883, 882, 881, 880, 879, 878, 877, 876, 875, 874, 873, 872, 871, 870, 944, 943, 942, 941, 940, 939, 938, 937, 936, 935, 934, 933, 932, 931, 930, 1245, 1246, 1247, 1248, 1249, 1250, 1251, 1252, 1253, 1254, 1255, 1256, 1257, 1258, 1259, 1019, 1018, 1017, 1016, 1015, 1014, 1013, 1012, 1011, 1010, 1009, 1008, 1007, 1006, 1005, 914, 913, 912, 911, 910, 909, 908, 907, 906, 905, 904, 903, 902, 901, 900, 915, 916, 917, 918, 919, 920, 921, 922, 923, 924, 925, 926, 927, 928, 929, 1004, 1003, 1002, 1001, 1000, 999, 998, 997, 996, 995, 994, 993, 992, 991, 990, 989, 988, 987, 986, 985, 984, 983, 982, 981, 980, 979, 978, 977, 976, 975, 974, 973, 972, 971, 970, 969, 968, 967, 966, 965, 964, 963, 962, 961, 960, 959, 958, 957, 956, 955, 954, 953, 952, 951, 950, 949, 948, 947, 946, 945, 1094, 1093, 1092, 1091, 1090, 1089, 1088, 1087, 1086, 1085, 1084, 1083, 1082, 1081, 1080, 1079, 1078, 1077, 1076, 1075, 1074, 1073, 1072, 1071, 1070, 1069, 1068, 1067, 1066, 1065]
    newarr = [0 for i in range(1260)]
    
    for i in range(1260):
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

    # File path for the text file
    file_path = 'led_text_file.txt'

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

if __name__ == '__main__':
    t_socket = threading.Thread(target=start_server)
    t_socket.start()
    t_socket.join()