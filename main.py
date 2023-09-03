"""
MikroTune: Automated Frequency and Bandwidth Tester for MikroTik Devices

Description:
    MikroTune is a Python-based tool designed to assist network administrators
    and engineers in testing different frequencies on MikroTik devices. The
    program iterates through specified frequency ranges, checks the connectivity
    and signal quality, and then performs a bandwidth test under optimal conditions.

Features:
    1. User-friendly CLI for entering device and test parameters.
    2. Support for custom frequency ranges with default values.
    3. Configurable bandwidth test parameters like protocol, direction, limit, and duration.
    4. Utilizes external JSON configuration for values such as signal and ping thresholds.
    5. Automated frequency changes with checks for station registration.
    6. Signal strength and ping response time validations before bandwidth tests.
    7. Comprehensive logging of test results for analysis.

Usage:
    Simply run the script and follow the CLI prompts to input necessary parameters.
    Results will be logged in a specified output file.

Disclaimer:
    Always use MikroTune in a controlled environment before deploying in a production setting.
    Improper use or incorrect configurations may disrupt network services. Ensure compliance
    with local regulations when adjusting frequencies.

Author:
    [Your Name / Your Organization]
"""

from typing import Dict

import routeros_api
import json
import time
import threading


class ConcurrentUtility:
    def __init__(self):
        self.values = {}  # A dictionary to store multiple concurrent values
        self.is_running = True

    def update_value(self, key, api_call, interval=5, **api_call_params):
        while self.is_running:
            response = api_call(**api_call_params)
            self.values[key] = response
            time.sleep(interval)


def gather_info():
    """
    Interactively gather information from the user about the AP and bandwidth test parameters.

    Returns:
    - tuple: A tuple containing dictionaries for AP details, frequency range, and bandwidth test parameters.
    """

    # Welcome message
    print("Welcome to the MikroTune Configuration Wizard!")
    input("Press Enter to begin...")

    # AP Details
    ap_details = {"IP": input("\nEnter AP IP Address: ")}

    while True:
        ap_details["username"] = input("Enter AP username: ")
        ap_details["password"] = input("Enter AP password: ")
        try:
            ap_details["port"] = int(input("Enter AP port (default 8728): ") or 8728)
            break
        except ValueError:
            print("Please enter a valid port number.")

    # Frequency Range
    frequency_range = input("\nEnter frequency range (default 4900-6100): ").split("-")
    if not frequency_range or len(frequency_range) != 2:
        frequency_range = [4900, 6100]
    else:
        frequency_range = [int(freq) for freq in frequency_range]

    # Bandwidth Test Parameters
    bandwidth_test_params: dict[str, str | None | int] = {
        "station_IP": input("\nEnter Station IP Address: ")
    }

    # Choose protocol with number
    protocol_options = ["tcp", "udp"]
    for idx, protocol in enumerate(protocol_options, start=1):
        print(f"{idx}. {protocol.upper()}")
    while True:
        choice = input("Choose Protocol (1 for TCP / 2 for UDP): ")
        if choice in ["1", "2"]:
            bandwidth_test_params["protocol"] = protocol_options[int(choice) - 1]
            break
        else:
            print("Invalid choice. Please choose 1 or 2.")

    # Choose direction with number
    direction_options = ["send", "receive", "both"]
    for idx, direction in enumerate(direction_options, start=1):
        print(f"{idx}. {direction}")
    while True:
        choice = input("Choose Direction (1 for send / 2 for receive / 3 for both): ")
        if choice in ["1", "2", "3"]:
            bandwidth_test_params["direction"] = direction_options[int(choice) - 1]
            break
        else:
            print("Invalid choice. Please choose 1, 2, or 3.")

    # Limit in MB
    limit_input = input("\nEnter limit in Mb (default None): ")
    if limit_input:
        try:
            bandwidth_test_params["limit"] = int(limit_input)
        except ValueError:
            bandwidth_test_params["limit"] = None
    else:
        bandwidth_test_params["limit"] = None

    # Duration
    while True:
        try:
            bandwidth_test_params["duration"] = int(
                input("\nEnter test duration in seconds: ")
            )
            break
        except ValueError:
            print("Please enter a valid duration in seconds.")

    return ap_details, frequency_range, bandwidth_test_params


def read_config_from_json(json_file_path):
    """
    Read configuration details from a given JSON file.

    Args:
    - json_file_path (str): Path to the JSON configuration file.

    Returns:
    - dict: A dictionary containing the configuration details.
    """
    with open(json_file_path, "r") as f:
        config_data = json.load(f)

    return config_data["config"]


def set_frequency(api, frequency):
    resource = api.get_resource("/interface/wireless")
    wireless_interfaces = resource.get()

    for interface in wireless_interfaces:
        try:
            print(frequency)
            resource.set(id=interface["id"], frequency=str(frequency))
            print(f"Frequency set to {frequency} for interface {interface['id']}")
        except Exception as e:
            print(f"Error setting frequency for interface {interface['id']}: {e}")


def update_ping_time(api, station_address, count=4):
    # Convert station_address and count to bytes before sending
    print(type(station_address), type(count))
    try:
        ping_response = api.get_resource("/").call(
            "ping", {"address": station_address, "count": "4"}
        )
        return float(ping_response["avg-rtt"])
    except Exception as e:
        print(f"Error while pinging: {e}")
        return float("inf")  # return a large number to signify an error


def check_station_registered(api, wait_time, config_ping_value, station_address):
    utility = ConcurrentUtility()
    registration_resource = api.get_resource("interface/wireless/registration-table")
    start_time = time.time()

    # Start a separate thread to ping the station and update the average ping time
    # threading.Thread(
    #     target=utility.update_value,
    #     args=("avg_ping_time", update_ping_time, 5),
    #     kwargs={"api": api, "station_address": station_address},
    # ).start()

    while time.time() - start_time < wait_time:
        registration_statuses = registration_resource.get()
        print(registration_statuses)  # For debugging

        for registration_status in registration_statuses:
            # Check if the station has registered
            if "station_name" in registration_status:
                # Check signal strength
                signal_strength = int(
                    registration_status.get("signal-strength", "-999")
                )  # default to a low value if not found
                if signal_strength > -70:
                    # Recall the current average ping time
                    avg_ping_time = utility.values.get("avg_ping_time", float("inf"))
                    print(f"Average ping time: {avg_ping_time}")  # For debugging

                    # Check both conditions: signal strength and ping average
                    if signal_strength > -70 and avg_ping_time < config_ping_value:
                        utility.is_running = False
                        return True

        # Wait a short while before checking again
        time.sleep(5)

    # Stop the ping thread
    utility.is_running = False

    # If the conditions aren't met within the wait_time, return False.
    return False


def log_results_to_file(results, file_path):
    with open(file_path, "a") as f:
        f.write(results)


def main():
    # ap_details, frequency_range, bandwidth_test_params = gather_info()
    config = read_config_from_json("config.json")
    # connection = routeros_api.RouterOsApiPool(
    #     ap_details["IP"],
    #     username=ap_details["username"],
    #     password=ap_details["password"],
    #     port=ap_details["port"],
    # )
    connection = routeros_api.RouterOsApiPool(
        "192.168.9.27", username="22", password="22", plaintext_login=True
    )
    # print(ap_details["IP"], ap_details["username"], ap_details["password"],)
    api = connection.get_api()

    frequency_range = [5000, 5100]
    for freq in range(frequency_range[0], frequency_range[1] + 1, 5):
        set_frequency(api, freq)

        if not check_station_registered(
            api,
            config["wait_for_registration"],
            config["valid_ping_time"],
            "192.168.9.28",
        ):
            continue

        # Do the bandwidth test here

    connection.disconnect()


if __name__ == "__main__":
    main()
