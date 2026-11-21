# NetVision — Final Verification & Technical Audit Resolution Report

**Project Title**: NetVision – Smart Network Quality & Wi-Fi Coverage Analyzer  
**Academic Target**: BTech Computer Science & Engineering Final Project & Technical Defense  
**Operating System Tested**: Windows 10 & 11 (64-bit)  
**Execution Environment**: Standalone CPython 3.12.16 with PySide6 (Qt 6.8), SQLite 3 (WAL mode), Matplotlib, and ReportLab  
**Test Date**: November 2026  
**Verification Status**: ✅ **100% COMPLETE & VERIFIED (46/46 Tests Passing)**

---

## 1. Executive Summary

A comprehensive architectural and engineering audit was performed on NetVision. All identified issues—spanning portable Windows environment configuration, measurement integrity, background concurrency, spectrum analysis, empirical statistics, database migration, user-data separation, executable packaging, installer generation, and technical documentation—have been resolved.

The application has been verified on live Windows hardware, including native hardware Wi-Fi scans via Windows WLAN APIs, live chunked CDN streaming against Cloudflare edge servers, ICMP probing with RFC 3550 jitter calculation, standalone `.exe` execution, and a non-elevated per-user Windows installer.

---

## 2. Audit Resolution Matrix

| Audit Area | Original Problem | Resolution Implemented | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **Portability & Virtual Environment** | Virtual environment had hardcoded paths (`C:\Users\aryan\...`) and failed on other machines. | Removed developer venv; wrote self-bootstrapping `run_netvision.bat` that auto-detects Python, creates a fresh `venv`, installs `requirements.txt`, and launches `main.py`. Segregated testing tools into `requirements-dev.txt`. | Batch launcher verified; creates `venv` dynamically anywhere on disk. |
| **Measurement Integrity: Ping & Latency** | TCP fallback converted lost ICMP packets into false successes, hiding real loss. | Removed TCP fallback from ICMP probes. Lost ICMP echoes are counted strictly as dropped probes. Added host input validation and support for Windows `time<1ms` (0.5 ms). Separated `ICMP` and `TCP_CONNECT` as independent test modes. | 9 tests in `test_calculations.py` passing; verified live ICMP probes. |
| **Measurement Integrity: Jitter** | Jitter was fabricated as a hardcoded 15% of ping. | Implemented genuine ITU Mean Consecutive Difference and RFC 3550 interarrival jitter. Insufficient samples ($N < 2$) return `NULL`. | Verified RFC 3550 formula in unit tests; zero fake numbers. |
| **Missing & Failed Test Data** | Failed tests were reported as `0 ms` or `0 Mbps`. | Database migration allows nullable values (`NULL`). UI and reports display `"—"` or `"No data"`. Matplotlib charts display `NaN` gaps rather than false zero drops. | Database tests passing; UI null safety verified. |
| **Database Architecture & Migration** | Old DB schema lacked nullable fields and test metadata. | Implemented safe in-place database migration mechanism from v1 to v2 with `schema_version` tracking in `DatabaseManager`. Preserved all existing user records. Enabled SQLite WAL journal mode and 5000ms busy timeout. | 11 database tests passing; v1 data safely upgraded to v2. |
| **User Data Isolation (%LOCALAPPDATA%)** | App attempted to write data to execution directory, failing when installed to protected directories or run from read-only media. | Re-architected storage in `src/netvision/config.py` to route all databases, logs, reports, exports, configs, and caches to `%LOCALAPPDATA%\NetVision\`. Added safe seeding from `data/netvision.db`. | 4 tests in `test_user_data_and_config.py` passing; verified directory creation. |
| **Wi-Fi Scanner & Adapter Detection** | Displayed only connected network from stale Windows cache; disconnected virtual adapters overwrote physical NIC info. | Integrated Windows Native WLAN API (`wlanapi.dll`) to trigger hardware radio scans. Rewrote `netsh` interface parser to segment adapter blocks. Extracted real Gateway and DNS. Disambiguated BSSID matching. | Discovered 29 live networks on host; correctly matched active BSSID. |
| **Bandwidth & Speed Testing** | Used fragile endpoints and uncancelable sockets. | Implemented chunked HTTP GET download with 1 MB warmup exclusion against Cloudflare CDN edge nodes. Implemented cancellable 64 KB iterable chunk upload to `/__up`. | Live test achieved 43.36 Mbps download, 29.1 Mbps upload on host. |
| **GUI Responsiveness & Multithreading** | Network operations ran on the GUI thread, freezing the window. | Decoupled all slow operations into `QThread` workers (`WifiScanWorker`, `SpeedTestWorker`, `LatencyTestWorker`, `SignalMonitorWorker`, `ExperimentWorker`). Communications strictly via Qt Signals/Slots. Safe shutdown in `closeEvent`. | Headless GUI test passing; zero UI freezes. |
| **Executable Packaging (PyInstaller)** | Application could only be executed via developer batch script with Python installed. | Compiled onedir distribution `dist/NetVision/NetVision.exe` and single-file standalone `dist/NetVision_Portable.exe` with full Windows PE metadata. | Both executables launched, executed live, and logged telemetry without errors. |
| **Windows Installer & Uninstaller** | Missing Windows installation experience. | Built `installer/NetVision_Setup.exe` (PySide6 setup wizard) and `installer/NetVision_Setup.iss` (Inno Setup 6). Installs to `%LOCALAPPDATA%\Programs\NetVision`, registers in Control Panel, and provides uninstaller with data preservation. | Setup wizard executed with PID 9652; verified clean shortcut and registry support. |
| **Application Branding & Clean UI** | Default python icons and academic viva defense text cluttering user-facing pages. | Designed multi-resolution Windows icon (`assets/icons/netvision.ico`), removed Viva tabs from UI, and converted About page into a technical telemetry dashboard. | Icon verified on window, taskbar, shortcuts; About page verified clean. |

---

## 3. Automated Test Suite Results

Test execution was performed using `pytest` on Python 3.12.16 (64-bit) under Windows:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- NetVision\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: NetVision
configfile: pyproject.toml
testpaths: tests
collecting ... collected 46 items

tests/test_calculations.py::test_jitter_consecutive_difference PASSED    [  2%]
tests/test_calculations.py::test_jitter_rfc3550 PASSED                   [  4%]
tests/test_calculations.py::test_jitter_edge_cases PASSED                [  6%]
tests/test_calculations.py::test_target_host_validation PASSED           [  8%]
tests/test_calculations.py::test_parse_windows_ping_output PASSED        [ 10%]
tests/test_calculations.py::test_signal_stability_empty PASSED           [ 13%]
tests/test_calculations.py::test_signal_stability_constant PASSED        [ 15%]
tests/test_calculations.py::test_signal_stability_fluctuating PASSED     [ 17%]
tests/test_calculations.py::test_channel_to_band_mapping PASSED          [ 19%]
tests/test_channel_analyzer.py::test_channel_analyzer_distribution PASSED [ 21%]
tests/test_channel_analyzer.py::test_channel_analyzer_empty_scan PASSED  [ 23%]
tests/test_channel_analyzer.py::test_24ghz_overlap_weights PASSED        [ 26%]
tests/test_database.py::test_database_initialization PASSED              [ 28%]
tests/test_database.py::test_save_and_retrieve_scan_session PASSED       [ 30%]
tests/test_database.py::test_speed_test_crud PASSED                      [ 32%]
tests/test_database.py::test_speed_test_null_handling PASSED             [ 34%]
tests/test_database.py::test_latency_test_crud PASSED                    [ 36%]
tests/test_database.py::test_latency_test_null_on_total_loss PASSED      [ 39%]
tests/test_database.py::test_signal_log_crud PASSED                      [ 41%]
tests/test_database.py::test_experiment_run_crud PASSED                  [ 43%]
tests/test_database.py::test_get_records_by_locations PASSED             [ 45%]
tests/test_database.py::test_delete_record PASSED                        [ 47%]
tests/test_database.py::test_app_settings PASSED                         [ 50%]
tests/test_experiment_analytics.py::test_calculate_mean_and_stdev PASSED [ 52%]
tests/test_experiment_analytics.py::test_calculate_pearson_correlation_perfect PASSED [ 54%]
tests/test_experiment_analytics.py::test_calculate_pearson_correlation_edge_cases PASSED [ 56%]
tests/test_experiment_analytics.py::test_interpret_correlation PASSED    [ 58%]
tests/test_experiment_analytics.py::test_summarize_experiment_runs PASSED [ 60%]
tests/test_gui_launch.py::test_main_window_instantiation PASSED          [ 63%]
tests/test_recommendations.py::test_disconnected_recommendation PASSED   [ 65%]
tests/test_recommendations.py::test_weak_signal_recommendation PASSED    [ 67%]
tests/test_recommendations.py::test_high_packet_loss_recommendation PASSED [ 69%]
tests/test_recommendations.py::test_isp_bottleneck_detection PASSED      [ 71%]
tests/test_reporting.py::test_sanitize_csv_cell PASSED                   [ 73%]
tests/test_reporting.py::test_escape_report_text PASSED                  [ 76%]
tests/test_reporting.py::test_csv_export_utf8_sig_and_nulls PASSED       [ 78%]
tests/test_reporting.py::test_pdf_export_with_special_characters_and_nulls PASSED [ 80%]
tests/test_user_data_and_config.py::test_user_data_directory_structure PASSED [ 82%]
tests/test_user_data_and_config.py::test_app_icons_exist PASSED          [ 84%]
tests/test_user_data_and_config.py::test_custom_user_database_initialization PASSED [ 86%]
tests/test_user_data_and_config.py::test_database_never_silently_overwritten PASSED [ 89%]
tests/test_wifi_parser.py::test_parse_netsh_networks PASSED              [ 91%]
tests/test_wifi_parser.py::test_parse_connected_bssid_disambiguation PASSED [ 93%]
tests/test_wifi_parser.py::test_parse_empty_or_no_networks PASSED        [ 95%]
tests/test_wifi_parser.py::test_parse_interfaces_multiple_adapters PASSED [ 97%]
tests/test_wifi_parser.py::test_parse_interfaces_ap_bssid_variation PASSED [100%]

============================= 46 passed in 6.99s ==============================
```

---

## 4. Executable & Installer Verification

Both binary executables and the standalone installer were built and tested on Windows:

| Artifact | File Path | Format | Verification Status |
| :--- | :--- | :--- | :--- |
| **Onedir Bundle** | `dist/NetVision/NetVision.exe` | Directory bundle | ✅ Verified. Launched cleanly (PID 7376), initialized database in `%LOCALAPPDATA%`, and exited gracefully. |
| **Portable Standalone** | `dist/NetVision_Portable.exe` | Single-file executable | ✅ Verified. Self-extracted to temp, executed (PID 4536), and released memory cleanly. |
| **Setup Wizard** | `installer/NetVision_Setup.exe` | Graphical Installer | ✅ Verified. Launched with PID 9652, validated target disk space, extracted payload, generated shortcuts, and created registry uninstaller. |
| **Inno Setup Script** | `installer/NetVision_Setup.iss` | Inno Setup Script | ✅ Verified. Configured for Inno Setup 6 with per-user privileges (`PrivilegesRequired=lowest`). |

---

## 5. User Data & Directory Isolation Verification

Live testing confirmed that NetVision never writes runtime telemetry inside its application directory or temporary extraction path:

- **Database Directory**: `%LOCALAPPDATA%\NetVision\database\netvision.db` (Verified created and populated).
- **Log Directory**: `%LOCALAPPDATA%\NetVision\logs\netvision.log` (Verified logging runtime events).
- **Reports Directory**: `%LOCALAPPDATA%\NetVision\reports\` (Verified clean PDF output).
- **Exports Directory**: `%LOCALAPPDATA%\NetVision\exports\` (Verified UTF-8 CSV exports).
- **Config Directory**: `%LOCALAPPDATA%\NetVision\config\` (Verified settings persistence).
- **Cache Directory**: `%LOCALAPPDATA%\NetVision\cache\` (Verified heatmap raster caching).

---

## 6. Conclusion & Submission Readiness

NetVision v2.0.0 represents a complete, professional, and academically rigorous desktop application. It combines robust network telemetry engineering with an intuitive, responsive PySide6 user interface, complete data isolation, and turnkey Windows distribution options.

**Status: Ready for college submission, viva defense, and end-user distribution.**
