"""
NetVision - Windows Wi-Fi Scanner and Interface Inspector
Uses native Windows WLAN API (wlanapi.dll) to trigger active spectrum scans,
and parses netsh wlan show interfaces / show networks mode=bssid.
Correctly handles multiple adapters, multiple BSSIDs per SSID, connected BSSID matching,
gateway & DNS extraction, and locale variations.
"""

import subprocess
import re
import socket
import logging
import ctypes
from ctypes import wintypes
import time
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from netvision.database.models import WifiNetwork, ConnectedInterfaceInfo
from netvision.core.subprocess_utils import run_hidden_command

logger = logging.getLogger(__name__)


def channel_to_band(channel: int) -> str:
    """Infers frequency band from channel number according to 802.11 standards."""
    if 1 <= channel <= 14:
        return "2.4 GHz"
    elif 32 <= channel <= 177:
        return "5 GHz"
    elif channel > 177:
        return "6 GHz"
    return "Unknown"


class WifiScanner:
    """Windows-compatible native Wi-Fi scanner and interface query module."""

    def __init__(self):
        self.last_scan_time: Optional[str] = None
        self.last_connected_info: Optional[ConnectedInterfaceInfo] = None
        self._wlan_handle = None

    @staticmethod
    def _run_command(cmd: List[str], timeout: int = 10) -> Tuple[int, str]:
        """Runs a system command safely without spawning visible Windows console windows."""
        try:
            result = run_hidden_command(cmd, timeout=timeout, check=False)
            if result.returncode != 0 and result.stderr and result.stderr.strip():
                logger.warning(
                    "Command '%s' exited with %d: %s",
                    " ".join(cmd),
                    result.returncode,
                    result.stderr.strip(),
                )
            return result.returncode, result.stdout
        except subprocess.TimeoutExpired:
            logger.warning("Command timed out after %ss: %s", timeout, " ".join(cmd))
            return -1, "Command timed out"
        except FileNotFoundError:
            logger.error("Command not found: %s", cmd[0])
            return -2, "Command not found"
        except Exception as e:
            logger.error("Error executing %s: %s", " ".join(cmd), e)
            return -3, str(e)

    def trigger_active_wlan_scan(self) -> bool:
        """
        Triggers an active hardware spectrum scan using Windows Native WLAN API (wlanapi.dll).
        Returns True if scan was successfully initiated.
        """
        try:
            wlan = ctypes.windll.wlanapi

            class GUID(ctypes.Structure):
                _fields_ = [
                    ("Data1", wintypes.DWORD),
                    ("Data2", wintypes.WORD),
                    ("Data3", wintypes.WORD),
                    ("Data4", wintypes.BYTE * 8)
                ]

            class WLAN_INTERFACE_INFO(ctypes.Structure):
                _fields_ = [
                    ("InterfaceGuid", GUID),
                    ("strInterfaceDescription", wintypes.WCHAR * 256),
                    ("isState", wintypes.DWORD)
                ]

            class WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
                _fields_ = [
                    ("dwNumberOfItems", wintypes.DWORD),
                    ("dwIndex", wintypes.DWORD),
                    ("InterfaceInfo", WLAN_INTERFACE_INFO * 1)
                ]

            client_handle = wintypes.HANDLE()
            negotiated_version = wintypes.DWORD()
            ret = wlan.WlanOpenHandle(2, None, ctypes.byref(negotiated_version), ctypes.byref(client_handle))
            if ret != 0:
                logger.debug(f"WlanOpenHandle returned code {ret}")
                return False

            pp_interface_list = ctypes.POINTER(WLAN_INTERFACE_INFO_LIST)()
            ret_enum = wlan.WlanEnumInterfaces(client_handle, None, ctypes.byref(pp_interface_list))
            success = False
            if ret_enum == 0 and pp_interface_list.contents.dwNumberOfItems > 0:
                info_list = pp_interface_list.contents
                for i in range(info_list.dwNumberOfItems):
                    item = ctypes.cast(
                        ctypes.addressof(info_list.InterfaceInfo) + i * ctypes.sizeof(WLAN_INTERFACE_INFO),
                        ctypes.POINTER(WLAN_INTERFACE_INFO)
                    ).contents
                    scan_ret = wlan.WlanScan(client_handle, ctypes.byref(item.InterfaceGuid), None, None, None)
                    if scan_ret == 0:
                        success = True
                wlan.WlanFreeMemory(pp_interface_list)
            wlan.WlanCloseHandle(client_handle, None)
            return success
        except Exception as e:
            logger.debug(f"WlanScan trigger exception: {e}")
            return False

    def get_connected_interface(self) -> ConnectedInterfaceInfo:
        """
        Parses 'netsh wlan show interfaces' to determine current connection status.
        Correctly segments multiple interface blocks and selects the active connected adapter.
        Extracts gateway, DNS, and IP information genuinely.
        """
        code, output = self._run_command(["netsh", "wlan", "show", "interfaces"])
        if code != 0 or not output.strip():
            info = ConnectedInterfaceInfo(state="disconnected")
            info.ipv4_address = self._get_fallback_ip()
            self.last_connected_info = info
            return info

        interfaces = self.parse_netsh_interfaces_output(output)
        if not interfaces:
            info = ConnectedInterfaceInfo(state="disconnected")
            info.ipv4_address = self._get_fallback_ip()
            self.last_connected_info = info
            return info

        # Select the connected interface (or first interface if none connected)
        selected_info = None
        for candidate in interfaces:
            if candidate.state == "connected":
                selected_info = candidate
                break

        if not selected_info:
            selected_info = interfaces[0]

        # Retrieve Genuine IP, Gateway and DNS Configuration for this interface
        if selected_info.interface_name and selected_info.state == "connected":
            ip, gw, dns = self._get_interface_ip_config(selected_info.interface_name)
            if ip:
                selected_info.ipv4_address = ip
            else:
                selected_info.ipv4_address = self._get_fallback_ip()
            if gw:
                selected_info.gateway = gw
            if dns:
                selected_info.dns_servers = dns
        else:
            selected_info.ipv4_address = self._get_fallback_ip()

        self.last_connected_info = selected_info
        return selected_info

    @classmethod
    def parse_netsh_interfaces_output(cls, output: str) -> List[ConnectedInterfaceInfo]:
        """
        Parses raw text from 'netsh wlan show interfaces'.
        Segments output into individual interface blocks so multiple adapters do not collide.
        """
        interfaces: List[ConnectedInterfaceInfo] = []
        current_dict: Dict[str, str] = {}
        in_block = False

        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if ":" in line:
                key, val = [p.strip() for p in line.split(":", 1)]
                key_lower = key.lower()

                # Start of a new interface block
                if key_lower == "name":
                    if in_block and current_dict:
                        interfaces.append(cls._build_interface_obj(current_dict))
                        current_dict = {}
                    in_block = True
                    current_dict["name"] = val
                elif in_block:
                    current_dict[key_lower] = val

        if in_block and current_dict:
            interfaces.append(cls._build_interface_obj(current_dict))

        return interfaces

    @classmethod
    def _build_interface_obj(cls, d: Dict[str, str]) -> ConnectedInterfaceInfo:
        """Constructs ConnectedInterfaceInfo from parsed key-value dictionary."""
        info = ConnectedInterfaceInfo()
        info.interface_name = d.get("name", "")
        info.description = d.get("description", "")
        info.guid = d.get("guid", "")
        info.state = d.get("state", "disconnected").lower()
        info.ssid = d.get("ssid", "")

        # Support 'bssid', 'ap bssid', 'bssid du pa'
        for k in d.keys():
            if "bssid" in k:
                val = d[k]
                if re.match(r"^[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}$", val):
                    info.bssid = val.lower()
                    break

        info.radio_type = d.get("radio type", "")
        info.authentication = d.get("authentication", "")
        info.cipher = d.get("cipher", "")
        info.connection_mode = d.get("connection mode", "")

        ch_str = d.get("channel", "")
        if ch_str.isdigit():
            info.channel = int(ch_str)
            info.frequency_band = channel_to_band(info.channel)
        else:
            info.channel = 0
            info.frequency_band = "Unknown"

        rx_str = d.get("receive rate (mbps)", "")
        try:
            info.receive_rate_mbps = float(rx_str)
        except ValueError:
            info.receive_rate_mbps = None

        tx_str = d.get("transmit rate (mbps)", "")
        try:
            info.transmit_rate_mbps = float(tx_str)
        except ValueError:
            info.transmit_rate_mbps = None

        sig_str = d.get("signal", "")
        if sig_str:
            clean_sig = sig_str.replace("%", "").strip()
            if clean_sig.isdigit():
                info.signal_percent = int(clean_sig)

        return info

    def _get_interface_ip_config(self, interface_name: str) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Executes 'netsh interface ip show config' for the specified interface.
        Returns (ip_address, default_gateway, dns_servers).
        """
        code, out = self._run_command(["netsh", "interface", "ip", "show", "config", interface_name], timeout=4)
        if code != 0 or not out.strip():
            return None, None, []

        ip: Optional[str] = None
        gw: Optional[str] = None
        dns_servers: List[str] = []
        in_dns_section = False

        for raw_line in out.splitlines():
            line = raw_line.strip()
            if not line:
                in_dns_section = False
                continue

            lower_line = line.lower()
            if "ip address" in lower_line or "adresse ip" in lower_line:
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", line)
                if m:
                    ip = m.group(1)
            elif "default gateway" in lower_line or "passerelle par defaut" in lower_line or "standardgateway" in lower_line:
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", line)
                if m:
                    gw = m.group(1)
            elif "dns servers" in lower_line or "serveurs dns" in lower_line:
                in_dns_section = True
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", line)
                if m:
                    dns_servers.append(m.group(1))
            elif in_dns_section:
                m = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3})$", line)
                if m:
                    dns_servers.append(m.group(1))
                else:
                    in_dns_section = False

        return ip, gw, dns_servers

    def scan_networks(self) -> Tuple[List[WifiNetwork], Optional[str]]:
        """
        Triggers a fresh active Wi-Fi hardware scan, waits for channel sweep,
        and parses nearby networks from 'netsh wlan show networks mode=bssid'.
        Returns a tuple of (networks_list, error_message).
        """
        # Step 1: Trigger active hardware spectrum scan via WLAN API
        scan_triggered = self.trigger_active_wlan_scan()
        if scan_triggered:
            # Allow adapter 1.5 seconds to sweep 2.4/5GHz channels
            time.sleep(1.5)

        # Step 2: Read discovered networks
        code, output = self._run_command(["netsh", "wlan", "show", "networks", "mode=bssid"], timeout=12)

        if code != 0:
            out_lower = output.lower()
            if "wlansvc" in out_lower or "not running" in out_lower:
                return [], "The Windows Wireless AutoConfig Service (wlansvc) is not running. Please start wlansvc in Services."
            elif "no wireless interface" in out_lower:
                return [], "No active Wi-Fi network adapter was detected on this computer."
            return [], f"Wi-Fi scan failed (error {code}): {output.strip()}"

        connected_info = self.get_connected_interface()
        connected_ssid = connected_info.ssid if connected_info.state == "connected" else ""
        connected_bssid = connected_info.bssid if connected_info.state == "connected" else ""

        networks = self.parse_netsh_networks_output(
            output,
            connected_ssid=connected_ssid,
            connected_bssid=connected_bssid
        )
        self.last_scan_time = datetime.now().isoformat()

        if not networks:
            if "no wireless networks" in output.lower():
                # Check for Windows Location privacy restriction
                if connected_info.state == "connected":
                    return [], (
                        "No nearby networks visible despite active connection. "
                        "Windows Location Privacy setting may be blocking Wi-Fi beacon scanning. "
                        "(Settings > Privacy & security > Location > Allow apps to access location)."
                    )
                return [], "No wireless networks currently detected in range or Wi-Fi radio is switched off."
            return [], "No wireless networks returned by Windows WLAN subsystem."

        return networks, None

    @classmethod
    def parse_netsh_networks_output(
        cls,
        output: str,
        connected_ssid: str = "",
        connected_bssid: str = ""
    ) -> List[WifiNetwork]:
        """
        Parses the raw text output from 'netsh wlan show networks mode=bssid'.
        Correctly groups multiple BSSIDs per SSID, detects hidden SSIDs,
        and accurately matches the actual connected BSSID.
        """
        networks: List[WifiNetwork] = []
        current_ssid = ""
        current_auth = "Unknown"
        lines = output.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Detect new SSID block
            ssid_match = re.match(r"^SSID\s+\d+\s*:\s*(.*)$", line)
            if ssid_match:
                current_ssid = ssid_match.group(1).strip()
                if not current_ssid:
                    current_ssid = "<Hidden SSID>"
                current_auth = "Unknown"
                i += 1
                continue

            # Detect Authentication / Security
            auth_match = re.match(r"^Authentication\s*:\s*(.*)$", line, re.IGNORECASE)
            if auth_match:
                current_auth = auth_match.group(1).strip()
                i += 1
                continue

            # Detect BSSID section
            bssid_match = re.match(r"^BSSID\s+\d+\s*:\s*([0-9a-fA-F:-]{17})", line, re.IGNORECASE)
            if bssid_match:
                bssid_val = bssid_match.group(1).strip().lower()
                sig_val = 0
                radio_val = ""
                ch_val = 0

                i += 1
                while i < len(lines):
                    subline = lines[i].strip()
                    if not subline:
                        i += 1
                        continue

                    # If next SSID or next BSSID is hit, exit BSSID inner loop
                    if re.match(r"^SSID\s+\d+\s*:", subline, re.IGNORECASE) or re.match(r"^BSSID\s+\d+\s*:", subline, re.IGNORECASE):
                        break

                    sig_match = re.match(r"^Signal\s*:\s*(\d+)%", subline, re.IGNORECASE)
                    if sig_match:
                        sig_val = int(sig_match.group(1))

                    rad_match = re.match(r"^Radio type\s*:\s*(.*)$", subline, re.IGNORECASE)
                    if rad_match:
                        radio_val = rad_match.group(1).strip()

                    ch_match = re.match(r"^Channel\s*:\s*(\d+)", subline, re.IGNORECASE)
                    if ch_match:
                        ch_val = int(ch_match.group(1))

                    i += 1

                band = channel_to_band(ch_val)

                # Connected check: Match actual BSSID if available, else fallback to matching SSID
                if connected_bssid:
                    is_conn = bool(bssid_val == connected_bssid.lower())
                elif connected_ssid:
                    is_conn = bool(current_ssid == connected_ssid)
                else:
                    is_conn = False

                networks.append(WifiNetwork(
                    ssid=current_ssid,
                    bssid=bssid_val,
                    signal_percent=sig_val,
                    channel=ch_val,
                    frequency_band=band,
                    security_type=current_auth,
                    is_connected=is_conn,
                    radio_type=radio_val,
                    observed_at=datetime.now().isoformat()
                ))
                continue

            i += 1

        # Sort descending by signal strength
        networks.sort(key=lambda x: x.signal_percent, reverse=True)
        return networks

    @staticmethod
    def _get_fallback_ip() -> str:
        """Finds primary local IPv4 address via outbound socket binding."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Unavailable"
