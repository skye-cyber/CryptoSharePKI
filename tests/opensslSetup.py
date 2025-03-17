import ctypes
import os
import platform
import subprocess
import sys
from urllib.request import urlretrieve

import requests

# Platform-specific paths
current_os = platform.system().lower()

# https://slproweb.com/download/Win64OpenSSL-3_4_0.exe   =221MB
# https://slproweb.com/download/Win64OpenSSL_Light-3_4_0.exe


def download_openssl(version, architecture):
    print("Downloading OpenSSL installer...")
    base_url = "https://slproweb.com/download/"
    # Correctly format the filename based on the version and architecture
    filename = f"Win{architecture}OpenSSL_Light-{version}.exe"
    url = f"{base_url}{filename}"
    download_path = os.path.join(os.getcwd(), filename)
    # Check if the file exists and is at least 221 MB
    if os.path.exists(download_path):  # and os.path.getsize(download_path) >= 221 * 1024 * 1024:  # 221 MB in bytes
        return download_path
    elif os.path.exists(download_path):
        print("Downloaded file is incomplete or corrupted. Restarting download")

    try:
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


def main():
    version = "3_4_0"  # Replace with the version you want to install
    architecture = "64"  # 32 for 32-bit, 64 for 64-bit
    installer_path = download_openssl(version, architecture)
    run_installer(installer_path)

    # Adjust this path if necessary
    open_ssl_bin_path = r'C:\Program Files\OpenSSL-Win64\bin'
    add_to_path(open_ssl_bin_path)
    verify_installation()


if __name__ == "__main__":
    if current_os == "windows":
        main()
    else:
        print("This is an OpenSSL installation for Windows only")
