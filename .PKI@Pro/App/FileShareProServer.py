import configparser
import os
import subprocess
import time
import zipfile

import magic
from flask import (Flask, after_this_request, render_template, request,
                   send_from_directory)

app = Flask(__name__)

# --------------Create a ConfigParser object--------------
config = configparser.ConfigParser()

# --------------Read the .ini file--------------
config.read('config.ini')


# --------------Helper function to set a default section--------------
def set_default_section(config, section):
    if section not in config:
        raise ValueError(
            f"Section '{section}' does not exist in the configuration.")
    return lambda key: config.get(section, key)


# --------------Set default section to RootCAserver--------------
get_value = set_default_section(config, 'SHARES')

SHARED_FOLDER_NAME = get_value('SHARED_FOLDER')
UPLOAD_FOLDER_NAME = get_value('UPLOAD_FOLDER')

server_key_path = os.path.abspath(get_value('SERVER_KEY'))
server_cert_path = os.path.abspath(get_value('SERVER_CERT'))

SHARED_FOLDER = os.path.expanduser(SHARED_FOLDER_NAME)  # Expand the user directory

UPLOAD_FOLDER = os.path.abspath(UPLOAD_FOLDER_NAME)

os.makedirs(SHARED_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
template = 'index.html'


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        file.save(os.path.join(SHARED_FOLDER, file.filename))
        return "File uploaded successfully!", 200
    except Exception as e:
        print(str(e))
        return "An error occurred while processing your request."


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        fpath = os.path.join(os.path.join(UPLOAD_FOLDER, filename))
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

            return send_from_directory(SHARED_FOLDER, os.path.basename(output_zip), as_attachment=True)
        else:
            return "File or directory not found.", 404
    except Exception as e:
        raise
        print(str(e))
        return "An error occurred while processing your request."


@app.template_filter('is_directory')
def is_directory(path):
    try:
        return os.path.isdir(os.path.join(SHARED_FOLDER, path))
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


@app.route('/')
def list_files():
    try:
        files = os.listdir(SHARED_FOLDER)
        return render_template(template, files=files, os=os)
    except Exception as e:
        print(str(e))
        return None


if __name__ == "__main__":
    if not os.path.exists(server_key_path) or not os.path.exists(server_cert_path):
        print("Generating server key and certificate...")
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
            '-keyout', server_key_path,
            '-out', server_cert_path,
            '-days', '365', '-nodes',
            '-subj', '/CN=CertServer'
        ])
    app.run(host="0.0.0.0", port=9001, ssl_context=(
        server_cert_path, server_key_path))
# deveoped bt skye @wambua
