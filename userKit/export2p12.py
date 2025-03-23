import os
import platform
import subprocess
import warnings
import configparser
import requests
import shutil
import sys
from utils.colors import (CYAN, GREEN, RED, RESET, YELLOW)


# Suppress the InsecureRequestWarning
warnings.filterwarnings(
    "ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

HOST_NAME = platform.node()  # Use the machine's hostname

# --------------Create a ConfigParser object--------------
config = configparser.ConfigParser()

# --------------Read the .ini file--------------
conf_path = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), "config.ini")
config.read(conf_path)


# --------------Helper function to set a default section--------------
def set_default_section(config, section):
    if section not in config:
        raise ValueError(
            f"Section '{section}' does not exist in the configuration.")
    return lambda key: config.get(section, key)


# --------------Set default section to RootCAserver--------------
get_value = set_default_section(config, 'PKI')
get_host_value = set_default_section(config, 'HOST')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(
    __file__), get_host_value('CERTIFICATE_DIRECTORY')))

# File paths for private key, CSR, and certificate
PRIVATE_KEY_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), BASE_DIR, f"{HOST_NAME}-CryptoShare.key"))
CSR_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), BASE_DIR, f"{HOST_NAME}-CryptoShare.csr"))
SIGNED_CERT_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), BASE_DIR, f"{HOST_NAME}-CryptoShare.pem"))


def are_dirs_same(src, dest):
    """
    Check if two directories are the same.

    Args:
        src (str): Source directory path
        dest (str): Destination directory path

    Returns:
        bool: True if both directories are the same, False otherwise
    """
    return os.path.abspath(os.path.dirname(src)) == os.path.abspath(dest)


def create_PKCS12():
    """
    Create a PKCS#12 (.p12) file for browser import.
    Args:
    None
    Returns:
    None
    """
    try:
        # Ensure required files exist
        if not os.path.exists(SIGNED_CERT_PATH) or not os.path.exists(PRIVATE_KEY_PATH):
            print(f"{RED}Error: Certificate or private key file is missing!{RESET}")
            return False

        output_file = os.path.abspath(os.path.join(os.path.dirname(
            __file__), BASE_DIR, f"{HOST_NAME}-CryptoShare.p12"))

        # Run OpenSSL to generate PKCS#12 file
        subprocess.run([
            "openssl", "pkcs12", "-export",
            "-in", SIGNED_CERT_PATH,
            "-inkey", PRIVATE_KEY_PATH,
            "-out", output_file,
            "-name", f"{HOST_NAME}-CryptoShare Certificate"
        ], check=True)

        # Copy the PKCS#12 file to the desired location with privilege check
        dest_path = os.path.abspath(BASE_DIR)
        if not are_dirs_same(output_file, dest_path):
            try:
                shutil.copy(output_file, dest_path)
            except PermissionError:
                print(
                    f"{RED}Permission denied! {YELLOW}Attempting to copy with elevated privileges...{RESET}")
                if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
                    subprocess.run(["sudo", "cp", output_file, dest_path])
                elif sys.platform.startswith("win"):
                    subprocess.run(["powershell", "Start-Process", "cmd", "-ArgumentList",
                                   f'/c copy "{output_file}" "{dest_path}"', "-Verb", "RunAs"])

        print(f"{GREEN}PKCS#12 file created and saved to: {CYAN}{dest_path}{RESET}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}OpenSSL Error: {e}{RESET}")
    except Exception as e:
        print(f"{RED}Unexpected Error: {e}{RESET}")
    return False
