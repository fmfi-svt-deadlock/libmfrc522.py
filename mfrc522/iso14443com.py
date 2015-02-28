import crcmod
from .mfrc522 import *
import struct

SEL_CASCADE_1   = 0x93
SEL_CASCADE_2   = 0x95
SEL_CASCADE_3   = 0x97

__crc_func = crcmod.mkCrcFun(0x11021, initCrc=0x6363)

def __calculate_crt(data):
    return struct.pack('<H', __crc_func(data))

def __perform_cascade(module, cascade_level):
    if cascade_level != SEL_CASCADE_1 and \
       cascade_level != SEL_CASCADE_2 and \
       cascade_level != SEL_CASCADE_3:
        return None

    # transmit ANTICOLLISION command
    uid_cln = module.transcieve(bytes((cascade_level, 0x20)))

    # transmit SELECT command
    data = bytes((cascade_level, 0x70)) + bytes(uid_cln)
    data += __calculate_crt(data)
    response = module.transcieve(data)

    if response[0] & 0x04:
        return uid_cln[1:4] + __perform_cascade(module, cascade_level + 2)
    elif response[0] & 0x24 == 0x20:
        return uid_cln[:4]
    elif response[0] & 0x24 == 0:
        return uid_cln[:4]

def get_id(module):
    module.write_register(MFRC522.Registers.BitFramingReg, 0x07)
    try:
        module.transcieve([0x26])  # REQA
        module.write_register(MFRC522.Registers.BitFramingReg, 0x00)
        return __perform_cascade(module, SEL_CASCADE_1)
    except NoTagError:
        return None

def are_cards_in_field(module):
    module.write_register(MFRC522.Registers.BitFramingReg, 0x07)
    try:
        module.transcieve([0x26])  # REQA
        try:
            module.transcieve([0x26])  # REQA second time, to reset the card
        except NoTagError:
            # There should be no response, no modulation to the second REQA
            pass
        return True
    except NoTagError:
        return False
