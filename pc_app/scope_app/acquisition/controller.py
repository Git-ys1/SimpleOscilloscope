from __future__ import annotations

import queue
import threading

from ..core.models import AcquisitionStats, ConnectionConfig, RunState, SampleBlock, SampleFrame, SignalConfig
from ..protocol.commands import line, set_signal
from ..protocol.stream_decoder import ProtocolStreamDecoder
from ..transport.factory import open_transport
from .statistics import AcquisitionStatistics


class AcquisitionController:
    def __init__(self) -> None:
        self.events: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self.state = RunState.DISCONNECTED
        self._transport = None
        self._decoder = ProtocolStreamDecoder()
        self._stats = AcquisitionStatistics()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def connect(self, config: ConnectionConfig) -> None:
        self.disconnect()
        self._transport = open_transport(config)
        self._decoder = ProtocolStreamDecoder()
        self._stop.clear()
        self._stats.reset()
        self.state = RunState.CONNECTED
        self._thread = threading.Thread(target=self._reader_loop, name="scope-acquisition", daemon=True)
        self._thread.start()
        self.send("ID?")
        self.send("STATUS")
        self.events.put(("state", self.state))

    def disconnect(self) -> None:
        self._stop.set()
        if self._transport is not None:
            try:
                self._transport.close()
            except Exception:
                pass
            self._transport = None
        self.state = RunState.DISCONNECTED
        self.events.put(("state", self.state))

    def send(self, command: str) -> None:
        if self._transport is None:
            return
        self._transport.write(line(command))

    def apply_signal(self, config: SignalConfig) -> None:
        if self._transport is None:
            return
        for command in set_signal(config):
            self._transport.write(command)

    def poll_events(self) -> list[tuple[str, object]]:
        items: list[tuple[str, object]] = []
        while True:
            try:
                items.append(self.events.get_nowait())
            except queue.Empty:
                return items

    def stats(self) -> AcquisitionStats:
        return self._stats.snapshot()

    def _reader_loop(self) -> None:
        assert self._transport is not None
        while not self._stop.is_set():
            try:
                raw = self._transport.read(512)
            except Exception as exc:
                self.state = RunState.ERROR
                self.events.put(("error", str(exc)))
                return
            if not raw:
                continue
            for event in self._decoder.feed(raw):
                self._handle_event(event)

    def _handle_event(self, event: object) -> None:
        if isinstance(event, SampleFrame):
            self.state = RunState.RUNNING
            stats = self._stats.update_sample(event)
            self.events.put(("sample", event))
            self.events.put(("stats", stats))
        elif isinstance(event, SampleBlock):
            self.state = RunState.RUNNING
            stats = self._stats.update_block(event)
            self.events.put(("block", event))
            self.events.put(("stats", stats))
        else:
            self.events.put(("frame", event))
