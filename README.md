# Python Management console for linux

## Program developed by Gustavo Wydler Azuaga - 2025-05-20

- Command-line Python utility script to manage Python versions and modules on Linux systems. 
- It supports operations such as:

  - Listing installed Python versions
  - Installing/uninstalling Python versions
  - Managing Python modules
  - Generating `requirements.txt`.

## 📁 Directory Structure

- Logs of actions are stored in the `python_linux_versions/` directory
- The directory is created in the same folder where the script is run.

---

## ⚙️ Detailed features

- ✅ List all installed Python versions and paths
- 📥 Install or uninstall Python versions using `apt` or `yum`
- 🔍 View the binary path for a specific Python version
- 📦 List pip packages or Python modules for a specific version
- 📝 Generate `requirements.txt` using `pip freeze`
- 🔎 Search for a module's installation status and availability on PyPI
- 📌 Install or uninstall Python modules
- 📚 Check which versions have a specific module installed
- 🪵 Log all actions with timestamped entries

---

## 🖥️ Supported Linux Distros

- Ubuntu / Debian (uses `apt`)
- CentOS / RHEL / AlmaLinux / Fedora (uses `yum`)

---

## 🧪 Requirements

- Python 3.x
  
- `colorama` Python package:
  
  ```bash
  pip3 install colorama
  ```
- To run the program:
- 
  ```bash
  python3.x python_linux_management_console.py
  ```
------------------------------------------------------------------------------------
