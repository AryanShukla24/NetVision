# NetVision — College Viva Preparation & Theory Guide

> **Prepared for BTech Computer Science & Engineering Students**  
> *Subject: Computer Networks, Operating Systems, Software Engineering & Desktop Application Architecture*

---

## 🎯 1. Fundamental Networking Concepts

### Q1. What is the difference between Wi-Fi Signal Strength and Internet Connection Speed?
**Answer:**  
They operate at different layers of the OSI model:
- **Wi-Fi Signal Strength** is a **Physical (Layer 1) and Data Link (Layer 2)** measurement. It represents the radio frequency (RF) energy and link quality between your laptop's wireless network interface card (NIC) and the local wireless router (Access Point).
- **Internet Speed (Throughput)** is a **Transport (Layer 4) and Application (Layer 7)** measurement. It measures the rate at which actual application data can travel across the entire path from your device, through the ISP gateway, across the internet backbone, to an external test server.
- **Key Viva Point**: You can have 100% Wi-Fi signal strength while having **0 Mbps** internet speed if the router's WAN/fiber cable is disconnected. NetVision explicitly measures and displays these two parameters independently.

---

### Q2. What is the difference between SSID and BSSID?
**Answer:**
- **SSID (Service Set Identifier)**: The human-readable name of a Wi-Fi network (e.g., `Campus_Student_WiFi`). Multiple physical access points can broadcast the same SSID to provide seamless roaming across a large building.
- **BSSID (Basic Service Set Identifier)**: The unique 48-bit hardware MAC address of the specific radio transmitter interface in the router (e.g., `00:1A:2B:3C:4D:5E`).
- In NetVision, the **Wi-Fi Scanner** detects and displays individual BSSIDs, allowing users to see if multiple routers are broadcasting the same campus SSID and identify which specific physical unit is closest.

---

### Q3. How does NetVision measure Wi-Fi Signal Quality, and how does it relate to RSSI?
**Answer:**
- Windows OS provides Wi-Fi signal quality as an integer percentage from `0%` to `100%`.
- In radio engineering, signal strength is measured as **RSSI (Received Signal Strength Indicator)** in decibels relative to one milliwatt (**dBm**), which is typically a negative number ranging from `-30 dBm` (exceptionally strong) to `-90 dBm` (barely detectable).
- A standard practical conversion formula used on Windows is:
  $$\text{RSSI (dBm)} \approx \left(\frac{\text{Signal \%}}{2}\right) - 100$$
  - `100%` $\approx -50\text{ dBm}$ (Excellent)
  - `75%` $\approx -62.5\text{ dBm}$ (Good)
  - `50%` $\approx -75\text{ dBm}$ (Fair)
  - `25%` $\approx -87.5\text{ dBm}$ (Poor)
- NetVision avoids claiming that the Windows percentage is an exact hardware RSSI reading and clearly labels it as a signal quality percentage.

---

### Q4. Explain the difference between 2.4 GHz, 5 GHz, and 6 GHz Wi-Fi bands.
**Answer:**
| Parameter | 2.4 GHz Band | 5 GHz Band | 6 GHz Band (Wi-Fi 6E/7) |
| :--- | :--- | :--- | :--- |
| **Wavelength** | Longer ($\approx 12.5\text{ cm}$) | Shorter ($\approx 6\text{ cm}$) | Very short ($\approx 5\text{ cm}$) |
| **Physical Range** | Longer range | Moderate range | Short range |
| **Obstacle Penetration** | Excellent through walls/concrete | Lower penetration; reflected by walls | Minimal penetration; best line-of-sight |
| **Channel Width** | 20 MHz (rarely 40 MHz) | 20, 40, 80, 160 MHz | Up to 160 / 320 MHz |
| **Interference** | High (microwaves, Bluetooth) | Low (cleaner spectrum) | Minimal (cleanest spectrum) |
| **Max Throughput** | Low (up to $\approx 300\text{ Mbps}$) | High (up to $\approx 1.3\text{ Gbps}+$) | Ultra-high ($2.4\text{ Gbps}+$) |

---

### Q5. Why are Channels 1, 6, and 11 the only recommended standard channels in 2.4 GHz?
**Answer:**
- In the 2.4 GHz band, standard channels are spaced **5 MHz** apart (e.g., Channel 1 is at 2412 MHz, Channel 2 is at 2417 MHz).
- However, each 802.11 transmission requires a channel width of **20 MHz** (or 22 MHz in 802.11b).
- Because 20 MHz is wider than the 5 MHz spacing, adjacent channels overlap heavily. For example, Channel 2 spills energy across Channels 1, 2, 3, and 4, causing adjacent-channel interference.
- **Channels 1 (2412 MHz), 6 (2437 MHz), and 11 (2462 MHz)** are spaced 25 MHz apart. Therefore, their 20 MHz channel signals do not overlap with each other. NetVision's Channel Analyzer uses this principle to recommend the optimal 2.4 GHz channel.

---

## ⚡ 2. Latency, Jitter, and Throughput Metrics

### Q6. What is Latency (Ping) and Round-Trip Time (RTT)?
**Answer:**
- **Latency** is the time taken for a packet of data to travel from the source host to the destination host.
- **Round-Trip Time (RTT)** is the total elapsed time from when the source transmits a probe packet (such as an ICMP Echo Request) until it receives the corresponding acknowledgement or response (ICMP Echo Reply).
- RTT is measured in milliseconds (ms). Factors affecting RTT include propagation delay, transmission delay, router processing delay, and queuing delay.

---

### Q7. What is Jitter, and what exact formulas does NetVision use to compute it?
**Answer:**
- **Jitter** is the statistical variance or fluctuation in packet arrival latency (also called Packet Delay Variation - PDV).
- If packets take 20ms, 21ms, 20ms, jitter is low (1ms). If packets take 10ms, 120ms, 15ms, 180ms, jitter is extremely high, causing audio dropouts in VoIP and stutter in online gaming.
- NetVision implements two standard calculations:
  1. **Mean Consecutive Difference** (ITU standard practical metric):
     $$\text{Jitter} = \frac{1}{N-1} \sum_{i=2}^{N} |\text{RTT}_i - \text{RTT}_{i-1}|$$
  2. **RFC 3550 (RTP/Audio Smoothing Filter)**:
     $$J = J + \frac{|D(i-1, i)| - J}{16}$$
     where $D(i-1, i) = \text{RTT}_i - \text{RTT}_{i-1}$.
- If fewer than 2 successful probe samples exist (e.g. 100% packet loss), jitter cannot be determined and is stored as `NULL` internally and displayed as `"—"`, never as fabricated values or zeros.

---

### Q8. Why must TCP connection timing never be mixed with ICMP RTT in the same test?
**Answer:**
- **Layer 3 vs Layer 4 Difference**: ICMP operates directly on top of the IP layer (Layer 3) without transport overhead. A TCP connection probe operates at Layer 4 and requires a full 3-way handshake (`SYN` $\rightarrow$ `SYN-ACK` $\rightarrow$ `ACK`), kernel socket allocation, TCP window scaling, and port filtering.
- **Masking Real Packet Loss**: In legacy/naive implementations, if an ICMP ping packet was dropped, fallback code would immediately attempt a TCP connect. If the TCP connect succeeded, the dropped ICMP packet was falsely reported as a success, completely hiding packet loss from the user.
- **NetVision Solution**: NetVision strictly isolates measurement methods. A lost ICMP echo is recorded honestly as a lost probe. Users can explicitly select either `ICMP Ping` or `TCP Connect (443)` as separate, independent diagnostic methods.

---

### Q9. What causes Packet Loss?
**Answer:**
Packet loss occurs when transmitted data packets fail to reach their destination. In NetVision, it is computed as:
$$\text{Packet Loss \%} = \left(\frac{\text{Unanswered Probes}}{\text{Total Probes Sent}}\right) \times 100$$
Common causes:
1. **Network Congestion & Bufferbloat**: Router queues overflow, dropping incoming packets.
2. **RF Interference & Attenuation**: Wi-Fi frame errors caused by physical distance, walls, or competing radio transmitters.
3. **Hardware / Cable Faults**: Damaged Ethernet patches or faulty ISP lines.
4. **Firewall / ICMP Filtering**: Security gateways blocking ICMP Echo Requests (Type 8) while allowing TCP traffic. NetVision allows testing TCP port 443 to diagnose whether loss is genuine network drop or administrative ICMP filtering.

---

### Q10. How does NetVision measure Download and Upload Speed?
**Answer:**
- NetVision uses a chunked HTTP streaming architecture against high-availability CDN edge nodes (such as Cloudflare's global edge speed endpoints).
- **Download Test**: The client streams binary chunks via HTTP GET over an active TCP socket connection. A 1 MB initial warmup chunk is excluded to prevent TCP Slow Start from skewing the final measurement. High-resolution timers (`time.perf_counter()`) track bytes received over elapsed time:
  $$\text{Throughput (Mbps)} = \frac{\text{Bytes Received} \times 8}{\text{Elapsed Seconds} \times 1,000,000}$$
- **Upload Test**: The client streams an iterable 64 KB chunked HTTP POST binary payload to the edge server endpoint (`/__up`) and computes the outbound transfer rate in real-time.
- **Cancellation & Safety**: The upload loop continuously evaluates thread cancellation flags, allowing immediate, clean user aborts without hanging the socket.
- **Progress Reporting**: Real-time callbacks update the PySide6 UI progress bar and current instantaneous transfer speed.

---

### Q11. How does NetVision compute Pearson Correlation in the Academic Experiment Module?
**Answer:**
- The **Pearson Correlation Coefficient ($r$)** measures the linear relationship between physical Wi-Fi signal quality percentage ($X$) and transport download throughput in Mbps ($Y$):
  $$r = \frac{\sum_{i=1}^{n} (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n} (x_i - \bar{x})^2 \sum_{i=1}^{n} (y_i - \bar{y})^2}}$$
- **Value Interpretation**:
  - $r > 0.8$: Very Strong Positive Correlation (throughput increases directly with signal).
  - $0.4 \le r \le 0.8$: Moderate to Strong Correlation.
  - $r \approx 0$: No Linear Correlation (e.g. throughput is capped by an ISP WAN bottleneck rather than Wi-Fi signal).
- **Mathematical Integrity Safeguards**: NetVision handles zero variance (e.g. tests conducted with unchanged signal) and sample counts $N < 3$ by reporting `"N/A (insufficient variance or samples < 3)"`, preventing division-by-zero errors.

---

### Q12. How does NetVision handle missing, failed, or cancelled measurements?
**Answer:**
- **No False Zeros**: A failed ping test or unavailable speed measurement must NEVER be represented as `0.0 ms` or `0.0 Mbps`. Zero milliseconds implies instant communication at infinite speed, which is physically impossible.
- **Relational Representation**: In the SQLite database schema, failed or unmeasured metrics are stored strictly as `NULL`.
- **User Interface & Reports**:
  - Displayed as `"—"` or `"No data"` in metric cards, tables, and PDF/CSV reports.
  - In Matplotlib charts, missing values are represented as `NaN`, creating clean visual gaps in time-series plots rather than plummeting to the origin.
  - Test records maintain an explicit `status` column: `'completed'`, `'failed'`, or `'cancelled'`.

---

## 🏗️ 3. Software Architecture & Implementation

### Q10. What design pattern does NetVision use, and how does it prevent the GUI from freezing?
**Answer:**
- NetVision follows the **Model-View-Controller (MVC) with Worker Threads** architecture.
- In desktop GUI programming (Qt/PySide6), the **Main Thread (UI Thread)** manages event handling, painting widgets, and user clicks.
- If a blocking network operation (such as `time.sleep()`, a 10-second download, or an ICMP ping probe) runs directly on the UI thread, the event loop blocks, Windows marks the window as "Not Responding", and the GUI freezes.
- **Solution in NetVision**:
  - All network I/O operations are encapsulated in `QThread` subclasses: `WifiScanWorker`, `SpeedTestWorker`, `LatencyTestWorker`, `SignalMonitorWorker`, and `ExperimentWorker`.
  - Workers communicate results back to the UI thread strictly using **Qt Signals and Slots**, which are thread-safe and asynchronous.

---

### Q11. Explain the SQLite database schema and ACID properties in NetVision.
**Answer:**
- NetVision uses SQLite 3 with WAL (Write-Ahead Logging) and enforced foreign key constraints (`PRAGMA foreign_keys = ON;`).
- **Relational Tables**:
  - `scan_sessions` & `wifi_networks`: 1-to-Many relationship with `ON DELETE CASCADE`. Stores surrounding wireless environment snapshots.
  - `speed_tests`: Stores download/upload Mbps, ping, jitter, location tag, and server.
  - `latency_tests`: Stores host, probe count, min/max/avg RTT, jitter, and packet loss.
  - `signal_logs`: Stores continuous signal telemetry with timestamps.
  - `locations`: Stores custom environment tags (*Library*, *Classroom*, *Cafe*, etc.).
  - `experiment_runs`: Stores multi-trial experimental runs for academic evaluation.
  - `app_settings`: Key-value configuration storage.
- **Indices**: B-tree indices created on timestamps and session IDs for sub-millisecond query performance during analytics rendering.

---

### Q12. Explain the Academic Experiment Workflow (Feature 18) and its scientific purpose.
**Answer:**
- In academic evaluation, single snapshot measurements are not scientifically valid because network performance fluctuates due to random fading, background traffic, and scheduling.
- NetVision features an **Academic Experiment Workflow** that executes repeated trials (5+ runs per condition) under identical user-labeled conditions (e.g. *Near Router* vs *Across Room*).
- It calculates statistical metrics:
  - **Mean ($\mu$)**: The expected performance.
  - **Standard Deviation ($\sigma$)**: The statistical spread or variability.
- It plots trial-by-trial throughput and correlation curves between Wi-Fi signal percentage and measured download bandwidth, demonstrating empirical networking research.

---

### Q13. How are PDF and CSV reports generated?
**Answer:**
- **PDF Generation**: Compiled using the Python `reportlab` library with a customized `SimpleDocTemplate`, flowable tables, and formatted typography. It includes network metadata, throughput history, latency tables, and diagnostic recommendations.
- **CSV Export**: Uses Python's standard `csv` module to output clean, comma-separated audit logs suitable for analysis in Microsoft Excel, R, or pandas.

---

### Q14. What are the key viva questions an examiner might ask about Python and PySide6?
**Answer:**
1. **Why PySide6 instead of Tkinter?**  
   *Answer*: PySide6 provides native Qt6 rendering, hardware acceleration, modern styling (QSS stylesheets), professional layout managers (`QGridLayout`, `QStackedWidget`), and thread-safe signal/slot primitives. Tkinter looks dated and lacks native support for complex background thread communication.
2. **What is a Signal and Slot in Qt?**  
   *Answer*: It is an implementation of the Observer pattern. A Signal is emitted when an event occurs (e.g., worker finished a test). A Slot is a function connected to that signal that executes in response.
3. **How does Python manage memory in this application?**  
   *Answer*: Python uses reference counting combined with a generational garbage collector. In NetVision, database connections are managed via context managers (`with conn:`) to prevent dangling locks.
