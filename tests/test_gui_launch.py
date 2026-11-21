"""
Integration Test for PySide6 GUI Launch and Page Transitions
Runs headlessly via offscreen QPA platform to verify zero GUI widget initialization errors.
"""

import os
import pytest
from PySide6.QtWidgets import QApplication
from netvision.ui.main_window import MainWindow
from netvision.database.db_manager import DatabaseManager
from netvision.database.models import WifiNetwork


@pytest.fixture(scope="session")
def qapp():
    """Initializes offscreen QApplication."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_instantiation(qapp, tmp_path):
    """Instantiates MainWindow, tests page switching across all 12 navigation sections."""
    db_file = tmp_path / "gui_test.db"
    db_manager = DatabaseManager(db_path=db_file)

    # Seed sample network so channel analysis doesn't invoke subprocess in unit test
    sample_nets = [
        WifiNetwork(ssid="MockAP", channel=6, signal_percent=80, frequency_band="2.4 GHz")
    ]
    db_manager.save_scan_session(sample_nets, active_interface="Wi-Fi", location_label="Lab")

    window = MainWindow(db_manager=db_manager)

    # Verify all 12 pages in stack
    assert window.stack.count() == 12

    # Switch through each page
    for i in range(12):
        window.switch_page(i)
        assert window.stack.currentIndex() == i

    window.close()
