from enum import Enum

class NoTagError(Exception):
    pass

class TransmissionError(Exception):
    pass

class Commands(Enum):
    PCD_IDLE            = 0x00
    PCD_AUTHENT         = 0x0E
    PCD_RECEIVE         = 0x08
    PCD_TRANSMIT        = 0x04
    PCD_TRANSCEIVE      = 0x0C
    PCD_RESETPHASE      = 0x0F
    PCD_CALCCRC         = 0x03

class Registers(Enum):
    Reserved00          = 0x00
    CommandReg          = 0x01
    ComIEnReg           = 0x02
    DivlEnReg           = 0x03
    CommIrqReg          = 0x04
    DivIrqReg           = 0x05
    ErrorReg            = 0x06
    Status1Reg          = 0x07
    Status2Reg          = 0x08
    FIFODataReg         = 0x09
    FIFOLevelReg        = 0x0A
    WaterLevelReg       = 0x0B
    ControlReg          = 0x0C
    BitFramingReg       = 0x0D
    CollReg             = 0x0E
    Reserved01          = 0x0F
    Reserved10          = 0x10
    ModeReg             = 0x11
    TxModeReg           = 0x12
    RxModeReg           = 0x13
    TxControlReg        = 0x14
    TxASKReg            = 0x15
    TxSelReg            = 0x16
    RxSelReg            = 0x17
    RxThresholdReg      = 0x18
    DemodReg            = 0x19
    Reserved11          = 0x1A
    Reserved12          = 0x1B
    MfTxReg             = 0x1C
    MfRxReg             = 0x1D
    Reserved14          = 0x1E
    SerialSpeedReg      = 0x1F
    Reserved20          = 0x20
    CRCResultRegL       = 0x21
    CRCResultRegH       = 0x22
    Reserved21          = 0x23
    ModWidthReg         = 0x24
    Reserved22          = 0x25
    RFCfgReg            = 0x26
    GsNReg              = 0x27
    CWGsPReg            = 0x28
    ModGsPReg           = 0x29
    TModeReg            = 0x2A
    TPrescalerReg       = 0x2B
    TReloadRegH         = 0x2C
    TReloadRegL         = 0x2D
    TCounterValueRegH   = 0x2E
    TCounterValueRegL   = 0x2F
    Reserved30          = 0x30
    TestSel1Reg         = 0x31
    TestSel2Reg         = 0x32
    TestPinEnReg        = 0x33
    TestPinValueReg     = 0x34
    TestBusReg          = 0x35
    AutoTestReg         = 0x36
    VersionReg          = 0x37
    AnalogTestReg       = 0x38
    TestDAC1Reg         = 0x39
    TestDAC2Reg         = 0x3A
    TestADCReg          = 0x3B
    Reserved31          = 0x3C
    Reserved32          = 0x3D
    Reserved33          = 0x3E
    Reserved34          = 0x3F

class MFRC522:

    MAX_LEN = 16

    def __init__(self, spi_dev):
        """Initializes a MFRC522 module.

        spi_dev should be an object representing a SPI interface to which
        the Reader is connected. It should have the following methods:
          * transfer(bytes):  Selects the slave, transfers bytes, unselects
                              the slave and returns received bytes.
          * hard_powerdown(): Sets NRST signal of the reader LOW, thus powering
                              it down
          * reset():          Sets NRST signal of the reader HIGH,
                              thus resetting it (and exiting the hard_powerdown)
                              If the NRST is already high, this function shall
                              set it LOW and then HIGH again.
        """

        self.spi = spi_dev

        self.reset()

        # Set TAuto - timer starts automatically after the enf of transmission
        #     TPrescaler_Hi - set to 0x0D
        self.write_register(Registers.TModeReg,      0x8D)
        # Set TPrescaler_Lo - set to 0x3E.
        # Together with TPrescaler_Hi the timer will run at approx 2KHz
        self.write_register(Registers.TPrescalerReg, 0x3E)
        # Set reload value to 0x1E. The timer will run for approx 15ms.
        self.write_register(Registers.TReloadRegH,   0x00)
        self.write_register(Registers.TReloadRegL,   0x1E)
        # Set Force100ASK: Forces a 100% ASK modulation independent of the
        #                  ModGSPReg setting
        self.write_register(Registers.TxASKReg,      0x40)
        # Set TXWaitRF   : Transmitter will only start if the RF field is
        #                  is present
        #     PolMFin    : MFIN pin is active HIGH
        #     CRCPreset  : to 0x6363 as specified in ISO/IEC 14443
        self.write_register(Registers.ModeReg,       0x3D)

        self.antenna_on()

    def write_register(self, register, val):
        if type(val) is int:
            val = bytes([val])
        # The format of the address byte is:
        # 7 (MSB): 1 - Read. 0 - write
        # 6 - 1  : Address
        # 0      : 0
        data = [register.value << 1]
        for byte in val:
            data.append(byte)
        self.spi.transfer(bytes(data))

    def read_register(self, register, amount=1):
        request = bytes(((register.value << 1) | 0x80,)*(amount+1))
        if (amount == 1):
            return self.spi.transfer(request)[1]
        else:
            return self.spi.transfer(request)[1:]

    def set_mask_in_register(self, register, mask):
        self.write_register(register, self.read_register(register) | mask)

    def clear_mask_in_register(self, register, mask):
        self.write_register(register, self.read_register(register) & (~mask))

    def reset(self):
        self.command(Commands.PCD_RESETPHASE)

    def antenna_on(self):
        # Set Tx2RFEn and TCRFEn: to make TX1 and TX2 pins deliver energy
        #                         carrier modulated by the transmission data
        #                         to the antenna
        self.set_mask_in_register(Registers.TxControlReg, 0x03)

    def antenna_off(self):
        self.clear_mask_in_register(Registers.TxControlReg, 0x03)

    def command(self, command):
        self.write_register(Registers.CommandReg, command.value)

    def calculate_crc_a(self, data):
        self.command(Commands.PCD_IDLE)
        # Flush the FIFO buffer
        self.set_mask_in_register(Registers.FIFOLevelReg, 0x80)

        self.write_register(Registers.FIFODataReg, data)

        self.command(Commands.PCD_CALCCRC)

        # Busy-wait for the CRC calculation to finish
        # the CRCIRq bit should become 0
        while not self.read_register(Registers.DivIrqReg) & 0x04:
            pass

        return bytes((self.read_register(Registers.CRCResultRegH),
                      self.read_register(Registers.CRCResultRegL)))

    def transceive(self, data):
        # Invert output interrupt signal; enable Tx interrupt, Rx interrupt,
        # idle interrupt, FIFO Low interrupt, ErrorInterrupt and TimerInterrupt
        self.write_register(Registers.ComIEnReg, 0xF7)
        # Clear interrupt request bits
        self.clear_mask_in_register(Registers.CommIrqReg, 0x80)
        # Flush the FIFO
        self.write_register(Registers.FIFOLevelReg, 0x80)

        self.write_register(Registers.FIFODataReg, data)

        self.command(Commands.PCD_TRANSCEIVE)

        bit_framing_reg = self.read_register(Registers.BitFramingReg)
        # Set StartSend bit
        self.write_register(Registers.BitFramingReg, bit_framing_reg | 0x80)

        # Busy wait for the transmission to finish, for the error to occur
        # or for the command timeout
        irq_reg = None
        while True:
            irq_reg = self.read_register(Registers.CommIrqReg)
            # Wait for interrupts: Tx and Rx complete, error or timeout
            if (irq_reg & 0x20 and irq_reg & 0x40) or (irq_reg & 0x03):
                break

        # Restore original BitFramingReg, thus clearing the StartSend flag
        self.write_register(Registers.BitFramingReg, bit_framing_reg)

        # Error interrupt has fired
        if irq_reg & 0x02:
            error = self.read_register(Registers.ErrorReg)
            if error & 0x1B:
                self.command(Commands.PCD_IDLE)
                raise TransmissionError()

        # Timeout interrupt has fired
        if irq_reg & 0x01:
            self.command(Commands.PCD_IDLE)
            raise NoTagError()

        response_bytes = self.read_register(Registers.FIFOLevelReg)

        response = self.read_register(Registers.FIFODataReg, response_bytes)

        self.command(Commands.PCD_IDLE)

        return response
