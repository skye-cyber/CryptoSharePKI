import configparser
import os
import subprocess
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import serialization
# from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.x509 import (CertificateBuilder, load_pem_x509_csr,
                               random_serial_number)
# from cryptography.x509.oid import NameOID
from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path
app = Flask(__name__)

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


# --------------Set default section to RootCAserver--------------
get_value = set_default_section(config, 'RootCAserver')

# ---------------Files and diretories names--------------
cert_validity = get_value('cert_validity')
ROOT_CA_DIR_NAME = get_value('ROOT_CA_DIR_NAME')
INTERMEDIATE_CA_DIR_NAME = get_value('INTERMEDIATE_CA_DIR_NAME')
ROOT_CA_KEY_FILE = get_value('ROOT_CA_KEY_FILE')
ROOT_CA_CERT_FILE = get_value('ROOT_CA_CERT_FILE')
INTERMEDIATE_CA_KEY_FILE = get_value('INTERMEDIATE_CA_KEY_FILE')
get_value('INTERMEDIATE_CA_KEY_FILE')
INTERMEDIATE_CA_CERT_FILE = get_value('INTERMEDIATE_CA_CERT_FILE')
server_key_file = get_value('server_key_file')
server_cert_file = get_value('server_cert_file')

# --------------Path to the directory storing certificates--------------
cert_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), get_value('cert_dir')))
rootCA_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ROOT_CA_DIR_NAME))
os.makedirs(cert_dir, exist_ok=True)
os.makedirs(INTERMEDIATE_CA_DIR_NAME, exist_ok=True)

# --------------Intermediate CA paths--------------
intermediate_ca_cert_path = os.path.abspath(os.path.join(os.path.join(Path(__file__).parent,INTERMEDIATE_CA_DIR_NAME, INTERMEDIATE_CA_CERT_FILE)))

intermediate_ca_key_path = os.path.abspath(os.path.join(Path(__file__).parent, INTERMEDIATE_CA_DIR_NAME, INTERMEDIATE_CA_KEY_FILE))

# --------------Path to server's private key and certificate--------------
RootCA_path = os.path.join(rootCA_dir, ROOT_CA_CERT_FILE)
server_key_path = os.path.join(rootCA_dir, server_key_file)
server_cert_path = os.path.join(cert_dir, server_cert_file)


def ensure_CA_file_exists():
    '''
Ensure intermediate CA exists
'''
    if not os.path.exists(intermediate_ca_cert_path) or not os.path.exists(intermediate_ca_key_path):
        raise FileNotFoundError("Intermediate CA certificate or key not found.")


def get_certificate_validity_period(cert_path):
    """
    Returns the remaining validity period of the certificate in cert_path.
    """
    try:
        # Run the OpenSSL command to get the expiry date
        result = subprocess.run(
            ["openssl", "x509", "-enddate", "-noout", "-in", cert_path],
            capture_output=True,
            text=True,
            check=True
        )

        # Extract the expiry date string
        expiry_date_str = result.stdout.strip().split("=")[1]

        # Parse the expiry date string into a datetime object
        expiry_date = datetime.strptime(
            expiry_date_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)

        # Get the current date and time in UTC
        current_date = datetime.now(timezone.utc)

        # Calculate the remaining validity period
        remaining_period = expiry_date - current_date

        return remaining_period
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during key or CSR generation: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def sign_csr(csr_data):
    """
    Signs a CSR using the Intermediate CA's certificate and private key.

    Args:
        csr_data (bytes): The CSR data in PEM format.

    Returns:
        bytes: The signed certificate in PEM format.
    """
    VALIDITY_DAYS = int(get_certificate_validity_period(intermediate_ca_cert_path).days)  # this a day behide itermediate ca expiry

    # Load Intermediate CA private key and certificate
    with open(intermediate_ca_cert_path, "rb") as cert_file, open(intermediate_ca_key_path, "rb") as key_file:
        intermediate_cert = x509.load_pem_x509_certificate(
            cert_file.read())
        intermediate_key = serialization.load_pem_private_key(
            key_file.read(), password=None)

    # Load the CSR
    csr = load_pem_x509_csr(csr_data)

    # Build and sign the certificate
    signed_cert = (
        CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(intermediate_cert.subject)
        .public_key(csr.public_key())
        .serial_number(random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        # 1-year validity
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=VALIDITY_DAYS))
        .sign(private_key=intermediate_key, algorithm=SHA256())
    )

    return signed_cert.public_bytes(serialization.Encoding.PEM)


@app.route('/<filename>', methods=['GET'])
def download_file(filename):
    """
    Handles requests to download a file from the certificate directory.
    """
    file_path = os.path.join(cert_dir, filename)
    if os.path.exists(file_path):
        return send_from_directory(cert_dir, filename, as_attachment=True)
    else:
        return "File not found", 404


@app.route('/submit-csr', methods=['POST'])
def process_csr():
    print("Processing request")
    """
    Handles CSR submission, signs it using the Intermediate CA, and returns both
    the signed certificate and Intermediate CA certificate in a single response.
    """

    if 'csr' not in request.files:
        return jsonify({"error": "CSR file is missing."}), 400

    csr_file = request.files['csr']
    try:
        # Read CSR content
        csr_data = csr_file.read()

        # Sign the CSR using the Intermediate CA
        signed_cert = sign_csr(csr_data)

        # Read Intermediate CA certificate
        with open(intermediate_ca_cert_path, "rb") as f, open(RootCA_path, 'rb') as rf:
            intermediate_cert = f.read()
            RootCA = rf.read()

        # Prepare response with both certificates
        response = {
            "signed_certificate": signed_cert.decode('utf-8'),
            "intermediate_certificate": intermediate_cert.decode('utf-8'),
            "CryptoshareRootCA": RootCA.decode('utf-8')
        }

        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": f"Failed to process CSR: {str(e)}"}), 500


def server(host="0.0.0.0:5000"):
    """
    Listen for incoming csr Request and process them
    Args:
    host: ip + port <i>For the server</i>
    """
    ensure_CA_file_exists()
    if ':' in host:
        ip, port = host.split(':')
    elif len(host) <= 4:
        ip, port = "0.0.0.0", host

    # Ensure the server has a self-signed certificate for HTTPS
    if not os.path.exists(server_key_path) or not os.path.exists(server_cert_path):
        print("Generating server key and certificate...")
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', server_key_path,
            '-out', server_cert_path,
            '-days', '365', '-nodes',
            '-subj', '/CN=CertServer'
        ])

    app.run(host=ip, port=int(port), ssl_context=(
        server_cert_path, server_key_path))


if __name__ == '__main__':
    ensure_CA_file_exists()
    # Ensure the server has a self-signed certificate for HTTPS
    if not os.path.exists(server_key_path) or not os.path.exists(server_cert_path):
        print("Generating server key and certificate...")
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', server_key_path,
            '-out', server_cert_path,
            '-days', '365', '-nodes',
            '-subj', '/CN=CertServer'
        ])

    app.run(host="0.0.0.0", port=5000, ssl_context=(
        server_cert_path, server_key_path))
