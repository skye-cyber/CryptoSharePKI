import os
import platform
import subprocess
import sys
from urllib.request import urlretrieve

import requests

# Platform-specific paths
current_os = platform.system().lower()

# https://slproweb.com/download/Win64OpenSSL_Light-3_4_0.exe


def download_openssl():
    # Correctly format the filename based on the version and architecture
    filename = os.path.join("src", "Win64OpenSSL_Light-3_4_0.exe")

    download_path = os.path.join(os.getcwd(), filename)

    if os.path.exists(download_path):
        print("Found OpenSSL installer...")
        return download_path
    elif os.path.exists(download_path):
        print("Downloaded file is incomplete or corrupted. Restarting download")

    try:
        url = "https://slproweb.com/download/Win64OpenSSL_Light-3_4_0.exe"
        print("Downloading OpenSSL installer...")
        # Verify if the URL is reachable before downloading
        response = requests.head(url)
        if response.status_code != 200:
            print(f"Error: Unable to find the file at {url}")
            sys.exit(1)
        else:
            content_length = float(response.headers.get(
                'content-length', 0)) / (1024 * 1024)
            print(f"Downloading: {content_length:.2f}MB")
            urlretrieve(url, download_path)
            print(f"OpenSSL installer downloaded to {download_path}")
        return download_path
    except Exception as e:
        print(f"Error downloading OpenSSL: {e}")
        sys.exit(1)


def run_installer(installer_path):
    print("Running OpenSSL installer...")
    try:
        subprocess.run([installer_path, "/silent", "/verysilent",
                       "/sp-", "/suppressmsgboxes"], check=True)
        print("OpenSSL installation completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running OpenSSL installer: {e}")
        sys.exit(1)


def add_to_path(open_ssl_bin_path):
    print("Adding OpenSSL to PATH environment variable...")
    try:
        # Use os.environ to modify PATH dynamically in the script
        os.environ["PATH"] += os.pathsep + open_ssl_bin_path
        print("OpenSSL added to PATH.")
    except Exception as e:
        print(f"Error adding OpenSSL to PATH: {e}")
        sys.exit(1)


def verify_installation():
    print("Verifying OpenSSL installation...")
    try:
        result = subprocess.run(['openssl', 'version'],
                                check=True, capture_output=True, text=True)
        print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error verifying OpenSSL installation: {e}")
        sys.exit(1)


def print_add_path_instructions():
    """Prints instructions on how to add a path to the system environment variable in Windows."""
    print(r"""
To add a path to the system environment variable in Windows, follow these steps:

1. Open the Start menu and search for 'Environment Variables'.
2. Click on 'Edit the system environment variables'.
3. In the System Properties window, click on the 'Environment Variables' button.
4. Under 'System variables', scroll down and find the 'Path' variable.
5. Select the 'Path' variable and click on the 'Edit' button.
6. Click on the 'New' button and enter the path you want to add.
7. Add 'C:\Program Files\OpenSSL-Win64\bin' in the field
8. Click on the 'OK' button to close the 'Edit environment variable' window.
9. Click on the 'OK' button to close the 'Environment Variables' window.
10. Click on the 'OK' button to close the System Properties window.
11. Open a new Command Prompt window for the changes to take effect.
    """)


def main():
    installer_path = download_openssl()
    run_installer(installer_path)

    # Adjust this path if necessary
    open_ssl_bin_path = r'C:\Program Files\OpenSSL-Win64\bin'
    add_to_path(open_ssl_bin_path)
    verify_installation()
    print_add_path_instructions()


if __name__ == "__main__":
    if current_os == "linux":
        main()
    else:
        print("This is an OpenSSL installation for Windows only")
