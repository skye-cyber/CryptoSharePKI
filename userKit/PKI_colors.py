from colorama import Fore, init
import platform

init(autoRESET=True)

# Determine color constants based on the operating system
if platform.system().lower() == 'windows':
    GREEN = Fore.GREEN
    BLUE = Fore.BLUE
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    RESET = Fore.RESET
elif platform.system().lower() == 'linux':
    RED = "\033[3;2;91m"
    BLUE = "\033[3;2;94m"
    CYAN = "\033[3;2;96m"
    GREEN = "\033[3;2;92m"
    MAGENTA = "\033[3;2;95m"
    YELLOW = "\033[3;2;93m"
    RESET = "\033[0m"
