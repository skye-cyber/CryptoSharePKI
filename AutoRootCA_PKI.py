import configparser
import os
import platform
import sys
from datetime import datetime, timedelta, timezone

from colorama import init
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.x509 import (BasicConstraints, CertificateBuilder, Name,
                               NameAttribute, random_serial_number)
from cryptography.x509.oid import NameOID
from PKI_colors import blue, cyan, green, magenta, red, reset, yellow

# --------------Create a ConfigParser object--------------
config = configparser.ConfigParser()

# --------------Read the .ini file--------------
config.read('config.ini')

# --------------Configurations--------------
init(autoreset=True)


# --------------Helper function to set a default section--------------
def set_default_section(config, section):
    if section not in config:
        raise ValueError(
            f"Section '{section}' does not exist in the configuration.")
    return lambda key: config.get(section, key)


# Set default section to RootCAserver
get_value = set_default_section(config, 'RootCAserver')

# ---------------Files and diretories names--------------
cert_validity = float(get_value('cert_validity'))
ROOT_CA_DIR_NAME = get_value('ROOT_CA_DIR_NAME')
INTERMEDIATE_CA_DIR_NAME = get_value('INTERMEDIATE_CA_DIR_NAME')
ROOT_CA_KEY_FILE = get_value('ROOT_CA_KEY_FILE')
ROOT_CA_CERT_FILE = get_value('ROOT_CA_CERT_FILE')
INTERMEDIATE_CA_KEY_FILE = get_value('INTERMEDIATE_CA_KEY_FILE')
get_value('INTERMEDIATE_CA_KEY_FILE')
INTERMEDIATE_CA_CERT_FILE = get_value('INTERMEDIATE_CA_CERT_FILE')

# ---------------Directories paths--------------
ROOT_CA_DIR_PATH = os.path.abspath(os.path.join(os.curdir, ROOT_CA_DIR_NAME))
INTERMEDIATE_CA_DIR_PATH = os.path.abspath(os.path.join(os.curdir, INTERMEDIATE_CA_DIR_NAME))
# --------------Create directories if they do not exist--------------
os.makedirs(ROOT_CA_DIR_PATH, exist_ok=True)
os.makedirs(INTERMEDIATE_CA_DIR_PATH, exist_ok=True)

# 1. Root CA Setup


def generate_root_ca():
    # Generate Root CA private key
    root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    root_key_path = os.path.join(ROOT_CA_DIR_PATH, ROOT_CA_KEY_FILE)
    with open(root_key_path, "wb") as key_file:
        key_file.write(
            root_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    print(f"Root CA private key saved to {green}{root_key_path}{reset}")

    # Generate Root CA certificate
    subject = issuer = Name([
        NameAttribute(NameOID.COUNTRY_NAME, "US"),
        NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "New York"),
        NameAttribute(NameOID.LOCALITY_NAME, "Wonderville"),
        NameAttribute(NameOID.ORGANIZATION_NAME, "Wonderville Town Hall"),
        NameAttribute(NameOID.COMMON_NAME, "Wonderville Root CA"),
    ])
    root_cert = (
        CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(root_key.public_key())
        .serial_number(random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        # 10 years validity
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=cert_validity))
        # Intermediate CA allowed
        .add_extension(BasicConstraints(ca=True, path_length=1), critical=True)
        .sign(private_key=root_key, algorithm=SHA256())
    )

    root_cert_path = os.path.join(ROOT_CA_DIR_PATH, ROOT_CA_CERT_FILE)
    with open(root_cert_path, "wb") as cert_file:
        cert_file.write(root_cert.public_bytes(serialization.Encoding.PEM))
    print(f"{green}Root CA certificate valid for {magenta}{cert_validity} days{green} saved to {cyan}{root_cert_path}{reset}")

# 2. Intermediate CA Setup


def generate_intermediate_ca():
    # Generate Intermediate CA private key
    intermediate_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048)
    intermediate_key_path = os.path.join(
        INTERMEDIATE_CA_DIR_PATH, INTERMEDIATE_CA_KEY_FILE)
    with open(intermediate_key_path, "wb") as key_file:
        key_file.write(
            intermediate_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    print(f"{green}Intermediate CA private key saved to {blue}{intermediate_key_path}{reset}")

    # Generate Intermediate CA CSR
    subject = Name([
        NameAttribute(NameOID.COUNTRY_NAME, "US"),
        NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "New York"),
        NameAttribute(NameOID.LOCALITY_NAME, "Wonderville"),
        NameAttribute(NameOID.ORGANIZATION_NAME, "Wonderville Town Hall"),
        NameAttribute(NameOID.COMMON_NAME, "Wonderville Intermediate CA"),
    ])
    intermediate_csr = (
        CertificateBuilder()
        .subject_name(subject)
        .public_key(intermediate_key.public_key())
        .serial_number(random_serial_number())
    )

    # Root CA signs the Intermediate CA certificate
    root_cert_path = os.path.join(ROOT_CA_DIR_PATH, ROOT_CA_CERT_FILE)
    root_key_path = os.path.join(ROOT_CA_DIR_PATH, ROOT_CA_KEY_FILE)
    with open(root_cert_path, "rb") as root_cert_file, open(root_key_path, "rb") as root_key_file:
        root_cert = x509.load_pem_x509_certificate(root_cert_file.read())
        root_key = serialization.load_pem_private_key(
            root_key_file.read(), password=None)

    intermediate_cert = (
        CertificateBuilder()
        .subject_name(subject)
        .issuer_name(root_cert.subject)
        .public_key(intermediate_key.public_key())
        .serial_number(random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        # 5 years validity
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=cert_validity))
        # No further delegation
        .add_extension(BasicConstraints(ca=True, path_length=0), critical=True)
        .sign(private_key=root_key, algorithm=SHA256())
    )

    intermediate_cert_path = os.path.join(
        INTERMEDIATE_CA_DIR_PATH, INTERMEDIATE_CA_CERT_FILE)
    with open(intermediate_cert_path, "wb") as cert_file:
        cert_file.write(intermediate_cert.public_bytes(
            serialization.Encoding.PEM))
    print(f"{green}Intermediate CA certificate {magenta}{cert_validity} days{green} saved to {yellow}{intermediate_cert_path}{reset}")

# 3. Process CSR from Hosts


def sign_host_csr(csr_path, output_cert_path):
    '''**Already implemented elsewhere**'''
    intermediate_key_path = os.path.join(
        INTERMEDIATE_CA_DIR_PATH, INTERMEDIATE_CA_KEY_FILE)
    intermediate_cert_path = os.path.join(
        INTERMEDIATE_CA_DIR_PATH, INTERMEDIATE_CA_CERT_FILE)

    with open(intermediate_cert_path, "rb") as int_cert_file, open(intermediate_key_path, "rb") as int_key_file:
        intermediate_cert = serialization.load_pem_x509_certificate(
            int_cert_file.read())
        intermediate_key = serialization.load_pem_private_key(
            int_key_file.read(), password=None)

    with open(csr_path, "rb") as csr_file:
        csr = serialization.load_pem_x509_csr(csr_file.read())

    signed_cert = (
        CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(intermediate_cert.subject)
        .public_key(csr.public_key())
        .serial_number(random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        # 1 year validity
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .sign(private_key=intermediate_key, algorithm=SHA256())
    )

    with open(output_cert_path, "wb") as cert_file:
        cert_file.write(signed_cert.public_bytes(serialization.Encoding.PEM))
    print(f"{green}Host certificate signed and saved to {magenta}{output_cert_path}{reset}")


def main():
    try:
        print(f"{yellow}Setting up Root CA...{reset}")
        generate_root_ca()
        print(f"{yellow}Setting up Intermediate CA...{reset}")
        generate_intermediate_ca()
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        print(f"{red}{e}{reset}")


# Main Function
if __name__ == "__main__":
    main()
