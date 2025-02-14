import os
import zipfile
import time
import magic
from flask import (Flask, after_this_request, render_template, request,
                   send_from_directory)

app = Flask(__name__)
UPLOAD_FOLDER = "~/Documents"  # "/shared_docs"
UPLOAD_FOLDER = os.path.expanduser(UPLOAD_FOLDER)  # Expand the user directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
template = 'index.html'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))
        return "File uploaded successfully!", 200
    except Exception as e:
        print(str(e))
        return "An error occurred while processing your request."


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        fpath = os.path.join(os.path.join(UPLOAD_FOLDER, filename))
        if os.path.isfile(fpath):
            return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
        elif os.path.isdir(fpath):
            # Create a ZipFile object in write mode
            output_zip = os.path.join(UPLOAD_FOLDER, f"{filename}.zip")

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
                output_zip_path = os.path.join(UPLOAD_FOLDER, output_zip)
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

            return send_from_directory(UPLOAD_FOLDER, os.path.basename(output_zip), as_attachment=True)
        else:
            return "File or directory not found.", 404
    except Exception as e:
        raise
        print(str(e))
        return "An error occurred while processing your request."


@app.template_filter('is_directory')
def is_directory(path):
    try:
        return os.path.isdir(os.path.join(UPLOAD_FOLDER, path))
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
        mime_type = mime.from_file(os.path.join(UPLOAD_FOLDER, path))
        return mime_type.split('/')[0] or 'application'
    except Exception as e:
        print(str(e))
        return None


@app.route('/')
def list_files():
    try:
        files = os.listdir(UPLOAD_FOLDER)
        return render_template(template, files=files, os=os)
    except Exception as e:
        print(str(e))
        return None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9001)
