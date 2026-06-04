from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from ..acquisition.controller import AcquisitionController
from ..core.app_settings import AppSettings, AppSettingsStore
from ..core.models import (
    AcquisitionStats,
    ConnectionConfig,
    DeviceIdentity,
    DeviceCapabilities,
    DeviceStatus,
    DisplayConfig,
    ErrorFrame,
    SignalConfig,
    TextFrame,
    TriggerConfig,
)
from ..core.ring_buffer import WaveformRingBuffer
from ..processing.autoset import autoset_from_waveform
from ..processing.pipeline import process_scope_frame
from ..processing.record_view import build_record_view
from ..storage.export_csv import export_csv
from .measurement_panel import MeasurementPanel
from .waveform_view import WaveformView


class ScopeWorkspace(QtCore.QObject):
    source_changed = QtCore.Signal(str)
    protocol_changed = QtCore.Signal(str)
    run_state_changed = QtCore.Signal(str)
    trigger_state_changed = QtCore.Signal(str)
    stats_changed = QtCore.Signal(AcquisitionStats)
    measurements_changed = QtCore.Signal(object)
    device_identity_changed = QtCore.Signal(object)
    message_changed = QtCore.Signal(str)
    display_changed = QtCore.Signal(DisplayConfig)
    trigger_changed = QtCore.Signal(TriggerConfig)
    sample_rate_changed = QtCore.Signal(int)
    capabilities_changed = QtCore.Signal(DeviceCapabilities)
    quality_changed = QtCore.Signal(str)

    def __init__(
        self,
        waveform: WaveformView,
        measurements: MeasurementPanel,
        settings: AppSettings,
        settings_store: AppSettingsStore,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.waveform = waveform
        self.measurements = measurements
        self.settings = settings
        self.settings_store = settings_store
        self.controller = AcquisitionController()
        self.buffer = WaveformRingBuffer()
        self.display_config = DisplayConfig(
            time_per_div_s=settings.time_per_div_s,
            volt_per_div_mv=settings.volt_per_div_mv,
        )
        self.trigger_config = TriggerConfig(mode=settings.trigger_mode, level_mv=settings.trigger_level_mv)
        self.single_hold: tuple[float, float] | None = None
        self.paused = False
        self.current_source = settings.source
        self.current_protocol = "BINARY"
        self.current_run_state = "STOP"
        self.sample_rate_hz = 10_000
        self.current_signal_frequency_hz = 1000
        self.capabilities = DeviceCapabilities()
        self.last_stats = AcquisitionStats()

        self.waveform.set_display_config(self.display_config)
        self.waveform.set_trigger_config(self.trigger_config)
        self.waveform.set_status("STOP")
        self.waveform.update_waveform(*self.buffer.arrays()[:2])

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.drain_events)
        self.timer.start()

    def connect_source(self, config: ConnectionConfig) -> None:
        try:
            self.buffer.clear()
            self.single_hold = None
            self.current_source = config.source
            self.source_changed.emit(config.source)
            self.controller.connect(config)
            self.current_run_state = "RUN"
            self.run_state_changed.emit("RUN")
            self.waveform.set_status("RUN")
            self.message_changed.emit(f"已连接: {config.source}")
            self.settings = replace(self.settings, source=config.source, baud=config.baud)
            self._save_settings()
        except Exception as exc:  # noqa: BLE001 - user-facing status
            self.current_run_state = "ERROR"
            self.run_state_changed.emit("ERROR")
            self.message_changed.emit(f"连接失败: {exc}")

    def disconnect_source(self) -> None:
        self.controller.disconnect()
        self.current_run_state = "STOP"
        self.run_state_changed.emit("STOP")
        self.waveform.set_status("STOP")
        self.device_identity_changed.emit(None)
        self.message_changed.emit("已断开")

    def send_command(self, command: str) -> None:
        self.controller.send(command)
        if command == "START":
            self.current_run_state = "RUN"
            self.run_state_changed.emit("RUN")
            self.waveform.set_status("RUN")
        elif command == "STOP":
            self.current_run_state = "STOP"
            self.run_state_changed.emit("STOP")
            self.waveform.set_status("STOP")

    def set_protocol_format(self, output_format: str) -> None:
        self.buffer.clear()
        self.single_hold = None
        self.waveform.update_waveform(*self.buffer.arrays()[:2])
        self.controller.send(f"SET FORMAT {output_format}")
        self.current_protocol = output_format
        self.protocol_changed.emit(output_format)
        self.message_changed.emit(f"协议请求: {output_format}")

    def apply_signal(self, wave: str, frequency_hz: int, amplitude_mv: int, offset_mv: int) -> None:
        self.current_signal_frequency_hz = frequency_hz
        self.controller.apply_signal(
            SignalConfig(
                wave=wave,
                frequency_hz=frequency_hz,
                amplitude_mv=amplitude_mv,
                offset_mv=offset_mv,
                sample_rate_hz=self.sample_rate_hz,
            )
        )
        self._update_quality_hint()
        self.message_changed.emit("测试信号源已更新")

    def set_sample_rate(self, sample_rate_hz: int) -> None:
        self.sample_rate_hz = sample_rate_hz
        self.sample_rate_changed.emit(sample_rate_hz)
        self.controller.send(f"SET RATE {sample_rate_hz}")
        self._update_quality_hint()
        self.message_changed.emit(f"采样率请求: {sample_rate_hz} Hz")

    def set_display_config(self, config: DisplayConfig) -> None:
        self.display_config = config
        self.waveform.set_display_config(config)
        self.display_changed.emit(config)
        self.settings = replace(
            self.settings,
            time_per_div_s=config.time_per_div_s,
            volt_per_div_mv=config.volt_per_div_mv,
        )
        self._save_settings()
        self.refresh_display(force=True)

    def set_trigger_config(self, config: TriggerConfig) -> None:
        self.trigger_config = config
        self.single_hold = None
        self.waveform.set_trigger_config(config)
        self.trigger_changed.emit(config)
        self.settings = replace(self.settings, trigger_mode=config.mode, trigger_level_mv=config.level_mv)
        self._save_settings()
        self.message_changed.emit(f"触发: {config.mode} {config.edge} @ {config.level_mv:.1f} mV")
        self.refresh_display(force=True)

    def set_paused(self, paused: bool) -> None:
        was_paused = self.paused
        self.paused = paused
        if paused:
            self.current_run_state = "STOP"
            self.run_state_changed.emit("STOP")
            self.waveform.set_status("STOP")
            self.message_changed.emit("显示已暂停；新采样不会回放")
            return
        if was_paused:
            self.clear_buffer()
            self.current_run_state = "RUN"
            self.run_state_changed.emit("RUN")
            self.waveform.set_status("RUN")
            self.message_changed.emit("显示已恢复，并使用新采样")

    def clear_buffer(self) -> None:
        self.buffer.clear()
        self.single_hold = None
        self.waveform.update_waveform(*self.buffer.arrays()[:2])
        frame = process_scope_frame(*self.buffer.arrays()[:2], self.display_config, self.trigger_config)
        self.measurements.update_measurements(frame.measurements)
        self.measurements_changed.emit(frame.measurements)

    def auto_scale(self) -> None:
        time_ms, value_mv, _sequence = self.buffer.arrays()
        result = autoset_from_waveform(time_ms / 1000.0, value_mv)
        self.set_display_config(result.display)
        self.set_trigger_config(result.trigger)
        self.message_changed.emit("自动设置已应用")

    def rearm_single(self) -> None:
        self.single_hold = None
        self.message_changed.emit("单次触发已重装")

    def run_demo(self, source: str = "fake://sine") -> None:
        self.connect_source(ConnectionConfig(source=source, baud=self.settings.baud))

    def export_csv_dialog(self, parent: QtWidgets.QWidget) -> None:
        time_ms, value_mv, _sequence = self.buffer.arrays()
        if time_ms.size == 0:
            self.message_changed.emit("没有可导出的采样")
            return
        start_path = self.settings.csv_export_path or "waveform.csv"
        path, _filter = QtWidgets.QFileDialog.getSaveFileName(parent, "导出波形 CSV", start_path, "CSV 文件 (*.csv)")
        if not path:
            return
        try:
            export_csv(path, time_ms, value_mv)
            self.settings = replace(self.settings, csv_export_path=str(Path(path).parent))
            self._save_settings()
            self.message_changed.emit(f"已导出 {path}")
        except Exception as exc:  # noqa: BLE001
            self.message_changed.emit(f"导出失败: {exc}")

    def drain_events(self) -> None:
        redraw = False
        for kind, payload in self.controller.poll_events():
            if kind == "sample":
                if self.paused:
                    continue
                self.buffer.append(payload)
                redraw = True
            elif kind == "block":
                if self.paused:
                    continue
                self.buffer.append_block(payload)
                redraw = True
            elif kind == "stats":
                self.last_stats = payload
                self.stats_changed.emit(payload)
                self.waveform.set_sample_context(payload.sample_rate_hz, self.buffer.size)
            elif kind == "error":
                self.current_run_state = "ERROR"
                self.run_state_changed.emit("ERROR")
                self.waveform.set_status("ERROR")
                self.message_changed.emit(str(payload))
            elif kind == "frame":
                self._handle_frame(payload)
            elif kind == "state":
                self.message_changed.emit(str(payload))
        if redraw:
            self.refresh_display()

    def refresh_display(self, force: bool = False) -> None:
        if self.paused and not force:
            return
        time_ms, value_mv, _sequence = self.buffer.arrays()
        frame = process_scope_frame(time_ms, value_mv, self.display_config, self.trigger_config, self.single_hold)
        if frame.trigger_state == "WAIT" and self.trigger_config.mode == "Normal":
            self.trigger_state_changed.emit("WAIT")
            self.run_state_changed.emit("WAIT")
            self.waveform.set_status(self.current_run_state, "WAIT")
            self.measurements.update_measurements(frame.measurements)
            return
        self.single_hold = frame.single_hold
        self.trigger_state_changed.emit(frame.trigger_state)
        self.waveform.set_status(self.current_run_state, frame.trigger_state)
        record = build_record_view(time_ms, value_mv, self.display_config, self.trigger_config, frame.reference_time_ms, frame.trigger_x_s)
        self.waveform.update_record(record)
        self.measurements.update_measurements(frame.measurements)
        self.measurements_changed.emit(frame.measurements)

    def _handle_frame(self, frame: object) -> None:
        if isinstance(frame, DeviceStatus):
            self.sample_rate_hz = frame.sample_rate_hz
            self.current_signal_frequency_hz = frame.frequency_hz
            self.sample_rate_changed.emit(frame.sample_rate_hz)
            self._update_quality_hint()
            state = "RUN" if frame.run_state.upper() == "RUN" else "STOP"
            self.current_run_state = state
            self.run_state_changed.emit(state)
            self.waveform.set_status(state)
        elif isinstance(frame, DeviceIdentity):
            self.device_identity_changed.emit(frame)
        elif isinstance(frame, DeviceCapabilities):
            self.capabilities = frame
            self.capabilities_changed.emit(frame)
            self.sample_rate_hz = min(max(self.sample_rate_hz, frame.rate_min), frame.rate_max)
            self.sample_rate_changed.emit(self.sample_rate_hz)
            self._update_quality_hint()
            self.message_changed.emit(
                f"能力: {frame.rate_max} Sa/s, {frame.freq_max} Hz, {frame.baud} baud, {frame.block_points} 点/块"
            )
        elif isinstance(frame, TextFrame):
            if frame.payload.startswith("FORMAT,"):
                protocol = frame.payload.split(",", 1)[1].strip().upper()
                self.current_protocol = protocol
                self.protocol_changed.emit(protocol)
            else:
                self.message_changed.emit(frame.payload)
        elif isinstance(frame, ErrorFrame):
            self.message_changed.emit(f"协议错误: {frame.reason}")
        else:
            self.message_changed.emit(str(frame))

    def _save_settings(self) -> None:
        try:
            self.settings_store.save(self.settings)
        except OSError as exc:
            self.message_changed.emit(f"设置保存失败: {exc}")

    def _update_quality_hint(self) -> None:
        if self.current_signal_frequency_hz <= 0 or self.sample_rate_hz <= 0:
            self.quality_changed.emit("")
            return
        recommended = self.current_signal_frequency_hz * 10
        if self.sample_rate_hz < recommended:
            self.quality_changed.emit(
                f"采样率偏低：当前信号 {self.current_signal_frequency_hz:g} Hz，采样率 {self.sample_rate_hz:g} Sa/s，至少建议 {recommended:g} Sa/s"
            )
        else:
            self.quality_changed.emit("")
