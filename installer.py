import os
import platform
import subprocess
import sys

# Platform-specific paths
current_os = platform.system().lower()


def run_installer(installer_path):
    print("Running OpenSSL installer...")
    try:
        subprocess.run([installer_path, "/silent", "/verysilent",
                       "/sp-", "/suppressmsgboxes"], check=True)
        print("OpenSSL installation completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running OpenSSL installer: {e}")
        sys.exit(1)


def add_to_path(open_ssl_bin_path):
    print("Adding OpenSSL to PATH environment variable...")
    try:
        # Use os.environ to modify PATH dynamically in the script
        os.environ["PATH"] += os.pathsep + open_ssl_bin_path
        print("OpenSSL added to PATH.")
    except Exception as e:
        print(f"Error adding OpenSSL to PATH: {e}")
        sys.exit(1)


def verify_installation():
    print("Verifying OpenSSL installation...")
    try:
        result = subprocess.run(['openssl', 'version'],
                                check=True, capture_output=True, text=True)
        print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error verifying OpenSSL installation: {e}")
        sys.exit(1)


def main():
    installer_path = os.path.join(os.getcwd(), 'Win64OpenSSL_Light-3_4_0.exe')
    run_installer(installer_path)

    # Adjust this path if necessary
    open_ssl_bin_path = r'C:\Program Files\OpenSSL-Win64\bin'
    add_to_path(open_ssl_bin_path)
    verify_installation()


if __name__ == "__main__":
    if current_os == "windows":
        main()
    else:
        print("This is an OpenSSL installation for Windows only")
