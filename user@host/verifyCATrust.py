import os
import platform
import subprocess


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

    ca_path = "./host_certs/IntermediateCA.pem" if ca_path is None else ca_path

    # Check if the Root CA certificate exists
    if not os.path.exists(ca_path):
        raise FileNotFoundError(
            f"Root CA certificate not found at: {ca_path}")

    # Determine the platform
    # 'linux', 'windows', or 'darwin' (macOS)
    current_os = platform.system().lower()

    if current_os == "linux":
        print("Verifying Root CA trust on Linux...")
        try:
            # Check if the Root CA is in the system's trusted store
            result = subprocess.run(
                ["openssl", "verify", "-CAfile",
                    "/etc/ssl/certs/ca-certificates.crt", ca_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("Root CA is trusted on Linux.")
                return True
            else:
                print(
                    f"Root CA is NOT trusted on Linux. Details: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error verifying Root CA on Linux: {e}")
            return False

    elif current_os == "windows":
        print("Verifying Root CA trust on Windows...")
        try:
            # Use certutil to verify the Root CA in the trusted store
            result = subprocess.run(
                ["certutil", "-verify", "-urlfetch", ca_path],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if "CertUtil: -verify command completed successfully." in result.stdout:
                print("Root CA is trusted on Windows.")
                return True
            else:
                print(
                    f"Root CA is NOT trusted on Windows. Details: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error verifying Root CA on Windows: {e}")
            return False

    else:
        raise NotImplementedError(
            f"Root CA trust verification is not supported for OS: {current_os}")
