import os
import platform
import subprocess
import warnings
import configparser
import requests
from .verifyCATrust import verify_root_ca_trust
from utils.colors import (BLUE, CYAN, GREEN, DCYAN, DBLUE, MAGENTA,
                          RED, RESET, YELLOW, DGREEN, BWHITE, DRED)


# Suppress the InsecureRequestWarning
warnings.filterwarnings(
    "ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

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

# ---------------Set Configuracion-------------

IP = get_value('INTERMEDIATE_IP')
PORT = get_value('INTERMEDIATE_CA_PORT')
# Replace with the sever mahine ip address
INTERMEDIATE_CA_URL = F"https://{IP}:{PORT}/submit-csr"

# Host-specific details
get_value = set_default_section(config, 'HOST')
HOST_NAME = platform.node()  # Use the machine's hostname
DOMAIN = get_value('DOMAIN')
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(
    __file__), get_value('CERTIFICATE_DIRECTORY')))

os.makedirs(BASE_DIR, exist_ok=True)  # Ensure output directory exists

# File paths for private key, CSR, and certificate
PRIVATE_KEY_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), BASE_DIR, f"{HOST_NAME}-CryptoShare.key"))
CSR_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), BASE_DIR, f"{HOST_NAME}-CryptoShare.csr"))
SIGNED_CERT_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), BASE_DIR, f"{HOST_NAME}-CryptoShare.pem"))

# change section to pki
get_value = set_default_section(config, 'PKI')
INTERMEDIATE_CA_CERT_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), BASE_DIR, get_value('INTERMEDIATE_CA_CERT_FILE')))
ROOTCA_CERT_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), BASE_DIR, get_value('ROOT_CA_CERT_FILE')))


# Platform-specific paths
current_os = platform.system().lower()


def _setup_():
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
    """
    Send CSR request to the ca_csr_server.
    Args:
    None
    Returns:
    None
    """
    try:
        with open(CSR_PATH, "rb") as csr_file:
            files = {"csr": csr_file}
            print(
                f"{CYAN}Submitting CSR for {MAGENTA}[{HOST_NAME}]{CYAN} to the Intermediate CA...{RESET}")

            # Send the CSR to the Intermediate CA
            response = requests.post(
                INTERMEDIATE_CA_URL, files=files, verify=False)

            if response.status_code == 200:  # Success
                # Parse the response content
                response_data = response.json()  # the server returns a JSON object
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
                        f"{BWHITE}Signed certificate received and saved to {GREEN}{SIGNED_CERT_PATH}{RESET}")

                    # Save the Intermediate CA certificate
                    with open(INTERMEDIATE_CA_CERT_PATH, "wb") as ca_file:
                        ca_file.write(intermediate_ca_content.encode())
                    print(
                        f"{BWHITE}Intermediate CA certificate received. Saved to: {MAGENTA}{INTERMEDIATE_CA_CERT_PATH}{RESET}")

                    # Save RootCA certificate
                    with open(ROOTCA_CERT_PATH, 'w') as root_cert:
                        root_cert.write(root_ca_content)
                    print(
                        f"{BWHITE}Root CA certificate received and saved to {YELLOW}{ROOTCA_CERT_PATH}{RESET}")

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


def main():
    """
    Generate self private key and csr request send to the ca_csr_server for signing.
    csr_server returns  3 certificates:\n
    <b>signed user certificate.</b>\n
    <b>intermediate certificate</b>\n
    <b>root CA certificate.</b>\n

    The result is a user with valid signed certificate
    Args:
        None
    Returns:
        None
    """
    try:
        _setup_()
        print(f"{DBLUE}Processing host: {DCYAN}{HOST_NAME}{RESET}")

        # Generate private key
        subprocess.run(["openssl", "genrsa", "-out",
                       PRIVATE_KEY_PATH, "2048"], check=True)
        print(f"{BLUE}Private key generated and saved to {GREEN}{PRIVATE_KEY_PATH}{RESET}")

        # Generate CSR
        subprocess.run(
            ["openssl", "req", "-new", "-key", PRIVATE_KEY_PATH,
                "-out", CSR_PATH, "-subj", f"/CN={HOST_NAME}.{DOMAIN}"],
            check=True
        )
        print(f"{GREEN}CSR generated and saved to {DGREEN}{CSR_PATH}{RESET}")

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
            print(f"{GREEN}Installing Root CA")
            print(f"{BWHITE}OS:{MAGENTA}Linux...{RESET}")
            print(f"Target:{YELLOW}/usr/share/ca-certificates/{RESET}")

            # Install Root CA into system-wide trust store
            subprocess.run(
                ["sudo", "cp", ROOTCA_CERT_PATH,
                    "/usr/share/ca-certificates/CryptoshareRootCA.crt"],
                check=True
            )

            print(f"{BWHITE}Update CA certificates{RESET}")
            # update CA certificates
            subprocess.run(["sudo", "update-ca-certificates"], check=True)

            print(f"{GREEN}Setting up Intermediate CA. {RESET}")
            print(f"Target:{YELLOW}/etc/ssl/certs/{RESET}")

            # Install Intermediate CA locally
            subprocess.run(
                ["sudo", "cp", INTERMEDIATE_CA_CERT_PATH, "/etc/ssl/certs/"],
                check=True
            )

            print(f"{BLUE}Install {CYAN}host/self{BLUE} certificate{RESET}")
            # Install host certificate
            subprocess.run(
                ["sudo", "cp", SIGNED_CERT_PATH, "/etc/ssl/certs/"],
                check=True
            )

            print(f"{GREEN}Certificates installed successfully on Linux!{RESET}")

        elif current_os == "windows":
            try:
                print(f"{GREEN}Installing Root CA")
                print(f"{BWHITE}OS:{MAGENTA}Linux...{RESET}")
                print(f"{BWHITE}Target: '{YELLOW}Root{RESET}'{BWHITE} store{RESET}")

                # Install Root CA into the system-wide "Root" store
                subprocess.run(
                    ["certutil", "-addstore", "Root", ROOTCA_CERT_PATH],
                    check=True
                )

                print(
                    f"{GREEN}Install Intermediate CA installed successfully{RESET}")
                print(f"{BWHITE}Target: '{YELLOW}CA{RESET}' {BWHITE} store.{RESET}")

                # Install Intermediate CA into the "CA" store
                subprocess.run(
                    ["certutil", "-addstore", "CA", INTERMEDIATE_CA_CERT_PATH],
                    check=True
                )
                print(
                    f"{GREEN}Install host certificate CA{RESET}")
                print(f"{BWHITE}Target: '{YELLOW}My{RESET}' {BWHITE}(Personal) store.{RESET}")

                # Install host certificate into the "My" (Personal) store
                subprocess.run(
                    ["certutil", "-addstore", "My", SIGNED_CERT_PATH],
                    check=True
                )

            except subprocess.CalledProcessError as e:
                print(f"{RED}Error installing certificates: {e}{RESET}")

            print(
                f"{DGREEN}All Certificates installed successfully{RESET}")

        else:
            raise NotImplementedError(f"OS '{current_os}' not supported.")

        # Verify Root CA trust
        is_trusted = verify_root_ca_trust(INTERMEDIATE_CA_CERT_PATH)
        if is_trusted:
            print(f"{GREEN}Root CA verification succeeded!{RESET}")
        else:
            print(f"{DRED}Root CA verification failed.{RESET}")

    except FileNotFoundError as e:
        print(f"{RED}File error: {YELLOW}{e}{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{RED}Error during certificate installation: {YELLOW}{e}{RESET}")
    except Exception as e:
        print(f"{RED}Unexpected error:{YELLOW} {e}{RESET}")


if __name__ == "__main__":
    main()
