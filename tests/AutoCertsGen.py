import os
import platform
import subprocess
import warnings

import requests
from colorama import Fore, init
from verifyCATrust import verify_root_ca_trust
from colors import BLUE, CYAN, GREEN, MAGENTA, RED, RESET, YELLOW

# Configuration
init(autoRESET=True)

# Suppress the InsecureRequestWarning
warnings.filterwarnings(
    "ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

# Intermediate CA configuration
# Replace with actual URL
INTERMEDIATE_CA_URL = "https://172.17.88.189:5000/submit-csr"  # Replace with the sever mahine ip address

# Host-specific details
HOST_NAME = platform.node()  # Use the machine's hostname
DOMAIN = "mydomain.com"  # Replace with your domain
BASE_DIR = os.path.abspath(os.path.join(os.curdir, "host_certs"))
os.makedirs(BASE_DIR, exist_ok=True)  # Ensure output directory exists

# File paths for private key, CSR, and certificate
PRIVATE_KEY_PATH = os.path.join(BASE_DIR, f"{HOST_NAME}.key")
CSR_PATH = os.path.join(BASE_DIR, f"{HOST_NAME}.csr")
SIGNED_CERT_PATH = os.path.join(BASE_DIR, f"{HOST_NAME}.pem")
INTERMEDIATE_CA_CERT_PATH = os.path.join(BASE_DIR, "IntermediateCA.pem")
ROOTCA_CERT_PATH = os.path.join(BASE_DIR, "CryptoshareRootCA.pem")


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
                f"{CYAN}Submitting CSR for {MAGENTA}{HOST_NAME}{CYAN} to the Intermediate CA...{RESET}")

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
                    "CryptoshareRootCA")

                if signed_cert_content and intermediate_ca_content and root_ca_content:
                    # Save the signed certificate
                    with open(SIGNED_CERT_PATH, "wb") as cert_file:
                        cert_file.write(signed_cert_content.encode())
                    print(
                        f"{GREEN}Signed certificate received and saved to {SIGNED_CERT_PATH}{RESET}")

                    # Save the Intermediate CA certificate
                    with open(INTERMEDIATE_CA_CERT_PATH, "wb") as ca_file:
                        ca_file.write(intermediate_ca_content.encode())
                    print(
                        f"{GREEN}Intermediate CA certificate received and saved to {INTERMEDIATE_CA_CERT_PATH}{RESET}")

                    # Save RootCA certificate
                    with open(ROOTCA_CERT_PATH, 'w') as root_cert:
                        root_cert.write(root_ca_content)
                    print(
                        f"{GREEN}Intermediate CA certificate received and saved to {ROOTCA_CERT_PATH}{RESET}")

                    # process_certificate_installation
                    process_certificate_installation()
                else:
                    print(
                        f"{RED}Failed to process response: Missing certificate data.{RESET}")
            else:
                print(
                    f"{RED}Failed to submit CSR for {HOST_NAME}. Status code: {response.status_code}{RESET}")
                print(f"{RED}Error message: {response.text}{RESET}")

    except Exception as e:
        print(f"{RED}Error while submitting CSR for {HOST_NAME}: {e}{RESET}")


# Main function


def main():
    try:
        print(f"{BLUE}Processing host: {HOST_NAME}{RESET}")

        # Generate private key
        subprocess.run(["openssl", "genrsa", "-out",
                       PRIVATE_KEY_PATH, "2048"], check=True)
        print(f"{GREEN}Private key generated and saved to {PRIVATE_KEY_PATH}{RESET}")

        # Generate CSR
        subprocess.run(
            ["openssl", "req", "-new", "-key", PRIVATE_KEY_PATH,
                "-out", CSR_PATH, "-subj", f"/CN={HOST_NAME}.{DOMAIN}"],
            check=True
        )
        print(f"{GREEN}CSR generated and saved to {CSR_PATH}{RESET}")

        # Submit CSR to Intermediate CA
        send_csr()

    except subprocess.CalledProcessError as e:
        print(f"{RED}Error occurRED during key or CSR generation: {e}{RESET}")
    except Exception as e:
        print(f"{RED}Unexpected error: {e}{RESET}")


def process_certificate_installation():
    """
    Downloads and installs signed certificates and the Intermediate CA certificate on the host.

    Args:
        server_url (str): The URL of the server hosting the signed certificates.
        host_name (str): The hostname of the current machine.
        pfx_password (str): The password for the PFX file. Defaults to "skyepass".

    Raises:
        FileNotFoundError: If requiRED files are missing.
        NotImplementedError: If the operating system is unsupported.
    """
    global ca_trust_dir, cert_dir, key_dir  # Ensure these variables are defined in the global scope

    try:

        # Install certificates
        if current_os == "linux":
            print(f"{GREEN}Installing Root CA on Linux...{RESET}")

            # Install Root CA into system-wide trust store
            subprocess.run(
                ["sudo", "cp", ROOTCA_CERT_PATH,
                    "/usr/local/share/ca-certificates/CryptoshareRootCA.crt"],
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

            print(f"{GREEN}Certificates installed successfully on Linux!{RESET}")

        elif current_os == "windows":
            print(f"{YELLOW}Installing certificates on Windows...{RESET}")

            try:
                # Install Root CA into the system-wide "Root" store
                subprocess.run(
                    ["certutil", "-addstore", "Root", ROOTCA_CERT_PATH],
                    check=True
                )
                print(f"{GREEN}Root CA installed successfully in the 'Root' store.{RESET}")

                # Install Intermediate CA into the "CA" store
                subprocess.run(
                    ["certutil", "-addstore", "CA", INTERMEDIATE_CA_CERT_PATH],
                    check=True
                )
                print(f"{GREEN}Intermediate CA installed successfully in the 'CA' store.{RESET}")

                # Install host certificate into the "My" (Personal) store
                subprocess.run(
                    ["certutil", "-addstore", "My", SIGNED_CERT_PATH],
                    check=True
                )
                print(f"{GREEN}Host certificate installed successfully in the 'My' store.{RESET}")

            except subprocess.CalledProcessError as e:
                print(f"{RED}Error installing certificates on Windows: {e}{RESET}")

            print(f"{GREEN}All Certificates installed successfully on Windows!{RESET}")

        else:
            raise NotImplementedError(f"OS '{current_os}' not supported.")

        # Verify Root CA trust
        is_trusted = verify_root_ca_trust(INTERMEDIATE_CA_CERT_PATH)
        if is_trusted:
            print(f"{GREEN}Root CA verification succeeded!{RESET}")
        else:
            print(f"{RED}Root CA verification failed.{RESET}")

    except FileNotFoundError as e:
        print(f"{RED}File error: {YELLOW}{e}{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{RED}Error during certificate installation: {YELLOW}{e}{RESET}")
    except Exception as e:
        print(f"{RED}Unexpected error:{YELLOW} {e}{RESET}")


if __name__ == "__main__":
    main()
