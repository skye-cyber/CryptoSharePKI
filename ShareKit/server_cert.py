from utils.colors import BLUE, GREEN, RED, DGREEN, RESET, MAGENTA, CYAN, YELLOW, BWHITE, DWHITE
import requests
import subprocess
from .read_config import _set_section_
import os

get_value = _set_section_()


class EFSCert:
    def __init__(self):
        self.server_key = os.path.abspath(os.path.join(
            os.path.dirname(__file__), get_value("server_key")))
        self.CSR_PATH = os.path.abspath(os.path.join(
            os.path.dirname(__file__), get_value("server_csr")))
        self.INTERMEDIATE_CA_URL = f"https://{get_value("INTERMEDIATE_IP")}:{get_value("INTERMEDIATE_CA_PORT")}/submit-csr"
        self.SIGNED_CERT_PATH = os.path.abspath(os.path.join(
            os.path.dirname(__file__), get_value("server_signed_cert")))
        self.INTERMEDIATE_CA_CERT_PATH = os.path.abspath(os.path.join(
            os.path.dirname(__file__), get_value("intermediate_ca_cert")))
        self.ROOTCA_CERT_PATH = os.path.abspath(os.path.join(
            os.path.dirname(__file__), get_value("rootCA_cert")))
        self.server_cert = os.path.abspath(os.path.join(
            os.path.dirname(__file__), get_value("server_cert")))
        self.CA_bundle = os.path.abspath(os.path.join(
            os.path.dirname(__file__), get_value("ca_bundle")))

    def ensure_ca_bundle(self):
        if os.path.exists(self.CA_bundle):
            print(f"[{BLUE}Bundle{RESET}]: {DGREEN}True")
            return True
        return self.create_ca_bundle()

    def create_ca_bundle(self) -> bool:
        try:
            print(f"{YELLOW}Creating CA cert bundle{RESET}")
            with open(self.INTERMEDIATE_CA_CERT_PATH, 'r') as f:
                ica_data = f.read()

            with open(self.ROOTCA_CERT_PATH, 'r') as f1:
                rca_data = f1.read()

            f_data = f"{ica_data}\n{rca_data}"

            with open(self.CA_bundle, 'w') as f2:
                f2.write(f_data)

            return True
        except Exception as e:
            print(f"{RED}{e}{RESET}")
            return False

    def send_csr(self) -> bool:
        try:
            with open(self.CSR_PATH, "rb") as csr_file:
                files = {"csr": csr_file}
                print(
                    f"{CYAN}Submitting CSR for {MAGENTA}EFS{CYAN} to the Intermediate CA...{RESET}")

                response = requests.post(
                    self.INTERMEDIATE_CA_URL, files=files, verify=False)

                if response.status_code == 200:
                    response_data = response.json()
                    signed_cert_content = response_data.get(
                        "signed_certificate")
                    intermediate_ca_content = response_data.get(
                        "intermediate_certificate")
                    root_ca_content = response_data.get("CryptoshareRootCA")

                    if signed_cert_content and intermediate_ca_content and root_ca_content:
                        with open(self.SIGNED_CERT_PATH, "wb") as cert_file:
                            cert_file.write(signed_cert_content.encode())
                        print(
                            f"{BWHITE}Signed certificate received and saved to {GREEN}{self.SIGNED_CERT_PATH}{RESET}")

                        with open(self.INTERMEDIATE_CA_CERT_PATH, "wb") as ca_file:
                            ca_file.write(intermediate_ca_content.encode())
                        print(
                            f"{BWHITE}Intermediate CA certificate received. Saved to: {MAGENTA}{self.INTERMEDIATE_CA_CERT_PATH}{RESET}")

                        with open(self.ROOTCA_CERT_PATH, 'w') as root_cert:
                            root_cert.write(root_ca_content)
                        print(
                            f"{BWHITE}Root CA certificate received and saved to {YELLOW}{self.ROOTCA_CERT_PATH}{RESET}")

                    else:
                        print(
                            f"{RED}Failed to process response: Missing certificate data.{RESET}")
                else:
                    print(
                        f"{RED}Failed to submit CSR for EFS. Status code: {response.status_code}{RESET}")
                    print(f"{RED}Error message: {response.text}{RESET}")
            return True

        except Exception as e:
            print(f"{RED}Error while submitting CSR for EFS: {e}{RESET}")
            return False

    def generate_cert(self):
        try:
            print(f"{DWHITE}Processing host: {YELLOW}EFS{RESET}")

            # Generate private key if it doesn't exist

            if all((os.path.exists(self.server_key), os.path.exists(self.SIGNED_CERT_PATH))):
                print(f"{YELLOW}Certificate exists: {BLUE}Not Regenerating{RESET}")
                return True

            subprocess.run(["openssl", "genrsa", "-out",
                            self.server_key, "2048"], check=True)
            print(
                f"Private key generated and saved to {CYAN}{self.server_key}{RESET}")

            # Generate CSR
            subprocess.run(
                ["openssl", "req", "-new", "-key", self.server_key,
                    "-out", self.CSR_PATH, "-subj", "/CN=EFS.ShareKit"],
                check=True
            )
            print(f"{MAGENTA}CSR generated and saved to {GREEN}{self.CSR_PATH}{RESET}")

            csr_okay = self.send_csr()

            if csr_okay:
                self.create_ca_bundle()

            return True
        except subprocess.CalledProcessError as e:
            print(f"{RED}Error occurRED during key or CSR generation: {e}{RESET}")
            return False
        except Exception as e:
            print(f"{RED}Unexpected error: {e}{RESET}")
            return False

    def is_valid_cert(self) -> bool:
        try:
            check = self.generate_cert()
            return check
        except Exception as e:
            print(f"{RED}{e}{RESET}")
            return False

