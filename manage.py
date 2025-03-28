#!/usr/bin/env python
import argparse
import os
import sys
import re
import threading
import subprocess
from ShareKit.net_scanner import get_ip_address
from utils.colors import (BLUE, IBLUE, GREEN, MAGENTA, RESET, DMAGENTA,
                          DBLUE, DGREEN, BWHITE, DWHITE, LBLUE, YELLOW, CYAN, IWHITE, RED)
from CryptoCA.RootCA import main as ca_init
from CryptoCA.IntermediateCA_self_monitor import monitor_intermediate_ca as intermiate_cert_monitor
from CryptoCA.CA_CSR_server import server as ca_csr_server
from ShareKit.EFS import share
from userKit.AutoCertsGen import main as user_cert_setup
from userKit.hostCertMonitor import monitor_certificate as self_cert_monitor
from userKit.export2p12 import create_PKCS12


def run_simulation(interface, device, server_mode=False):
    """
    Executes the simulation script in a separate network namespace.

    Args:
        interface (str): The name of the network namespace.
        device (str):  The name of the virtual ethernet device.
        server_mode (bool, optional): If True, starts the simulation in server mode. Defaults to False.

    Returns:
        bool: True on success, False on failure.  Returns None if server mode and server exited.
    """
    ip = get_ip_address(device)
    if not ip:
        print(
            f"Skipping simulation on {YELLOW}{interface}{RESET} because no IP address was found.")
        return False  # Exit if no IP address

    command = f"sudo ip netns exec {interface} python3 simulate.py --devip {ip}:9001"

    if server_mode:
        print(f"{DWHITE}Starting simulation server in namespace {YELLOW}{interface}{RESET} with command: {MAGENTA}{command}{RESET}")
    else:
        print(f"{DWHITE}Running simulation client in namespace {YELLOW}{interface}{RESET} with command: {MAGENTA}{command}{RESET}")

    try:
        # Use subprocess.Popen for non-blocking execution (for servers)
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if server_mode:
            # Wait for the server to start by looking for a specific output
            while True:
                if process.stdout:
                    line = process.stdout.readline()
                else:
                    line = ''
                if not line:
                    if process.poll() is not None:
                        # Server process has exited unexpectedly.
                        error_output = process.stderr.read()  # Read any error output
                        print(
                            f"Server in namespace {YELLOW}{interface}{RESET} exited prematurely. Error output:\n{RED}{error_output}{RESET}")
                        return None
                    continue  # Keep reading if the process is still running
                print(f"[{IBLUE}Server Output{RESET}]: {line.strip()}")  # print the server output
                if re.search(r"Press CTRL\+C to quit", line):  # Adjust this regex as needed
                    print(f"Server in namespace {CYAN}{interface}{RESET} started successfully.")
                    return process  # Return the process object
                elif re.search(r"error", line, re.IGNORECASE):
                    error_output = process.stderr.read()
                    print(
                        f"Server in namespace {YELLOW}{interface}{RESET} encountered an error. Error output:\n{RED}{error_output}{RESET}")
                    return None

        else:
            # For clients, wait for completion and get output
            process.wait()
            output, error = process.communicate()
            if process.returncode != 0:
                print(
                    f"Error running client in {YELLOW}{interface}{RESET}: {RED}{error}{RESET}")
                return False
            else:
                print(
                    f"Client in {YELLOW}{interface}{RESET} {GREEN}completed. {RESET}[{BLUE}Output{RESET}]:\n{output}")
                return True

    except subprocess.CalledProcessError as e:
        print(
            f"Error running simulation in namespace {YELLOW}{interface}{RESET}: {RED}{e}{RESET}")
        # Print stderr from the shell command
        print(f"Command output (stderr):\n{IWHITE}{e.stderr}{RESET}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description=f"""{BWHITE}CryptoSharePKI{RESET}: {LBLUE}Secure PKI powered file sharing manager.{RESET}
        \n{BWHITE}Usage{RESET}: {CYAN}python{RESET} manage.py <{YELLOW}command{RESET}> <{MAGENTA}subcommand{RESET}> [options]
        \n\nAvailable Commands:
        \n  init     Initialize RootCA setup
        \n  server   Start CA server
        \n  monitor  Monitor CA status
        \n  setup    Setup certification for self
        \n  share    File sharing operations
        \n  run      Run the Flask application""",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="command", help=f"{DMAGENTA}Sub-commands{RESET}")

    # Initialize RootCA setup
    init_parser = subparsers.add_parser(
        "init", help=f"{BLUE}Initialize RootCA setup{RESET}")

    # Server sub-commands
    server_parser = subparsers.add_parser(
        "server", help=f"{BLUE}Server operations{RESET}")
    server_subparsers = server_parser.add_subparsers(
        dest="server_type", help=f"{DMAGENTA}Server types{RESET}")

    server_root_parser = server_subparsers.add_parser(
        "root", help=f"{BLUE}Start Root CA server{RESET}")
    server_intermediate_parser = server_subparsers.add_parser(
        "intermediate", help=f"{BLUE}Start Intermediate CA server{RESET}")
    server_all_parser = server_subparsers.add_parser(
        "all", help=f"{BLUE}Start all CA servers{RESET}")

    # Monitor sub-commands
    monitor_parser = subparsers.add_parser(
        "monitor", help=f"{BLUE}Monitor CA status{RESET}")
    monitor_subparsers = monitor_parser.add_subparsers(
        dest="monitor_type", help=f"{DMAGENTA}Monitor types{RESET}")

    monitor_intermediate_parser = monitor_subparsers.add_parser(
        "intermediate", help=f"{BLUE}Monitor Intermediate CA{RESET}")
    monitor_root_parser = monitor_subparsers.add_parser(
        "root", help=f"{BLUE}Monitor Root CA{RESET}")
    monitor_self_parser = monitor_subparsers.add_parser(
        "self", help=f"{BLUE}Monitor self (Intermediate CA){RESET}")
    monitor_all_parser = monitor_subparsers.add_parser(
        "all", help=f"{BLUE}Monitor all CAs{RESET}")

    # Setup certification
    setup_parser = subparsers.add_parser(
        "setup", help=f"{BLUE}Setup certification for self{RESET}")

    # Share file server
    share_parser = subparsers.add_parser(
        "share", help=f"{BLUE}File sharing operations{RESET}")
    share_parser.add_argument(
        "-H",
        "--host",
        help=f"{BLUE}IP and port the server should run on eg 0.0.0.0:5000{RESET}",
    )
    share_parser.add_argument(
        "-Sm",
        "--simulate",
        nargs="*",
        help=f"{BLUE}Simulate device network sharing.{RESET}",
    )

    # Run Flask server
    run_parser = subparsers.add_parser(
        "run", help=f"{BLUE}Run the Flask application{RESET}")
    run_parser.add_argument(
        "-D", "--debug", action="store_true", help=f"{BLUE}Activate debug mode.{RESET}"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "init":
        print(
            f"[{BLUE}server{RESET}]: {GREEN}Initializing{YELLOW} Root CA{BLUE} && {YELLOW}Intermediate CA{RESET}"
        )
        ca_init()

    elif args.command == "setup":
        print(f"[{DBLUE}+{RESET}] {MAGENTA}Setting up user: {DGREEN}Self{RESET}")
        user_cert_setup()
        create_PKCS12()

    elif args.command == "run":
        if args.debug:
            os.system(
                "flask --app=ShareKit/EFS.py --debug run --host=0.0.0.0 --port=9001 --reload"
            )
        else:
            os.system(
                "flask --no-debug --app=ShareKit/EFS.py run --host=0.0.0.0 --port=9001 --reload"
            )

    elif args.command == "server":
        if not args.server_type:
            server_parser.print_help()
            return
        if args.server_type == "root" or args.server_type == "all":
            print(f"[{BLUE}server{RESET}]: {GREEN}Starting{YELLOW} Root CA{RESET}")
            ca_csr_server()
        if args.server_type == "intermediate" or args.server_type == "all":
            print(
                f"[{BLUE}server{RESET}]: {GREEN}Starting{YELLOW} Intermediate CA{RESET}")
            ca_csr_server()

    elif args.command == "monitor":
        if not args.monitor_type:
            monitor_parser.print_help()
            return
        if args.monitor_type == "intermediate":
            print(f"[{BLUE}MON{RESET}]: Target: {YELLOW}Intermediate CA{RESET}")
            intermiate_cert_monitor()
        elif args.monitor_type == "self":
            print(f"[{BLUE}MON{RESET}]: Target: {YELLOW}Self{RESET}")
            self_cert_monitor()
        elif args.monitor_type == "root":
            print(f"[{BLUE}MON{RESET}]: Target: {YELLOW}Root CA{RESET}")
            # Add root CA monitoring function call if needed.
            pass
        elif args.monitor_type == "all":
            print(f"[{BLUE}MON{RESET}]: Target: {YELLOW}ALL{RESET}")
            self_cert_monitor()
            intermiate_cert_monitor()

    elif args.command == "share":
        if args.simulate:
            devices = [f"veth{i}" for i in range(1, int(args.simulate[0]))]
            interfaces = [f"dev{i}" for i in range(1, int(args.simulate[0]))]

            threads = []
            for interface, device in zip(interfaces, devices):
                # Create a thread for each simulation
                thread = threading.Thread(
                    target=run_simulation, args=(interface, device))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            print(f"{GREEN}All simulations completed.{RESET}")

        elif args.host:
            print(
                f"[{BLUE}SHARE{RESET}]: Sharing with host: {GREEN}{args.host}{RESET}")
            share(host=args.host)
        else:
            print(f"[{BLUE}SHARE{RESET}]: {GREEN}Sharing files{RESET}")
            share()

    elif args.command == "run":
        if args.debug:
            os.system(
                "flask --app=ShareKit/EFS.py --debug run --host=0.0.0.0 --port=9001 --reload"
            )
        else:
            os.system(
                "flask --no-debug --app=ShareKit/EFS.py run --host=0.0.0.0 --port=9001 --reload"
            )
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nQuit!")
        sys.exit()
