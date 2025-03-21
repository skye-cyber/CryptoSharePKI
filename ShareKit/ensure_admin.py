import pickle
import tempfile
import inspect
import os
import sys
import ctypes
import platform
import subprocess


def run_with_elevation():
    """Attempts to elevate privileges on Windows or Linux"""
    if platform.system() == "Windows":
        if ctypes.windll.shell32.IsUserAnAdmin():
            print("[INFO] Running as administrator")
        else:
            print("[INFO] Elevating privileges...")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    else:
        if os.geteuid() == 0:
            print("[INFO] Running as root")
        else:
            print("[INFO] Please run the script as root (using sudo)")
            os.system('sudo')
            os.seteuid(0)
    return


def drop_privileges():
    """Drops privileges on Unix-based systems"""
    if platform.system() == "Windows":
        print("[INFO] Cannot drop privileges on Windows")
    else:
        try:
            import pwd
            user = pwd.getpwuid(os.getuid())
            os.setuid(user.pw_uid)  # Drop to original user privileges
            print("[INFO] Dropped privileges successfully")
            return
        except Exception as e:
            print(f"[ERROR] Failed to drop privileges: {e}")


def elevate_and_run(func, *args, **kwargs):
    """
    Elevates privileges, runs a function in a separate process, and returns its result.
    The function's return value is serialized (pickled) and sent via stdout.
    """
    # Extract the function's source code
    func_code = inspect.getsource(func)
    module = inspect.getmodule(func)
    module_code = inspect.getsource(module) if module else ""
    # Extract import statements from the module (basic approach)
    imports = "\n".join(
        line for line in module_code.splitlines()
        if line.startswith("import") or line.startswith("from") and not line.endswith("relative")
    )

    # Ensure the function code is properly formatted
    func_code = "\n".join(
        line for line in func_code.splitlines() if line.strip())

    # Create a temporary script that will run the function and pickle its return value
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as temp_script:
        script_path = temp_script.name
        temp_script.write(f"{imports}\n\n{func_code}\n\n")
        # Write code to call the function and output its result via pickle
        temp_script.write("import sys, pickle\n")
        # Build the function call with passed arguments
        args_repr = ", ".join(repr(arg) for arg in args)
        kwargs_repr = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
        comma = ", " if args_repr and kwargs_repr else ""
        temp_script.write(
            f"result = {func.__name__}({args_repr}{comma}{kwargs_repr})\n")
        temp_script.write("sys.stdout.buffer.write(pickle.dumps(result))\n")

    try:
        if os.name == 'nt':  # Windows
            if ctypes.windll.shell32.IsUserAnAdmin():
                result = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True, text=False
                )
            else:
                # Elevate via PowerShell on Windows
                command = (
                    f'powershell -Command "Start-Process -Verb RunAs -FilePath \'{sys.executable}\' '
                    f'-ArgumentList \'{script_path}\'"'
                )
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=False
                )
        elif os.name == 'posix':  # Linux/macOS
            command = ["sudo", "-E", sys.executable, script_path]
            result = subprocess.run(
                command, capture_output=True, text=False
            )
            if result.stderr:
                print(result.stderr)
        else:
            raise OSError("Unsupported OS")

        # Deserialize and return the result from the temporary script
        try:
            response = pickle.loads(result.stdout)
            if not response:
                print(result.stderr)
            return response if response else []
        except Exception:
            pass

    finally:
        os.remove(script_path)


def privileged_task():
    return [{"return": "Privileged operation completed."}]


if __name__ == "__main__":
    output = elevate_and_run(privileged_task)
    print(output)
