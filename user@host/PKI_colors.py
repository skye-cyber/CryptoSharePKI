from colorama import Fore, init
import platform

init(autoreset=True)

# Determine color constants based on the operating system
if platform.system().lower() == 'windows':
    green = Fore.GREEN
    blue = Fore.BLUE
    red = Fore.RED
    yellow = Fore.YELLOW
    cyan = Fore.CYAN
    magenta = Fore.MAGENTA
    reset = Fore.RESET
elif platform.system().lower() == 'linux':
    red = "\033[3;2;91m"
    blue = "\033[3;2;94m"
    cyan = "\033[3;2;96m"
    green = "\033[3;2;92m"
    magenta = "\033[3;2;95m"
    yellow = "\033[3;2;93m"
    reset = "\033[0m"
