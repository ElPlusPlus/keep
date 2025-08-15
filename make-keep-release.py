import subprocess
import pwd

# 1. Validate settings

# SSH disabled
result = subprocess.run(
        ["systemctl", "is-active", "dropbear"],
        capture_output=True, text=True
    )
ssh_dropbear_active = result.stdout.strip() == "active"

if ssh_dropbear_active:
    raise Exception("SSH enabled. Disable it before delivering device.")

# Network wiped
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
        return []  # nmcli not installed
if check_networkmanager():
    raise Exception("Wifi networks are still stored")

# Epp is running and docker is cleaned
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
if not check_container_running():
    raise Exception("Epp container is not running.")

# Ansible is setup
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

# Bluez (Bluetooth) is running
def is_bluetooth_service_active(service):
    """Check if a given systemd service is active."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True, text=True
        )
        return result.stdout.strip() == "active"
    except Exception:
        return False
if not is_bluetooth_service_active():
    raise Exception("Bluetooth service is not active.")

def is_bluetooth_service_enabled(service):
    """Check if a given systemd service is enabled at boot."""
    try:
        result = subprocess.run(
            ["systemctl", "is-enabled", service],
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

# Check no login user
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


# 2. Generate version
print("Generating fingerprint...")
subprocess.run(["python", "generate-keep-version.py"], check=True)