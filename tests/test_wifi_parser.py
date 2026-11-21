"""
Unit Tests for Windows Netsh Wi-Fi Parser
Tests parsing of real-world multi-BSSID netsh outputs, hidden SSIDs,
multiple network adapters, connected BSSID matching, and edge error conditions.
"""

from netvision.core.wifi_scanner import WifiScanner


SAMPLE_NETSH_OUTPUT = """
Interface name : Wi-Fi 
There are 4 networks currently visible. 

SSID 1 : Campus_HighSpeed
    Network type            : Infrastructure
    Authentication          : WPA2-Personal
    Encryption              : CCMP 
    BSSID 1                 : 00:1a:2b:3c:4d:5e
         Signal             : 94%  
         Radio type         : 802.11ax
         Channel            : 36 
         Basic rates (Mbps) : 6 12 24
         Other rates (Mbps) : 9 18 36 48 54
    BSSID 2                 : 00:1a:2b:3c:4d:5f
         Signal             : 78%  
         Radio type         : 802.11ax
         Channel            : 6 

SSID 2 : Library_Guest
    Network type            : Infrastructure
    Authentication          : Open
    Encryption              : None 
    BSSID 1                 : 10:20:30:40:50:60
         Signal             : 45%  
         Radio type         : 802.11n
         Channel            : 11 

SSID 3 : 
    Network type            : Infrastructure
    Authentication          : WPA2-Enterprise
    Encryption              : CCMP 
    BSSID 1                 : aa:bb:cc:dd:ee:ff
         Signal             : 60%  
         Radio type         : 802.11ac
         Channel            : 149 
"""

SAMPLE_MULTI_INTERFACE_OUTPUT = """
There are 2 interfaces on the system: 

    Name                   : Wi-Fi
    Description            : Realtek RTL8723DE 802.11b/g/n PCIe Adapter
    GUID                   : 856b5846-30d4-4eb4-be72-4ad7991a87ee
    Physical address       : 28:cd:c4:a0:ff:73
    State                  : connected
    SSID                   : Airtel_maha_9259
    BSSID                  : 30:15:77:fc:ae:a6
    Network type           : Infrastructure
    Radio type             : 802.11n
    Authentication         : WPA2-Personal
    Cipher                 : CCMP
    Connection mode        : Auto Connect
    Channel                : 11
    Receive rate (Mbps)    : 72.2
    Transmit rate (Mbps)   : 72.2
    Signal                 : 88% 
    Profile                : Airtel_maha_9259 

    Name                   : Local Area Connection* 1
    Description            : Microsoft Wi-Fi Direct Virtual Adapter
    GUID                   : 12345678-aaaa-bbbb-cccc-123456789abc
    Physical address       : 2a:cd:c4:a0:ff:73
    State                  : disconnected
    Radio type             : 802.11n
    Authentication         : WPA2-Personal
    Cipher                 : CCMP
    Connection mode        : Not configured
"""


def test_parse_netsh_networks():
    """Tests parsing multiple SSIDs and BSSIDs with security and radio specs."""
    networks = WifiScanner.parse_netsh_networks_output(
        SAMPLE_NETSH_OUTPUT,
        connected_ssid="Campus_HighSpeed",
        connected_bssid="00:1a:2b:3c:4d:5e"
    )

    # 4 BSSID entries total across 3 SSIDs
    assert len(networks) == 4

    # First network (highest signal 94%)
    first = networks[0]
    assert first.ssid == "Campus_HighSpeed"
    assert first.bssid == "00:1a:2b:3c:4d:5e"
    assert first.signal_percent == 94
    assert first.channel == 36
    assert first.frequency_band == "5 GHz"
    assert first.security_type == "WPA2-Personal"
    assert first.radio_type == "802.11ax"
    assert first.is_connected is True

    # Check that second BSSID with same SSID is NOT marked connected when BSSID doesn't match
    second = next(n for n in networks if n.bssid == "00:1a:2b:3c:4d:5f")
    assert second.ssid == "Campus_HighSpeed"
    assert second.is_connected is False

    # Check hidden SSID parsing (SSID 3 has empty name)
    hidden = next((n for n in networks if n.bssid == "aa:bb:cc:dd:ee:ff"), None)
    assert hidden is not None
    assert hidden.ssid == "<Hidden SSID>"
    assert hidden.channel == 149
    assert hidden.frequency_band == "5 GHz"
    assert hidden.security_type == "WPA2-Enterprise"
    assert hidden.signal_percent == 60


def test_parse_connected_bssid_disambiguation():
    """Verifies that actual connected BSSID takes precedence over matching SSID."""
    networks = WifiScanner.parse_netsh_networks_output(
        SAMPLE_NETSH_OUTPUT,
        connected_ssid="Campus_HighSpeed",
        connected_bssid="00:1a:2b:3c:4d:5f"  # second BSSID is the connected one
    )
    bssid_5e = next(n for n in networks if n.bssid == "00:1a:2b:3c:4d:5e")
    bssid_5f = next(n for n in networks if n.bssid == "00:1a:2b:3c:4d:5f")
    assert bssid_5e.is_connected is False
    assert bssid_5f.is_connected is True


def test_parse_empty_or_no_networks():
    """Tests handling of empty netsh output."""
    networks = WifiScanner.parse_netsh_networks_output("", connected_ssid="")
    assert len(networks) == 0

    no_nets = "There are no wireless networks currently visible."
    networks2 = WifiScanner.parse_netsh_networks_output(no_nets, connected_ssid="")
    assert len(networks2) == 0


def test_parse_interfaces_multiple_adapters():
    """Verifies that multiple adapter blocks are parsed independently and connected adapter is retained."""
    interfaces = WifiScanner.parse_netsh_interfaces_output(SAMPLE_MULTI_INTERFACE_OUTPUT)
    assert len(interfaces) == 2

    # Physical Wi-Fi adapter is connected
    wifi_iface = interfaces[0]
    assert wifi_iface.interface_name == "Wi-Fi"
    assert wifi_iface.state == "connected"
    assert wifi_iface.ssid == "Airtel_maha_9259"
    assert wifi_iface.bssid == "30:15:77:fc:ae:a6"
    assert wifi_iface.channel == 11
    assert wifi_iface.signal_percent == 88

    # Virtual adapter is disconnected
    virt_iface = interfaces[1]
    assert virt_iface.interface_name == "Local Area Connection* 1"
    assert virt_iface.state == "disconnected"


def test_parse_interfaces_ap_bssid_variation():
    """Verifies that AP BSSID key variant is parsed correctly."""
    sample = """
    Name                   : Wi-Fi
    Description            : Intel Wi-Fi 6 AX200
    State                  : connected
    SSID                   : Office_Network
    AP BSSID               : 11:22:33:44:55:66
    Signal                 : 75%
    Channel                : 36
    """
    interfaces = WifiScanner.parse_netsh_interfaces_output(sample)
    assert len(interfaces) == 1
    assert interfaces[0].bssid == "11:22:33:44:55:66"
    assert interfaces[0].channel == 36
    assert interfaces[0].frequency_band == "5 GHz"
    assert interfaces[0].signal_percent == 75
