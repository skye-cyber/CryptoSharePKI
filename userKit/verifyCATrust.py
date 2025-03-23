import os
import platform
import subprocess
from utils.colors import BWHITE, BLUE, RESET, GREEN, MAGENTA, DBLUE, RED


def verify_root_ca_trust(ca_path: None):
    """
    Verifies if the Root CA certificate is trusted on the current system.

    Parameters:
    - root_ca_path (str): Path to the Root CA certificate file.

    Returns:
    - bool: True if the Root CA is trusted, False otherwise.

    Raises:
    - FileNotFoundError: If the Root CA certificate file does not exist.
    - NotImplementedError: If the operating system is unsupported.
    """

    ca_path = os.path.abspath("./host_certs/CryptoshareIntermediateCA.pem") if ca_path is None else ca_path

    # Check if the Root CA certificate exists
    if not os.path.exists(ca_path):
        raise FileNotFoundError(
            f"Root CA certificate not found at: {ca_path}")

    # Determine the platform
    # 'linux', 'windows', or 'darwin' (macOS)
    current_os = platform.system().lower()

    if current_os == "linux":
        print(f"{MAGENTA}Verifying Root CA trust{RESET}")
        print(f"[{BLUE}System{RESET}]: {BWHITE}Linux...{RESET}")
        try:
            # Check if the Root CA is in the system's trusted store
            result = subprocess.run(
                ["sudo", "openssl", "verify", "-CAfile",
                    "/usr/share/ca-certificates/CryptoshareRootCA.crt", ca_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"[{DBLUE}status{RESET}] Root CA:{GREEN}Trusted{RESET}")
                return True
            else:
                print(f"[{DBLUE}status{RESET}] Root CA: {RED}NOT trusted.{RESET}")
                print(f"[{DBLUE}ERR{RESET}]: {RED}{result.stderr}{RED}")
                return False
        except Exception as e:
            print(f"Error verifying Root CA: {e}")
            return False

    elif current_os == "windows":
        print(f"""Verifying Root CA trust\n
        [{BLUE}System{RESET}]: {BWHITE}Linux...{RESET}""")
        try:
            # Use certutil to verify the Root CA in the trusted store
            result = subprocess.run(
                ["certutil", "-verify", "-urlfetch", ca_path],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if "CertUtil: -verify command completed successfully." in result.stdout:
                print(f"[{DBLUE}status{RESET}] Root CA:{GREEN}Trusted{RESET}")
                return True
            else:
                print(f"[{DBLUE}status{RESET}] Root CA: {RED}NOT trusted.{RESET}")
                print(f"[{DBLUE}ERR{RESET}]: {RED}{result.stderr}{RED}")
                return False
        except Exception as e:
            print(f"Error verifying Root CA: {e}")
            return False

    else:
        raise NotImplementedError(
            f"Root CA trust verification is not supported for OS: {MAGENTA}{current_os}{RESET}")
