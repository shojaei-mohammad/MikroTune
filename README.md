
# MikroTune: Automated Frequency and Bandwidth Tester for MikroTik Devices

## Description
MikroTune is a Python-based tool created to help network administrators and engineers in testing various frequencies on MikroTik devices. The software cycles through given frequency ranges, inspects the connection and signal quality, and then carries out a bandwidth test under the best conditions.

## Features
- **User-friendly CLI**: Effortlessly input device and test parameters.
- **Custom Frequency Ranges**: Includes default values.
- **Configurable Bandwidth Parameters**: Define protocol, direction, limit, and duration.
- **External JSON Configuration**: Set values for signal strength and ping thresholds.
- **Automated Frequency Adjustments**: Ensure station registration is active.
- **Data Validations**: Signal strength and ping response time checks prior to bandwidth tests.
- **Logging**: Detailed test results for further analysis.

## Usage
Execute the script and adhere to the CLI prompts to provide the necessary parameters. The results will be saved to a predefined output file.

## Disclaimer
Use MikroTune in a controlled setting before implementing it in a live environment. Wrong usage or misconfigurations can interrupt network services. Abide by local laws when adjusting frequencies.


## Date of Creation
September 2, 2023

## Getting Started

1. **Prerequisites**: Install the necessary Python libraries:

2. **Setup**:
- Place `config.json` in the same directory as the script. This file should contain parameters such as wait times and valid ping times.
- Ensure the MikroTik device has API access enabled.

3. **Execution**:
- Navigate to the directory where the script resides.
- Run the script:
- Follow the command-line prompts to input required parameters.

4. **Output**:
- Results are stored in the 'Results.txt' file within the same directory.

## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## License

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)



## Authors

- [@shojaei-mohammd](https://www.github.com/shojaei-mohammad)






