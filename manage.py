import argparse
from AutoRootCA_PKI import main as AutoRoot
from IntermCA_self_monitor import monitor_intermediate_ca as intermiateMonitor
from CA_server import server
from ShareKit.EFS import share
import os


def main():
    parser = argparse.ArgumentParser(description="CryptoSharePKI manager")
    parser.add_argument('-init', action="store_true",
                        help="Initialize RootCA setup")
    parser.add_argument('-S', '--server', action="store_true",
                        help="Start Listener for Intermediate CA sign requests requests.")
    parser.add_argument('-sM', '--self_monitor', action="store_true",
                        help="Monitor self (IntermediateCA for expiry)")

    parser.add_argument('-SH', '--share', action="store_true",
                        help="Run file sharing server")

    parser.add_argument(
        '-H', '--host', help="IP and port the server should run on eg 0.0.0.0:5000")

    parser.add_argument('-R', '--run', action="store_true", help="Run the app.")
    parser.add_argument('-D', '--debug', action="store_true", help="Activate debug mode.")

    args = parser.parse_args()

    if args.init:
        AutoRoot()

    elif args.run:
        if args.debug:
            os.system(
                    "flask --app=ShareKit/EFS.py --debug run --host=0.0.0.0 --port=9001 --reload")
        else:
            os.system("flask --no-debug --app=ShareKit/EFS.py  run --host=0.0.0.0 --port=9001 --reload")

    elif args.server:
        server()

    elif args.self_monitor:
        intermiateMonitor()

    elif args.share:
        if args.host:
            share(host=args.host)
        else:
            share()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
