import struct
import crcmod
from .mfrc522 import MFRC522, Commands, Registers, NoTagError, TransmissionError

SEL_CASCADE_1   = 0x93
SEL_CASCADE_2   = 0x95
SEL_CASCADE_3   = 0x97

_crc_func = crcmod.mkCrcFun(0x11021, initCrc=0x6363)

def _calculate_crc(data):
    return struct.pack('<H', _crc_func(data))

def _perform_cascade(mfrc522, cascade_level):
    if cascade_level != SEL_CASCADE_1 and \
       cascade_level != SEL_CASCADE_2 and \
       cascade_level != SEL_CASCADE_3:
        return None

    # transmit ANTICOLLISION command
    uid_cln = mfrc522.transceive(bytes((cascade_level, 0x20)))

    # transmit SELECT command
    data = bytes((cascade_level, 0x70)) + bytes(uid_cln)
    data += _calculate_crc(data)
    response = mfrc522.transceive(data)

    if response[0] & 0x04:
        return uid_cln[1:4] + _perform_cascade(mfrc522, cascade_level + 2)
    elif response[0] & 0x24 == 0x20:
        return uid_cln[:4]
    elif response[0] & 0x24 == 0:
        return uid_cln[:4]

def get_id(mfrc522):
    mfrc522.write_register(Registers.BitFramingReg, 0x07)
    mfrc522.transceive([0x26])  # REQA
    mfrc522.write_register(Registers.BitFramingReg, 0x00)
    return _perform_cascade(mfrc522, SEL_CASCADE_1)

def are_cards_in_field(mfrc522):
    mfrc522.write_register(Registers.BitFramingReg, 0x07)
    try:
        mfrc522.transceive([0x26])  # REQA
        try:
            mfrc522.transceive([0x26])  # REQA second time, to reset the card
        except NoTagError:
            # There should be no response, no modulation to the second REQA
            pass
        return True
    except NoTagError:
        return False
