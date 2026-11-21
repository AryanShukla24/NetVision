"""
NetVision - Shared Authoritative Academic Report Content Module
Supplies structured, 100% codebase-verified content, real telemetry values,
tables, formulas, code excerpts, and figure definitions for both:
- NetVision_Project_Report.docx
- NetVision_Project_Report.pdf
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SHOTS_DIR = ROOT_DIR / "docs" / "screenshots"
DIAGRAMS_DIR = ROOT_DIR / "docs" / "diagrams"

# Load genuine live telemetry recorded from the running application
_summary_path = SHOTS_DIR / "live_telemetry_summary.json"
LIVE_DATA = json.loads(_summary_path.read_text(encoding="utf-8")) if _summary_path.exists() else {}

PROJECT_TITLE = "NetVision"
PROJECT_SUBTITLE = "Smart Network Quality & Wi-Fi Coverage Analyzer"
APP_VERSION = "2.0.0"

TEAM_MEMBERS = [
    ("1", "Aryan Shukla", "09117702724"),
    ("2", "Aaditya Rawat", "07917702724"),
    ("3", "Kushal Shedha", "08817702724"),
]

ABBREVIATIONS = [
    ("AP", "Access Point"),
    ("API", "Application Programming Interface"),
    ("BOM", "Byte Order Mark (UTF-8 encoding marker for spreadsheet compatibility)"),
    ("BSSID", "Basic Service Set Identifier (MAC address of a wireless radio interface)"),
    ("CCMP", "Counter Mode Cipher Block Chaining Message Authentication Code Protocol"),
    ("CDN", "Content Delivery Network"),
    ("CRUD", "Create, Read, Update, Delete"),
    ("CSV", "Comma-Separated Values"),
    ("DDE", "Dynamic Data Exchange"),
    ("DLL", "Dynamic Link Library"),
    ("DNS", "Domain Name System"),
    ("DTO", "Data Transfer Object"),
    ("ER", "Entity-Relationship"),
    ("GUI", "Graphical User Interface"),
    ("HTTP / HTTPS", "Hypertext Transfer Protocol / Secure"),
    ("ICMP", "Internet Control Message Protocol"),
    ("IEEE", "Institute of Electrical and Electronics Engineers"),
    ("IPv4", "Internet Protocol Version 4"),
    ("ISP", "Internet Service Provider"),
    ("ITU-T", "International Telecommunication Union — Telecommunication Standardization Sector"),
    ("LAN / WLAN", "Local Area Network / Wireless Local Area Network"),
    ("Mbps", "Megabits per Second"),
    ("MVC", "Model-View-Controller"),
    ("NIC", "Network Interface Card"),
    ("OS", "Operating System"),
    ("PDF", "Portable Document Format"),
    ("PHY", "Physical Layer (OSI Layer 1)"),
    ("RF", "Radio Frequency"),
    ("RFC", "Request for Comments"),
    ("RSSI", "Received Signal Strength Indicator"),
    ("RTT", "Round-Trip Time"),
    ("SD", "Standard Deviation"),
    ("SQL", "Structured Query Language"),
    ("SSID", "Service Set Identifier"),
    ("TCP", "Transmission Control Protocol"),
    ("TLS", "Transport Layer Security"),
    ("UI", "User Interface"),
    ("VoIP", "Voice over Internet Protocol"),
    ("WAL", "Write-Ahead Logging (SQLite concurrency mode)"),
    ("WAN", "Wide Area Network"),
    ("WPA2 / WPA3", "Wi-Fi Protected Access 2 / 3"),
    ("XML", "Extensible Markup Language"),
]

FIGURES_LIST = [
    ("Figure 4.1", "NetVision v2.0.0 Layered System Architecture", DIAGRAMS_DIR / "system_architecture.png"),
    ("Figure 4.2", "End-to-End Measurement Data Flow and QThread Concurrency Lifecycle", DIAGRAMS_DIR / "data_flow_diagram.png"),
    ("Figure 4.3", "Relational SQLite Database Entity-Relationship Diagram (Schema v2)", DIAGRAMS_DIR / "er_diagram.png"),
    ("Figure 4.4", "Application Startup, Diagnostic Execution, and Integrity Workflow", DIAGRAMS_DIR / "application_workflow.png"),
    ("Figure 9.1", "Main Dashboard — Active Link Overview, Metric Cards, and Radio/Gateway Parameters", SHOTS_DIR / "01_dashboard.png"),
    ("Figure 9.2", "Nearby Wi-Fi Network Scanner — Live Discovery of 31 Access Points", SHOTS_DIR / "02_wifi_scanner.png"),
    ("Figure 9.3", "Wi-Fi Signal & RF Stability Analyzer — Continuous Polling and Stability Metrics", SHOTS_DIR / "03_signal_analyzer.png"),
    ("Figure 9.4", "Network Speed & Bandwidth Test — Cloudflare Global Edge Throughput Measurement", SHOTS_DIR / "04_speed_test.png"),
    ("Figure 9.5", "Latency Monitor — Isolated ICMP Echo Probing, RTT Graph, and Packet Loss", SHOTS_DIR / "05_latency_monitor.png"),
    ("Figure 9.6", "Channel Analyzer — 2.4 GHz AP Distribution and Spectral Overlap Recommendation", SHOTS_DIR / "06_channel_analyzer.png"),
    ("Figure 9.7", "History & Analytics — Persistent SQLite Archive with Filtering and Trend Plots", SHOTS_DIR / "07_history_analytics.png"),
    ("Figure 9.8", "Cross-Location Comparative Analytics — Multi-Environment Signal, Speed, and Latency", SHOTS_DIR / "08_location_comparison.png"),
    ("Figure 9.9", "Academic Experiment — Multi-Trial Evaluation, Spread, and Correlation Guard", SHOTS_DIR / "09_academic_experiment.png"),
    ("Figure 9.10", "Audit Reports & Data Export — Rule-Based Recommendations and PDF/CSV Generation", SHOTS_DIR / "10_audit_reports.png"),
    ("Figure 9.11", "System Settings & Threshold Configuration — Targets, Thresholds, and Custom Locations", SHOTS_DIR / "11_settings.png"),
    ("Figure 9.12", "About NetVision — System Architecture Summary and Host Runtime Telemetry", SHOTS_DIR / "12_about_netvision.png"),
]

TABLES_LIST = [
    ("Table 2.1", "Comparison of Existing Network Diagnostic Tools vs. NetVision"),
    ("Table 3.1", "Functional Requirements Specification"),
    ("Table 3.2", "Non-Functional Requirements Specification"),
    ("Table 3.3", "Hardware and Software Environment Requirements"),
    ("Table 5.1", "Verified Technology Stack and Dependency Roles"),
    ("Table 7.1", "Centralized Default Network Quality Evaluation Thresholds"),
    ("Table 7.2", "IEEE 802.11 2.4 GHz Spectral Overlap Weights Implemented in ChannelAnalyzer"),
    ("Table 7.3", "Conceptual Distinction Between Signal Quality, Link Speed, Throughput, and Latency"),
    ("Table 8.1", "Complete Relational SQLite Schema Inventory (9 Tables, Schema v2)"),
    ("Table 8.2", "User-Data Directory Isolation Under %LOCALAPPDATA%\\NetVision"),
    ("Table 10.1", "Automated Test Suite Breakdown (pytest — 46 Passing Cases)"),
    ("Table 10.2", "Detailed System Verification and Validation Test-Case Matrix"),
    ("Table 11.1", "Genuine Live Hardware and WAN Measurements Recorded on Test Machine"),
    ("Table 11.2", "Live 2.4 GHz Channel Occupancy Distribution Observed on Test Host (31 APs)"),
]

REFERENCES = [
    "[1] IEEE Computer Society, 'IEEE Standard for Information Technology — Telecommunications and Information Exchange between Systems — Local and Metropolitan Area Networks — Specific Requirements — Part 11: Wireless LAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications,' IEEE Std 802.11-2020, 2020.",
    "[2] J. Postel, 'Internet Control Message Protocol,' Internet Engineering Task Force (IETF), RFC 792, September 1981. [Online]. Available: https://www.rfc-editor.org/rfc/rfc792",
    "[3] H. Schulzrinne, S. Casner, R. Frederick, and V. Jacobson, 'RTP: A Transport Protocol for Real-Time Applications,' IETF, RFC 3550 (Section 6.4.1 — Interarrival Jitter), July 2003. [Online]. Available: https://www.rfc-editor.org/rfc/rfc3550",
    "[4] R. Braden, 'Requirements for Internet Hosts — Application and Support,' IETF, RFC 1123 (Section 2.1 — Host Names and Numbers), October 1989. [Online]. Available: https://www.rfc-editor.org/rfc/rfc1123",
    "[5] Microsoft Corporation, 'Native Wifi API Reference (wlanapi.h / wlanapi.dll),' Microsoft Learn Documentation. [Online]. Available: https://learn.microsoft.com/en-us/windows/win32/nativewifi/portal",
    "[6] Microsoft Corporation, 'Netsh Commands for Wireless Local Area Network (WLAN),' Microsoft Learn Documentation. [Online]. Available: https://learn.microsoft.com/en-us/windows-server/networking/technologies/netsh/netsh-wlan",
    "[7] The Qt Company, 'Qt for Python (PySide6) Official Documentation,' Version 6.x. [Online]. Available: https://doc.qt.io/qtforpython-6/",
    "[8] SQLite Consortium, 'Write-Ahead Logging (WAL) in SQLite,' SQLite Documentation. [Online]. Available: https://www.sqlite.org/wal.html",
    "[9] J. D. Hunter, 'Matplotlib: A 2D Graphics Environment,' Computing in Science & Engineering, vol. 9, no. 3, pp. 90–95, 2007.",
    "[10] ReportLab Inc., 'ReportLab PDF Library User Guide,' Version 4.x. [Online]. Available: https://docs.reportlab.com/",
    "[11] PyInstaller Development Team, 'PyInstaller Manual,' Version 6.x. [Online]. Available: https://pyinstaller.org/en/stable/",
    "[12] pytest Development Team, 'pytest: Helps You Write Better Programs,' Official Documentation. [Online]. Available: https://docs.pytest.org/",
    "[13] J. F. Kurose and K. W. Ross, Computer Networking: A Top-Down Approach, 8th ed. Pearson Education, 2021.",
]

ABSTRACT_TEXT = (
    "Modern academic campuses, offices, and residential environments rely heavily on IEEE 802.11 wireless local area networks "
    "(Wi-Fi) for everyday internet access, video conferencing, cloud computing, and interactive applications. Despite this reliance, "
    "end users and network administrators frequently struggle to diagnose intermittent slowdowns, packet drops, or location-dependent "
    "degradation because native operating system indicators condense complex multi-layer networking conditions into a single signal icon. "
    "Moreover, strong Wi-Fi signal reception does not guarantee adequate wide-area internet throughput or low round-trip latency.\n\n"
    "NetVision — Smart Network Quality & Wi-Fi Coverage Analyzer (v2.0.0) is a native 64-bit Windows desktop application engineered "
    "using Python 3.12, PySide6 (Qt 6), SQLite 3 (Write-Ahead Logging mode), Matplotlib, and ReportLab to unify physical-layer wireless "
    "inspection with Layer 3/4 latency diagnostics, Layer 7 throughput benchmarking, cross-location comparative analytics, multi-trial "
    "empirical experimentation, and structured audit reporting.\n\n"
    "Unlike ad-hoc scripts that blend incompatible metrics or fabricate missing values, NetVision enforces strict measurement integrity: "
    "it invokes the Windows Native WLAN API (wlanapi.dll via ctypes) to trigger active hardware spectrum scans before parsing netsh output; "
    "it isolates ICMP echo probing from TCP 3-way handshake probes so dropped ICMP packets are never masked; it measures WAN download and "
    "upload throughput via chunked HTTPS streaming against Cloudflare Global Edge with a 1 MB TCP slow-start warm-up exclusion; it models "
    "2.4 GHz spectral overlap across standard channels (1, 6, and 11) while explicitly disclosing consumer NIC hardware limitations; and it "
    "represents missing or failed measurements strictly as SQL NULL and '—' / 'No data' in the user interface.\n\n"
    "All blocking network and OS operations are decoupled onto five dedicated QThread background workers communicating via Qt Signals and "
    "Slots, preserving UI responsiveness and supporting clean cancellation. Runtime telemetry is isolated under %LOCALAPPDATA%\\NetVision "
    "across nine normalized SQLite tables with automated schema versioning. The system is validated by 46 passing automated pytest unit and "
    "integration tests alongside live Windows hardware verification (discovering 31 live nearby access points, measuring 47.35 Mbps download "
    "and 33.30 Mbps upload throughput, and recording 12.0 ms average ICMP RTT with 0.0% packet loss), and is packaged into standalone "
    "PyInstaller executables and a non-elevated Windows setup wizard."
)


def get_chapters():
    """Returns structured list of all 12 chapters with blocks: ('h2', ...), ('p', ...), ('bullet', [...]),
    ('formula', ...), ('code', ...), ('table', (caption, headers, rows)), ('figure', (fig_no, caption, path, desc))."""
    return [
        # =====================================================================
        # CHAPTER 1
        # =====================================================================
        {
            "num": "1",
            "title": "INTRODUCTION",
            "blocks": [
                ("h2", "1.1 Background"),
                ("p", "Wireless local area networks (WLANs) based on the IEEE 802.11 family of standards have become the primary last-hop access medium in homes, universities, and enterprise workplaces. While wireless connectivity offers convenience and mobility, radio-frequency (RF) links are inherently susceptible to distance attenuation, structural obstructions (walls, glass, concrete), co-channel and adjacent-channel contention from neighboring access points, and fluctuating wide-area network (WAN) conditions upstream of the local router."),
                ("p", "When users experience buffering during video lectures, lag spikes in real-time applications, or sluggish downloads, diagnosing the actual root cause requires examining multiple layers of the TCP/IP protocol stack simultaneously. A user must inspect the Layer 1/2 wireless interface (signal strength, channel, band, and PHY link rate), Layer 3 IP routing and ICMP round-trip time (RTT), Layer 4 transport jitter and packet loss, and Layer 7 application-level throughput. NetVision was designed to bring these complementary diagnostic dimensions together in a single, reliable, and academically transparent Windows desktop application."),

                ("h2", "1.2 Introduction to Computer Networks and Wi-Fi"),
                ("p", "In the TCP/IP layered networking model, end-to-end communication quality is governed by the weakest link across every participating layer. At the Physical (PHY) and Data Link (MAC) layers, IEEE 802.11 radios operate primarily in unlicensed 2.4 GHz and 5 GHz (and newer 6 GHz) Industrial, Scientific, and Medical (ISM) frequency bands. In the 2.4 GHz band, channels are spaced 5 MHz apart while standard 802.11b/g/n transmissions occupy 20 MHz of bandwidth, meaning adjacent channels overlap spectrally and only Channels 1, 6, and 11 remain mutually non-overlapping. Because Wi-Fi uses Carrier Sense Multiple Access with Collision Avoidance (CSMA/CA), dense deployments sharing the same or overlapping channels contend for airtime, introducing queueing delay and retransmissions."),
                ("p", "Above the wireless hop, the Network layer (IPv4/IPv6 and ICMP) handles packet forwarding across local gateways and ISP routers, while the Transport layer (TCP/UDP) governs reliability, congestion control (such as TCP slow start and window scaling), and sensitivity to packet loss and delay variation (jitter). Evaluating wireless network performance rigorously therefore requires separating local RF metrics from end-to-end internet performance rather than treating a single signal icon as a proxy for total quality."),

                ("h2", "1.3 Motivation"),
                ("p", "The primary motivation for building NetVision emerged from recurring diagnostic challenges encountered in college hostels, classrooms, libraries, and home workspaces:"),
                ("bullet", [
                    "Opacity of Built-In Indicators: The standard Windows taskbar Wi-Fi icon shows only coarse signal bars and hides BSSID identity, operating channel, radio standard, link rate, gateway, and signal fluctuation over time.",
                    "Fragmented Workflows: Investigating a slow connection typically forces users to juggle command-line tools (netsh, ping, ipconfig) alongside ad-supported web speed tests, none of which correlate results or store structured history.",
                    "Misleading Diagnostics in Informal Tools: Many lightweight scripts blur measurement integrity—masking dropped ICMP packets behind TCP fallbacks, fabricating jitter as a fixed percentage of ping, or plotting failed tests as zero.",
                    "Need for Empirical Multi-Location Analysis: Students and IT staff comparing Wi-Fi coverage across rooms or conducting Computer Networks lab experiments require repeatable multi-trial logging, statistical spread calculations, and exportable audit reports."
                ]),

                ("h2", "1.4 Problem Statement"),
                ("p", "Users and administrators on Windows computers lack a unified, non-intrusive desktop diagnostic tool that accurately measures local Wi-Fi conditions alongside end-to-end internet performance without sacrificing measurement honesty. Specifically, existing lightweight workflows fail to: (1) distinguish local wireless signal quality and PHY link rate from actual WAN download/upload throughput; (2) isolate ICMP echo packet loss from TCP connection latency; (3) estimate 2.4 GHz co-channel and adjacent-channel overlap transparently; (4) persist timestamped multi-location measurements in a structured local database; and (5) automate multi-trial empirical experiments and audit-ready PDF/CSV reporting without requiring administrative privileges or manual Python environment configuration."),

                ("h2", "1.5 Objectives"),
                ("p", "The concrete engineering objectives implemented and verified in NetVision v2.0.0 are:"),
                ("bullet", [
                    "Inspect active Windows wireless interface telemetry (SSID, BSSID, radio standard, security/cipher, channel, band, Rx/Tx link rate, IPv4, gateway, DNS) and discover surrounding access points via native Windows WLAN APIs.",
                    "Monitor Wi-Fi signal percentage continuously over time, computing session mean, standard deviation, min/max spread, and disconnection detection.",
                    "Measure genuine WAN download and upload throughput via chunked HTTPS streaming against Cloudflare Global Edge with TCP warm-up exclusion and responsive cancellation.",
                    "Evaluate round-trip latency, jitter, and packet loss using strictly isolated ICMP or TCP 3-way handshake probes while preserving failed measurements as SQL NULL.",
                    "Analyze Wi-Fi channel occupancy across 2.4 GHz (with 20 MHz overlap weights) and 5 GHz bands to recommend less congested channels with transparent hardware disclaimers.",
                    "Persist all telemetry in a local SQLite 3 database (WAL mode) under %LOCALAPPDATA%\\NetVision, enabling historical trend charts, multi-location comparison, and multi-trial academic experiments.",
                    "Generate rule-based diagnostic recommendations and export XML-safe ReportLab PDF reports and formula-sanitized UTF-8 CSV datasets.",
                    "Deliver portable standalone Windows executables (PyInstaller) and a per-user Windows Setup Wizard requiring zero Python installation."
                ]),

                ("h2", "1.6 Scope of the Project"),
                ("p", "NetVision targets 64-bit Microsoft Windows 10 and Windows 11 desktop and laptop systems equipped with standard IEEE 802.11 wireless adapters managed by the Windows WLAN AutoConfig service (wlansvc). The application operates strictly in user space without requiring kernel drivers, packet injection hardware, or elevated administrator rights during normal operation. Active WAN benchmarking (speed tests and external ping targets) requires an active internet connection, whereas local interface inspection, Wi-Fi scanning, signal logging, historical analytics, and report generation function offline. Non-Windows operating systems (Linux, macOS) and dedicated hardware RF spectrum analysis (detecting non-802.11 interference such as microwave ovens or Bluetooth frequency hopping) are explicitly outside the current scope."),

                ("h2", "1.7 Project Contributions"),
                ("p", "Key technical contributions achieved through this project include:"),
                ("bullet", [
                    "A clean src/netvision Python package architecture separating PySide6 UI views (12 pages), 5 asynchronous QThread workers, 8 core domain modules, and a versioned SQLite persistence layer.",
                    "Strict measurement integrity enforcement: zero synthetic/mock metrics, zero ICMP loss masking, regex-validated ping targets, genuine consecutive-difference and RFC 3550 jitter formulas, and NULL-safe visualization.",
                    "An empirical Academic Experiment module calculating sample mean, sample standard deviation, and variance-guarded Pearson correlation coefficients across repeated trials.",
                    "Production Windows packaging with %LOCALAPPDATA% user-data separation, multi-resolution branding icons, standalone portable/onedir binaries, and a custom PySide6 installer/uninstaller suite verified by 46 automated pytest cases."
                ]),

                ("h2", "1.8 Organization of the Report"),
                ("p", "The remainder of this report is organized as follows. Chapter 2 reviews existing network diagnostic utilities and identifies their limitations. Chapter 3 details functional, non-functional, hardware, and software requirements along with a feasibility study. Chapter 4 presents the layered system architecture, data flow, ER model, and operational workflow. Chapter 5 explains the verified technology stack. Chapter 6 provides an in-depth module-by-module implementation walkthrough grounded in the actual source code. Chapter 7 formalizes the measurement methodology and mathematical equations. Chapter 8 documents the SQLite database schema and user-data management strategy. Chapter 9 serves as an illustrated user guide featuring 12 live screenshots from the running application. Chapter 10 presents unit, integration, packaging, and live hardware validation results. Chapter 11 discusses genuine empirical measurements and limitations, and Chapter 12 concludes the report with clearly demarcated future scope."),
            ],
        },

        # =====================================================================
        # CHAPTER 2
        # =====================================================================
        {
            "num": "2",
            "title": "LITERATURE AND EXISTING SYSTEM STUDY",
            "blocks": [
                ("h2", "2.1 Built-In Operating System Network Utilities"),
                ("p", "Microsoft Windows provides several command-line diagnostic utilities natively, including netsh wlan (Wireless LAN interface and network queries), ping.exe (ICMP Echo Request/Reply testing), ipconfig (IPv4/IPv6 addressing, gateway, and DNS configuration), and tracert (hop-by-hop route tracing). While these tools interface directly with the operating system network stack and provide trustworthy raw measurements, they operate exclusively as stateless, text-based commands. Users must manually invoke separate commands, parse verbose console text, and record outputs in external spreadsheets to observe trends or compare rooms. Furthermore, netsh wlan show networks relies on the OS cached scan list unless an active hardware scan is explicitly triggered through the Native Wifi API (WlanScan in wlanapi.dll)."),

                ("h2", "2.2 Traditional Wi-Fi Scanning Tools"),
                ("p", "Dedicated wireless survey tools (such as commercial Wi-Fi analyzers and enterprise site-survey suites) visualize nearby SSIDs, BSSIDs, channels, and RSSI values. However, consumer-oriented scanners typically focus exclusively on Layer 1/2 radio beacons and omit integrated internet throughput testing, ICMP latency/jitter probing, and multi-trial statistical experimentation. Conversely, enterprise RF site-survey suites require expensive licenses or proprietary USB spectrum analyzer dongles, placing them outside the budget and accessibility of students and everyday Windows users."),

                ("h2", "2.3 Browser-Based Internet Speed Testing Services"),
                ("p", "Web-based speed test platforms measure Layer 7 download/upload throughput and server ping using browser HTTP/WebSocket transfers. While convenient for quick one-off checks, browser tools are isolated from local operating system Wi-Fi telemetry—they cannot inspect the user's connected BSSID, Wi-Fi signal percentage, radio standard, operating channel, or surrounding AP congestion. Consequently, a browser speed test showing 15 Mbps cannot tell the user whether the bottleneck is a weak 2.4 GHz Wi-Fi signal, severe channel crowding, or an ISP bandwidth cap."),

                ("h2", "2.4 Ping-Based Command-Line Diagnostics"),
                ("p", "ICMP ping utilities remain the standard mechanism for checking Layer 3 reachability, round-trip time, and packet loss. However, default Windows ping executes only four probes and prints only integer millisecond minimum, maximum, and average summary lines—omitting jitter calculation, live RTT visualization, historical storage, and selectable TCP 3-way handshake probing when corporate firewalls block ICMP echo traffic."),

                ("h2", "2.5 Comparative Study and Gap Analysis"),
                ("p", "Table 2.1 summarizes the technical capabilities and limitations of isolated existing tools in contrast to the unified architecture implemented in NetVision v2.0.0."),
                ("table", (
                    "Table 2.1: Comparison of Existing Network Diagnostic Tools vs. NetVision",
                    ["Capability / Feature", "Windows CLI (netsh/ping)", "Web Speed Tests", "Basic Wi-Fi Scanners", "NetVision v2.0.0"],
                    [
                        ["Active Hardware Wi-Fi Scan (wlanapi.dll)", "Manual / Cached", "Not Available", "Yes", "Yes (Automated)"],
                        ["Connected Link, Gateway & DNS Inspection", "Separate commands", "No", "Partial", "Yes (Unified)"],
                        ["Continuous Signal Stability (Mean, SD)", "No", "No", "Limited", "Yes (Real-time)"],
                        ["WAN Download / Upload Speed Test", "No", "Yes", "No", "Yes (Cloudflare CDN)"],
                        ["Isolated ICMP & TCP Latency + Jitter", "ICMP only, no jitter", "Server ping only", "No", "Yes (Isolated + Jitter)"],
                        ["2.4 GHz Overlap Channel Recommendation", "No", "No", "Some tools", "Yes (Weighted Model)"],
                        ["Persistent SQLite History & Comparisons", "No", "Cloud/Account", "Rarely", "Yes (Local SQLite WAL)"],
                        ["Multi-Trial Academic Experiment + Pearson r", "No", "No", "No", "Yes (Built-in)"],
                        ["Audit PDF & Formula-Safe CSV Export", "No", "Limited", "Paid tiers", "Yes (Local Offline)"],
                    ]
                )),
                ("p", "As shown in Table 2.1, the primary gap in existing systems is not a shortage of isolated measurements, but the absence of an integrated, transparent, local-first desktop tool that combines radio-layer awareness, honest transport/WAN probing, location-tagged persistence, and reproducible empirical reporting."),
            ],
        },

        # =====================================================================
        # CHAPTER 3
        # =====================================================================
        {
            "num": "3",
            "title": "REQUIREMENTS ANALYSIS",
            "blocks": [
                ("h2", "3.1 Functional Requirements"),
                ("p", "Functional requirements define the concrete capabilities implemented across NetVision's 12 user-facing pages and core measurement engines. Table 3.1 catalogs each verified functional requirement."),
                ("table", (
                    "Table 3.1: Functional Requirements Specification",
                    ["Req ID", "Module", "Requirement Description"],
                    [
                        ["FR-01", "Dashboard", "Display active Wi-Fi SSID, BSSID, band, channel, radio standard, link rate, local IPv4, gateway, DNS, and latest speed/latency metrics."],
                        ["FR-02", "Wi-Fi Scanner", "Trigger an active hardware scan via wlanapi.dll, parse netsh mode=bssid output, disambiguate multiple BSSIDs per SSID, filter/sort results, and persist sessions."],
                        ["FR-03", "Signal Analyzer", "Continuously poll active signal % at user-selected intervals, render real-time Matplotlib plots, compute mean/SD/range stability, and detect disconnections."],
                        ["FR-04", "Speed Test", "Measure WAN download (1 MB warm-up + 10 MB stream), upload (5 MB chunked POST), and TCP edge ping/jitter against Cloudflare Global Edge with cancellation."],
                        ["FR-05", "Latency Monitor", "Execute user-configured probe counts using strictly isolated ICMP or TCP_CONNECT methods, validating target hosts and computing min/max/avg RTT, jitter, and packet loss %."],
                        ["FR-06", "Channel Analyzer", "Group detected APs by 2.4 GHz, 5 GHz, and 6 GHz bands; apply 20 MHz overlap weights on 2.4 GHz; recommend optimal channels with hardware scope disclaimer."],
                        ["FR-07", "History & Analytics", "Query, filter (by text, location, and date range), visualize, and safely delete stored speed tests, latency tests, and signal logs from SQLite."],
                        ["FR-08", "Location Comparison", "Compare arbitrary user-selected locations side-by-side across signal quality, throughput, and probe-weighted latency while excluding failed runs."],
                        ["FR-09", "Academic Experiment", "Run 3–10 automated repeated trials under named conditions, archiving results and computing sample mean, sample SD, and variance-guarded Pearson correlation (r)."],
                        ["FR-10", "Audit Reports", "Generate rule-based diagnostic recommendations and export XML-escaped ReportLab PDF reports and formula-sanitized UTF-8 BOM CSV files."],
                        ["FR-11", "Settings & About", "Persist customizable ping hosts, polling intervals, quality thresholds, and custom location tags in SQLite; display host runtime diagnostics."],
                        ["FR-12", "Packaging & Setup", "Operate without admin rights, isolate user data in %LOCALAPPDATA%\\NetVision, and support standalone EXE and per-user Windows installer execution."],
                    ]
                )),

                ("h2", "3.2 Non-Functional Requirements"),
                ("table", (
                    "Table 3.2: Non-Functional Requirements Specification",
                    ["Req ID", "Quality Attribute", "Target Specification"],
                    [
                        ["NFR-01", "Responsiveness", "All blocking OS/network calls execute on QThread workers; main GUI thread remains responsive (<100 ms event handling) with instant Stop/Abort support."],
                        ["NFR-02", "Measurement Integrity", "No fabricated metrics, no ICMP-to-TCP fallback masking, strict NULL representation for missing/failed probes, and transparent hardware disclaimers."],
                        ["NFR-03", "Data Durability", "SQLite 3 configured with WAL journal mode, foreign key enforcement, 5000 ms busy timeout, and non-destructive schema migrations."],
                        ["NFR-04", "Security & Safety", "Strict regex/IP validation of ping targets prevents command injection; whitelisted SQL table names for deletion; CSV formula sanitization and PDF XML escaping."],
                        ["NFR-05", "Portability", "Zero hardcoded developer usernames or paths; packaged binaries run on clean Windows 10/11 PCs without Python installed."],
                        ["NFR-06", "Usability", "Consistent dark slate desktop theme, readable typography, clear color-coded quality indicators, and safe user-data preservation during uninstallation."],
                    ]
                )),

                ("h2", "3.3 Hardware Requirements"),
                ("p", "NetVision is lightweight in compute and memory footprint and operates comfortably on standard student and office laptops. Hardware and software environment specifications are detailed in Table 3.3."),

                ("h2", "3.4 Software Requirements"),
                ("table", (
                    "Table 3.3: Hardware and Software Environment Requirements",
                    ["Category", "Minimum Requirement", "Recommended / Tested Environment"],
                    [
                        ["Operating System", "Windows 10 (64-bit)", "Windows 10 / Windows 11 (64-bit)"],
                        ["Processor", "Dual-core x86-64 CPU (1.6 GHz)", "Quad-core x86-64 CPU (2.0 GHz+)"],
                        ["Memory (RAM)", "4 GB RAM", "8 GB RAM or higher"],
                        ["Disk Space", "250 MB free space (installed app + logs)", "500 MB free space (for historical DB & PDFs)"],
                        ["Network Adapter", "IEEE 802.11b/g/n Wi-Fi adapter", "Dual-band 802.11ac / 802.11ax (Wi-Fi 5/6) adapter"],
                        ["OS Services", "WLAN AutoConfig (wlansvc) running", "Active internet connection for WAN tests"],
                        ["Runtime (End User)", "None (standalone EXE / Setup Wizard)", "NetVision_Setup.exe or NetVision_Portable.exe"],
                        ["Runtime (Developer)", "Python 3.10+ (64-bit), pip, venv", "Python 3.12.16, PySide6 6.8, pytest 9.2"],
                    ]
                )),

                ("h2", "3.5 User Requirements"),
                ("p", "The application serves two primary user personas: (1) everyday Windows users or IT troubleshooters who want one-click installation, intuitive visual feedback, and clear recommendations without typing terminal commands; and (2) Computer Science students and faculty who need reproducible multi-trial experiment logging, raw CSV data exports, statistical spread metrics, and transparent documentation of every underlying formula."),

                ("h2", "3.6 Constraints"),
                ("bullet", [
                    "Platform Dependency: Wireless scanning uses Windows-specific APIs (wlanapi.dll and netsh), constraining native Wi-Fi features to Windows 10 and 11.",
                    "Adapter Band Visibility: The operating system can only report access points on frequency bands supported by the physical wireless NIC (for instance, a 2.4 GHz-only adapter cannot scan 5 GHz or 6 GHz channels).",
                    "Non-802.11 Interference Blindness: Standard consumer Wi-Fi cards do not expose raw RF spectral power density; channel congestion analysis is therefore strictly beacon-based.",
                    "Network Policy Restrictions: Corporate or campus firewalls that drop ICMP echo packets will report 100% ICMP loss; users must explicitly switch the Latency Monitor method to TCP Connect when testing behind ICMP-blocking policies.",
                    "Non-Elevated Execution: Both the application and per-user installer must function cleanly under standard Windows user accounts without requiring UAC administrator elevation."
                ]),

                ("h2", "3.7 Feasibility Study"),
                ("bullet", [
                    "Technical Feasibility: High. Python 3.12 combined with PySide6, ctypes access to wlanapi.dll, built-in sqlite3, Matplotlib, and ReportLab provides mature, well-documented interfaces for every required subsystem without exotic native C++ build toolchains.",
                    "Operational Feasibility: High. Standalone PyInstaller executables and a graphical setup wizard eliminate dependency setup friction for end users, while %LOCALAPPDATA% isolation avoids Windows File System permission errors.",
                    "Economic Feasibility: High. All runtime libraries, testing frameworks, and packaging utilities are open-source and free of licensing fees, and WAN throughput tests use Cloudflare's publicly accessible edge endpoints.",
                    "Schedule Feasibility: Achieved. Iterative phase-based engineering allowed incremental verification via 46 automated pytest cases and live hardware testing before final packaging."
                ]),
            ],
        },

        # =====================================================================
        # CHAPTER 4
        # =====================================================================
        {
            "num": "4",
            "title": "SYSTEM DESIGN AND ARCHITECTURE",
            "blocks": [
                ("h2", "4.1 Overall System Architecture"),
                ("p", "NetVision implements a four-tier Layered Model-View-Controller (MVC) desktop architecture that cleanly decouples user-interface rendering from blocking network I/O, domain computations, and relational storage. Separating these concerns ensures that measurement algorithms can be unit-tested independently without launching a GUI, while background worker threads keep the Qt event loop responsive during multi-second network transfers."),
                ("figure", (
                    "Figure 4.1",
                    "NetVision v2.0.0 Layered System Architecture",
                    DIAGRAMS_DIR / "system_architecture.png",
                    "Layered view illustrating the Presentation Tier (PySide6 MainWindow and 12 pages), Asynchronous Concurrency Tier (5 QThread workers), Core Domain Tier (8 specialized Python modules), Windows OS/Network Tier, and isolated %LOCALAPPDATA% SQLite persistence tier."
                )),

                ("h2", "4.2 Module Architecture"),
                ("p", "The source repository adheres to the modern Python src/ packaging convention (configured in pyproject.toml), eliminating implicit current-working-directory import issues and supporting clean PyInstaller bundling:"),
                ("bullet", [
                    "src/netvision/config.py: Centralizes application metadata (v2.0.0), PyInstaller frozen vs. source path resolution (sys._MEIPASS), %LOCALAPPDATA%\\NetVision directory initialization, template database seeding, default quality thresholds, and the dark slate color palette.",
                    "src/netvision/core/: Contains non-GUI measurement and analytical engines—wifi_scanner.py, signal_monitor.py, speed_tester.py, latency_monitor.py, channel_analyzer.py, experiment_analytics.py, recommendation_engine.py, reporter.py, and workers.py.",
                    "src/netvision/database/: Contains typed dataclass Data Transfer Objects (models.py) and DatabaseManager (db_manager.py) handling SQLite WAL connections, schema v1-to-v2 migration, indexing, and parameterized CRUD operations.",
                    "src/netvision/ui/: Contains MainWindow (main_window.py), global QSS stylesheet (theme.py), reusable UI components (cards.py, chart_widget.py), and 12 dedicated page controllers under ui/pages/."
                ]),

                ("h2", "4.3 Data Flow and Asynchronous Concurrency"),
                ("p", "Because Windows marks any GUI application whose main event loop stalls for more than ~2 seconds as 'Not Responding', NetVision strictly prohibits executing blocking subprocesses (netsh, ping.exe) or streaming HTTP sockets on the main thread. Figure 4.2 illustrates the end-to-end asynchronous data flow from user action through background execution, SQLite persistence, and signal-driven UI updates."),
                ("figure", (
                    "Figure 4.2",
                    "End-to-End Measurement Data Flow and QThread Concurrency Lifecycle",
                    DIAGRAMS_DIR / "data_flow_diagram.png",
                    "Data flow from user interaction to QThread worker dispatch, core probe execution, NULL-safe calculation, SQLite WAL persistence, and non-blocking Matplotlib/table updates via Qt Signals and Slots."
                )),

                ("h2", "4.4 User Interface Design"),
                ("p", "The graphical interface employs a persistent left-hand navigation sidebar paired with a QStackedWidget content canvas inside MainWindow (1280×800 default, 1024×680 minimum). Twelve navigation views organize functionality logically from live monitoring (Dashboard, Wi-Fi Scanner, Signal Analyzer, Speed Test, Latency Monitor, Channel Analyzer) to retrospective analysis (History & Analytics, Location Comparison, Academic Experiment, Audit Reports) and system administration (Settings, About NetVision). A high-contrast dark slate theme (Slate 900 #0f172a background, Slate 800 #1e293b cards, Sky 400 #38bdf8 accents, Emerald/Amber/Rose status cues) ensures legibility during classroom projector demonstrations and extended monitoring sessions."),

                ("h2", "4.5 Database Design"),
                ("p", "All empirical observations are persisted locally in SQLite 3 with PRAGMA foreign_keys = ON, PRAGMA journal_mode = WAL, and PRAGMA busy_timeout = 5000. Write-Ahead Logging permits simultaneous readers (such as the History or Location Comparison pages) and background writers (such as SignalMonitorWorker) without database lock contention. Nullable REAL columns are explicitly used for speed, RTT, and jitter metrics so failed or cancelled runs store genuine SQL NULL values rather than distorting statistics with zeros."),

                ("h2", "4.6 Entity Relationship Diagram"),
                ("figure", (
                    "Figure 4.3",
                    "Relational SQLite Database Entity-Relationship Diagram (Schema v2)",
                    DIAGRAMS_DIR / "er_diagram.png",
                    "Actual relational structure of netvision.db verified from db_manager.py, highlighting the 1:N ON DELETE CASCADE relationship between scan_sessions and wifi_networks and consistent location_label tagging across telemetry tables."
                )),

                ("h2", "4.7 Important Database Tables"),
                ("p", "The schema comprises nine tables: scan_sessions (parent metadata for each Wi-Fi sweep), wifi_networks (child BSSID observations linked via session_id), speed_tests (download/upload/ping/jitter/status records), latency_tests (ICMP or TCP_CONNECT probe aggregates), signal_logs (timestamped continuous signal samples), locations (unique user-defined environment tags seeded with Home, College Library, Classroom, Cafe, and Office), experiment_runs (multi-trial academic experiment series), app_settings (persisted key-value configuration), and schema_version (audit trail for automated migrations). Complete column specifications appear in Chapter 8."),

                ("h2", "4.8 Application Workflow"),
                ("p", "Figure 4.4 outlines the full operational lifecycle from initial startup and safe directory/database bootstrapping through active probing, analytical evaluation, and audit report export, together with the measurement integrity guardrails enforced across every stage."),
                ("figure", (
                    "Figure 4.4",
                    "Application Startup, Diagnostic Execution, and Integrity Workflow",
                    DIAGRAMS_DIR / "application_workflow.png",
                    "Sequential operational lifecycle and cross-cutting measurement integrity rules enforced throughout NetVision v2.0.0."
                )),
            ],
        },

        # =====================================================================
        # CHAPTER 5
        # =====================================================================
        {
            "num": "5",
            "title": "TECHNOLOGY STACK",
            "blocks": [
                ("h2", "5.1 Verified Runtime and Development Dependencies"),
                ("p", "Every software component listed in Table 5.1 is directly verified from requirements.txt, requirements-dev.txt, pyproject.toml, and the project source code. Runtime dependencies are strictly segregated from testing and packaging tools to keep installations lean and reproducible."),
                ("table", (
                    "Table 5.1: Verified Technology Stack and Dependency Roles",
                    ["Component", "Version / Package", "Engineering Role in NetVision"],
                    [
                        ["Programming Language", "Python 3.12 (supports 3.10–3.12)", "Primary implementation language for core engines, dataclasses, ctypes FFI, and UI controllers."],
                        ["Desktop GUI Toolkit", "PySide6 (>=6.6.0, <7.0.0)", "Official Qt 6 Python bindings powering MainWindow, QStackedWidget pages, tables, dialogs, and QThread concurrency."],
                        ["Plotting & Visualization", "Matplotlib (>=3.8.0, <4.0.0)", "Embedded FigureCanvasQTAgg charts for live signal plots, RTT timelines, channel bar charts, comparisons, and experiment scatter plots."],
                        ["Numerical & Tabular", "NumPy (>=1.26.0), Pandas (>=2.1.0)", "Array handling, NaN gap masking for missing chart points, and structured analytical aggregations."],
                        ["HTTP & Networking", "requests (>=2.31.0), urllib3 (>=2.0.0), socket", "Streaming HTTPS chunked downloads/uploads against Cloudflare Global Edge and raw TCP socket handshake timing."],
                        ["Windows OS Telemetry", "wlanapi.dll (ctypes), netsh, ping.exe", "Active hardware 802.11 scans, wireless interface/BSSID parsing, IP/gateway/DNS extraction, and native ICMP echo probes."],
                        ["Relational Storage", "SQLite 3 (Python stdlib sqlite3)", "Embedded ACID relational database configured with WAL mode, foreign keys, and schema migrations."],
                        ["PDF & CSV Reporting", "ReportLab (>=4.0.0), Python csv/xml", "Programmatic multi-section PDF audit reports with XML entity escaping and Excel-safe UTF-8 BOM CSV exports."],
                        ["Automated Testing", "pytest (>=7.4.0, tested on 9.2.0)", "Unit, parser, database, reporting, config isolation, and headless GUI test verification (46 passing tests)."],
                        ["Windows Packaging", "PyInstaller 6.x, Inno Setup 6 (.iss)", "Standalone onedir/onefile Windows executables, Windows PE version metadata, and per-user Setup Wizard."],
                    ]
                )),

                ("h2", "5.2 Rationale for Key Architectural Technology Choices"),
                ("bullet", [
                    "PySide6 over Tkinter or Electron: PySide6 delivers native Qt 6 rendering performance, full CSS-like QSS theming, high-DPI clarity, and built-in QThread/Signal-Slot thread safety without the high RAM overhead of bundling a Chromium browser engine.",
                    "Native wlanapi.dll + netsh over Third-Party Wi-Fi Libraries: Many third-party Python Wi-Fi packages fail on modern Windows 10/11 builds or silently return stale OS scan caches. Calling WlanOpenHandle, WlanEnumInterfaces, and WlanScan directly via ctypes before parsing netsh wlan show networks mode=bssid ensures fresh hardware sweeps with zero external driver installation.",
                    "Cloudflare Global Edge Streaming over Legacy Speedtest Wrappers: Direct chunked HTTPS streaming to speed.cloudflare.com/__down and /__up eliminates fragile server-list scraping, gives full control over warm-up exclusion, and enables responsive per-64KB-chunk cancellation.",
                    "SQLite 3 in WAL Mode: Provides zero-configuration embedded persistence with strong relational integrity, fast indexed queries, and concurrent read/write safety suitable for desktop telemetry.",
                    "ReportLab for PDF Generation: Generates crisp vector typography and structured tables locally offline without requiring LaTeX, wkhtmltopdf, or headless browsers on the target user's Windows PC."
                ]),
            ],
        },

        # =====================================================================
        # CHAPTER 6
        # =====================================================================
        {
            "num": "6",
            "title": "IMPLEMENTATION",
            "blocks": [
                ("h2", "6.1 Application Initialization and User-Data Isolation"),
                ("p", "Application startup begins in main.py, which resolves src/ into sys.path when executed from source, initializes rotating file logging to %LOCALAPPDATA%\\NetVision\\logs\\netvision.log, configures high-DPI Qt scaling, applies DARK_THEME_QSS, attaches the application icon (assets/icons/netvision.png / .ico), and instantiates MainWindow."),
                ("p", "Path resolution is centralized in src/netvision/config.py. When packaged with PyInstaller (getattr(sys, 'frozen', False) is True), static read-only assets resolve from sys._MEIPASS, whereas all mutable runtime data routes to get_user_data_dir() (%LOCALAPPDATA%\\NetVision\\). Upon import, ensure_app_directories() creates database/, logs/, reports/, exports/, config/, and cache/. If netvision.db does not yet exist in the user folder and a template exists in data/netvision.db, it is copied once without ever overwriting an existing user database."),

                ("h2", "6.2 Dashboard Module"),
                ("p", "Implemented in src/netvision/ui/pages/dashboard_page.py, the Dashboard provides an at-a-glance health summary of the active network link. On launch (via a 300 ms QTimer.singleShot to allow immediate window painting) and whenever the user clicks Refresh Link, MainWindow queries WifiScanner.get_connected_interface() alongside the most recent speed and latency records from DatabaseManager. Six MetricCard widgets display Wi-Fi Signal Quality (%), Download Speed (Mbps), Upload Speed (Mbps), Round-Trip Ping (ms), Network Jitter (ms), and Packet Loss (%). Below the cards, the Active Radio & Gateway Parameters panel renders BSSID, Radio Standard, Security/Cipher, Receive and Transmit Link Rates, Local IPv4, Default Gateway, and DNS Servers. Missing values render explicitly as '—' or 'No data'."),

                ("h2", "6.3 Wi-Fi Scanner Module"),
                ("p", "Implemented in src/netvision/core/wifi_scanner.py and ui/pages/scanner_page.py, the Wi-Fi Scanner overcomes Windows scan-cache staleness by invoking trigger_active_wlan_scan() via ctypes.windll.wlanapi (opening a handle with WlanOpenHandle, enumerating adapters with WlanEnumInterfaces, triggering WlanScan on each interface GUID, and freeing memory via WlanFreeMemory / WlanCloseHandle). After allowing the radio to sweep channels, scan_networks() executes netsh wlan show networks mode=bssid with UTF-8 replacement decoding."),
                ("p", "Interface inspection (get_connected_interface) segments netsh wlan show interfaces output strictly at each 'Name' key so disconnected virtual adapters (such as Microsoft Wi-Fi Direct Virtual Adapters) cannot overwrite an active physical NIC. It then runs netsh interface ip show config <interface_name> to extract authentic IPv4, Default Gateway, and DNS server addresses, and disambiguates identical SSIDs operating on different radios by matching the exact connected BSSID MAC address."),
                ("code",
                 "def channel_to_band(channel: int) -> str:\n"
                 "    if 1 <= channel <= 14:\n"
                 "        return '2.4 GHz'\n"
                 "    elif 32 <= channel <= 177:\n"
                 "        return '5 GHz'\n"
                 "    elif channel > 177:\n"
                 "        return '6 GHz'\n"
                 "    return 'Unknown'"),

                ("h2", "6.4 Signal Analyzer Module"),
                ("p", "Implemented in src/netvision/core/signal_monitor.py and ui/pages/signal_page.py, the Signal Analyzer polls the active Wi-Fi interface inside SignalMonitorWorker at a configurable interval (default 2 seconds, sleeping in 0.1-second slices to permit rapid thread stopping). Each tick records a SignalLogEntry into SQLite tagged with the selected location, maintains a rolling 300-sample in-memory window, and computes session stability (mean, standard deviation, min, max, range, and categorical label). To avoid sliding-window X-axis collisions, SignalPage uses a strictly monotonic sample index counter rather than list length. If the adapter disconnects, connection_changed alerts the UI immediately rather than repeating stale percentages."),

                ("h2", "6.5 Speed Test Module"),
                ("p", "Implemented in src/netvision/core/speed_tester.py and ui/pages/speed_page.py, CloudflareSpeedEngine executes three distinct phases inside SpeedTestWorker:"),
                ("bullet", [
                    "Phase 1 — Edge TCP Latency & Jitter: Opens 5 sequential TCP sockets to speed.cloudflare.com:443, timing only the TCP 3-way handshake with time.perf_counter() to compute mean edge ping and consecutive-difference jitter without confusing HTTP transfer time for ping.",
                    "Phase 2 — Warm-Up Excluded Download: Downloads an initial 1 MB warm-up payload (excluded from throughput timing) so TCP congestion window scaling stabilizes, then streams 10 MB in 64 KB chunks while emitting real-time progress and checking self._abort on every chunk.",
                    "Phase 3 — Cancellable Chunked Upload: Streams 5 MB via a Python generator yielding 64 KB blocks to https://speed.cloudflare.com/__up, enforcing a 20-second total timeout and immediate cancellation if the user clicks Stop Test."
                ]),

                ("h2", "6.6 Latency Monitor Module"),
                ("p", "Implemented in src/netvision/core/latency_monitor.py and ui/pages/latency_page.py, LatencyMonitor strictly validates every user-supplied target host via validate_target_host()—rejecting empty strings, leading '-' or '/' option flags, and shell metacharacters, while permitting valid IPv4/IPv6 addresses or RFC 1123 hostnames up to 253 characters."),
                ("p", "Crucially, ICMP probing (_probe_icmp via ping -n 1 -w <timeout_ms> <host>) and TCP 3-way handshake probing (_probe_tcp_connect across ports 53, 443, and 80) are exposed as completely separate selectable methods ('ICMP' vs. 'TCP_CONNECT'). A dropped ICMP packet is never silently masked by a TCP connection fallback. Sub-millisecond Windows replies ('time<1ms') are parsed as 0.5 ms, and locale-independent failure phrases ('request timed out', 'destination host unreachable', 'general failure', etc.) return None."),

                ("h2", "6.7 Jitter and Packet Loss Calculation"),
                ("p", "In latency_monitor.py, calculate_jitter(rtts, method) computes delay variation strictly when at least two valid RTT replies exist (returning None otherwise). Both ITU-style mean consecutive difference (default in run_test) and the RFC 3550 Section 6.4.1 smoothed interarrival jitter filter are implemented and unit-tested. When all probes fail (100% packet loss), min_rtt_ms, max_rtt_ms, avg_rtt_ms, and jitter_ms are stored as None (SQL NULL) so failed tests never appear as 0 ms."),
                ("code",
                 "def calculate_jitter(\n"
                 "    rtts: List[float], method: str = 'consecutive_difference'\n"
                 ") -> Optional[float]:\n"
                 "    if not rtts or len(rtts) < 2:\n"
                 "        return None\n"
                 "    if method == 'rfc3550':\n"
                 "        j = abs(rtts[1] - rtts[0])\n"
                 "        for i in range(2, len(rtts)):\n"
                 "            j += (abs(rtts[i] - rtts[i - 1]) - j) / 16.0\n"
                 "        return round(j, 2)\n"
                 "    diffs = [abs(rtts[i] - rtts[i - 1]) for i in range(1, len(rtts))]\n"
                 "    return round(sum(diffs) / len(diffs), 2)"),

                ("h2", "6.8 Channel Analyzer Module"),
                ("p", "Implemented in src/netvision/core/channel_analyzer.py and ui/pages/channel_page.py, ChannelAnalyzer partitions discovered access points into separate 2.4 GHz, 5 GHz, and 6 GHz views. On 2.4 GHz, it evaluates candidate non-overlapping channels [1, 6, 11] using overlap weights (1.0, 0.75, 0.50, 0.25, 0.0 for channel deltas 0, 1, 2, 3, >=4) multiplied by a signal-strength factor (1 + signal%/100). On 5 GHz, where 20 MHz channels do not overlap adjacent channels, it evaluates standard UNII channels [36, 40, 44, 48, 149, 153, 157, 161] by fewest competing APs. If no scan data exists, has_data returns False and no recommendation is fabricated. Every analysis response embeds an explicit hardware scope disclaimer noting that consumer Wi-Fi NICs cannot detect non-802.11 RF interference."),

                ("h2", "6.9 History and Analytics Module"),
                ("p", "Implemented in src/netvision/ui/pages/history_page.py, HistoryPage displays tabbed archives of stored Speed Tests, Latency/Ping Tests, and Signal Logs from SQLite. Users can filter records interactively by search text (SSID, location, server/host), location dropdown, and optional calendar date range, visualize historical download throughput trends in an embedded Matplotlib chart, and remove individual records via whitelisted SQL deletion (delete_record validates table names against an explicit set to eliminate SQL injection risk)."),

                ("h2", "6.10 Location Comparison Module"),
                ("p", "Implemented in src/netvision/ui/pages/comparison_page.py, ComparisonPage enables side-by-side multi-environment evaluation. Users select any subset of configured locations via a checkable QListWidget. DatabaseManager queries speed tests, latency tests, and signal logs filtered by those exact location labels without arbitrary row truncation. Averages exclude failed/cancelled runs, latency means are weighted by probe count, separate sample counts (Signal Samples, Speed Tests, Ping Tests) are reported per location, and missing metrics are omitted from bar plots rather than plotted as zero."),

                ("h2", "6.11 Academic Experiment Module"),
                ("p", "Implemented in src/netvision/core/experiment_analytics.py, ExperimentWorker, and ui/pages/experiment_page.py, this module supports structured Computer Networks lab experimentation. Users specify a condition label (e.g., 'Condition A — Near Router'), target ping host, location tag, and trial count (3 to 10 runs). For each trial, ExperimentWorker sequentially captures Wi-Fi signal %, runs a Cloudflare speed test, and executes an ICMP latency probe, persisting every run under a shared experiment_id. The analytics engine computes sample mean and sample standard deviation (statistics.stdev) and calculates Pearson correlation (r) between signal % and download throughput—explicitly returning None ('N/A — insufficient variance or samples < 3') if fewer than 3 paired observations exist or either series has near-zero variance. A second tab archives all historical experiments from SQLite."),

                ("h2", "6.12 Report Generation and Recommendation Engine"),
                ("p", "RecommendationEngine (src/netvision/core/recommendation_engine.py) evaluates live interface, speed, latency, and channel metrics against centralized thresholds (DEFAULT_THRESHOLDS or user-saved settings) to produce structured Recommendation objects with Severity, Category, Observed Evidence, and Actionable Advice—including ISP bottleneck detection when Wi-Fi signal is >=75% but WAN download speed is <10 Mbps."),
                ("p", "ReportGenerator (src/netvision/core/reporter.py) exports two formats into %LOCALAPPDATA%\\NetVision\\reports\\: (1) styled multi-section PDF audit reports via ReportLab SimpleDocTemplate with xml.sax.saxutils.escape() protecting against XML tag characters such as '<Hidden SSID>'; and (2) unified UTF-8 BOM (utf-8-sig) CSV exports passing every string cell through sanitize_csv_cell() to prepend a single quote before spreadsheet formula triggers ('=', '+', '-', '@')."),

                ("h2", "6.13 Database Operations and Migrations"),
                ("p", "DatabaseManager (src/netvision/database/db_manager.py) initializes nine tables and nine indices automatically and tracks schema state via the schema_version table. When upgrading a Version 1 database to Version 2, _apply_migrations() safely recreates latency_tests and speed_tests with nullable metric columns and additional method/status metadata, copying all existing historical rows without data loss before swapping table names and recording Version 2."),

                ("h2", "6.14 Background Threads and Safe Lifecycle"),
                ("p", "Five QThread subclasses in src/netvision/core/workers.py—WifiScanWorker, SpeedTestWorker, LatencyTestWorker, SignalMonitorWorker, and ExperimentWorker—encapsulate all slow operations. MainWindow maintains persistent object references to active workers so Python's garbage collector never destroys a running QThread. During window shutdown, MainWindow.closeEvent() signals abort/stop on every active worker and waits up to 1000 ms for clean socket and subprocess termination."),

                ("h2", "6.15 Error Handling, Input Validation, and Windows Packaging"),
                ("p", "Every subprocess call enforces explicit timeouts and UTF-8 error replacement; network timeouts catch requests.exceptions.Timeout and socket.timeout cleanly; and unhandled worker exceptions emit failed DTOs rather than crashing the GUI. For deployment, scripts/build_exe.py compiles both dist/NetVision/NetVision.exe (onedir) and dist/NetVision_Portable.exe (onefile) with embedded Windows PE version info (scripts/windows_version_info.txt) and multi-resolution netvision.ico. Furthermore, scripts/build_installer.py compiles uninstaller_gui.py and installer_gui.py into installer/NetVision_Setup.exe, which installs per-user into %LOCALAPPDATA%\\Programs\\NetVision, creates Desktop and Start Menu shortcuts, registers in HKCU\\...\\Uninstall\\NetVision, and preserves user databases by default upon uninstallation. An Inno Setup 6 script (installer/NetVision_Setup.iss) is also provided."),
            ],
        },

        # =====================================================================
        # CHAPTER 7
        # =====================================================================
        {
            "num": "7",
            "title": "MEASUREMENT METHODOLOGY",
            "blocks": [
                ("h2", "7.1 Wi-Fi Signal Quality and Threshold Classification"),
                ("p", "Windows reports wireless reception quality through netsh and the Native Wifi API as an integer percentage from 0% to 100% (internally mapped by Windows WLAN drivers from hardware RSSI in dBm, typically interpolating -100 dBm as 0% and -50 dBm or stronger as 100%). NetVision preserves the exact OS-reported signal percentage without back-calculating approximate dBm claims, and categorizes reception using centralized configurable thresholds (Table 7.1)."),
                ("table", (
                    "Table 7.1: Centralized Default Network Quality Evaluation Thresholds (config.py)",
                    ["Metric", "Excellent", "Good", "Fair", "Poor"],
                    [
                        ["Wi-Fi Signal Quality (%)", ">= 75%", "50% – 74%", "30% – 49%", "< 30%"],
                        ["Round-Trip Latency (ms)", "<= 30 ms", "31 – 60 ms", "61 – 100 ms", "> 100 ms"],
                        ["Packet Loss (%)", "0.0%", "<= 1.0%", "1.1% – 3.0%", "> 3.0% (Critical > 5%)"],
                        ["Download Speed (Mbps)", ">= 50.0 Mbps", "25.0 – 49.9 Mbps", "10.0 – 24.9 Mbps", "< 10.0 Mbps"],
                    ]
                )),

                ("h2", "7.2 Wi-Fi Channel, Frequency Band, and Link Rate"),
                ("p", "Frequency bands are derived deterministically from the IEEE 802.11 channel number reported by netsh: Channels 1–14 map to 2.4 GHz, Channels 32–177 map to 5 GHz, and Channels >177 map to 6 GHz. Receive and Transmit Link Rates (Mbps) are parsed directly from the Windows interface block ('Receive rate (Mbps)' and 'Transmit rate (Mbps)'), representing the current Layer 1/2 PHY modulation and coding scheme (MCS) negotiated between the client NIC and access point."),

                ("h2", "7.3 WAN Download and Upload Throughput"),
                ("p", "Application-layer throughput is measured in megabits per second (Mbps, decimal base 10^6 per networking convention) after excluding initial connection setup and—for downloads—a 1 MB warm-up transfer that allows TCP slow start to open the congestion window:"),
                ("formula", "Throughput (Mbps) = (Total Bytes Transferred × 8) / (Transfer Elapsed Time in Seconds × 1,000,000)"),
                ("p", "Elapsed time is sampled using Python's monotonic high-resolution clock (time.perf_counter()), ensuring system wall-clock adjustments cannot corrupt throughput calculations. Downloads transfer 10,000,000 bytes (10 MB) in 65,536-byte chunks from speed.cloudflare.com/__down?bytes=10000000; uploads stream 5,000,000 bytes (5 MB) in 65,536-byte chunks via HTTP POST to speed.cloudflare.com/__up."),

                ("h2", "7.4 Round-Trip Time (RTT) and Packet Loss"),
                ("p", "During a latency test of N sent probes, let S = {r_1, r_2, ..., r_k} denote the ordered set of k successful round-trip replies (in milliseconds) and L = N - k denote the number of timed-out or unreachable probes. When k > 0, NetVision computes:"),
                ("formula", "Mean RTT (ms) = (1 / k) × Σ_{i=1}^{k} r_i     |     Min RTT = min(S)     |     Max RTT = max(S)"),
                ("formula", "Packet Loss (%) = (L / N) × 100.0"),
                ("p", "When k = 0 (all probes lost), Packet Loss is 100.0% and Min/Max/Mean RTT and Jitter are recorded strictly as SQL NULL. When Windows ping.exe reports 'time<1ms' on a fast local gateway, NetVision records 0.5 ms to distinguish genuine sub-millisecond replies from missing values."),

                ("h2", "7.5 Jitter Calculation"),
                ("p", "Jitter quantifies short-term variation in packet delay and requires at least two valid consecutive replies (k >= 2; otherwise NULL). NetVision implements two documented methods in calculate_jitter():"),
                ("formula", "1. Mean Consecutive Difference (Active Default in run_test):   J_cd = (1 / (k - 1)) × Σ_{i=2}^{k} |r_i - r_{i-1}|"),
                ("formula", "2. RFC 3550 Section 6.4.1 Smoothed Interarrival Jitter (Optional):   J_i = J_{i-1} + (|r_i - r_{i-1}| - J_{i-1}) / 16"),
                ("p", "Documenting both formulas explicitly ensures academic transparency: Mean Consecutive Difference is used as the default metric in LatencyMonitor.run_test() and CloudflareSpeedEngine.measure_edge_latency_and_jitter(), while the RFC 3550 exponential moving estimator is also implemented and verified in unit tests."),

                ("h2", "7.6 Continuous Signal Stability"),
                ("p", "For a session window of n signal observations {s_1, ..., s_n}, SignalMonitor computes the session mean and population standard deviation:"),
                ("formula", "Mean Signal = (1 / n) × Σ s_i     |     σ = sqrt( (1 / n) × Σ (s_i - Mean Signal)^2 )"),
                ("p", "Links are categorized as 'Very Stable' (σ <= 3.0), 'Moderate Fluctuation' (3.0 < σ <= 7.0), or 'Highly Unstable' (σ > 7.0)."),

                ("h2", "7.7 2.4 GHz Spectral Overlap Estimation"),
                ("p", "In the 2.4 GHz band, each 802.11 channel spans 20 MHz around centers separated by 5 MHz. ChannelAnalyzer estimates cumulative interference on each standard candidate channel c in {1, 6, 11} by summing weighted contributions from every detected 2.4 GHz access point j:"),
                ("formula", "Overlap Score(c) = Σ_j  w(|ch_j - c|) × (1.0 + signal_j / 100.0)"),
                ("table", (
                    "Table 7.2: IEEE 802.11 2.4 GHz Spectral Overlap Weights Implemented in ChannelAnalyzer",
                    ["Channel Delta |ch_j - c|", "Frequency Separation", "Overlap Classification", "Weight w"],
                    [
                        ["0", "0 MHz", "Co-Channel (Direct Overlap)", "1.00"],
                        ["1", "5 MHz", "High Adjacent Overlap", "0.75"],
                        ["2", "10 MHz", "Medium Adjacent Overlap", "0.50"],
                        ["3", "15 MHz", "Slight Adjacent Overlap", "0.25"],
                        [">= 4", ">= 20 MHz", "Non-Overlapping", "0.00"],
                    ]
                )),
                ("p", "The candidate channel with the minimum Overlap Score(c) is recommended. Because consumer NICs cannot measure non-Wi-Fi RF noise or actual channel airtime utilization, this score is explicitly labeled in both the UI and reports as an AP-beacon-based estimate."),

                ("h2", "7.8 Academic Experiment Statistical Metrics"),
                ("p", "Across m completed experiment trials, experiment_analytics.py computes sample mean, sample standard deviation (Bessel-corrected denominator m - 1 via Python statistics.stdev), and Pearson product-moment correlation coefficient r between Wi-Fi signal percentage (X) and download throughput (Y):"),
                ("formula", "r = Sum[ (x_i - mean_x)(y_i - mean_y) ] / sqrt( Sum[(x_i - mean_x)^2] × Sum[(y_i - mean_y)^2] )"),
                ("p", "To prevent division by zero or spurious correlations on small or stationary datasets, calculate_pearson_correlation() returns None whenever fewer than 3 valid paired points exist or either series has variance <= 10^-9."),

                ("h2", "7.9 Distinguishing Core Network Performance Concepts"),
                ("p", "A central pedagogical goal of NetVision is helping students and evaluators distinguish four frequently conflated networking metrics. Table 7.3 contrasts these concepts using genuine measurements recorded on the test machine."),
                ("table", (
                    "Table 7.3: Conceptual Distinction Between Signal Quality, Link Speed, Throughput, and Latency",
                    ["Metric", "Protocol Layer", "What It Measures", "Real Host Observation"],
                    [
                        ["Wi-Fi Signal Quality (%)", "Layer 1 (PHY)", "Relative RF power received from the local access point.", "83% (Excellent on Ch 11, 2.4 GHz)"],
                        ["Wi-Fi Link Speed (Mbps)", "Layer 1/2 (PHY/MAC)", "Maximum raw bit rate negotiated over the wireless hop (includes framing & CSMA/CA overhead).", "72.2 Mbps Rx / 72.2 Mbps Tx (802.11n)"],
                        ["Internet Throughput (Mbps)", "Layer 7 (End-to-End)", "Actual useful payload bits per second transferred across Wi-Fi, router, ISP, and WAN CDN.", "47.35 Mbps Down / 33.30 Mbps Up"],
                        ["Network Latency (ms)", "Layer 3/4 (RTT)", "Round-trip time for a small probe packet to reach a remote host and return.", "12.0 ms Avg ICMP RTT to 8.8.8.8 (0% loss)"],
                    ]
                )),
            ],
        },

        # =====================================================================
        # CHAPTER 8
        # =====================================================================
        {
            "num": "8",
            "title": "DATABASE AND DATA MANAGEMENT",
            "blocks": [
                ("h2", "8.1 SQLite Engine Configuration"),
                ("p", "NetVision uses Python's built-in sqlite3 module targeting a single relational file at %LOCALAPPDATA%\\NetVision\\database\\netvision.db. Every connection returned by DatabaseManager.get_connection() sets sqlite3.Row for dictionary-style access and applies three critical pragmas: PRAGMA foreign_keys = ON (enforcing referential integrity), PRAGMA journal_mode = WAL (Write-Ahead Logging for non-blocking concurrent reads and writes), and PRAGMA busy_timeout = 5000 (preventing transient lock exceptions during rapid background worker writes)."),

                ("h2", "8.2 Complete Relational Schema Inventory"),
                ("p", "Table 8.1 documents all nine tables verified directly from src/netvision/database/db_manager.py."),
                ("table", (
                    "Table 8.1: Complete Relational SQLite Schema Inventory (9 Tables, Schema v2)",
                    ["Table Name", "Primary / Foreign Keys", "Key Columns & Nullability", "Purpose"],
                    [
                        ["scan_sessions", "PK id", "timestamp, total_networks, active_interface, location_label", "Parent header for each Wi-Fi scan sweep."],
                        ["wifi_networks", "PK id; FK session_id -> scan_sessions(id) CASCADE", "ssid, bssid, signal_percent, channel, frequency_band, security_type, is_connected, radio_type, observed_at", "Individual BSSID access points observed in a scan session."],
                        ["speed_tests", "PK id", "timestamp, download_mbps (NULL), upload_mbps (NULL), ping_ms (NULL), jitter_ms (NULL), duration_sec, server_name, network_ssid, location_label, status, error_message", "Historical WAN speed test records supporting failed/cancelled NULLs."],
                        ["latency_tests", "PK id", "timestamp, target_host, ping_count, min/max/avg_rtt_ms (NULL), jitter_ms (NULL), packet_loss_percent, method, status, network_ssid, location_label", "ICMP and TCP_CONNECT latency test summaries."],
                        ["signal_logs", "PK id", "timestamp, network_ssid, bssid, signal_percent, channel, frequency_band, location_label", "Time-series Wi-Fi signal observations from Signal Analyzer."],
                        ["locations", "PK id; UNIQUE name", "name, created_at, description", "Reusable environment tags (Home, College Library, Classroom, Cafe, Office, + custom)."],
                        ["experiment_runs", "PK id", "experiment_id, condition_label, run_number, timestamp, network_ssid, location_label, signal_percent, ping_ms, jitter_ms, packet_loss_percent, download_mbps, upload_mbps, target_host, status", "Multi-trial academic experiment series grouped by experiment_id."],
                        ["app_settings", "PK key", "value, updated_at", "Persisted thresholds, ping targets, and polling defaults."],
                        ["schema_version", "PK version", "applied_at, description", "Tracks database schema version for safe in-place upgrades."],
                    ]
                )),

                ("h2", "8.3 Indexing and Query Optimization"),
                ("p", "To maintain sub-millisecond historical filtering and multi-location aggregation as scan logs grow, nine B-tree indices are created automatically during initialization: idx_wifi_session, idx_speed_time, idx_speed_loc, idx_latency_time, idx_latency_loc, idx_signal_time, idx_signal_loc, idx_experiment_id, and idx_experiment_loc. Location comparison queries fetch records using parameterized IN (?, ?, ...) clauses across user-selected location names without artificial row limits."),

                ("h2", "8.4 Schema Versioning and Safe Data Migration"),
                ("p", "Early v1 database files enforced NOT NULL constraints on speed and latency columns and lacked method/status tracking. DatabaseManager._apply_migrations() inspects PRAGMA table_info() and schema_version on startup; when upgrading v1 to v2, it creates replacement tables (latency_tests_v2, speed_tests_v2), copies every existing row verbatim with sensible defaults ('ICMP', 'completed'), replaces the tables atomically inside a transaction, rebuilds indices, and inserts version 2 into schema_version. Existing user records are never discarded or overwritten."),

                ("h2", "8.5 Runtime User-Data Isolation and Persistence"),
                ("p", "Separating program binaries from user data ensures NetVision operates cleanly when installed under %LOCALAPPDATA%\\Programs\\NetVision or launched from a read-only USB drive. Table 8.2 summarizes the runtime folder layout."),
                ("table", (
                    "Table 8.2: User-Data Directory Isolation Under %LOCALAPPDATA%\\NetVision",
                    ["Subfolder", "Resolved Path", "Stored Artifacts"],
                    [
                        ["database/", "%LOCALAPPDATA%\\NetVision\\database\\netvision.db", "Primary SQLite 3 database, WAL (-wal), and shared-memory (-shm) files."],
                        ["logs/", "%LOCALAPPDATA%\\NetVision\\logs\\netvision.log", "Timestamped rotating application diagnostic logs."],
                        ["reports/", "%LOCALAPPDATA%\\NetVision\\reports\\", "Generated ReportLab PDF audit reports and exported CSV files."],
                        ["exports/", "%LOCALAPPDATA%\\NetVision\\exports\\", "User-initiated data exports."],
                        ["config/", "%LOCALAPPDATA%\\NetVision\\config\\", "User configuration files."],
                        ["cache/", "%LOCALAPPDATA%\\NetVision\\cache\\", "Temporary runtime cache files."],
                    ]
                )),
                ("p", "During uninstallation via uninstall.exe, the checkbox 'Also delete saved network scan history, databases, and reports' is unchecked by default, ensuring user measurements remain intact unless deletion is explicitly confirmed."),
            ],
        },

        # =====================================================================
        # CHAPTER 9
        # =====================================================================
        {
            "num": "9",
            "title": "SCREENSHOTS AND USER GUIDE",
            "blocks": [
                ("p", "All figures in this chapter are genuine, unedited screenshots captured directly from the running NetVision v2.0.0 desktop application on Windows 10 (64-bit) using real wireless hardware observations (Realtek RTL8723DE 802.11b/g/n adapter connected to SSID Airtel_maha_9259) and genuine local SQLite database records."),

                ("h2", "9.1 Application Launch and Dashboard"),
                ("figure", (
                    "Figure 9.1",
                    "Main Dashboard — Active Link Overview, Metric Cards, and Radio/Gateway Parameters",
                    SHOTS_DIR / "01_dashboard.png",
                    "Dashboard displaying the active connection banner (Airtel_maha_9259, 2.4 GHz, Channel 11, IP 192.168.1.9, Excellent status badge), six live/latest health metric cards (83% signal, 47.4 Mbps download, 33.3 Mbps upload, 12.0 ms ICMP ping, 5.8 ms jitter, 0.0% loss), and the bottom Active Radio & Gateway Parameters panel (BSSID 30:15:77:fc:ae:a6, 802.11n, WPA2-Personal/CCMP, 72.2 Mbps Rx/Tx link rate, Gateway 192.168.1.1, DNS 8.8.8.8 / 8.8.4.4)."
                )),
                ("p", "Users can observe both physical-layer Wi-Fi status and latest end-to-end internet performance immediately on startup. Clicking Refresh Link re-queries the active Windows adapter, while Quick Network Test initiates a fast latency probe without leaving the overview page."),

                ("h2", "9.2 Wi-Fi Scanner"),
                ("figure", (
                    "Figure 9.2",
                    "Nearby Wi-Fi Network Scanner — Live Discovery of 31 Access Points",
                    SHOTS_DIR / "02_wifi_scanner.png",
                    "Wi-Fi Scanner populated by an active Windows WLAN API scan showing 31 real nearby access points sorted by signal quality, highlighting the connected BSSID (Airtel_maha_9259 at 86%, Ch 11, 2.4 GHz, WPA2-Personal, 802.11ax AP) alongside neighboring SSIDs, channels, bands, security types, and MAC addresses."
                )),
                ("p", "Users select a Location Label, click Scan Networks, and can immediately search by SSID, channel, or band or sort by signal strength. Each completed scan automatically saves a parent session and child network rows into SQLite."),

                ("h2", "9.3 Signal Analyzer"),
                ("figure", (
                    "Figure 9.3",
                    "Wi-Fi Signal & RF Stability Analyzer — Continuous Polling and Stability Metrics",
                    SHOTS_DIR / "03_signal_analyzer.png",
                    "Signal Analyzer displaying six live observations of Airtel_maha_9259 (Current Signal 83%, Average Signal 83.0%, Stability 0.0 sigma classified 'Very Stable', Spread 83–83%, Range 0%) plotted against monotonic sample indices."
                )),
                ("p", "This view is used to detect intermittent RF fading or walk-test signal drops when moving between rooms. Users can adjust the polling interval (in seconds), tag samples with a location label, and clear the live session window at any time."),

                ("h2", "9.4 Speed Test"),
                ("figure", (
                    "Figure 9.4",
                    "Network Speed & Bandwidth Test — Cloudflare Global Edge Throughput Measurement",
                    SHOTS_DIR / "04_speed_test.png",
                    "Speed Test module displaying a completed Cloudflare Global Edge measurement finished in 3.9 seconds (47.4 Mbps download, 33.3 Mbps upload, 28.4 ms TCP edge server ping) with a comparative throughput bar chart and cancellable Stop Test control."
                )),
                ("p", "This view measures true Layer 7 WAN bandwidth rather than local Wi-Fi link speed. Progress updates continuously across the latency, download, and upload phases while remaining fully interruptible."),

                ("h2", "9.5 Latency Monitor"),
                ("figure", (
                    "Figure 9.5",
                    "Latency Monitor — Isolated ICMP Echo Probing, RTT Graph, and Packet Loss",
                    SHOTS_DIR / "05_latency_monitor.png",
                    "Latency Monitor illustrating 6 live ICMP probes to 8.8.8.8 (Min 7 ms, Avg 12.0 ms, Max 32 ms, Jitter 5.8 ms consecutive variation, Packet Loss 0.0%) with a probe-by-probe RTT sequence plot."
                )),
                ("p", "Users can enter any valid IPv4/IPv6 address or hostname, choose between isolated ICMP Ping or TCP Connect methods, configure probe count, and inspect transient latency spikes (such as Probe 1 at 32 ms settling to 7–9 ms on Probes 2–6)."),

                ("h2", "9.6 Channel Analyzer"),
                ("figure", (
                    "Figure 9.6",
                    "Channel Analyzer — 2.4 GHz AP Distribution and Spectral Overlap Recommendation",
                    SHOTS_DIR / "06_channel_analyzer.png",
                    "Channel Analyzer visualizing 31 real 2.4 GHz APs: heavy congestion on Channel 11 (11 APs) and Channel 6 (9 APs) versus lower occupancy on Channel 1 (4 APs), recommending Channel 1 (overlap score 7.4) alongside an explicit hardware scope disclaimer."
                )),
                ("p", "Switching between the 2.4 GHz and 5 GHz tabs prevents mixing channel numbering across bands. On the test laptop's single-band 2.4 GHz adapter, the 5 GHz summary honestly reports 'No data. No 5 GHz networks detected in range'."),

                ("h2", "9.7 History and Analytics"),
                ("figure", (
                    "Figure 9.7",
                    "History & Analytics — Persistent SQLite Archive with Filtering and Trend Plots",
                    SHOTS_DIR / "07_history_analytics.png",
                    "History & Analytics displaying historical download throughput trends (37.4 Mbps and 47.4 Mbps across completed runs) with search, location filter, date range controls, tabbed views (Speed Tests, Latency/Ping Tests, Signal Logs), and per-row Delete actions."
                )),
                ("p", "This page provides longitudinal visibility across testing days and sessions, confirming that records survive application restarts inside SQLite."),

                ("h2", "9.8 Location Comparison"),
                ("figure", (
                    "Figure 9.8",
                    "Cross-Location Comparative Analytics — Multi-Environment Signal, Speed, and Latency",
                    SHOTS_DIR / "08_location_comparison.png",
                    "Location Comparison displaying checkable location filters (Cafe, Classroom, College Library, Home, Office) and side-by-side average Wi-Fi signal %, WAN download speed, and latency bar charts built strictly from persisted records."
                )),
                ("p", "Only locations possessing genuine data for a metric appear in each bar chart (e.g., Cafe and Home appear for Signal and Latency, while Cafe appears for Speed where speed tests were recorded), proving that missing locations are never falsified as zero."),

                ("h2", "9.9 Academic Experiment"),
                ("figure", (
                    "Figure 9.9",
                    "Academic Experiment — Multi-Trial Evaluation, Spread, and Correlation Guard",
                    SHOTS_DIR / "09_academic_experiment.png",
                    "Academic Experiment page displaying 5 genuine trials under Condition A (Mean Signal 88.0% +-0.0%, Mean Download 43.8 +-2.3 Mbps, Mean Latency 12.1 +-2.5 ms, Mean Jitter 8.1 +-4.7 ms), trial-by-trial throughput plot, and scatter plot honestly reporting 'Correlation: N/A (insufficient variance or samples < 3)'."
                )),
                ("p", "Notice how the scatter plot verifies statistical honesty: because the laptop remained stationary at 88% signal across all 5 trials (zero variance in X), Pearson correlation is mathematically undefined and explicitly reported as N/A rather than fabricated."),

                ("h2", "9.10 Audit Reports"),
                ("figure", (
                    "Figure 9.10",
                    "Audit Reports & Data Export — Rule-Based Recommendations and PDF/CSV Generation",
                    SHOTS_DIR / "10_audit_reports.png",
                    "Audit Reports page listing live evidence-backed diagnostic findings (GOOD: Strong Wi-Fi Radio Link at 83%; TIP: Connected on 2.4 GHz band; GOOD: Low Latency 12.0 ms; TIP: Suboptimal Channel 11 vs Channel 1) alongside Generate PDF Report, Export Raw CSV, and Open Reports Folder buttons."
                )),

                ("h2", "9.11 Settings and About NetVision"),
                ("figure", (
                    "Figure 9.11",
                    "System Settings & Threshold Configuration — Targets, Thresholds, and Custom Locations",
                    SHOTS_DIR / "11_settings.png",
                    "Settings page allowing users to customize default ping target host (8.8.8.8), signal polling interval (2 s), signal/latency/loss/speed quality thresholds, and custom location tags persisted in SQLite."
                )),
                ("figure", (
                    "Figure 9.12",
                    "About NetVision — System Architecture Summary and Host Runtime Telemetry",
                    SHOTS_DIR / "12_about_netvision.png",
                    "About NetVision page detailing core architectural components alongside live host runtime telemetry (Windows 10 64-bit, Python 3.12.16, PySide6/Qt 6.8, and exact resolved %LOCALAPPDATA%\\NetVision database and log paths)."
                )),
            ],
        },

        # =====================================================================
        # CHAPTER 10
        # =====================================================================
        {
            "num": "10",
            "title": "TESTING AND VALIDATION",
            "blocks": [
                ("h2", "10.1 Testing Objectives"),
                ("p", "Verification of NetVision focused on four objectives: (1) mathematical accuracy of latency, jitter, signal stability, overlap scoring, and experiment statistics; (2) parser robustness across real Windows netsh and ping outputs including multi-adapter and hidden-SSID edge cases; (3) database reliability including NULL preservation, WAL concurrency, and v1-to-v2 schema migration; and (4) live operational validation on Windows hardware and packaged executables."),

                ("h2", "10.2 Unit and Integration Testing (Automated Pytest Suite)"),
                ("p", "Automated verification was executed using pytest 9.2.0 on Python 3.12.16 (64-bit) under Windows 10. All 46 automated test cases across nine test modules passed in 6.99 seconds with zero skips or failures (Table 10.1)."),
                ("table", (
                    "Table 10.1: Automated Test Suite Breakdown (pytest — 46 Passing Cases)",
                    ["Test Module", "Test Count", "Verified Scope", "Result"],
                    [
                        ["tests/test_calculations.py", "9", "Consecutive-difference & RFC 3550 jitter, edge cases (<2 samples), target host injection validation, Windows ping parsing (time<1ms, timeouts), signal stability, channel-to-band mapping.", "9 / 9 PASSED"],
                        ["tests/test_channel_analyzer.py", "3", "Channel AP distribution, empty scan NULL safety, 2.4 GHz overlap weight matrix.", "3 / 3 PASSED"],
                        ["tests/test_database.py", "11", "Schema init, WAL mode, scan sessions, CRUD for speed/latency/signal/experiment tables, NULL handling on failed/100%-loss runs, multi-location queries, record deletion, app_settings.", "11 / 11 PASSED"],
                        ["tests/test_experiment_analytics.py", "5", "Sample mean/SD, perfect Pearson r, zero-variance / N<3 edge cases, correlation interpretation, full experiment summary.", "5 / 5 PASSED"],
                        ["tests/test_gui_launch.py", "1", "Headless PySide6 MainWindow instantiation with temporary DB and clean lifecycle.", "1 / 1 PASSED"],
                        ["tests/test_recommendations.py", "4", "Disconnected link, weak signal, high packet loss, and strong-signal/low-speed ISP bottleneck rules.", "4 / 4 PASSED"],
                        ["tests/test_reporting.py", "4", "CSV formula-injection sanitization, XML entity escaping (<Hidden SSID>), UTF-8 BOM CSV nulls, ReportLab PDF generation with special characters.", "4 / 4 PASSED"],
                        ["tests/test_user_data_and_config.py", "4", "%LOCALAPPDATA% folder layout, multi-resolution icon existence, custom DB initialization, non-overwrite guarantee.", "4 / 4 PASSED"],
                        ["tests/test_wifi_parser.py", "5", "netsh network parsing, connected BSSID disambiguation, empty scans, multiple adapters, AP BSSID locale variations.", "5 / 5 PASSED"],
                    ]
                )),

                ("h2", "10.3 Application, Packaging, and Live Hardware Testing"),
                ("p", "In addition to automated pytest verification (which uses synthetic fixtures for deterministic parser/math assertions), live operational testing was conducted directly on the Windows 10 host machine with its physical Realtek RTL8723DE wireless adapter and live internet access, as well as against all compiled Windows executables:"),
                ("bullet", [
                    "Live Wi-Fi Hardware Scan: Triggered WlanScan via wlanapi.dll and parsed 31 real surrounding access points, accurately matching active BSSID 30:15:77:fc:ae:a6 on Channel 11 and extracting Gateway 192.168.1.1 and DNS 8.8.8.8 / 8.8.4.4.",
                    "Live ICMP & WAN Tests: Executed 6 live ICMP probes to 8.8.8.8 (Min 7.0 ms, Avg 12.0 ms, Max 32.0 ms, Jitter 5.8 ms, 0.0% loss) and live Cloudflare Global Edge streaming (47.35 Mbps download, 33.30 Mbps upload, 28.4 ms TCP edge ping in 3.88 s).",
                    "Packaged Binary Execution: Verified live launch and clean termination of dist/NetVision/NetVision.exe (PID 7376), dist/NetVision_Portable.exe (PID 4536), and installer/NetVision_Setup.exe (PID 9652), confirming runtime log and DB creation in %LOCALAPPDATA%\\NetVision."
                ]),

                ("h2", "10.4 Comprehensive Test-Case Matrix"),
                ("p", "Table 10.2 documents individual verification test cases, strictly distinguishing executed tests (PASS) from hardware/platform scenarios that could not be exercised on the available single-band Windows 10 host (labeled NOT TESTED)."),
                ("table", (
                    "Table 10.2: Detailed System Verification and Validation Test-Case Matrix",
                    ["Test ID", "Test Description", "Input / Condition", "Expected Result", "Actual Result", "Status"],
                    [
                        ["TC-01", "Host injection validation", "Host='-n 10 8.8.8.8' or '8.8.8.8; calc'", "Raises ValueError rejecting flags/metacharacters", "ValueError raised in unit test", "PASS"],
                        ["TC-02", "ICMP sub-ms & timeout parsing", "Windows 'time<1ms' & 'Request timed out.'", "Returns 0.5 ms and None respectively", "Returned 0.5 and None", "PASS"],
                        ["TC-03", "ICMP isolation on 100% loss", "All probes timed out (ICMP mode)", "Loss=100%, min/max/avg/jitter=NULL, no TCP fallback", "Stored NULLs & 100% loss", "PASS"],
                        ["TC-04", "Jitter formulas (<2 samples)", "Single RTT [14.0] or empty []", "Returns None (no fabricated jitter)", "Returned None", "PASS"],
                        ["TC-05", "Multi-adapter netsh parsing", "2 adapters: 1 disconnected virtual, 1 connected", "Selects active connected physical adapter", "Selected active adapter & BSSID", "PASS"],
                        ["TC-06", "2.4 GHz overlap scoring", "APs on Ch 1, 2, 6, 11 with signal weights", "Applies weights 1.0/0.75/0.50/0.25 correctly", "Exact scores verified", "PASS"],
                        ["TC-07", "PDF XML & CSV DDE safety", "SSID='<Hidden & Test>', cell='=CMD|...'", "Escapes XML entities; prefixes formula with '", "Valid PDF & safe UTF-8 CSV", "PASS"],
                        ["TC-08", "SQLite v1->v2 migration & non-overwrite", "Existing user DB with prior records", "Migrates cleanly preserving all existing rows", "All rows preserved; WAL active", "PASS"],
                        ["TC-09", "Live Windows Wi-Fi scan", "Realtek RTL8723DE on Windows 10", "Discovers nearby APs & active gateway/DNS", "31 APs found; BSSID & GW matched", "PASS"],
                        ["TC-10", "Live Cloudflare speed test", "Active internet via Airtel_maha_9259", "Completes download/upload with progress", "47.35 down / 33.30 up in 3.88s", "PASS"],
                        ["TC-11", "Live ICMP ping to 8.8.8.8", "6 ICMP probes at 0.2s interval", "Computes RTT, jitter, and loss", "Avg 12.0 ms, Jitter 5.8 ms, 0% loss", "PASS"],
                        ["TC-12", "Packaged EXEs & Setup Wizard", "Launch NetVision.exe, Portable & Setup.exe", "Launches standalone & writes to LOCALAPPDATA", "PIDs 7376, 4536, 9652 verified", "PASS"],
                        ["TC-13", "Live 5 GHz / 6 GHz hardware scan", "Dual-band Wi-Fi 6 / 6E physical NIC", "Detects 5 GHz / 6 GHz channels & recommends", "Host NIC is 2.4 GHz-only (RTL8723DE)", "NOT TESTED"],
                        ["TC-14", "Clean second-PC deployment test", "Fresh Windows 11 PC with no Python", "Setup Wizard installs & runs standalone", "Verified locally; no 2nd PC available", "NOT TESTED"],
                    ]
                )),

                ("h2", "10.5 Testing Limitations"),
                ("p", "Two validation boundaries are noted honestly: (1) 5 GHz and 6 GHz band parsing and channel recommendation logic are verified via automated unit tests with synthetic netsh payloads, but live over-the-air 5 GHz/6 GHz scanning could not be executed because the development laptop houses a 2.4 GHz-only Realtek RTL8723DE adapter; and (2) although PyInstaller standalone binaries and Setup Wizard launched cleanly on the build host without invoking venv, full clean-machine verification on a completely separate Windows 11 PC without Python installed remains a recommended final step before broader distribution."),
            ],
        },

        # =====================================================================
        # CHAPTER 11
        # =====================================================================
        {
            "num": "11",
            "title": "RESULTS AND DISCUSSION",
            "blocks": [
                ("h2", "11.1 Empirical Live Hardware and WAN Results"),
                ("p", "Live execution of NetVision v2.0.0 on the host Windows 10 laptop produced concrete, internally consistent network diagnostics across every protocol layer. Table 11.1 consolidates the genuine measurements recorded in %LOCALAPPDATA%\\NetVision\\database\\netvision.db at the time of final verification."),
                ("table", (
                    "Table 11.1: Genuine Live Hardware and WAN Measurements Recorded on Test Machine",
                    ["Measurement Parameter", "Observed Genuine Value", "Diagnostic Interpretation"],
                    [
                        ["Wireless Adapter", "Realtek RTL8723DE 802.11b/g/n PCIe", "Single-band 2.4 GHz 1×1 802.11n adapter (max 72.2 Mbps PHY)."],
                        ["Connected SSID / BSSID", "Airtel_maha_9259 (30:15:77:fc:ae:a6)", "Active connection disambiguated via exact BSSID match."],
                        ["Signal Quality & Stability", "83% (Mean 83.0%, SD 0.0 sigma, 6 ticks)", "Excellent, highly stable indoor reception."],
                        ["Operating Channel & Band", "Channel 11 (2.4 GHz)", "Heavily congested channel sharing airtime with 10 other APs."],
                        ["PHY Link Rate (Rx / Tx)", "72.2 Mbps / 72.2 Mbps", "Maximum Layer 1/2 20 MHz 802.11n signaling rate."],
                        ["IPv4 / Gateway / DNS", "192.168.1.9 / 192.168.1.1 / 8.8.8.8, 8.8.4.4", "Valid local DHCP assignment and public Google DNS."],
                        ["Cloudflare WAN Speed Test", "47.35 Mbps Down / 33.30 Mbps Up (3.88 s)", "~65.6% efficiency of 72.2 Mbps PHY rate—textbook 802.11 MAC overhead."],
                        ["ICMP Latency to 8.8.8.8", "Min 7.0 ms, Avg 12.0 ms, Max 32.0 ms", "Low average latency; transient 32 ms spike on Probe 1."],
                        ["ICMP Jitter & Packet Loss", "5.8 ms consecutive diff / 0.0% Loss", "Zero packet loss; suitable for VoIP and video calls."],
                        ["5-Trial Experiment (Cond. A)", "Signal 88.0% +-0%, Down 43.8 +-2.3 Mbps", "Consistent throughput; Correlation honestly marked N/A (0 variance in X)."],
                        ["Persisted DB Inventory", "5 scans, 123 AP rows, 300 signal logs, 11 ping tests, 2 speed tests, 5 experiment runs", "Verified persistent SQLite WAL storage surviving restarts."],
                    ]
                )),

                ("h2", "11.2 Real-World 2.4 GHz Channel Congestion Analysis"),
                ("p", "During the live scan of 31 surrounding access points (Table 11.2), NetVision uncovered severe 2.4 GHz crowding typical of dense urban apartment environments: 20 of the 31 access points clustered on Channels 6 and 11, while 7 access points operated on overlapping intermediate channels (2, 3, 7, 9, 10), degrading adjacent-channel performance."),
                ("table", (
                    "Table 11.2: Live 2.4 GHz Channel Occupancy Distribution Observed on Test Host (31 APs)",
                    ["Channel", "Direct AP Count", "Average Signal (%)", "Co-Channel Score", "Congestion Label"],
                    [
                        ["Channel 1 (Recommended)", "4", "36.8%", "5.47 (Overlap: 7.39)", "Moderate (Best Choice)"],
                        ["Channel 2", "1", "9.0%", "1.09", "Low (Overlaps Ch 1 & 6)"],
                        ["Channel 3", "2", "10.0%", "2.20", "Low (Overlaps Ch 1 & 6)"],
                        ["Channel 6", "9", "26.3%", "11.37", "Heavy"],
                        ["Channel 7", "1", "27.0%", "1.27", "Low (Overlaps Ch 6 & 11)"],
                        ["Channel 9", "1", "7.0%", "1.07", "Low (Overlaps Ch 6 & 11)"],
                        ["Channel 10", "2", "8.0%", "2.16", "Low (Overlaps Ch 11)"],
                        ["Channel 11 (Current AP)", "11", "19.9%", "13.19", "Heavy"],
                    ]
                )),
                ("p", "By computing the weighted spectral overlap model across standard non-overlapping channels {1, 6, 11}, ChannelAnalyzer produced an immediately actionable engineering finding: moving the router from Channel 11 (11 direct APs, co-channel score 13.19) to Channel 1 (4 direct APs, cumulative overlap score 7.39) substantially reduces co-channel contention."),

                ("h2", "11.3 Engineering Discussion and Limitations"),
                ("p", "The live findings validate NetVision's core architectural premise. First, the observed ratio between the 72.2 Mbps 802.11n PHY link rate and 47.35 Mbps WAN download throughput empirically demonstrates why PHY link rate cannot be equated with internet speed: 802.11 MAC headers, interframe spacing, acknowledgements, CSMA/CA backoff contention among 11 APs on Channel 11, and TCP/TLS overhead consume roughly 30–35% of raw signaling capacity. Second, the Academic Experiment's refusal to report a Pearson correlation coefficient when signal remained constant at 88.0% demonstrates that statistical safeguards prevent misleading academic conclusions."),
                ("p", "At the same time, practical limitations remain transparent: NetVision is Windows-specific for wireless scanning, estimates congestion from AP beacons rather than hardware RF spectrum sweeps, uses single-stream HTTP transfers to Cloudflare Edge for speed benchmarking, and distributes unsigned PyInstaller binaries (which may trigger Windows SmartScreen warnings on first launch on another machine)."),
            ],
        },

        # =====================================================================
        # CHAPTER 12
        # =====================================================================
        {
            "num": "12",
            "title": "CONCLUSION AND FUTURE SCOPE",
            "blocks": [
                ("h2", "12.1 Conclusion"),
                ("p", "NetVision — Smart Network Quality & Wi-Fi Coverage Analyzer (v2.0.0) successfully achieves its goal of delivering a trustworthy, modular, and submission-ready Windows desktop application for comprehensive wireless and internet quality evaluation. Through a clean four-tier src/netvision architecture combining PySide6, QThread asynchronous workers, native Windows WLAN APIs (wlanapi.dll and netsh), Cloudflare Global Edge chunked streaming, isolated ICMP/TCP probing, SQLite 3 WAL persistence, and ReportLab/CSV reporting, NetVision eliminates the fragmentation and measurement-integrity pitfalls common in ad-hoc network utilities."),
                ("p", "All 12 application modules are implemented, tested across 46 passing automated pytest unit and integration tests, validated against genuine Windows hardware and live internet links, documented transparently, and packaged into both a portable single-file executable (NetVision_Portable.exe) and a non-elevated Windows Setup Wizard (NetVision_Setup.exe) with safe user-data isolation under %LOCALAPPDATA%\\NetVision."),

                ("h2", "12.2 Future Scope"),
                ("p", "The following capabilities are NOT currently implemented in v2.0.0 and represent clear avenues for future engineering expansion:"),
                ("bullet", [
                    "Interactive Spatial Floor-Plan Heatmaps: Allow users to import building floor plans, record location-tagged signal coordinates, and render interpolated 2D coverage maps.",
                    "Multi-Stream & Multi-Server Bandwidth Benchmarking: Support parallel TCP streams (4–8 concurrent sockets) to saturate gigabit fiber links and allow selectable regional speed-test endpoints.",
                    "Expanded Layer 3/7 Diagnostics: Integrate hop-by-hop traceroute latency profiling, DNS resolution latency comparisons (ISP DNS vs. 8.8.8.8 vs. 1.1.1.1), and loaded latency (bufferbloat) testing during active uploads/downloads.",
                    "Cross-Platform Wireless Backends: Abstract the platform interface behind OS adapters supporting NetworkManager / iw on Linux and CoreWLAN on macOS.",
                    "Code-Signed Enterprise Deployment & Scheduled Monitoring: Add Authenticode digital code signing to eliminate Windows SmartScreen prompts and support optional scheduled background telemetry logging with anomaly alerts."
                ]),
            ],
        },
    ]
