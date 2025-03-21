import os
import zipfile
import time
import magic
import configparser
from flask import (Flask, after_this_request, render_template, request, jsonify,
                   send_from_directory, abort)
from pathlib import Path
from .net_scanner import main as scanner

app = Flask(__name__)

# --------------Create a ConfigParser object--------------
config = configparser.ConfigParser()

# --------------Read the .ini file--------------
conf_path = os.path.join(os.path.relpath(Path(__file__).parent), "sharekit-conf.ini")
config.read(conf_path)


# --------------Helper function to set a default section--------------
def set_default_section(config, section):
    if section not in config:
        raise ValueError(
            f"Section '{section}' does not exist in the configuration.")
    return lambda key: config.get(section, key)


# --------------Set default section to RootCAserver--------------
get_value = set_default_section(config, 'ShareKit')


SHARED_FOLDER = get_value("shared-Folder")
if not SHARED_FOLDER:
    env = os.getenv("ShareKit_Shared_Folder")
    SHARED_FOLDER = env if env else "~/Documents"

SHARED_FOLDER = os.path.expanduser(SHARED_FOLDER)  # Expand the user directory
os.makedirs(SHARED_FOLDER, exist_ok=True)

template = 'index.html'

app = Flask(__name__, template_folder="App/templates",
            static_folder="App/static")  # Custom static folder)

devices = []
# app.config['SHARED_FOLDER'] = SHARED_FOLDER


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
        return "An error occurred while processing your request."


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
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


@app.route('/view/<path:dir>', methods=['GET'])
def open_dir(dir):
    try:
        path = os.path.join(SHARED_FOLDER, dir)

        if not os.path.exists(path):  # Check if path exists
            abort(404)  # Return 404 if path doesn't exist

        if not os.path.isdir(path):
            return [path]  # If it's a file, return the file path

        items = []
        for item in os.listdir(path):
            items.append(os.path.join(path, item))

        return render_template(template, files=items, os=os)

    except Exception as e:
        print(str(e))
        abort(500)  # Return 500 for internal server error


@app.route('/')
def net_devices():
    global devices
    try:
        if not devices:
            devices = scanner('wlan0')
        return render_template(template, devices=devices, os=os)
    except Exception as e:
        raise
        print(str(e))
        return None


@app.route('/<device>')
def show_device_shares(device):
    try:
        files = os.listdir(SHARED_FOLDER)
        return render_template(template, files=files, os=os)
    except Exception as e:
        print(str(e))
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


def share(host="0.0.0.0:9001"):
    if ':' in host:
        ip, port = host.split(':')
    elif len(host) <= 4:
        ip, port = "0.0.0.0", host
    app.run(host=ip, port=int(port))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9001)
