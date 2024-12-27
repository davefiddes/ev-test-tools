""" Home for mystery messages """

from message import PeriodicMessage


MSGS = [
    # Put myster messages here in the form:
    # (
    #   0x5B3,
    #    "40,10,FE,30,00,00,00,00",
    #    5,
    # ),
]


def get_messages(sbox):
    return [
        PeriodicMessage(sbox, can_id, bytes.fromhex(data.replace(",", "")), hz)
        for (can_id, data, hz) in MSGS
    ] + [
        k(sbox)
        for k in globals().values()
        if type(k) == type and k != PeriodicMessage and issubclass(k, PeriodicMessage)
    ]
