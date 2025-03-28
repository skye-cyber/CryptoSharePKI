import os
import zipfile
import time
import magic
from flask import (Flask, after_this_request, redirect, render_template, request, jsonify,
                   send_from_directory, abort, session)
from pathlib import Path
from .net_scanner import main as scanner
from .net_scanner import get_correct_local_ip
from .read_config import _set_section_
from .server_cert import EFSCert
from ssl import SSLContext
import ssl
import requests
from utils.colors import RED, RESET
# from OpenSSL import SSL as ssl

app = Flask(__name__)

get_value = _set_section_()

# --------------Set default server cert && key--------------
CSR_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), get_value("server_csr")))

SHARED_FOLDER = get_value("shared-Folder")
if not SHARED_FOLDER:
    env = os.getenv("ShareKit_Shared_Folder")
    SHARED_FOLDER = env if env else "~/Documents"

SHARED_FOLDER = os.path.expanduser(SHARED_FOLDER)  # Expand the user directory

os.makedirs(SHARED_FOLDER, exist_ok=True)

os.makedirs(os.path.dirname(CSR_PATH), exist_ok=True)

ca_cert_bundle = os.path.abspath(os.path.join(
    os.path.dirname(__file__), get_value("ca_bundle")))

template = 'index.html'

app = Flask(__name__, template_folder="App/templates",
            static_folder="App/static",
            static_url_path="/static")  # Custom static folder)

app.secret_key = "shadow-wiskozin-nil@now-sel"

self_ip = "192.168.1.101"  # get_correct_local_ip()

devices = []
# app.config['SHARED_FOLDER'] = SHARED_FOLDER


def is_remote(host):
    global self_ip
    try:
        if not self_ip:
            self_ip = get_correct_local_ip()
        print(host, self_ip)
        return (host != self_ip)
    except Exception as e:
        print(e)


@app.route('/static/<path:filename>')
def custom_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'App/static'), filename)


@app.route('/<path:dir>', methods=['GET'])
def open_svg_dir(dir):
    try:
        path = os.path.join(Path(__file__).parent, dir)

        if not os.path.exists(path):
            abort(404)

        if not os.path.isdir(path):
            abort(400)  # bad request if it's not a directory

        svg_files = []
        for filename in os.listdir(path):
            if filename.lower().endswith('.svg'):
                svg_files.append(os.path.join(path, filename))

        return render_template(template, svg_files=svg_files)

    except Exception as e:
        print(str(e))
        abort(500)


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        file.save(os.path.join(SHARED_FOLDER, file.filename))
        return "File uploaded successfully!", 200
    except Exception as e:
        print(str(e))
        return "An error occurRED while processing your request."


@app.route('/download/<device>/<path:filename>', methods=['GET'])
def download_file(device, filename):
    try:

        fpath = os.path.join(os.path.join(SHARED_FOLDER, filename))

        if os.path.isfile(fpath):
            return send_from_directory(SHARED_FOLDER, filename, as_attachment=True)
        elif os.path.isdir(fpath):
            # Create a ZipFile object in write mode
            output_zip = os.path.join(SHARED_FOLDER, f"{filename}.zip")

            with zipfile.ZipFile(output_zip, 'w') as zipf:
                # Walk through the directory and add files to the zip
                for root, _, files in os.walk(fpath):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Write the file to the zip file with a relative path
                        zipf.write(file_path, os.path.relpath(
                            file_path, start=fpath))

            # Function to delete the zip file after it has been sent
            @after_this_request
            def remove_file(response):
                output_zip_path = os.path.join(SHARED_FOLDER, output_zip)
                try:
                    while True:
                        # Ensure the response is complete before deleting the file
                        if response.status_code == 200:
                            try:
                                print(f"Deleting {output_zip_path}")
                                os.remove(output_zip_path)
                                break
                            except Exception as e:
                                print(f"Error removing file: {e}")
                        time.sleep(2)
                except Exception as e:
                    print(e)
                return response

            return send_from_directory(SHARED_FOLDER, os.path.basename(output_zip), device=device, as_attachment=True)
        else:
            return "File or directory not found.", 404
    except Exception as e:
        raise
        print(str(e))
        return "An error occurRED while processing your request."


@app.template_filter('is_directory')
def is_directory(path):
    try:
        is_dir = False
        path = path[1:] if path.startswith('/') else path
        fpath = os.path.join(SHARED_FOLDER, path)
        is_dir = os.path.isdir(fpath)
        return is_dir
    except Exception as e:
        print(str(e))
        return None


@app.template_filter('mime_type')
def get_mime_type(path):
    """
    Determine the MIME type of a file based on its extension.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The MIME type of the file or 'application/octet-stream' if unknown.
    """
    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(os.path.join(SHARED_FOLDER, path))
        return mime_type.split('/')[0] or 'application'
    except Exception as e:
        print(str(e))
        return None


@app.template_filter('split')
def split_str(obj, delimiter=SHARED_FOLDER):
    _new = obj.split(delimiter)[-1]
    _str = _new[1:] if _new.startswith('/') else _new
    return _str


@app.route('/view/<device>/<path:dir>', methods=['GET'])
def open_dir(device, dir):
    try:

        path = os.path.join(SHARED_FOLDER, dir)
        if not os.path.exists(path):  # Check if path exists
            abort(404)  # Return 404 if path doesn't exist

        if not os.path.isdir(path):
            return [path]  # If it's a file, return the file path

        print(path)
        files = []
        for item in os.listdir(path):
            files.append(os.path.join(path, item))

        return render_template(template, files=files, device=device, os=os)

    except Exception as e:
        print(str(e))
        abort(500)  # Return 500 for internal server error


@app.route('/files/<device>', methods=['GET'])
def shared(device):
    try:
        path = os.path.abspath(SHARED_FOLDER)
        if not os.path.exists(path):  # Check if path exists
            abort(404)  # Return 404 if path doesn't exist

        if not os.path.isdir(path):
            return [path]  # If it's a file, return the file path

        files = []
        for item in os.listdir(path):
            files.append(os.path.join(path, item))
        return render_template(template, files=files, device=device, os=os)

    except Exception as e:
        print(str(e))
        abort(500)  # Return 500 for internal server error


@app.route('/')
def net_devices():
    global devices
    try:
        if not devices:
            devices = scanner(interface='wlan0', simulate=True)
        return render_template(template, devices=devices, os=os)
    except Exception as e:
        raise
        print(str(e))
        return None


@app.route('/<device>', methods=["GET"])
def show_device_shares(device):
    """
    Contacts the target device at `device_ip` and retrieves its shared files.
    """
    try:
        if is_remote(device):
            session["device"] = device
            remote_url = f"https://{device}:9001/files/{device}"
            # Redirect the client to the remote URL.
            # The client's browser will then perform the HTTPS request and handle SSL verification.
            return redirect(remote_url)
        else:
            files = os.listdir(SHARED_FOLDER)
            return render_template(template, files=files, device=device, os=os)
    except Exception as e:
        raise
        print(f"{RED}{e}{RESET}")
        return None


@app.route('/shared/walk')
def get_shared_files():
    try:
        files_ls = []
        files_ls = [file for _, _, files in os.walk(
            SHARED_FOLDER) for file in files]
        return jsonify(files_ls)
    except Exception as e:
        print(str(e))
        return None


@app.route('/shared/walk/path')
def get_shared_file_paths():
    try:
        files_ls = []
        for root, dirs, files in os.walk(SHARED_FOLDER):
            for file in files:
                _files = os.path.join(root, file)
                files_ls.append(_files)
        return jsonify(files_ls)
    except Exception as e:
        print(str(e))
        return None


@app.route('/shared/list_dir/<dir>')
def _list_dir(dir):
    try:
        for root, dirs, files in os.walk(SHARED_FOLDER):
            for _dir in dirs:
                if str(_dir) == str(dir):
                    f_dir = os.path.join(root, _dir)
                    files = os.listdir(f_dir)
        return jsonify(files)
    except Exception as e:
        print(str(e))
        return None


@app.template_filter('get_icon')
def get_icon(dev_os):
    if dev_os.lower().startswith('linux'):
        return 'images/linux.png'
    elif dev_os.lower() == "window":
        return 'images/win10.jpeg'
    else:
        return 'images/default-icon.png'


def communicate_remote(remote_url):
    try:
        response = requests.get(remote_url, timeout=6, verify=ca_cert_bundle)
        response.raise_for_status()
        # Return the HTML page from the remote device
        print(response)
        return response.text
    except requests.RequestException:
        raise
        return False


def info_callback(connection, where, ret):
    """
    Set an info callback to get more detailed information during the handshake.
    This function hooks into SSL state changes.
    The callback receives parameters that can help you trace the handshake steps.
    Args:
    connection
    where
    ret
    .
    Returns:
    None
    """
    if where & ssl.SSL_CB_HANDSHAKE_START:
        print("Handshake started")
    if where & ssl.SSL_CB_HANDSHAKE_DONE:
        print("Handshake finished")
    # You can print additional state information here.
    # Note: The callback is called for various SSL events.
    print("where:", where, "ret:", ret)


def set_cert_ss_context():
    """
    Configures the SSL context for the server, enabling client certificate authentication.

    Returns:
        ssl.SSLContext: The configuRED SSL context.
    """
    # 1. Load Server Certificate and Key:
    #    -  This is the certificate that the server will present to clients.
    #    -  It should be the certificate that was signed by your Intermediate CA
    #       (i.e.,  the one issued to your Flask server).
    server_cert_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), get_value("server_signed_cert")))
    server_key_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), get_value("server_key")))
    # This ensures compatibility with newer TLS versions (e.g., TLS 1.3).
    context = SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Enforce strong security settings
    # This enforces modern, secure cipher algorithms.
    context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20")

    context.load_cert_chain(certfile=server_cert_path, keyfile=server_key_path)

    # 2. Load CA Certificate for Client Verification:
    #    -  This is the certificate of the CA that signed the *client* certificates.
    #    -  The server uses this to verify the authenticity of the certificates presented by clients.
    #    -  This should be your Intermediate CA certificate.
    # intermediate_ca_cert_path = os.path.abspath(os.path.join(os.path.dirname(__file__), get_value("intermediate_ca_cert")))
    context.load_verify_locations(cafile=ca_cert_bundle)

    # 3.  Require Client Certificates:
    #     -  This setting is crucial for enforcing client certificate authentication.
    #     -  The server will reject connections from clients that do not present a valid certificate.
    context.verify_mode = ssl.CERT_REQUIRED

    # context.set_info_callback(info_callback)

    return context


def share(host="0.0.0.0:9001"):
    if ':' in host:
        ip, port = host.split(':')
    elif len(host) <= 4:
        ip, port = "0.0.0.0", host

    check_cert = EFSCert().is_valid_cert()

    ca_bundle = EFSCert().ensure_ca_bundle()

    if all((check_cert, ca_bundle)):
        app.run(host=ip, port=int(port), debug=True,
                ssl_context=set_cert_ss_context())


if __name__ == "__main__":
    check_cert = EFSCert().generate_cert()

    if check_cert:
        app.run(host="0.0.0.0", port=9001, ssl_context=set_cert_ss_context())
