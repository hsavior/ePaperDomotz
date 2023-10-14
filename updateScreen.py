#!/usr/bin/python3
# -*- coding:utf-8 -*-
import sys
import os
import time
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import logging
import requests
import json
import epaper  # Import the epaper library from Waveshare
import netifaces

logging.basicConfig(level=logging.DEBUG)

# Define constants
FONT_DIR = './fonts/'
IMAGE_DIR = './images/'

# Define global variables for API Key and Agent ID
API_KEY = None
AGENT_ID = None
API_URL = None

# Load API configuration from the external file
try:
    with open('updateScreen.conf', 'r') as config_file:
        config = json.load(config_file)
        API_KEY = config.get('api_key')
        AGENT_ID = config.get('agent_id')
        API_URL = config.get('api_url')
except FileNotFoundError:
    print("Configuration file 'updateScreen.conf' not found.")
except json.JSONDecodeError as e:
    print(f"Error parsing JSON in 'updateScreen.conf': {e}")

def fetch_speeds():
    global API_KEY, AGENT_ID, API_URL  # Access the global variables
    if API_KEY and AGENT_ID and API_URL:
        try:
            headers = {'Accept': 'application/json', 'X-Api-Key': API_KEY}
            url = f'{API_URL}/public-api/v1/agent/{AGENT_ID}/history/network/speed'
            r = requests.get(url, params={}, headers=headers)
            r.raise_for_status()
            apiResponse = r.json()

            if apiResponse:
                speedDown = apiResponse[-1]['values'][0]
                speedDown = float(speedDown) / 1000000
                speedDown = round(speedDown, 2)
                speedUp = apiResponse[-1]['values'][1]
                speedUp = float(speedUp) / 1000000
                speedUp = round(speedUp, 2)
                return speedDown, speedUp
            else:
                print("API response is empty.")
                return None, None
        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the API request: {e}")
            return None, None
    else:
        print("API key and/or Agent ID and/or API URL not found in the configuration file.")
        return None, None


def uptime():
    days_ago = 30
    current_time = datetime.now()
    days_ago_time = current_time - timedelta(days=days_ago)
    timestamp = int(days_ago_time.timestamp())
    global API_KEY, AGENT_ID, API_URL  # Access the global variables
    if API_KEY and AGENT_ID and API_URL:
        try:
            headers = {'Accept': 'application/json', 'X-Api-Key': API_KEY}
            url = f'{API_URL}/public-api/v1/agent/{AGENT_ID}/uptime?from={timestamp}'
            r = requests.get(url, params={}, headers=headers)
            r.raise_for_status()
            apiResponse = r.json()
            uptime = float(apiResponse['uptime'])
            uptime = round(uptime, 2)  # Round to two decimal places
            return uptime
        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the API request: {e}")
            return None

def status():
    global API_KEY, AGENT_ID, API_URL  # Access the global variables
    if API_KEY and AGENT_ID and API_URL:
        headers = {'Accept': 'application/json', 'X-Api-Key': API_KEY}
        url = f'{API_URL}/public-api/v1/agent/{AGENT_ID}'

        try:
            r = requests.get(url, params={}, headers=headers)
            r.raise_for_status()
            apiResponse = r.json()
            status = apiResponse['status']['value']
            return status
        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the API request: {e}")
            return None
    else:
        print("API key and/or Agent ID and/or API URL not found in the configuration file.")
        return None

def localip(interface_name='wlan0'):
    try:
        # Get the IP address associated with the specified network interface
        ipaddr = netifaces.ifaddresses(interface_name)[netifaces.AF_INET][0]['addr']
        return ipaddr
    except (ValueError, KeyError, IndexError) as e:
        print(f"Error retrieving local IP address for {interface_name}: {e}")
        return None


def devices():
    global API_KEY, AGENT_ID, API_URL  # Access the global variables

    # Check if API_KEY and AGENT_ID are defined
    if API_KEY is None or AGENT_ID is None or API_URL is None:
        print("API key and/or Agent ID and/or API URL not found in global variables.")
        return None

    headers = {'Accept': 'application/json', 'X-Api-Key': API_KEY}
    url = f'{API_URL}/public-api/v1/agent/{AGENT_ID}/device'

    try:
        r = requests.get(url, params={}, headers=headers)
        data = r.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the API request: {e}")
        return None

    total_devices = len(data)
    i = 0
    important_down = 0
    important_total = 0
    common_total = 0
    common_down = 0
    total_online = 0
    encountered_main_ids = []  # List to store encountered main_id values

    while i < total_devices:
        device = data[i]
        main_id = device.get('main_id')

        if main_id is not None and main_id in encountered_main_ids:
            # Skip processing this device
            i += 1
            continue
        elif main_id is not None:
            encountered_main_ids.append(main_id)

        status = device.get('status')  # Check if 'status' key exists
        if status is not None:
            protocol = device['protocol']
            if protocol == "CLUSTER":
                i += 1
            else:
                importance = device['importance']

                if importance == "VITAL":
                    important_total += 1
                    if status == "DOWN":
                        important_down += 1
                elif importance == "FLOATING":
                    common_total += 1
                    if status == "DOWN":
                        common_down += 1
                if status == "ONLINE" or status == "OFFLINE":
                    display_name = device['display_name']
                    print(f"Display Name: {display_name} ", device['id'])
                    total_online += 1
            i += 1
        else:
            i += 1
    return (
        str(total_devices),
        str(total_online),
        str(important_total),
        str(important_down),
        str(common_total),
        str(common_down)
    )

def init_epd():
    # Initialize the e-Paper display using the Waveshare epaper library
    epd = epaper.epaper('epd2in9bc').EPD()
    return epd

def load_fonts():
    font18 = ImageFont.truetype(os.path.join(FONT_DIR, 'rockwell.ttf'), 18)
    font14 = ImageFont.truetype(os.path.join(FONT_DIR, 'rockwell_bold.ttf'), 14)
    font10 = ImageFont.truetype(os.path.join(FONT_DIR, 'rockwell_bold.ttf'), 10)
    connectIcon = ImageFont.truetype(os.path.join(FONT_DIR, 'globe_icons.ttf'), 45)
    return font18, font14, font10, connectIcon

def fetch_data():
    # Fetch download and upload speeds from the API
    download_speed, upload_speed = fetch_speeds()
    # Check if the speeds were fetched successfully
    if download_speed is not None and upload_speed is not None:
        # Format the speeds as strings
        speedDown = f'{download_speed}'
        speedUp = f'{upload_speed}'
    else:
        # Use default values or indicate an error if speeds couldn't be fetched
        speedDown = 'N/A'
        speedUp = 'N/A'

    status_value = status()
    stat = status_value if status_value is not None else 'UNKNOWN'

    ip_value = localip()
    ip_now = ip_value if ip_value is not None else 'UNKNOWN'

    uptime_now = uptime()
    uptime_now = f'{uptime_now}' if uptime_now is not None else 'UNKNOWN'

    devices_data = devices()
    if devices_data is not None:
        total_devices, total_online, important_total, important_down, common_total, common_down = devices_data
    else:
        total_online = 'N/A'
        important_down = 'N/A'

    return (
        speedDown, speedUp, stat, ip_now,
        total_online, important_down, uptime_now
    )

def draw_on_image(image_black, image_red, data, fonts):
    draw_black = ImageDraw.Draw(image_black)
    draw_red = ImageDraw.Draw(image_red)

    font18, font14, font10, connectIcon = fonts

    # Ensure 'data' contains at least 9 values (provide default values for missing data)
    data += ('N/A',) * (10 - len(data))

    (
        devices_online, important_devices_offline, download_label,
        upload_label, download_speed, upload_speed,
        status, connection_icon, ip, uptime_now
    ) = data

    # Draw text and data on images at the exact positions
    draw_black.text((30, 0), 'Devices Online:', font=font14, fill=0)  # Black text
    draw_black.text((30, 14), 'Important Devices Down:', font=font14, fill=0)  # Black text
    draw_black.text((2, 38), 'Download:', font=font18, fill=0)  # Black text
    draw_black.text((2, 58), 'Upload:', font=font18, fill=0)  # Black text
    draw_black.text((2, 78), 'Uptime:', font=font18, fill=0)  # Black text

    draw_red.text((90, 38), download_speed, font=font18, fill=0)  # Red text
    draw_red.text((66, 58), upload_speed, font=font18, fill=0)  # Red text
    draw_red.text((66, 78), f'{uptime_now}%', font=font18, fill=0)  # Red text
    draw_red.text((147, 0), devices_online, font=font14, fill=0)  # Devices Online
    draw_red.text((210, 14), important_devices_offline, font=font14, fill=0)  # Important Devices Offline


    if status == "OFFLINE":
        draw_red.text((245, 40), status, font=font10, fill=0)  # Print Status DOWN in RED
        draw_red.text((245, 0), 'c', font=connectIcon, fill=0)  # Connection Icon in RED
    else:
        draw_black.text((245, 40), status, font=font10, fill=0)  # Print Status ONLINE in BLACK
        draw_black.text((245, 0), 'c', font=connectIcon, fill=0)  # Connection Icon in BLACK

    draw_black.text((2, 110), 'Settings:', font=font14, fill=0)  # Black text
    draw_red.text((63, 110), f'http://{ip}:5000', font=font14, fill=0)  # Black text

def main():
    time.sleep(60)
    logging.info("Rack Panel ePaper")

    # Initialize e-Paper display
    epd = init_epd()

    # Load fonts
    fonts = load_fonts()

    try:
        while True:
            # Fetch data
            speedDown, speedUp, stat, ip_now, total_online, important_down, uptime_now = fetch_data()

            # Create clean black and red frames
            image_black = Image.open(os.path.join(IMAGE_DIR, 'domotz_b.bmp'))
            image_red = Image.open(os.path.join(IMAGE_DIR, 'domotz_r.bmp'))

            # Draw data on images
            data = (
                total_online,
                important_down,
                'Download:',
                'Upload:',
                speedDown + ' Mbps',
                speedUp + ' Mbps',
                stat,
                'c',
                ip_now,
                uptime_now
            )
            draw_on_image(image_black, image_red, data, fonts)

            # Display on e-Paper using Waveshare library
            epd.init()
            epd.display(epd.getbuffer(image_black), epd.getbuffer(image_red))
            epd.sleep()

            # Sleep for 30 minutes (1800 seconds)
            time.sleep(1740)

    except KeyboardInterrupt:
        logging.info("Keyboard interrupt, exiting.")
    finally:
        dt = datetime.now()
        print("e-Paper Updated", dt)

if __name__ == "__main__":
   main()
