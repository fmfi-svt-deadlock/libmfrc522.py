from enum import Enum

class NoTagError(Exception):
    pass

class TransmissionError(Exception):
    pass

class MFRC522:

    MAX_LEN = 16

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
        CRCResultRegM       = 0x21
        CRCResultRegL       = 0x22
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

    def __init__(self, spi_dev):
        """Initializes a MFRC522 module.

        spi_dev should be an object representing a SPI interface to which
        the Reader is connected. It should have the following methods:
          * transfer(bytes):  Selects the slave, transfers bytes, unselects
                              the slave and returns received bytes.
          * hard_powerdown(): Pulls NRST signal of the reader LOW, thus powering
                              it down
          * reset():          Pushes NRST signal of the reader HIGH,
                              thus resetting it (and exiting the hard_powerdown)
                              If the NRST is already high, this function shall
                              pull it LOW and then HIGH again.
        """

        self.spi = spi_dev

        self.reset()

        self.write_register(MFRC522.Registers.TModeReg,      0x8D)
        self.write_register(MFRC522.Registers.TPrescalerReg, 0x3E)
        self.write_register(MFRC522.Registers.TReloadRegL,   0x1E)
        self.write_register(MFRC522.Registers.TReloadRegH,   0x00)
        self.write_register(MFRC522.Registers.TxASKReg,      0x40)
        self.write_register(MFRC522.Registers.ModeReg,       0x3D)

        self.antenna_on()

    def write_register(self, register, val):
        self.spi.transfer(bytes((register.value << 1, val)))

    def read_register(self, register):
        return self.spi.transfer(bytes(((register.value << 1) | 0x80, 0)))[1]

    def set_mask_in_register(self, reg, mask):
        self.write_register(reg, self.read_register(reg) | mask)

    def clear_mask_in_register(self, reg, mask):
        self.write_register(reg, self.read_register(reg) & (~mask))

    def reset(self):
        self.command(MFRC522.Commands.PCD_RESETPHASE)

    def antenna_on(self):
        self.set_mask_in_register(MFRC522.Registers.TxControlReg, 0x03)

    def antenna_off(self):
        self.clear_mask_in_register(MFRC522.Registers.TxControlReg, 0x03)

    def command(self, command):
        self.write_register(MFRC522.Registers.CommandReg, command.value)

    def transcieve(self, data):
        self.write_register(MFRC522.Registers.ComIEnReg, 0xF7)
        self.clear_mask_in_register(MFRC522.Registers.CommIrqReg, 0x80)
        self.set_mask_in_register(MFRC522.Registers.FIFOLevelReg, 0x80)

        self.command(MFRC522.Commands.PCD_IDLE)

        for byte in data:
            self.write_register(MFRC522.Registers.FIFODataReg, byte)

        self.command(MFRC522.Commands.PCD_TRANSCEIVE)

        self.set_mask_in_register(MFRC522.Registers.BitFramingReg, 0x80)

        # Busy wait for the transmission to finish, for the error to occur
        # or for the command timeout
        while True:
            irq_reg = self.read_register(MFRC522.Registers.CommIrqReg)
            if (irq_reg & 0x20 and irq_reg & 0x40) or (irq_reg & 0x03):
                break

        self.clear_mask_in_register(MFRC522.Registers.BitFramingReg, 0x80)

        if (self.read_register(MFRC522.Registers.ErrorReg) & 0x1B):
            self.command(MFRC522.Commands.PCD_IDLE)
            raise TransmissionError()

        if self.read_register(MFRC522.Registers.CommIrqReg) & 0x01:
            self.command(MFRC522.Commands.PCD_IDLE)
            raise NoTagError()

        response = []

        response_bytes = self.read_register(MFRC522.Registers.FIFOLevelReg)

        for i in range(0, response_bytes):
            response.append(self.read_register(MFRC522.Registers.FIFODataReg))

        self.command(MFRC522.Commands.PCD_IDLE)

        return response
