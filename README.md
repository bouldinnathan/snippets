# Easy Mode Python Utility README

## Introduction

The Easy Mode Python utility is a versatile script designed to simplify Python package management and multi-threading tasks for developers. It provides a set of classes and functions aimed at automating common tasks such as package installation, file reading, API calls, and threading operations.

## Features

- **Easy_installer**: Automates the installation of Python packages and external tools.
- **Generic_threader & gt**: Simplifies the process of applying a function across multiple data points in parallel, using threading for efficiency.
- **Read_file**: A utility function for reading files with automatic character encoding detection.
- **API_gen**: A class for generating and managing API calls with rate limiting.
- **Crypto**: Facilitates asynchronous API calls to cryptocurrency exchanges.
- **Selenium_prep**: Assists in setting up Selenium WebDriver for automated web browsing.

## Installation

Before using this script, ensure you have Python installed on your system. Clone the repository or download `easy_mode.py` directly from GitHub. No additional installation steps are required, as the script is self-contained.

## Usage

### Easy_installer

```python
from easy_mode import Easy_installer

# To install a package
installer = Easy_installer()
installer.easy("package_name")

# To install from a URL
installer.easy("https://github.com/example_repo")
```

### Generic_threader & gt (Shorthand for Generic Threader)

```python
from easy_mode import generic_threader, gt

# Define a function to run in parallel
def example_function(data):
    # Process data
    return data

# Use generic_threader or gt for parallel processing
result = gt(example_function, data_list, thread_count=4)
```

### Read_file

```python
from easy_mode import read_file

# Read a text file
text = read_file("path/to/your/file.txt")
```

### API_gen

```python
from easy_mode import api_gen

api = api_gen()
api.add("https://api.example.com/data", headers={"Authorization": "Bearer token"}, timer=1)

# Fetch data
for data in api.call_api():
    print(data)
```

### Crypto

```python
from easy_mode import Crypto

crypto = Crypto()
result = crypto.get_simple(['BTC/USD'], ['binance'])
print(result)
```

### Selenium_prep

```python
from easy_mode import selenium_prep

# Download and setup Selenium WebDriver
driver_path = selenium_prep(version="Latest")
```

## Contributing

Contributions are welcome! If you have suggestions or improvements, feel free to fork the repository and submit a pull request.

## License

This project is open-source and available under the MIT License.

For more detailed examples and advanced usage, refer to the inline comments within the `easy_mode.py` script.
