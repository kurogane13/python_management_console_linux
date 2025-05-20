import os
import subprocess
import datetime
import re
import glob
import shutil
from pathlib import Path
from colorama import Fore, Style, init
import sys

init(autoreset=True)

LOG_DIR = Path("python_linux_versions")
LOG_DIR.mkdir(exist_ok=True)

def log_action(log_name, message, output=""):
    timestamp = datetime.datetime.now()
    log_file = LOG_DIR / f"{log_name}_{timestamp.strftime('%Y%m%d_%H_%M_%S')}.log"
    time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, "a") as f:
        f.write(f"[{time_str}] {message}\n")
        if output:
            f.write(f"{output}\n\n")

def get_linux_distro():
    if Path("/etc/os-release").exists():
        with open("/etc/os-release") as f:
            data = f.read()
            if "ID=ubuntu" in data or "ID=debian" in data:
                return "apt"
            elif any(distro in data for distro in ["centos", "rhel", "fedora", "almalinux"]):
                return "yum"
    return None

def find_installed_python_versions():
    seen = set()
    versions = []
    for path in os.environ["PATH"].split(":"):
        if Path(path).exists():
            for file in os.listdir(path):
                if re.fullmatch(r"python3(\.\d+)?", file):
                    full_path = Path(path) / file
                    if os.access(full_path, os.X_OK):
                        version_output = subprocess.getoutput(f"{full_path} --version")
                        entry = (version_output.strip(), str(full_path))
                        if entry not in seen:
                            seen.add(entry)
                            versions.append(entry)
    return sorted(versions)

def list_python_versions():
    versions = find_installed_python_versions()
    print(Fore.CYAN + "\nInstalled Python Versions:\n")
    output = ""
    if not versions:
        output = "No Python versions found."
        print(Fore.YELLOW + output)
    else:
        for version, path in versions:
            line = f"{version} -> {path}"
            output += line + "\n"
            print(Fore.GREEN + line)
    log_action("list_python_versions", "Listed all installed Python versions.", output.strip())

def install_python_version():
    list_python_versions()
    version = input(Fore.CYAN + "\nEnter Python version to install (e.g., 3.9): ")
    package_manager = get_linux_distro()
    if not package_manager:
        print(Fore.RED + "Unsupported Linux distribution.")
        return

    print(Fore.YELLOW + f"\nInstalling Python {version}...")
    if package_manager == "apt":
        output = subprocess.getoutput(f"sudo apt update && sudo apt install -y python{version}")
    else:
        output = subprocess.getoutput(f"sudo yum install -y python{version}")

    print(Fore.GREEN + output)
    log_action("install_python_version", f"Installed Python {version}", output)

def uninstall_python_version():
    list_python_versions()
    version = input(Fore.CYAN + "\nEnter Python version to uninstall (e.g., 3.9): ")
    package_manager = get_linux_distro()
    if not package_manager:
        print(Fore.RED + "Unsupported Linux distribution.")
        return

    print(Fore.YELLOW + f"\nUninstalling Python {version}...")
    if package_manager == "apt":
        output = subprocess.getoutput(f"sudo apt remove -y python{version}")
    else:
        output = subprocess.getoutput(f"sudo yum remove -y python{version}")

    bin_path = Path(f"/usr/bin/python{version}")
    remove_output = ""
    if bin_path.exists():
        rm_result = subprocess.getoutput(f"sudo rm -f {bin_path}")
        remove_output = f"Removed binary at {bin_path}\n{rm_result}"
        print(Fore.GREEN + remove_output)

    full_output = output + "\n" + remove_output
    log_action("uninstall_python_version", f"Uninstalled Python {version}", full_output.strip())

def show_all_python_paths():
    versions = find_installed_python_versions()
    print(Fore.CYAN + "\nAll Installed Python Binaries and Paths:\n")
    output = ""
    for version, path in versions:
        line = f"{version}: {path}"
        print(Fore.GREEN + line)
        output += line + "\n"
    log_action("show_all_paths", "Displayed all Python binary paths.", output.strip())

def show_path_for_version():
    version = input(Fore.CYAN + "\nEnter Python version to lookup path (e.g., 3.9): ")
    versions = find_installed_python_versions()
    found = False
    output = ""
    for v, path in versions:
        if f"Python {version}" in v:
            output = f"Path for Python {version}: {path}"
            print(Fore.GREEN + output)
            found = True
            break
    if not found:
        output = f"No path found for Python {version}"
        print(Fore.RED + output)
    log_action("show_path_for_version", f"Checked path for version {version}", output)

def list_installed_packages(version):
    print()
    result = subprocess.getoutput(f"python{version} -m pip list")
    print(Fore.GREEN + result)
    log_action("list_installed_packages", f"Listed pip packages for Python {version}", result)

def list_installed_modules(version):
    print()
    result = subprocess.getoutput(f'python{version} -c "help(\'modules\')"')
    print(Fore.GREEN + result)
    log_action("list_installed_modules", f"Listed modules for Python {version}", result)

def generate_requirements(version):
    output_path = Path(f"./requirements_python{version}.txt")
    os.system(f"python{version} -m pip freeze > {output_path}")
    with open(output_path) as f:
        content = f.read()
    print(Fore.GREEN + f"\nrequirements.txt generated at: {output_path}\n")
    print(content)
    log_action("generate_requirements", f"Generated requirements.txt for Python {version}", content)

def search_module(version):
    module = input(Fore.CYAN + "Enter module name to search: ").strip()
    try:
        # Check if installed
        output = subprocess.check_output(
            [f"python{version}", "-m", "pip", "show", module],
            stderr=subprocess.DEVNULL
        ).decode().strip()

        if output:
            print(Fore.GREEN + f"Module '{module}' is already installed for Python {version}.")
            log_action("search_module", f"Module '{module}' FOUND (installed) for Python {version}")
            return
    except subprocess.CalledProcessError:
        pass  # Not installed, move on to checking availability

    print(Fore.YELLOW + f"Module '{module}' is not installed. Checking availability on PyPI...")

    try:
        output = subprocess.check_output(
            [f"python{version}", "-m", "pip", "index", "versions", module],
            stderr=subprocess.STDOUT
        ).decode()

        if "Available versions" in output:
            print(Fore.GREEN + f"{output}")
            log_action("search_module", f"Module '{module}' AVAILABLE (not installed) for Python {version}")
        else:
            print(Fore.RED + f"Module '{module}' not found on PyPI for Python {version}.")
            log_action("search_module", f"Module '{module}' NOT found (PyPI) for Python {version}")
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Error checking module availability: {e.output.decode().strip()}")
        log_action("search_module", f"Error checking module '{module}' for Python {version}")

def install_module(version):
    module = input(Fore.CYAN + "Enter module name to install: ")
    print(Fore.YELLOW + f"Checking availability of module '{module}' for Python {version}...")
    # Use pip search index; handle errors more gracefully
    check = subprocess.getoutput(f"python{version} -m pip index versions {module} 2>&1")
    if "ERROR" in check or "WARNING" in check:
        print(Fore.RED + f"Module '{module}' not found in pip index or not available.")
        log_action("install_module", f"Failed to locate module {module} for Python {version}", check)
        return

    print(Fore.GREEN + check)
    confirm = input(Fore.CYAN + f"Install '{module}' for Python {version}? (y/n): ")
    if confirm.lower() == 'y':
        result = subprocess.getoutput(f"python{version} -m pip install {module}")
        print(Fore.GREEN + result)
        log_action("install_module", f"Installed module {module} in Python {version}", result)

def search_installed_module():
    module = input(Fore.CYAN + "Enter module name to search (installed only): ").strip()
    found_versions = []

    # Look for all python3.x binaries
    python_binaries = sorted(glob.glob("/usr/bin/python3.*"))

    if not python_binaries:
        print(Fore.RED + "No Python 3.x versions found.")
        return

    print(Fore.YELLOW + f"\nChecking if module '{module}' is installed in the following Python versions:")

    for python_bin in python_binaries:
        version = python_bin.split("/")[-1]
        if not shutil.which(python_bin):
            continue

        try:
            output = subprocess.check_output(
                [python_bin, "-m", "pip", "show", module],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            if output:
                print(Fore.GREEN + f"\n✔ Module '{module}' is INSTALLED for {version}:")
                print(output)
                found_versions.append(version)
        except subprocess.CalledProcessError:
            print(Fore.RED + f"✘ Module '{module}' is NOT installed for {version}.")

    if not found_versions:
        log_action("search_installed_module", f"Module '{module}' not installed in any Python version.")
    else:
        log_action("search_installed_module", f"Module '{module}' installed in: {', '.join(found_versions)}")

def uninstall_module(version):
    module = input(Fore.CYAN + "Enter module name to uninstall: ")
    installed = subprocess.getoutput(f"python{version} -m pip show {module}")
    if not installed or "Name:" not in installed:
        print(Fore.RED + f"Module '{module}' is NOT installed in Python {version}")
        log_action("uninstall_module", f"Attempted to uninstall non-existent module {module} in Python {version}", installed)
        return

    print(Fore.GREEN + f"Module '{module}' is installed.\n{installed}")
    confirm = input(Fore.CYAN + f"Uninstall '{module}' from Python {version}? (y/n): ")
    if confirm.lower() == 'y':
        result = subprocess.getoutput(f"python{version} -m pip uninstall -y {module}")
        print(Fore.GREEN + result)
        log_action("uninstall_module", f"Uninstalled module {module} from Python {version}", result)

def view_logs():
    print(Fore.CYAN + "\nAvailable Log Files (Grouped by Function):\n")
    logs = ""

    log_files_by_function = {}

    for file in sorted(LOG_DIR.glob("*.log")):
        filename = file.name
        parts = filename.replace(".log", "").split("_")

        # Extract full function name by excluding last parts that are timestamps
        # e.g., list_installed_packages_20250520_10_30_45 -> list_installed_packages
        func_name = "_".join(parts[:-3]) if len(parts) >= 4 else "_".join(parts[:-1])

        if func_name not in log_files_by_function:
            log_files_by_function[func_name] = []
        log_files_by_function[func_name].append(file)

    for func_name in sorted(log_files_by_function):
        print(Fore.GREEN + f"\n[{func_name}]")
        logs += f"[{func_name}]\n"
        for log_file in sorted(log_files_by_function[func_name], key=lambda f: f.name):
            print(Fore.YELLOW + f"- {log_file}")
            logs += f"- {log_file}\n"

    log_action("view_logs", "Viewed log files grouped by function name.", logs.strip())

def search_in_logs():
    view_logs()
    file = input(Fore.CYAN + "\nEnter log file name: ")
    regex = input(Fore.CYAN + "Enter regex pattern to search: ")
    filepath = LOG_DIR / file
    if not filepath.exists():
        print(Fore.RED + "Log file not found.")
        return
    with open(filepath) as f:
        matches = [line for line in f if re.search(regex, line)]
    if matches:
        print(Fore.GREEN + f"\nMatches found in {file}:\n")
        for match in matches:
            print(match.strip())
    else:
        print(Fore.YELLOW + "No matches found.")

    log_action("search_logs", f"Searched for '{regex}' in {file}", "\n".join(matches))

def read_log_file():
    print("\n========== Available Log Files ==========")
    try:
        view_logs()
        print("=========================================")
        filename = input("Enter the exact filename of the log you want to read: ").strip()
        filepath = os.path.join(LOG_DIR, filename)

        if not os.path.isfile(filepath):
            print(f"File '{filename}' does not exist in {LOG_DIR}.")
            return

        print(f"\n========== Contents of {filename} ==========")
        with open(filepath, 'r') as f:
            print(f.read())
        print("============================================")

    except Exception as e:
        print(f"An error occurred: {e}")

def prompt_user(prompt_text):
    """Prompt for user input."""
    return input(f"{prompt_text}: ").strip()

def confirm(prompt_text):
    """Prompt for yes/no confirmation."""
    return input(f"{prompt_text} [y/N]: ").strip().lower() == "y"


def get_python_executable(python_version):
    """Check and return Python executable path."""
    path = shutil.which(f"python{python_version}")
    return path


def is_library_version_on_pypi(python_exec, library, version):
    """Check if a library version exists on PyPI using pip index."""
    try:
        result = subprocess.run(
            [python_exec, "-m", "pip", "index", "versions", library],
            capture_output=True,
            text=True
        )
        if result.returncode != 0 or "Available versions:" not in result.stdout:
            return False

        versions_line = [line for line in result.stdout.splitlines() if "Available versions:" in line]
        if versions_line:
            all_versions = re.findall(r"[\d.]+", versions_line[0])
            return version in all_versions
        return False
    except Exception as e:
        print(f"❌ PyPI check failed: {e}")
        return False


def install_library():
    print("📦 INSTALL MODE")

    # Prompt 1: Python version
    python_version = prompt_user("Enter the Python version (e.g., 3.9)")
    python_exec = get_python_executable(python_version)
    if not python_exec:
        print(f"❌ Python {python_version} not found. Please install it or choose a valid version.")
        return
    print(f"✅ Python {python_version} found: {python_exec}")

    # Prompt 2: Library name
    library = prompt_user("Enter the name of the library to install")

    # Prompt 3: Library version
    version = prompt_user(f"Enter the version of '{library}' to install")

    # Validate library version on PyPI
    print(f"🔍 Checking if {library}=={version} exists on PyPI...")
    if not is_library_version_on_pypi(python_exec, library, version):
        print(f"❌ {library}=={version} is not available on PyPI.")
        return
    print(f"✅ {library}=={version} is available on PyPI.")

    # Prompt 4: Confirmation
    if not confirm(f"Do you want to install {library}=={version} for Python {python_version}?"):
        print("🚫 Installation cancelled.")
        return

    # Perform the installation
    try:
        subprocess.run(
            [python_exec, "-m", "pip", "install", f"{library}=={version}"],
            check=True
        )
        print(f"✅ {library}=={version} successfully installed for Python {python_version}.")
        log_action(logfile, f"Successfully installed {library}=={version} for Python {python_version}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        log_action(logfile, f"❌ Installation failed: {library}=={version} for Python {python_version}")


def check_library_version_installed(python_exec, library, version):
    """Check if a specific version of a library is installed."""
    try:
        result = subprocess.run(
            [python_exec, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True
        )
        installed_packages = result.stdout.strip().splitlines()
        return any(line == f"{library}=={version}" for line in installed_packages)
    except Exception:
        return False


def uninstall_library():
    print("🗑️ UNINSTALL MODE")

    # Prompt 1: Python version
    python_version = prompt_user("Enter the Python version (e.g., 3.9)")
    python_exec = get_python_executable(python_version)
    if not python_exec:
        print(f"❌ Python {python_version} not found. Please install it or choose a valid version.")
        return
    print(f"✅ Python {python_version} found: {python_exec}")

    # Prompt 2: Library name
    library = prompt_user("Enter the name of the library to uninstall")

    # Prompt 3: Library version
    version = prompt_user(f"Enter the version of '{library}' to uninstall")

    # Validate if this version is currently installed
    print(f"🔍 Checking if {library}=={version} is installed for Python {python_version}...")
    if not check_library_version_installed(python_exec, library, version):
        print(f"❌ {library}=={version} is not installed for Python {python_version}.")
        return
    print(f"✅ {library}=={version} is currently installed.")

    # Prompt 4: Confirmation
    if not confirm(f"Do you want to uninstall {library}=={version} for Python {python_version}?"):
        print("🚫 Uninstallation cancelled.")
        return

    # Perform the uninstallation
    try:
        subprocess.run(
            [python_exec, "-m", "pip", "uninstall", "-y", library],
            check=True
        )
        print(f"✅ {library}=={version} successfully uninstalled from Python {python_version}.")
        log_action(logfile, f"Successfully uninstalled {library}=={version} for Python {python_version}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Uninstallation failed: {e}")
        log_action(logfile, f"❌ Uninstallation failed for library: {library}=={version}, for Python {python_version}")

def python_package_menu():
    version = input(Fore.CYAN + "\nEnter Python version (e.g., 3.9): ")
    while True:
        print(Fore.YELLOW + f"""
Python Package Manager for Python {version}
-------------------------------------------
1. List installed packages
2. List installed modules
3. Search for an installed module
4. Generate requirements.txt
5. Search for a library
6. Install a library
7. Uninstall a library
8. Install a specific version of a library
9. Uninstall a specific version of a library
10. Back to main menu
""")
        choice = input(Fore.GREEN + "Enter your choice: ")
        if choice == "1":
            list_installed_packages(version)
        elif choice == "2":
            list_installed_modules(version)
        elif choice == "3":
            search_installed_module()
        elif choice == "4":
            generate_requirements(version)
        elif choice == "5":
            search_module(version)
        elif choice == "6":
            install_module(version)
        elif choice == "7":
            uninstall_module(version)
        elif choice == "8":
            install_library()
        elif choice == "9":
            uninstall_library()
        elif choice == "10":
            break
        else:
            print(Fore.RED + "Invalid choice. Please try again.")

def main_menu():
    while True:
        print(Fore.WHITE + """
╔══════════════════════════════════════════════╗
║        Python Version and Module Tool        ║
╠══════════════════════════════════════════════╣
║ 1. List installed Python versions            ║
║ 2. Install a Python version                  ║
║ 3. Uninstall a Python version                ║
║ 4. Show all Python paths                     ║
║ 5. Show path for specific Python version     ║
║ 6. Manage Python packages/modules            ║
║ 7. List all log files                        ║
║ 8. Read a logfile                            ║
║ 9. Search in logs                            ║
║ 10. Exit                                     ║
╚══════════════════════════════════════════════╝
""")
        choice = input(Fore.GREEN + "Enter your choice: ")
        if choice == "1":
            list_python_versions()
        elif choice == "2":
            install_python_version()
        elif choice == "3":
            uninstall_python_version()
        elif choice == "4":
            show_all_python_paths()
        elif choice == "5":
            show_path_for_version()
        elif choice == "6":
            python_package_menu()
        elif choice == "7":
            view_logs()
        elif choice == "8":
            read_log_file()
        elif choice == "9":
            search_in_logs()
        elif choice == "10":
            print(Fore.YELLOW + "Exiting. Goodbye!")
            break
        else:
            print(Fore.RED + "Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()
