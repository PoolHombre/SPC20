"""Sequent Microsystems Industrial 4-20 mA HAT adapter."""
from __future__ import annotations
import time

from .base import RawSample, SensorAdapter


class SequentAdapter(SensorAdapter):
    """Real Sequent Microsystems Industrial HAT reader (Raspberry Pi I2C).

    Requires smbus2: pip install smbus2
    """

    def __init__(self) -> None:
        try:
            import smbus2  # type: ignore
            self._bus = smbus2.SMBus(1)
        except ImportError:
            raise RuntimeError("smbus2 not installed — run: pip install smbus2")

    def read(self) -> RawSample:
        # Sequent Microsystems 4-20mA HAT register map
        # Channels return raw 16-bit value; divide by 1000 to get mA
        def _read_channel(ch: int) -> float:
            addr = 0x40 + ch
            raw = self._bus.read_word_data(addr, 0x00)
            return raw / 1000.0

        # Digital input 1 on Sequent HAT — pump run signal
        pump = bool(self._bus.read_byte_data(0x20, 0x00) & 0x01)

        return RawSample(
            p1_ma=_read_channel(0),
            p2_ma=_read_channel(1),
            p3_ma=_read_channel(2),
            flow_ma=_read_channel(3),
            pump_running=pump,
            timestamp=time.time(),
        )
