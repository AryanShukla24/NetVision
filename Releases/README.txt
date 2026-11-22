================================================================================
  NETVISION 2.0 - SMART NETWORK QUALITY & WI-FI COVERAGE ANALYZER
================================================================================
Release Version : 2.0.0
Architecture    : Windows 64-bit (x64)
Compatibility   : Windows 10 (Build 19041+) / Windows 11 (64-bit)

--------------------------------------------------------------------------------
1. OVERVIEW
--------------------------------------------------------------------------------
NetVision is a professional desktop network monitoring, Wi-Fi coverage analyzer,
and diagnostics utility featuring:
- Real-time ICMP ping latency, dual-probe tracking, and packet loss detection.
- Live Wi-Fi RF environment scanning, channel interference, and signal graphs.
- High-throughput multi-stream and single-stream download/upload speed testing.
- Fully customizable, independent floating statistics overlay widgets with
  live desktop background capture and drag-and-drop visual positioning.
- Automated Executive Summary & Technical PDF report generation.
- Zero external runtime dependencies: bundled completely with Python runtime,
  Qt/PySide6, Matplotlib, and Windows native integration.

--------------------------------------------------------------------------------
2. SYSTEM REQUIREMENTS
--------------------------------------------------------------------------------
- Operating System : Windows 10 (Version 2004 / Build 19041 or newer) or Windows 11
- Architecture     : 64-bit (x86_64 / AMD64)
- CPU              : 1.6 GHz dual-core or faster x86-64 processor
- RAM              : 4 GB minimum (8 GB recommended)
- Disk Space       : ~250 MB free space
- Display          : 1280x720 minimum (1920x1080 Full HD recommended)
- Network Adapter  : 802.11a/b/g/n/ac/ax Wi-Fi adapter (for wireless analytics)
                     and/or standard Ethernet adapter

--------------------------------------------------------------------------------
3. RUNNING THE PORTABLE VERSION (NetVision-Portable.zip)
--------------------------------------------------------------------------------
The portable edition is ideal for running from a USB flash drive or testing
without system installation:

Step 1: Extract the contents of "NetVision-Portable.zip" to any directory of
        your choice (e.g., Desktop, Documents, or USB drive).
Step 2: Open the extracted folder and double-click "NetVision.exe".
Step 3: The application will launch immediately. No setup, administrative
        rights, or runtime installations (Python, Node, etc.) are needed.

DATA STORAGE BEHAVIOR:
- Standard Mode (Default): User database, measurement history, and logs are
  safely kept in "%LOCALAPPDATA%\NetVision". This ensures your data persists
  even if you move or replace the portable executable folder.
- Fully Self-Contained USB Mode: If you want all settings and data saved
  directly inside the portable directory (e.g., on a thumb drive), create an
  empty file named "portable.dat" in the same folder as "NetVision.exe".
  NetVision will detect this and write all databases and logs to a local
  "user_data" subfolder instead.

--------------------------------------------------------------------------------
4. USING THE WINDOWS INSTALLER (NetVision-Setup.exe)
--------------------------------------------------------------------------------
The installer edition provides complete Windows shell integration:

Step 1: Double-click "NetVision-Setup.exe" to launch the Setup Wizard.
Step 2: Choose your installation folder (defaults to %LOCALAPPDATA%\Programs\NetVision,
        requiring no administrator/UAC privileges).
Step 3: Select whether to create a Desktop shortcut and Start Menu folder.
Step 4: Click "Install". When complete, optionally check "Launch NetVision now"
        and click "Finish".

HOW TO UNINSTALL:
- Option A: Go to Windows Settings > Apps > Installed apps (or Control Panel >
  Programs and Features), locate "NetVision", and select "Uninstall".
- Option B: Open the Windows Start Menu, go to the NetVision folder, and
  click "Uninstall NetVision".
- Option C: Run "uninstall.exe" directly from the installation folder.

The uninstaller removes all installed application binaries and shortcuts.
It prompts whether you wish to preserve your measurement database and history
or perform a complete wipe.

--------------------------------------------------------------------------------
5. PERMISSIONS & SECURITY
--------------------------------------------------------------------------------
- Standard Permissions: NetVision runs with normal user privileges. No
  administrator rights are requested or needed for day-to-day monitoring.
- Network Access: Windows Defender Firewall may prompt you on the first run.
  Allow network access so NetVision can ping network gateways, measure DNS
  resolution times, and run speed tests against remote test endpoints.
- Wi-Fi BSSID Discovery: On Windows 10/11, ensure Windows Location Services
  are enabled in Windows Privacy Settings. Windows requires location permission
  to reveal nearby Wi-Fi network BSSIDs and MAC addresses.
- Overlay Transparency: Overlay widgets require Desktop Window Manager (DWM)
  hardware acceleration, enabled by default in all modern Windows installations.

--------------------------------------------------------------------------------
6. TROUBLESHOOTING
--------------------------------------------------------------------------------
Q: Windows SmartScreen shows "Windows protected your PC" on launch.
A: This occurs because NetVision is an open-source project without an enterprise
   EV code-signing certificate ($400+/year). Click "More info" and then click
   "Run anyway". The binary contains only authentic NetVision code and standard
   Python/Qt libraries.

Q: Speed test results seem slower than my ISP plan.
A: Ensure background downloads, torrents, or streaming services are paused.
   For Gigabit connections, select "Multi-stream" mode in the Speed Test page
   to saturate high-bandwidth links.

Q: Overlay widgets do not remember their screen positions.
A: Open Settings > Positioning, arrange the widgets as desired on the live
   desktop preview canvas, and click "Save & Apply Layout". Positions are saved
   permanently in your user profile.

================================================================================
Support & Documentation: https://github.com/netvision/netvision
Copyright (C) 2026 NetVision Contributors. All Rights Reserved.
================================================================================
