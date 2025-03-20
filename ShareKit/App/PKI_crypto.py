r"""
File Encryption and Decryption Script with Directory Monitoring

Features:
1. Watches a shared folder (via SMB or local) for file changes.
2. Encrypts all newly created files with the public key of the originating system.
3. Decrypts encrypted files when opened and re-encrypts them after closure.
4. Logs all encryption, decryption, and file-related events.

---

Setting Up an SMB Shared Folder:

1. **On Unix/Linux**:
   - Install Samba:
     ```
     sudo apt update
     sudo apt install samba
     ```
   - Configure Samba to share a folder:
     - Edit the Samba configuration file:
       ```
       sudo nano /etc/samba/smb.conf
       ```
     - Add the following:
       ```
       [shared_folder]
       path = /path/to/shared_folder
       browsable = yes
       writable = yes
       read only = no
       guest ok = yes
       ```
     - Restart Samba:
       ```
       sudo systemctl restart smbd
       ```
     - Access the shared folder on other machines:
       ```
       smb://<server_ip>/shared_folder
       ```

2. **On Windows**:
   - Right-click the folder → *Properties* → *Sharing* → *Advanced Sharing* → Enable sharing.
   - Assign appropriate permissions (e.g., Everyone for testing).
   - Access the shared folder:
     ```
     \\<server_ip>\<shared_folder>
     ```

---

Script Configuration:
- Set `WATCHED_DIR` to the mounted shared folder.
- Ensure `PUBLIC_KEY_STORE` contains public keys of machines in the format `<machine_identity>.pem`.

Dependencies:
- cryptography
- watchdog
- logging

Run:
- Mount the shared folder and run the script to start monitoring.
"""

import logging
import os
import subprocess
import tempfile
import time

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Configure logging
logging.basicConfig(
    filename="PKI_crypto.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Configuration
WATCHED_DIR = "/mnt/shared_folder"  # Path to the mounted shared folder
# Path to the public key directory
PUBLIC_KEY_STORE = "/mnt/shared_folder/public_keys"
PRIVATE_KEY_PATH = "private_key.pem"  # Path to the private key for decryption
ENCRYPTED_EXTENSION = ".enc"  # Extension for encrypted files

# Load the private key
with open(PRIVATE_KEY_PATH, "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(), password=None
    )


class FileEncryptDecryptHandler(FileSystemEventHandler):
    def on_created(self, event):
        """
        Handle newly created files in the watched directory.
        """
        if event.is_directory:
            return
        self.encrypt_file(event.src_path)

    def on_modified(self, event):
        """
        Handle file modifications in the watched directory.
        """
        if event.is_directory:
            return
        if event.src_path.endswith(ENCRYPTED_EXTENSION):
            self.decrypt_and_open(event.src_path)

    def encrypt_file(self, file_path):
        """
        Encrypts a file using the public key of the originating system.

        Args:
            file_path (str): Path to the file to encrypt.
        """
        if file_path.endswith(ENCRYPTED_EXTENSION):
            return  # Skip already encrypted files

        # Identify the originating system (machine identity)
        machine_identity = self.get_machine_identity(file_path)
        if not machine_identity:
            logging.warning(
                f"Could not identify the originating system for {file_path}")
            return

        # Fetch the public key
        public_key_path = os.path.join(
            PUBLIC_KEY_STORE, f"{machine_identity}.pem")
        if not os.path.exists(public_key_path):
            logging.error(
                f"Public key not found for machine: {machine_identity}")
            return

        try:
            # Load the public key
            with open(public_key_path, "rb") as key_file:
                public_key = serialization.load_pem_public_key(key_file.read())

            # Read plaintext
            with open(file_path, "rb") as f:
                plaintext = f.read()

            # Encrypt the file
            ciphertext = public_key.encrypt(
                plaintext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # Save encrypted file
            encrypted_file_path = file_path + ENCRYPTED_EXTENSION
            with open(encrypted_file_path, "wb") as f:
                f.write(ciphertext)

            # Delete the original file
            os.remove(file_path)
            logging.info(f"File encrypted: {encrypted_file_path}")

        except Exception as e:
            logging.error(f"Error encrypting file {file_path}: {e}")

    def decrypt_and_open(self, file_path):
        """
        Decrypts an encrypted file and opens it with the default application.

        Args:
            file_path (str): Path to the encrypted file.
        """
        try:
            # Read ciphertext
            with open(file_path, "rb") as f:
                ciphertext = f.read()

            # Decrypt the file
            plaintext = private_key.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # Save the plaintext to a temporary file
            temp_dir = tempfile.gettempdir()
            decrypted_file_path = os.path.join(temp_dir, os.path.basename(
                file_path).replace(ENCRYPTED_EXTENSION, ""))
            with open(decrypted_file_path, "wb") as f:
                f.write(plaintext)

            logging.info(
                f"Decrypted file saved temporarily at {decrypted_file_path}")

            # Open the file with the default application
            if os.name == "nt":  # Windows
                os.startfile(decrypted_file_path)
            elif os.name == "posix":  # Linux/macOS
                subprocess.run(["xdg-open", decrypted_file_path], check=False)
            else:
                logging.error("Unsupported OS. Cannot open the file.")

            # Wait for the user to close the file
            input("Press Enter to re-encrypt and close the file...")

            # Re-encrypt the file
            self.encrypt_file(decrypted_file_path)

            # Securely delete the temporary plaintext file
            os.remove(decrypted_file_path)
            logging.info(
                f"Temporary file {decrypted_file_path} deleted securely.")

        except Exception as e:
            logging.error(f"Error during decryption or opening: {e}")

    @staticmethod
    def get_machine_identity(file_path):
        """
        Extracts the machine identity from the file's metadata or path.
        For SMB, the machine name is often part of the share path.

        Args:
            file_path (str): Path to the file.

        Returns:
            str: Machine identity if available, else None.
        """
        try:
            # Extract machine identity from SMB share path (if applicable)
            if "\\\\" in file_path or "//" in file_path:
                parts = file_path.replace("\\", "/").split("/")
                if len(parts) > 2:
                    return parts[2]  # Machine name in SMB path
        except Exception as e:
            logging.error(f"Error extracting machine identity: {e}")
        return None


def start_observer():
    """
    Starts the directory observer.
    """
    event_handler = FileEncryptDecryptHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCHED_DIR, recursive=True)
    observer.start()

    logging.info(f"Watching directory: {WATCHED_DIR}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    # Ensure the watched directory exists
    os.makedirs(WATCHED_DIR, exist_ok=True)
    os.makedirs(PUBLIC_KEY_STORE, exist_ok=True)

    # Start the directory observer
    start_observer()
