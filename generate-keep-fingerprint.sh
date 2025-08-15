#!/bin/bash

OUTPUT_FILE="keep-fingerprint.json"

# Build JSON
{
echo "{"
echo "  \"dietpi_version\": \"$(echo $G_DIETPI_VERSION_CORE.$G_DIETPI_VERSION_SUB.$G_DIETPI_VERSION_RC 2>/dev/null || echo 'Not installed')\","
echo "  \"debian_version\": \"$(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '\"' 2>/dev/null || echo 'Unknown')\","
echo "  \"kernel_version\": \"$(uname -r 2>/dev/null || echo 'Unknown')\","
echo "  \"python3_version\": \"$(python3 --version 2>/dev/null || echo 'Not installed')\","
echo "  \"docker_version\": \"$(docker --version 2>/dev/null || echo 'Not installed')\","
echo "  \"docker_compose_version\": \"$(docker compose version 2>/dev/null || echo 'Not installed')\","
echo "  \"git_version\": \"$(git --version 2>/dev/null || echo 'Not installed')\","
echo "  \"gcc_version\": \"$(gcc --version 2>/dev/null | head -n 1 || echo 'Not installed')\","
echo "  \"make_version\": \"$(make --version 2>/dev/null | head -n 1 || echo 'Not installed')\","
echo "  \"systemd_version\": \"$(systemctl --version 2>/dev/null | head -n 1 || echo 'Not installed')\","
echo "  \"openssl_version\": \"$(openssl version 2>/dev/null || echo 'Not installed')\","
echo "  \"ansible_version\": \"$(ansible --version 2>/dev/null | head -n 1 || echo 'Not installed')\","
echo "  \"bluez_version\": \"$(bluetoothctl --version 2>/dev/null || echo 'Not installed')\","
echo "  \"networkctl_version\": \"$(networkctl --version 2>/dev/null | head -n 1 || echo 'Not installed')\","
echo "  \"networkmanager_version\": \"$(nmcli --version 2>/dev/null || echo 'Not installed')\","
echo "  \"wpa_supplicant_version\": \"$(wpa_supplicant -v 2>/dev/null | head -n 1 || echo 'Not installed')\","
echo "  \"iproute2_version\": \"$(ip -V 2>/dev/null || echo 'Not installed')\","
echo "  \"epp_version\": \"$(docker exec epp_epp-app poetry version -s 2>/dev/null || echo 'Not installed')\""
echo "}"
} > "$OUTPUT_FILE"

echo "Version information saved to $OUTPUT_FILE"
