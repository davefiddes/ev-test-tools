"""CAN messages sent by the SBox"""

from message import CounterField, PeriodicMessage


class Current(PeriodicMessage):
    """
    Current passing through the SBox current shunt.
        bit 0-23: Signed-integer current value in mA
        bit 44-48: counter cycles 0 -> E
    """

    def __init__(self, car):
        super().__init__(
            car, 0x200, bytearray.fromhex("020000802201D971"), 100
        )
        # Alive counter counts 0xE0..0x00 in upper nibble of byte 5
        self.alive = CounterField(self.data, 5, 0xF0, delta=1, skip=0xF)

    def update(self):
        self.alive.update()

        # fill out current value


class PackVoltage(PeriodicMessage):
    """
    Pack Voltage.
        bit 0-23: Signed-integer voltage value in mV
        bit 44-48: counter cycles 0 -> E
    """

    def __init__(self, car):
        super().__init__(
            car, 0x210, bytearray.fromhex("F60900800004C8A7"), 100
        )
        # Alive counter counts 0xE0..0x00 in upper nibble of byte 5
        self.alive = CounterField(self.data, 5, 0xF0, delta=1, skip=0xF)

    def update(self):
        self.alive.update()

        # fill out voltage value


class PostContactorVoltage(PeriodicMessage):
    """
    Voltage measured after the contactors.
        bit 0-23: Signed-integer voltage value in mV
        bit 44-48: counter cycles 0 -> E
    """

    def __init__(self, car):
        super().__init__(
            car, 0x220, bytearray.fromhex("230000800101C6F0"), 100
        )
        # Alive counter counts 0xE0..0x00 in upper nibble of byte 5
        self.alive = CounterField(self.data, 5, 0xF0, delta=1, skip=0xF)

    def update(self):
        self.alive.update()

        # fill out voltage value


def get_messages(car):
    return [
        k(car)
        for k in globals().values()
        if type(k) == type and k != PeriodicMessage and issubclass(k, PeriodicMessage)
    ]
