import configparser
import os
import subprocess
import time
from datetime import datetime
import sys
import pytz
from pathlib import Path
# Function to trigger Root CA renewal
from .RootCA import main
from utils.colors import BLUE, CYAN, GREEN, MAGENTA, RED, RESET, YELLOW

# --------------Create a ConfigParser object--------------
config = configparser.ConfigParser()

# --------------Read the .ini file--------------
conf_path = os.path.join(os.path.relpath(Path(__file__).parent), "config.ini")
config.read(conf_path)
# --------------Helper function to set a default section--------------


def set_default_section(config, section):
    if section not in config:
        raise ValueError(
            f"Section '{section}' does not exist in the configuration.")
    return lambda key: config.get(section, key)


# Set default section to RootCAserver
get_value = set_default_section(config, 'RootCAserver')

# ---------------Files and diretories names--------------
INTERMEDIATE_CA_DIR_NAME = get_value('INTERMEDIATE_CA_DIR_NAME')
INTERMEDIATE_CA_CERT_FILE = get_value('INTERMEDIATE_CA_CERT_FILE')
RENEWAL_THRESHOLD_DAYS = int(get_value('RENEWAL_THRESHOLD_DAYS'))  # Renew <?> days before expiration
cert_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), INTERMEDIATE_CA_DIR_NAME, INTERMEDIATE_CA_CERT_FILE))


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
    start_date = ensure_utc(datetime.strptime(start_date_str, "%b %d %H:%M:%S %Y %Z"))

    # Parse the expiry date string into a naive datetime object
    expiry_date = ensure_utc(datetime.strptime(expiry_date_str, "%b %d %H:%M:%S %Y %Z"))

    return start_date, expiry_date


def monitor_intermediate_ca():
    """
    Monitors the Intermediate CA certificate and triggers renewal if close to expiration.
    """
    while True:
        try:
            start_date, expiry_date = get_certificate_dates(cert_dir)

            # Get the current date and time in UTC
            current_date = datetime.now().now(pytz.UTC)
            print(f"Certificate expires on: {YELLOW}{expiry_date}{RESET}")

            # Calculate the remaining validity period
            remaining_period = expiry_date - current_date
            remaining_days = remaining_period.days
            print(remaining_period)
            print(
                f"The certificate is valid for: {MAGENTA}{remaining_period.days}{RESET} days, {MAGENTA}{remaining_period.seconds // 3600}{RESET} hours, and {CYAN}{(remaining_period.seconds % 3600) // 60}{RESET} minutes.")

            if remaining_days <= RENEWAL_THRESHOLD_DAYS:
                print(
                    f"{YELLOW}Intermediate CA certificate is about to expire. Initiating renewal process...{RESET}")
                main()  # Trigger the Root CA renewal process
            else:
                print(
                    f"{GREEN}Intermediate CA certificate is still valid. Monitoring...{RESET}")

            # Sleep for a day before the next check
            time.sleep(86400)

        except Exception as e:
            print(
                f"{RED}Error while monitoring Intermediate CA certificate:{RESET} {e}")
            time.sleep(60)  # Retry after 1 minute on failure
        except KeyboardInterrupt:
            print("\nQuit")
            sys.exit()


if __name__ == "__main__":
    print(f"{CYAN}===Monitoring {BLUE}{cert_dir}{CYAN} certificate==={RESET}")
    monitor_intermediate_ca()
