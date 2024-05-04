import requests
import time

# esp-32 that is hosting the touch sensor input ip:
url = 'http://10.42.200.104:80/'

def get_sensor_status():
    try:
        response = requests.get(url, timeout=2)  # Send a GET request to the ESP32
        if response.status_code == 200:
            print("Response from ESP32:", response.text)  # Print the response from ESP32
        else:
            print("Failed to retrieve data, status code:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Error connecting to the server:", e)

if __name__ == '__main__':
    while True:
        get_sensor_status()  # Check sensor status
        time.sleep(1)  # Wait for 1 second before checking again
