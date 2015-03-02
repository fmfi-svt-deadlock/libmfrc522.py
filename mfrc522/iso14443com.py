import struct
from enum import Enum
import crcmod
from .mfrc522 import (MFRC522, Commands, Registers, NoTagError,
                      TransmissionError)

# 0x11021 is hex representation of the CRC polynomial used by the ISO/IEC1444
# 0x6363 is the preset value.
_crc_func = crcmod.mkCrcFun(0x11021, initCrc=0x6363)

class CardCommands(Enum):
    REQA         = 0x26
    ANTICOLL_n   = (0x93, 0x95, 0x97)

class CardException(Exception):
    """The card did something unexpected."""
    pass

def _calculate_crc(data):
    return struct.pack('<H', _crc_func(data))

def _perform_cascade(mfrc522):
    result = b''
    for cascade_level in CardCommands.ANTICOLL_n.value:
        # transmit ANTICOLLISION command
        uid_cln = mfrc522.transceive(bytes([cascade_level, 0x20]))
        if len(uid_cln) != 5:
            raise CardException

        # transmit SELECT command
        data = bytes((cascade_level, 0x70)) + bytes(uid_cln)
        data += _calculate_crc(data)
        response = mfrc522.transceive(data)

        if response[0] & 0x24 == 0x00:
            # UID complete, PICC is NOT compliant with ISO/IEC 14443-4
            # TODO should we care?
            result += uid_cln[:4]
            return result
        if response[0] & 0x24 == 0x20:
            # UID complete, PICC compliant with ISO/IEC 14443-4
            result += uid_cln[:4]
            return result
        elif response[0] & 0x04:
            result += uid_cln[1:4]
            # UID incomplete; continue the cascade
        else:
            # Something's wrong if we get here.
            raise CardException
    # This cascade should always return UID, it should never end and get here.
    raise CardException

def get_id(mfrc522):
    mfrc522.write_register(Registers.BitFramingReg, 0x07)
    mfrc522.transceive(CardCommands.REQA.value)
    mfrc522.write_register(Registers.BitFramingReg, 0x00)
    return _perform_cascade(mfrc522)

def are_cards_in_field(mfrc522):
    mfrc522.write_register(Registers.BitFramingReg, 0x07)
    try:
        mfrc522.transceive(CardCommands.REQA.value)
        try:
            # The second REQA command will reset the card
            mfrc522.transceive(CardCommands.REQA.value)
        except NoTagError:
            # There should be no response, no modulation to the second REQA
            pass
        return True
    except NoTagError:
        return False
