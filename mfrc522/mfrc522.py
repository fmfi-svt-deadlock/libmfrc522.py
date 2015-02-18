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
        CommIEnReg          = 0x02
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
        TxAutoReg           = 0x15
        TxSelReg            = 0x16
        RxSelReg            = 0x17
        RxThresholdReg      = 0x18
        DemodReg            = 0x19
        Reserved11          = 0x1A
        Reserved12          = 0x1B
        MifareReg           = 0x1C
        Reserved13          = 0x1D
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

        # TODO initialize the module
        # self.init()

    def write_register(self, register, val):
        self.spi.transfer(bytes((register.value << 1, val)))

    def read_register(self, register):
        return self.spi.transfer(bytes(((register.value << 1) | 0x80, 0)))[1]

    def set_mask_in_register(self, reg, mask):
        self.write_register(reg, self.read_register(reg) | mask)

    def clear_mask_in_register(self, reg, mask):
        self.write_register(reg, self.read_register(reg) & (~mask))
