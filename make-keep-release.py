import subprocess
import pwd
import argparse

parser = argparse.ArgumentParser("Make Keep release")
parser.add_argument("step", help="Skip to step and continue from there.", type=int, nargs='?')
args = parser.parse_args()
step = args.step or 0

# A. Validate settings

# 1. SSH disabled
if step < 2:
    result = subprocess.run(
            ["systemctl", "is-active", "dropbear"],
            capture_output=True, text=True
        )
    ssh_dropbear_active = result.stdout.strip() == "active"

    if ssh_dropbear_active:
        raise Exception("SSH enabled. Disable it before delivering device.")

# 2. Network wiped
if step < 3:
    def check_networkmanager():
        """Check for saved Wi-Fi profiles if NetworkManager is used."""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
                capture_output=True, text=True
            )
            connections = []
            for line in result.stdout.splitlines():
                name, conn_type = line.split(":")
                if conn_type == "wifi":
                    connections.append(name)
            return connections
        except FileNotFoundError:
            raise Exception("Nmcli is not installed")
    if check_networkmanager():
        raise Exception("Wifi networks are still stored")

# 3. Epp is running and docker is cleaned
if step < 4:
    def check_container_running(container_name):
        """Check if a specific Docker container is running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                capture_output=True, text=True
            )
            running_containers = [c.strip() for c in result.stdout.splitlines() if c.strip()]
            return container_name in running_containers
        except FileNotFoundError:
            return None  # Docker not installed
    if not check_container_running("epp_epp-app"):
        raise Exception("Epp container is not running.")

# 4. Ansible is setup
if step < 5:
    def check_ansible_installed():
        """Check if Ansible is installed."""
        result = subprocess.run(
            ["which", "ansible"], capture_output=True, text=True
        )
        return bool(result.stdout.strip())
    if not check_ansible_installed():
        raise Exception("Ansible is not installed")

    def check_ansible_scheduled():
        """Check cron jobs for Ansible commands."""
        scheduled = []
        # System-wide cron
        try:
            cron_dirs = ["/etc/cron.d", "/var/spool/cron/crontabs"]
            for cron_dir in cron_dirs:
                if os.path.exists(cron_dir):
                    for root, _, files in os.walk(cron_dir):
                        for file in files:
                            path = os.path.join(root, file)
                            try:
                                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                                    for line in f:
                                        if "ansible" in line and not line.strip().startswith("#"):
                                            scheduled.append(f"{path}: {line.strip()}")
                            except PermissionError:
                                pass
        except Exception:
            pass
        # User crontab
        try:
            result = subprocess.run(
                ["crontab", "-l"], capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if "ansible" in line and not line.strip().startswith("#"):
                    scheduled.append(f"user crontab: {line.strip()}")
        except subprocess.CalledProcessError:
            pass  # no crontab for user
        return scheduled
    if not check_ansible_scheduled():
        raise Exception("Ansible script is not scheduled")

# 5. Bluez (Bluetooth) is running
if step < 6:
    def is_bluetooth_service_active():
        """Check if a given systemd service is active."""
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "bluetooth"],
                capture_output=True, text=True
            )
            return result.stdout.strip() == "active"
        except Exception:
            return False
    if not is_bluetooth_service_active():
        raise Exception("Bluetooth service is not active.")

    def is_bluetooth_service_enabled():
        """Check if a given systemd service is enabled at boot."""
        try:
            result = subprocess.run(
                ["systemctl", "is-enabled", "bluetooth"],
                capture_output=True, text=True
            )
            return result.stdout.strip() == "enabled"
        except Exception:
            return False
    if not is_bluetooth_service_enabled():
        raise Exception("Bluetooth service is not enabled")

    def is_bluetooth_powered():
        """Check if Bluetooth adapter is powered using bluetoothctl."""
        try:
            result = subprocess.run(
                ["bluetoothctl", "show"],
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if "Powered:" in line:
                    return "yes" in line.lower()
            return False
        except FileNotFoundError:
            return None  # bluetoothctl not installed
    if not is_bluetooth_powered():
        raise Exception("Bluetooth adapter is not powered using bluetoothctl")

# 6. Check no login user
if step < 7:
    def list_human_login_users(min_uid=1000):
        """Return a list of human users (UID >= min_uid) with valid login shells."""
        users = []
        for user in pwd.getpwall():
            if (
                user.pw_uid >= min_uid and
                "nologin" not in user.pw_shell and
                "false" not in user.pw_shell
            ):
                users.append(user.pw_name)
        return users
    if list_human_login_users():
        raise Exception("There exists users with login.")


# B. Generate version
print("Generating fingerprint...")
subprocess.run(["python3", "generate-keep-version.py"], check=True)