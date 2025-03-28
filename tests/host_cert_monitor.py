import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timedelta

import pytz
# Your existing function for CSR generation and submission
from AutoCertsGen import send_csr
from colors import BLUE, CYAN, GREEN, MAGENTA, RED, RESET, YELLOW

HOST_NAME = platform.node()
# Adjust based on your environment
CERT_PATH = f"/etc/ssl/certs/{HOST_NAME}.pem"  # For linux systems
RENEWAL_THRESHOLD_DAYS = 4  # 10  # Renew 4 days before expiration

# Platform-specific paths
current_os = platform.system().lower()


def ensure_utc(dt):
    """
    Ensures the given datetime object is in UTC.

    Args:
        dt (datetime): The datetime object to process.

    Returns:
        datetime: A timezone-aware datetime object in UTC.
    """
    if dt.tzinfo is None:  # Naive datetime
        return dt.replace(tzinfo=pytz.UTC)
    return dt.astimezone(pytz.UTC)  # Convert to UTC if it has a timezone


def get_certificate_dates(cert_path):
    """
    Returns the issue (Not Before) and expiration (Not After) dates of the certificate in cert_path.
    """
    if current_os == 'linux':
        try:
            # Extract issue date (Not Before)
            result_start = subprocess.run(
                ["openssl", "x509", "-startdate", "-noout", "-in", cert_path],
                capture_output=True,
                text=True,
                check=True
            )
            start_date_str = result_start.stdout.strip().split("=")[1]

            # Extract the expiry date (Not After)
            result_end = subprocess.run(
                ["openssl", "x509", "-enddate", "-noout", "-in", cert_path],
                capture_output=True,
                text=True,
                check=True
            )
            expiry_date_str = result_end.stdout.strip().split("=")[1]

            # Parse the start date string into a naive datetime object
            start_date = ensure_utc(datetime.strptime(
                start_date_str, "%b %d %H:%M:%S %Y %Z"))

            # Parse the expiry date string into a naive datetime object
            expiry_date = ensure_utc(datetime.strptime(
                expiry_date_str, "%b %d %H:%M:%S %Y %Z"))

            return start_date, expiry_date
        except Exception as e:
            print(f"Error: {e}")
            raise

    elif current_os == 'windows':
        try:
            import win32com.client
        except ImportError:
            print("pywin32 Not Found: Installing...")
            os.system('python -m pip install pywin32')

        store_name = 'My'  # Personal store
        subject_name = f'{HOST_NAME}.pem'  # Default host file
        """
        Retrieves the creation and expiry dates of a certificate from the Windows Certificate Store.

        Args:
            store_name (str): The certificate store name (e.g., "My", "Root", "CA").
            subject_name (str): The subject name of the certificate.

        Returns:
            tuple: A tuple containing the NotBefore (creation date) and NotAfter (expiry date).
        """
        try:
            # Open the certificate store
            store = win32com.client.Dispatch("CAPICOM.Store")
            # 2 = LocalMachine, 0 = CAPICOM_STORE_OPEN_READ_ONLY
            store.Open(2, store_name, 0)

            # Search for the certificate
            for cert in store.Certificates:
                if subject_name.lower() in cert.SubjectName.lower():
                    not_before = ensure_utc(cert.ValidFromDate)
                    not_after = ensure_utc(cert.ValidToDate)
                    return not_before, not_after

            raise Exception(
                f"Certificate with subject '{subject_name}' not found in store '{store_name}'.")

        except Exception as e:
            print(f"Error: {e}")
            raise


def monitor_certificate():
    """
    Monitors the host certificate and triggers renewal if close to expiration.
    """
    while True:
        try:
            start_date, expiry_date = get_certificate_dates(CERT_PATH)
            print(f"Certificate expires on: {YELLOW}{expiry_date}{RESET}")
            # Get the current date and time in UTC
            current_date = datetime.now(pytz.UTC)

            # Calculate the remaining validity period
            remaining_period = expiry_date - current_date
            remaining_days = remaining_period.days

            print(
                f"The certificate is valid for: {MAGENTA}{remaining_period.days}{RESET} days, {MAGENTA}{remaining_period.seconds // 3600}{RESET} hours, and {CYAN}{(remaining_period.seconds % 3600) // 60}{RESET} minutes.")

            if remaining_days <= RENEWAL_THRESHOLD_DAYS:
                print(
                    f"{YELLOW}{HOST_NAME} CA certificate is about to expire. Initiating renewal process...{RESET}")
                send_csr()  # Trigger the Root CA renewal process
            else:
                print(
                    f"{GREEN}{HOST_NAME} CA certificate is still valid. Monitoring...{RESET}")

            # Sleep for a day before the next check
            time.sleep(86400)

        except Exception as e:
            print(
                f"{RED}Error while monitoring Intermediate CA certificate:{RESET} {e}")
            time.sleep(60)  # Retry after 1 minute on failure
        except KeyboardInterrupt:
            print("\nQuit!")
            sys.exit()


if __name__ == "__main__":
    print(f"{CYAN}===Monitoring {BLUE}{HOST_NAME}{CYAN} certificate==={RESET}")
    monitor_certificate()
