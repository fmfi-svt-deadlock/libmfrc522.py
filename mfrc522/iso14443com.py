from .mfrc522 import *

SEL_CASCADE_1   = 0x93
SEL_CASCADE_2   = 0x95
SEL_CASCADE_3   = 0x97

def __perform_cascade(module, cascade_level):

    if cascade_level != SEL_CASCADE_1 and \
       cascade_level != SEL_CASCADE_2 and \
       cascade_level != SEL_CASCADE_3:
        return None

    # print('Performing cascade', cascade_level)

    module.write_register(MFRC522.Registers.BitFramingReg, 0x00)

    # transmit ANTICOLLISION command
    uid_cln = module.transcieve(bytes((cascade_level, 0x20)))

    # TODO check for collisions, screw it for now

    # transmit SELECT command
    data = bytes((cascade_level, 0x70)) + bytes(uid_cln)
    data += module.calculate_crc_a(data)
    response = module.transcieve(data)

    if response[0] & 0x04:
        # print('UID incomplete, cascading...')
        return uid_cln[1:4] + __perform_cascade(module, cascade_level + 2)
    elif response[0] & 0x24 == 0x20:
        # print('UID complete, PICC compliant with ISO/IEC 14443-4')
        return uid_cln[:4]
    elif response[0] & 0x24 == 0:
        # print('UID complete, PICC not compliant with ISO/IEC 14443-4')
        return uid_cln[:4]

def get_ids(module):
    module.write_register(MFRC522.Registers.BitFramingReg, 0x07)
    try:
        # module.transcieve([0x26])  # REQA
        return __perform_cascade(module, SEL_CASCADE_1)

    except NoTagError:
        return None

def are_cards_in_field(module):
    module.write_register(MFRC522.Registers.BitFramingReg, 0x07)
    try:
        module.transcieve([0x26])  # REQA
        return True
    except NoTagError:
        return False
