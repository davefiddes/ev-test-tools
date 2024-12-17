#!/usr/bin/env python
#
import asyncio
import can
import math
import sys
import datetime
import time
import signal
from can.notifier import MessageRecipient
from typing import List

from PySide6.QtCore import Qt, QObject, Signal, Slot, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)
from PySide6 import QtAsyncio

import sbox_can_messages
import other

can_log_name = f"{datetime.datetime.now().isoformat()}-sbox-sim.log"
can_log = open(can_log_name, "w")
print(f"Writing CAN messages to {can_log_name}")


class Car:
    def __init__(self):
        # fields updated by user
        self.voltage = 350
        self.current = 0

        # fields updated from CAN
        self.msgs_per_sec = 0
        self.pos_contactor_closed = False
        self.neg_contactor_closed = False
        self.pch_contactor_closed = False

        # internal stuff
        self.bus = None

        self._new_msgs = 0
        self._last_sec = 0
        self._last_inverter_v = 0

        # Set up all the messages we'll be sending
        self.tx_messages = {}
        for mod in (sbox_can_messages, other):
            for m in mod.get_messages(self):
                assert (
                    m.arbitration_id not in self.tx_messages
                )  # check for accidental dupes
                self.tx_messages[m.arbitration_id] = m

    @property
    def output_voltage(self) -> float:
        """Synthesize the output voltage based on the state of the
        contactors"""
        if ((self.pos_contactor_closed or self.pch_contactor_closed)
                and self.neg_contactor_closed):
            return self.voltage
        else:
            return 0

    def on_message(self, msg: can.Message):
        """Handle updates, will be called from a non-asyncio non-Qt thread!!"""
        print(msg, file=can_log)
        if msg.arbitration_id in self.tx_messages:
            print(
                f"WARNING: {msg.arbitration_id:#x} appears in both TX and RX")

        # update the msgs per second counter
        self._new_msgs += 1
        sec = int(time.time())
        if sec != self._last_sec:
            self.msgs_per_sec = self._new_msgs
            self._new_msgs = 0
            self._last_sec = sec

        if msg.arbitration_id == 0x100:
            # ControlContactors
            pass

        elif msg.arbitration_id == 0x300:
            # Setup
            pass

    async def rx_coro(self, bus: can.BusABC):
        """Receive from the CAN bus and log whatever it sends us, plus invoke handler."""
        reader = can.AsyncBufferedReader()

        listeners: List[MessageRecipient] = [
            reader,  # AsyncBufferedReader() listener
        ]

        # Note: the async version of this class doesn't use asyncio event loop
        # unless the bus has a filno() property to use for the listener. It falls
        # back to a thread, meaning the callbacks are called in the thread context
        # still. This is incompoatible with the Python QAsyncioEventLoopPolicy that
        # requires any thread using asyncio to be main thread or a QThread
        self._notifier = can.Notifier(bus, listeners)
        self._notifier.add_listener(self.on_message)

    async def start(self):
        """Set up the asyncio sbox-sim "model" """
        if "--virtual" in sys.argv:
            self.bus = can.interface.Bus("virtual", interface="virtual")
        else:
            self.bus = can.Bus()

        # gather creates a task for each coroutine
        await asyncio.gather(
            self.rx_coro(self.bus),
            *(m.coro(self.bus, can_log) for m in self.tx_messages.values()),
        )


class MainWindow(QMainWindow):
    def __init__(self, car):
        super().__init__()
        self.car = car

        widget = QWidget()
        self.setCentralWidget(widget)

        layout = QVBoxLayout(widget)

        status_layout = QHBoxLayout()
        self.pos_contactor = QLabel("--")
        self.neg_contactor = QLabel("--")
        self.pch_contactor = QLabel("--")
        for w in (QLabel("Positive contactor:"),
                  self.pos_contactor,
                  QLabel("Negative contactor:"),
                  self.neg_contactor,
                  QLabel("Pre-charge contactor:"),
                  self.pch_contactor):
            status_layout.addWidget(w)
        layout.addLayout(status_layout)

        self.msgs_per_sec = QLabel("-")
        layout.addWidget(self.msgs_per_sec)

        layout.addWidget(QLabel("Voltage:"))
        self.edit_voltage = QDoubleSpinBox()
        self.edit_voltage.setRange(0, 500)
        self.edit_voltage.setValue(self.car.voltage)
        self.edit_voltage.valueChanged.connect(self.on_voltage_changed)
        layout.addWidget(self.edit_voltage)

        layout.addWidget(QLabel("Current:"))
        self.edit_current = QDoubleSpinBox()
        self.edit_current.setRange(-200.0, 200.0)
        self.edit_current.setValue(self.car.current)
        self.edit_current.valueChanged.connect(self.on_current_changed)
        layout.addWidget(self.edit_current)

        txGroup = QGroupBox("Enabled TX Messages")
        txLayout = QGridLayout()
        COLS = 3
        num_msgs = len(car.tx_messages)
        msgs_per_col = math.ceil(num_msgs / COLS)
        txGroup.setLayout(txLayout)
        for i, m in enumerate(
            sorted(car.tx_messages.values(), key=lambda m: m.arbitration_id)
        ):
            summary = m.__class__.__name__
            if "\n" in summary:
                summary = summary[: summary.index("\n")]
            cb = QCheckBox(hex(m.arbitration_id) + " - " + summary)
            cb.setChecked(m.enabled)
            cb.toggled.connect(m.set_enabled)
            txLayout.addWidget(cb, i % msgs_per_col, i // msgs_per_col)
        layout.addWidget(txGroup)

        self.refresh = QTimer(app)
        self.refresh.timeout.connect(self.refresh_ui)
        self.refresh.start(250)

    @Slot(bool)
    def on_voltage_changed(self, value):
        print(f"Voltage now {value}")
        self.car.voltage = value

    @Slot(bool)
    def on_current_changed(self, value):
        print(f"Current now {value}")
        self.car.current = value

    @Slot()
    def refresh_ui(self):
        self.pos_contactor.setText(
            "ON" if self.car.pos_contactor_closed else "OFF")
        self.neg_contactor.setText(
            "ON" if self.car.neg_contactor_closed else "OFF")
        self.pch_contactor.setText(
            "ON" if self.car.pch_contactor_closed else "OFF")

        self.msgs_per_sec.setText(f"{self.car.msgs_per_sec} messages/sec")


class AsyncHelper(QObject):

    def __init__(self, worker, entry):
        super().__init__()
        self.entry = entry
        self.worker = worker
        if hasattr(self.worker, "start_signal") and isinstance(
            self.worker.start_signal, Signal
        ):
            self.worker.start_signal.connect(self.on_worker_started)

    @Slot()
    def on_worker_started(self):
        print("on_worker_started")
        asyncio.ensure_future(self.entry())


if __name__ == "__main__":
    car = Car()

    if "--no-ui" in sys.argv:
        asyncio.run(car.start())
    else:

        # Otherwise, display a UI while running model in background asyncio
        app = QApplication(sys.argv)
        asyncio.set_event_loop_policy(QtAsyncio.QAsyncioEventLoopPolicy())

        main_window = MainWindow(car)
        main_window.show()

        # Run car.start() coro on the event loop, once it exists.
        # Seems a bit verbose...?
        timer = QTimer(app)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: asyncio.ensure_future(car.start()))
        timer.start()

        signal.signal(signal.SIGINT, signal.SIG_DFL)

        asyncio.get_event_loop().run_forever()
