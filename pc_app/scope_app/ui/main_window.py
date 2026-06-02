from __future__ import annotations

from dataclasses import replace

from PySide6 import QtCore, QtWidgets

from ..core.app_settings import AppSettingsStore
from ..version import APP_NAME, APP_ORG, APP_VERSION
from . import theme
from .measurement_panel import MeasurementPanel as MeasurementBar
from .panels.acquisition_panel import AcquisitionPanel
from .panels.connection_panel import ConnectionPanel
from .panels.display_panel import DisplayPanel
from .panels.measurement_panel import MeasurementPanel
from .panels.signal_generator_panel import SignalGeneratorPanel
from .panels.trigger_panel import TriggerPanel
from .scope_workspace import ScopeWorkspace
from .status_bar import ScopeStatusBar
from .waveform_view import WaveformView
from .welcome_dialog import SafetyWelcomeDialog


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, default_source: str, default_baud: int) -> None:
        super().__init__()
        self.settings_store = AppSettingsStore()
        settings = self.settings_store.load()
        if default_source:
            settings = replace(settings, source=default_source)
        settings = replace(settings, baud=default_baud)

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1080, 680)
        self.resize(settings.window_width, settings.window_height)

        self.waveform = WaveformView()
        self.measurement_bar = MeasurementBar()
        self.status = ScopeStatusBar()
        self.setStatusBar(self.status)

        self.workspace = ScopeWorkspace(self.waveform, self.measurement_bar, settings, self.settings_store, self)

        self.connection_panel = ConnectionPanel(settings.source, settings.baud)
        self.acquisition_panel = AcquisitionPanel()
        self.display_panel = DisplayPanel()
        self.trigger_panel = TriggerPanel()
        self.measurement_panel = MeasurementPanel()
        self.signal_panel = SignalGeneratorPanel()

        self._build_shell()
        self._connect_signals()
        self._apply_theme()
        self._sync_initial_state(settings.source)
        if settings.show_safety_on_start:
            QtCore.QTimer.singleShot(250, self.show_safety_dialog)

    def connect_to_source(self) -> None:
        self.connection_panel._connect()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        self.workspace.disconnect_source()
        settings = replace(
            self.workspace.settings,
            window_width=max(1, self.width()),
            window_height=max(1, self.height()),
        )
        try:
            self.settings_store.save(settings)
        except OSError:
            pass
        super().closeEvent(event)

    def show_safety_dialog(self) -> None:
        dialog = SafetyWelcomeDialog(self)
        dialog.dismissed.connect(self._set_safety_auto_show)
        dialog.open()

    def _build_shell(self) -> None:
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.waveform, 1)
        layout.addWidget(self.measurement_bar, 0)
        self.setCentralWidget(central)

        self._build_menu()
        self._build_toolbar()
        self._build_dock()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        export_action = file_menu.addAction("Export CSV")
        export_action.triggered.connect(lambda: self.workspace.export_csv_dialog(self))
        file_menu.addSeparator()
        quit_action = file_menu.addAction("Exit")
        quit_action.triggered.connect(self.close)

        help_menu = self.menuBar().addMenu("Help")
        safety_action = help_menu.addAction("接线与安全说明")
        safety_action.triggered.connect(self.show_safety_dialog)
        about_action = help_menu.addAction("About SimpleScope PC")
        about_action.triggered.connect(self.show_about_dialog)

    def show_about_dialog(self) -> None:
        QtWidgets.QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<b>{APP_NAME}</b><br>"
            f"Version: {APP_VERSION}<br>"
            f"Organization: {APP_ORG}<br><br>"
            "A compact STM32 oscilloscope upper-computer application.",
        )

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar("Scope")
        toolbar.setMovable(False)
        actions = [
            ("Connect", self.connection_panel._connect),
            ("Run", lambda: self.workspace.send_command("START")),
            ("Stop", lambda: self.workspace.send_command("STOP")),
            ("Single", self.workspace.rearm_single),
            ("AutoSet", self.workspace.auto_scale),
            ("Demo", lambda: self.workspace.run_demo("fake://sine")),
            ("Export", lambda: self.workspace.export_csv_dialog(self)),
        ]
        for text, slot in actions:
            action = toolbar.addAction(text)
            action.triggered.connect(lambda _checked=False, slot=slot: slot())

    def _build_dock(self) -> None:
        dock_content = QtWidgets.QWidget()
        dock_layout = QtWidgets.QVBoxLayout(dock_content)
        dock_layout.setContentsMargins(10, 10, 10, 10)
        dock_layout.setSpacing(10)
        for title, panel in [
            ("Connection 连接", self.connection_panel),
            ("Acquisition 采集", self.acquisition_panel),
            ("Display 显示", self.display_panel),
            ("Trigger 触发", self.trigger_panel),
            ("Measurements 测量", self.measurement_panel),
            ("Signal Generator 测试信号源", self.signal_panel),
        ]:
            dock_layout.addWidget(self._section(title, panel))
        dock_layout.addStretch(1)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(dock_content)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        dock = QtWidgets.QDockWidget("Scope Controls", self)
        dock.setObjectName("ScopeControlsDock")
        dock.setWidget(scroll)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetFloatable)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

    def _connect_signals(self) -> None:
        self.connection_panel.connect_requested.connect(self.workspace.connect_source)
        self.connection_panel.disconnect_requested.connect(self.workspace.disconnect_source)
        self.connection_panel.format_requested.connect(self.workspace.set_protocol_format)
        self.acquisition_panel.command_requested.connect(self.workspace.send_command)
        self.acquisition_panel.single_requested.connect(self.workspace.rearm_single)
        self.acquisition_panel.clear_requested.connect(self.workspace.clear_buffer)
        self.acquisition_panel.sample_rate_requested.connect(self.workspace.set_sample_rate)
        self.display_panel.display_requested.connect(self.workspace.set_display_config)
        self.display_panel.auto_scale_requested.connect(self.workspace.auto_scale)
        self.display_panel.grid_changed.connect(lambda enabled: self.waveform.showGrid(x=enabled, y=enabled, alpha=0.34))
        self.trigger_panel.trigger_requested.connect(self.workspace.set_trigger_config)
        self.trigger_panel.trigger_rearm_requested.connect(self.workspace.rearm_single)
        self.signal_panel.signal_requested.connect(self.workspace.apply_signal)
        self.signal_panel.output_command_requested.connect(self.workspace.send_command)

        self.workspace.source_changed.connect(self.status.set_source)
        self.workspace.protocol_changed.connect(self.status.set_protocol)
        self.workspace.protocol_changed.connect(self.connection_panel.set_protocol)
        self.workspace.run_state_changed.connect(self.status.set_run_state)
        self.workspace.trigger_state_changed.connect(self.trigger_panel.set_trigger_state)
        self.workspace.stats_changed.connect(self.status.set_stats)
        self.workspace.stats_changed.connect(self.acquisition_panel.set_stats)
        self.workspace.measurements_changed.connect(self.measurement_panel.update_measurements)
        self.workspace.device_identity_changed.connect(self.connection_panel.set_device_identity)
        self.workspace.message_changed.connect(self.status.set_scope_message)
        self.workspace.display_changed.connect(self.display_panel.set_display_values)
        self.workspace.sample_rate_changed.connect(self.acquisition_panel.set_sample_rate)

    def _sync_initial_state(self, source: str) -> None:
        self.status.set_source(source)
        self.status.set_protocol("BINARY")
        self.status.set_run_state("STOP")
        self.connection_panel.set_source(source)
        self.connection_panel.set_protocol("BINARY")
        self.display_panel.set_display_values(self.workspace.display_config)

    def _set_safety_auto_show(self, show: bool) -> None:
        self.workspace.settings = replace(self.workspace.settings, show_safety_on_start=show)
        self.settings_store.save(self.workspace.settings)

    def _section(self, title: str, widget: QtWidgets.QWidget) -> QtWidgets.QGroupBox:
        group = QtWidgets.QGroupBox(title)
        layout = QtWidgets.QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(widget)
        return group

    def _apply_theme(self) -> None:
        self.setStyleSheet(theme.app_stylesheet())
