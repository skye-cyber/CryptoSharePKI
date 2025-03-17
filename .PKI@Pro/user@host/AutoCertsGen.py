import os
import platform
import subprocess
import warnings
import configparser
import requests
from colorama import Fore, init
from verifyCATrust import verify_root_ca_trust
from PKI_colors import blue, cyan, green, magenta, red, reset, yellow

# Configuration
init(autoreset=True)

# Suppress the InsecureRequestWarning
warnings.filterwarnings(
    "ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

# --------------Create a ConfigParser object--------------
config = configparser.ConfigParser()

# --------------Read the .ini file--------------
config.read('config.ini')


# --------------Helper function to set a default section--------------
def set_default_section(config, section):
    if section not in config:
        raise ValueError(
            f"Section '{section}' does not exist in the configuration.")
    return lambda key: config.get(section, key)


# --------------Set default section to RootCAserver--------------
get_value = set_default_section(config, 'PKI')

# ---------------Set Configuracion-------------

IP = get_value('INTERMEDIATE_IP')
PORT = get_value('INTERMEDIATE_CA_PORT')
INTERMEDIATE_CA_URL = F"https://{IP}:{PORT}/submit-csr"  # Replace with the sever mahine ip address

# Host-specific details
get_value = set_default_section(config, 'HOST')
HOST_NAME = platform.node()  # Use the machine's hostname
DOMAIN = get_value('DOMAIN')
BASE_DIR = os.path.abspath(os.path.join(os.curdir, get_value('CERTIFICATE_DIRECTORY')))
os.makedirs(BASE_DIR, exist_ok=True)  # Ensure output directory exists

# File paths for private key, CSR, and certificate
PRIVATE_KEY_PATH = os.path.join(BASE_DIR, f"{HOST_NAME}.key")
CSR_PATH = os.path.join(BASE_DIR, f"{HOST_NAME}.csr")
SIGNED_CERT_PATH = os.path.join(BASE_DIR, f"{HOST_NAME}.pem")

# change section to pki
get_value = set_default_section(config, 'PKI')
INTERMEDIATE_CA_CERT_PATH = os.path.join(BASE_DIR, get_value('INTERMEDIATE_CA_CERT_FILE'))
ROOTCA_CERT_PATH = os.path.join(BASE_DIR, get_value('ROOT_CA_CERT_FILE'))


# Platform-specific paths
current_os = platform.system().lower()

# Ensure the private key file exists
for file in (PRIVATE_KEY_PATH, SIGNED_CERT_PATH, ROOTCA_CERT_PATH):
    if not os.path.exists(file):
        with open(file, 'w') as file:
            file.write("")  # Create an empty file
        print(f"Created file: {file}")
    else:
        print(f"File already exists: {file}")

    # Function to send the CSR to the Intermediate CA


def send_csr():
    try:
        with open(CSR_PATH, "rb") as csr_file:
            files = {"csr": csr_file}
            print(
                f"{cyan}Submitting CSR for {magenta}{HOST_NAME}{cyan} to the Intermediate CA...{reset}")

            # Send the CSR to the Intermediate CA
            response = requests.post(
                INTERMEDIATE_CA_URL, files=files, verify=False)

            if response.status_code == 200:  # Success
                # Parse the response content
                response_data = response.json()  # Assuming the server returns a JSON object
                signed_cert_content = response_data.get("signed_certificate")
                intermediate_ca_content = response_data.get(
                    "intermediate_certificate")
                root_ca_content = response_data.get(
                    "WondervilleRootCA")

                if signed_cert_content and intermediate_ca_content and root_ca_content:
                    # Save the signed certificate
                    with open(SIGNED_CERT_PATH, "wb") as cert_file:
                        cert_file.write(signed_cert_content.encode())
                    print(
                        f"{green}Signed certificate received and saved to {SIGNED_CERT_PATH}{reset}")

                    # Save the Intermediate CA certificate
                    with open(INTERMEDIATE_CA_CERT_PATH, "wb") as ca_file:
                        ca_file.write(intermediate_ca_content.encode())
                    print(
                        f"{green}Intermediate CA certificate received and saved to {INTERMEDIATE_CA_CERT_PATH}{reset}")

                    # Save RootCA certificate
                    with open(ROOTCA_CERT_PATH, 'w') as root_cert:
                        root_cert.write(root_ca_content)
                    print(
                        f"{green}Intermediate CA certificate received and saved to {ROOTCA_CERT_PATH}{reset}")

                    # process_certificate_installation
                    process_certificate_installation()
                else:
                    print(
                        f"{red}Failed to process response: Missing certificate data.{reset}")
            else:
                print(
                    f"{red}Failed to submit CSR for {HOST_NAME}. Status code: {response.status_code}{reset}")
                print(f"{red}Error message: {response.text}{reset}")

    except Exception as e:
        print(f"{red}Error while submitting CSR for {HOST_NAME}: {e}{reset}")


# Main function


def main():
    try:
        print(f"{blue}Processing host: {HOST_NAME}{reset}")

        # Generate private key
        subprocess.run(["openssl", "genrsa", "-out",
                       PRIVATE_KEY_PATH, "2048"], check=True)
        print(f"{green}Private key generated and saved to {PRIVATE_KEY_PATH}{reset}")

        # Generate CSR
        subprocess.run(
            ["openssl", "req", "-new", "-key", PRIVATE_KEY_PATH,
                "-out", CSR_PATH, "-subj", f"/CN={HOST_NAME}.{DOMAIN}"],
            check=True
        )
        print(f"{green}CSR generated and saved to {CSR_PATH}{reset}")

        # Submit CSR to Intermediate CA
        send_csr()

    except subprocess.CalledProcessError as e:
        print(f"{red}Error occurred during key or CSR generation: {e}{reset}")
    except Exception as e:
        print(f"{red}Unexpected error: {e}{reset}")


def process_certificate_installation():
    """
    Downloads and installs signed certificates and the Intermediate CA certificate on the host.

    Args:
        server_url (str): The URL of the server hosting the signed certificates.
        host_name (str): The hostname of the current machine.
        pfx_password (str): The password for the PFX file. Defaults to "skyepass".

    Raises:
        FileNotFoundError: If required files are missing.
        NotImplementedError: If the operating system is unsupported.
    """
    global ca_trust_dir, cert_dir, key_dir  # Ensure these variables are defined in the global scope

    try:

        # Install certificates
        if current_os == "linux":
            print(f"{green}Installing Root CA on Linux...{reset}")

            # Install Root CA into system-wide trust store
            subprocess.run(
                ["sudo", "cp", ROOTCA_CERT_PATH,
                    "/usr/local/share/ca-certificates/WondervilleRootCA.crt"],
                check=True
            )

            # update CA certificates
            subprocess.run(["sudo", "update-ca-certificates"], check=True)

            # Install Intermediate CA locally
            subprocess.run(
                ["sudo", "cp", INTERMEDIATE_CA_CERT_PATH, "/etc/ssl/certs/"],
                check=True
            )

            # Install host certificate
            subprocess.run(
                ["sudo", "cp", SIGNED_CERT_PATH, "/etc/ssl/certs/"],
                check=True
            )

            print(f"{green}Certificates installed successfully on Linux!{reset}")

        elif current_os == "windows":
            print(f"{yellow}Installing certificates on Windows...{reset}")

            try:
                # Install Root CA into the system-wide "Root" store
                subprocess.run(
                    ["certutil", "-addstore", "Root", ROOTCA_CERT_PATH],
                    check=True
                )
                print(f"{green}Root CA installed successfully in the 'Root' store.{reset}")

                # Install Intermediate CA into the "CA" store
                subprocess.run(
                    ["certutil", "-addstore", "CA", INTERMEDIATE_CA_CERT_PATH],
                    check=True
                )
                print(f"{green}Intermediate CA installed successfully in the 'CA' store.{reset}")

                # Install host certificate into the "My" (Personal) store
                subprocess.run(
                    ["certutil", "-addstore", "My", SIGNED_CERT_PATH],
                    check=True
                )
                print(f"{green}Host certificate installed successfully in the 'My' store.{reset}")

            except subprocess.CalledProcessError as e:
                print(f"{red}Error installing certificates on Windows: {e}{reset}")

            print(f"{green}All Certificates installed successfully on Windows!{reset}")

        else:
            raise NotImplementedError(f"OS '{current_os}' not supported.")

        # Verify Root CA trust
        is_trusted = verify_root_ca_trust(INTERMEDIATE_CA_CERT_PATH)
        if is_trusted:
            print(f"{green}Root CA verification succeeded!{reset}")
        else:
            print(f"{red}Root CA verification failed.{reset}")

    except FileNotFoundError as e:
        print(f"{red}File error: {yellow}{e}{reset}")
    except subprocess.CalledProcessError as e:
        print(f"{red}Error during certificate installation: {yellow}{e}{reset}")
    except Exception as e:
        print(f"{red}Unexpected error:{yellow} {e}{reset}")


if __name__ == "__main__":
    main()
