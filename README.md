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
- **exponential_backoff**: Retries transient failures with capped delays, jitter, and cancellation.
- **resolve_file_location**: Resolves local paths and already-mounted SMB locations, including KDE/KIOFuse.

## Installation

Before using this script, ensure you have Python installed on your system. Clone the repository or download `easy_mode.py` directly from GitHub. No additional installation steps are required, as the script is self-contained.

## Usage

### Easy_installer

```python
from easy_mode import Easy_installer

# To install a package
installer = Easy_installer()
installer.easy("selenium")
installer.easy("platform")

# To install where import name and pip install name are different
installer.easy("beautifulsoup4",import_name="bs4")

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
driver = selenium_prep(version="Latest")
driver.get("https://google.com")
```

### Exponential backoff

The new helpers require Python 3.10+ and use **only the standard library**.
`easy_mode.py` imports each helper only when its function is called. Importing
`easy_mode` does not load these modules or require their files for older APIs.
No Pillow, NumPy, Flask, Selenium, or other optional packages are needed.

Clone this repository, or keep `exponential_backoff.py` and/or `file_locations.py`
beside `easy_mode.py` according to which functions you use. Each helper module
also works independently of `easy_mode.py` and of the other helper.

```python
from easy_mode import exponential_backoff

def read_report():
    with open("report.csv", "rb") as report:
        return report.read()

data = exponential_backoff(
    read_report,
    retries=5,       # Additional attempts after the first call.
    delay=1.0,       # 1, 2, 4, 8, 16 seconds, plus up to 20% jitter.
    max_delay=30.0,  # Cap includes jitter.
)
```

The default predicate retries transient filesystem/network errors such as
timeouts, resets, stale handles, and temporary I/O errors. Missing files,
permissions, and invalid input fail immediately. The final exception is raised
unchanged. Retries reset for each call; there is no global counter.

To customize retryable exceptions, pass `retry_if=lambda error: ...`. For custom
logging, pass `on_retry(error, retry_number, delay_seconds, label)`, or set
`on_retry=None` to silence it. For worker cancellation, pass a shared
`threading.Event` as `stop_event`; setting it interrupts waits and raises
`RetryCancelled`. It cannot forcibly interrupt an operation already in progress.

Direct imports and shared worker settings are also available:

```python
from exponential_backoff import exponential_backoff, RetryPolicy, RetryCancelled

policy = RetryPolicy(retries=5)
# Use policy.run(operation, "description") across threads.
# Call policy.stop.set() when shutting down.
```

### File and SMB locations

```python
from easy_mode import resolve_file_location

file_path, source_uri = resolve_file_location("./report.csv")
folder_path, source_uri = resolve_file_location(
    "smb://reader@fileserver.example/books/Library With Spaces",
    require_directory=True,
)
```

The return value is `(pathlib.Path, canonical_smb_uri_or_None)`. Existing files
and folders are accepted; `require_directory=True` restricts it to folders.
Both literal spaces and URL-encoded names are supported. The helpers don't
contain application-specific server addresses or book metadata.

Linux discovery covers CIFS/SMB, GNOME/GVfs, and KDE/Dolphin KIOFuse, including
changing per-session mount paths. Windows URLs use the current UNC connection.
The resolver uses existing mounts: it never logs in, requests credentials,
installs anything, or creates a mount. Run as the user that opened the share.

For other mount systems, macOS, or manually mapped locations, pass
`mount_path="/path/to/the/full/target"`. It must point to the complete supplied
file/folder location, not merely the share root. Missing/inaccessible locations
raise `ValueError`. Server aliases and IP addresses are matched as written;
the resolver does not perform DNS lookups.

You can also import directly with
`from file_locations import resolve_file_location`. The helpers stay separate;
backoff can wrap a subsequent read when needed:

```python
file_path, _ = resolve_file_location(
    "smb://reader@fileserver.example/books/Library With Spaces/cover.jpg"
)
data = exponential_backoff(file_path.read_bytes, label="reading cover")
```

Run the helper tests without installing any packages:

```sh
python -m unittest discover -s tests -v
```

## Contributing

Contributions are welcome! If you have suggestions or improvements, feel free to fork the repository and submit a pull request.

## License

This project is open-source and available under the MIT License.

For more detailed examples and advanced usage, refer to the inline comments within the `easy_mode.py` script.
