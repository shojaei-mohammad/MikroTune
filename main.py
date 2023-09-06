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
    Mohammad Shojaei
    Contact: m.shojaei@hotmail.com

Date:
    Created on: September 2, 2023
"""
import datetime

import routeros_api
import json
import time


SHARED_DATA = {}


def gather_info():
    """
    Interactively gather information from the user about the AP and bandwidth test parameters.

    Returns:
    - tuple: A tuple containing dictionaries for AP details, frequency range, and bandwidth test parameters.
    """

    # Welcome message
    message = """
      ___       __   __         ___    ___  __                   __   __  ___            ___ 
|  | |__  |    /  ` /  \  |\/| |__      |  /  \     |\/| | |__/ |__) /  \  |  |  | |\ | |__  
|/\| |___ |___ \__, \__/  |  | |___     |  \__/     |  | | |  \ |  \ \__/  |  \__/ | \| |___ 
                                                                                                                                                                                                                                                                                                                                                                                                                                                    
    """
    print(message)
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

    # Specify Limit or Unlimited
    specify_limit = input("\nDo you want to specify a limit? (yes/no) [no]: ").lower()
    if specify_limit == "yes":
        loca_tx = input("Enter local Tx limit in Mbps (default unlimited): ")
        remote_tx = input("Enter remote TX limit in Mbps (default unlimited): ")

        bandwidth_test_params["local_tx"] = int(loca_tx) if loca_tx else "unlimited"
        bandwidth_test_params["remote_tx"] = (
            int(remote_tx) if remote_tx else "unlimited"
        )
    else:
        bandwidth_test_params["local_tx"] = "unlimited"
        bandwidth_test_params["remote_tx"] = "unlimited"

    # Duration
    while True:
        try:
            bandwidth_test_params["duration"] = (
                int(input("\nEnter test duration in seconds: ")) + 1
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
            resource.set(id=interface["id"], frequency=str(frequency))
            print(f"Frequency set to {frequency} for interface {interface['name']}")
        except Exception as e:
            print(f"Error setting frequency for interface {interface['name']}: {e}")


def update_ping_time(api, ap_address, station_address, count=4):
    """
    Pings the station from the access point (AP) to get the average round-trip time (RTT).

    Args:
    - api (object): An instance or object representing the API to interact with.
    - ap_address (str): IP Address of the Access Point.
    - station_address (str): IP Address of the Station to be pinged.
    - count (int, optional): Number of ping attempts. Defaults to 4.

    Returns:
    - float: Average RTT if successful, or a large number (float("inf")) indicating timeout or an error.

    Raises:
    - Exception: Any exception that occurs while pinging.
    """
    try:
        # Send ping requests via the API
        ping_responses = api.get_resource("/").call(
            "ping",
            {"address": station_address, "count": "4", "src-address": ap_address},
        )

        # Check if 'avg-rtt' exists in the last response
        if "avg-rtt" in ping_responses[-1]:
            # Extracting avg-rtt from the last dictionary in the list and stripping the 'ms'
            avg_rtt = float(ping_responses[-1]["avg-rtt"].rstrip("ms"))
            return avg_rtt
        else:
            # If 'avg-rtt' doesn't exist, it indicates a potential issue
            print("Ping timeout or other issues detected.")
            return float("inf")

    except Exception as e:
        print(f"Error while pinging: {e}")
        return float("inf")  # return a large number to signify an error


def check_station_registered(
    api, wait_time, config_ping_value, ap_address, station_address
):
    """
    Checks if a station is registered within a given wait time and meets specific ping and signal strength conditions.

    Args:
    - api (object): An instance or object representing the API to interact with.
    - wait_time (int): Time (in seconds) to wait and check for the station's registration.
    - config_ping_value (float): Threshold value for the average ping time.
    - ap_address (str): IP Address of the Access Point.
    - station_address (str): IP Address of the Station to be checked.

    Returns:
    - bool: True if station meets conditions, False otherwise.
    """
    registration_resource = api.get_resource("interface/wireless/registration-table")
    start_time = time.time()
    is_station_registered = False

    while time.time() - start_time < wait_time:
        registration_status = registration_resource.get()

        # Check if the station has registered based on list length
        if len(registration_status) > 0:
            is_station_registered = True

        # If the station is registered, start pinging
        if is_station_registered:
            print("Station registered, waiting for readiness!")
            time.sleep(20)
            print("Start pinging")
            avg_ping_time = update_ping_time(api, ap_address, station_address)
            SHARED_DATA["average_ping_time"] = avg_ping_time
            print(f"Average ping time: {avg_ping_time}")

            signal_strength = int(registration_status[0].get("signal-strength", "-999"))
            SHARED_DATA["signal"] = signal_strength

            # Check both conditions: signal strength and ping average
            if signal_strength > -70 and avg_ping_time < config_ping_value:
                return True
            else:
                # Exit the loop if station is ready but doesn't meet ping/signal conditions
                break

        # Wait a short while before checking again
        time.sleep(5)

    # If the conditions aren't met within the wait_time, return False.
    return False


def run_bandwidth_test(api, params):
    """
    Run the bandwidth test using the MikroTik RouterOS API.

    Args:
    - api (routeros_api.RouterOsApi): The API instance for RouterOS communication.
    - params (dict): Dictionary containing bandwidth test parameters.

    Returns:
    - dict: Dictionary containing bandwidth test results.
    """

    # Mapping for protocol
    protocol_map = {"tcp": "tcp", "udp": "udp"}

    # Preparing bandwidth test arguments
    test_args = {
        "address": params["station_IP"],
        "duration": str(params["duration"]),
        "protocol": protocol_map[params["protocol"]],
    }

    # Depending on direction, specify more arguments
    if params["direction"] == "send":
        test_args["direction"] = "transmit"
    elif params["direction"] == "receive":
        test_args["direction"] = "receive"
    elif params["direction"] == "both":
        test_args["direction"] = "both"

    # If local_tx and remote_tx are not 'unlimited', set them in test_args
    if params["local_tx"] != "unlimited":
        test_args["local-tx-speed"] = f"{params['local_tx']}M"

    if params["remote_tx"] != "unlimited":
        test_args["remote-tx-speed"] = f"{params['remote_tx']}M"

    try:
        test_results = api.get_resource("/tool").call("bandwidth-test", test_args)

        return test_results
    except Exception as e:
        print(f"Error while executing bandwidth test: {e}")
        return None


def main():
    ap_details, frequency_range, bandwidth_test_params = gather_info()
    config = read_config_from_json("config.json")
    connection = routeros_api.RouterOsApiPool(
        ap_details["IP"],
        username=ap_details["username"],
        password=ap_details["password"],
        port=ap_details["port"],
        plaintext_login=True,
    )

    api = connection.get_api()
    bps_fields = [
        "tx-current",
        "tx-10-second-avg",
        "tx-total-avg",
        "rx-current",
        "rx-10-second-average",
    ]
    for freq in range(frequency_range[0], frequency_range[1] + 1, 5):
        set_frequency(api, freq)

        if not check_station_registered(
            api,
            config["wait_for_registration"],
            config["valid_ping_time"],
            ap_details.get("IP"),
            bandwidth_test_params.get("station_IP"),
        ):
            continue
        test_time = datetime.datetime.now()
        print(f"Running test for frequency: {freq}MHz")
        result = run_bandwidth_test(api, bandwidth_test_params)
        average_ping_time = SHARED_DATA["average_ping_time"]
        signal = SHARED_DATA["signal"]
        ap_ip = ap_details.get("IP")
        station_ip = bandwidth_test_params.get("station_IP")
        # Prepare the headers and data lines
        headers = [
            "status",
            "duration",
            "tx-current",
            "tx-10-second-avg",
            "tx-total-avg",
            "rx-current",
            "rx-10-second-average",
            "rx-total-avg",
            "random-data",
            "direction",
            "conn-count",
            ".section",
            "local-cpu-load",
            "remote-cpu-load",
        ]

        with open("Results.txt", "a") as file:
            # Test Parameters Table
            file.write("+{:-^24}+{:-^26}+\n".format("", ""))
            file.write("| {:<23}| {:<25}|\n".format("Parameter", "Value"))
            file.write("+{:-^24}+{:-^26}+\n".format("", ""))
            file.write("| {:<23}| {:<25}|\n".format("Frequency", freq))
            file.write(
                "| {:<23}| {:<25}|\n".format("Average Ping Time", average_ping_time)
            )
            file.write("| {:<23}| {:<25}|\n".format("Signal", signal))
            file.write("| {:<23}| {:<25}|\n".format("AP IP", ap_ip))
            file.write("| {:<23}| {:<25}|\n".format("Station IP", station_ip))
            file.write("+{:-^25}+{:-^25}+\n\n".format("", ""))

            # Data Table Headers
            file.write(
                "| {:<13}| {:<9}| {:<11}| {:<17}| {:<13}| {:<11}| {:<17}| {:<13}| {:<12}| {:<9}| {:<10}| {:<8}| {:<15}| {:<15}|".format(
                    *headers
                )
            )
            file.write("\n")
            file.write(
                "+{:-^14}+{:-^10}+{:-^12}+{:-^18}+{:-^14}+{:-^12}+{:-^18}+{:-^14}+{:-^13}+{:-^10}+{:-^11}+{:-^9}+{:-^16}+{:-^16}+\n".format(
                    *[""] * len(headers)
                )
            )

            # Print data rows
            for entry in result:
                # Convert values from bps to Mbps
                for field in bps_fields:
                    if field in entry and entry[field] != "-":
                        entry[field] = (
                            float(entry[field]) / 1_000_000
                        )  # Convert to Mbps

                values = [entry.get(header, "-") for header in headers]
                data_line = "| {:<13}| {:<9}| {:<11}| {:<17}| {:<13}| {:<11}| {:<17}| {:<13}| {:<12}| {:<9}| {:<10}| {:<8}| {:<15}| {:<15}|\n".format(
                    *values
                )
                file.write(data_line)

            file.write(
                "+{:-^14}+{:-^10}+{:-^12}+{:-^18}+{:-^14}+{:-^12}+{:-^18}+{:-^14}+{:-^13}+{:-^10}+{:-^11}+{:-^9}+{:-^16}+{:-^16}+".format(
                    *[""] * len(headers)
                )
            )

        # Wait for the test duration plus an additional delay before moving to the next frequency
        time.sleep(bandwidth_test_params["duration"] + 3)

    connection.disconnect()


if __name__ == "__main__":
    main()
