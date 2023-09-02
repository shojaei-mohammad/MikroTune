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
    # This is a placeholder. The real command to set the frequency might differ.
    api.get_binary_resource("/").call("set/frequency", {"frequency": frequency})


def check_station_registered(api, wait_time):
    # Placeholder logic to check if station is registered
    # We'll wait for the provided duration and then check if the station is registered.
    # The exact method to check station registration will depend on the RouterOS commands available.
    time.sleep(wait_time)
    # For example:
    # registration_status = api.get_binary_resource('/').call('interface/wireless/registration-table/get')
    # return 'station_name' in registration_status


def check_ping_and_signal(api, valid_ping, valid_signal):
    # Use the provided RouterOS API commands to check the ping and signal strength.
    # The exact methods might differ based on the RouterOS version and available commands.
    ping_response = api.get_binary_resource("/").call(
        "ping", {"address": "station_ip", "count": "1"}
    )
    # Assuming the ping response contains an 'avg-rtt' field:
    ping_value = int(ping_response[0]["avg-rtt"])
    # Placeholder for signal strength:
    # signal_response = api.get_binary_resource('/').call('get_signal_strength_command')
    # signal_value = int(signal_response['signal_strength'])

    return ping_value <= valid_ping  # and signal_value >= valid_signal


def log_results_to_file(results, file_path):
    with open(file_path, "a") as f:
        f.write(results)


def main():
    ap_details, frequency_range, bandwidth_test_params = gather_info()
    config = read_config_from_json("config.json")
    connection = routeros_api.RouterOsApiPool(
        ap_details["IP"],
        username=ap_details["username"],
        password=ap_details["password"],
        port=ap_details["port"],
    )
    api = connection.get_api()

    for freq in range(frequency_range[0], frequency_range[1] + 1, 5):
        set_frequency(api, freq)

        if not check_station_registered(api, config["wait_for_regisration"]):
            continue

        if not check_ping_and_signal(
            api, config["valid_ping_time"], config["valid_tx_signal"]
        ):
            continue

        # Do the bandwidth test here

    connection.disconnect()


if __name__ == "__main__":
    main()
