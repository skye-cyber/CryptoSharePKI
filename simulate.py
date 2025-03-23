from ShareKit.EFS import share
import argparse


def _exec_():
    parser = argparse.ArgumentParser(description="CryptoSharePKI manager")
    parser.add_argument('-dip', '--devip',
                        help="Simulate device network sharing.")

    args = parser.parse_args()
    try:
        if args.devip:
            share(host=args.devip)  # Corrected to use `args.devip`
        else:
            share()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    _exec_()
