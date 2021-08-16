#! /usr/bin/env python3

# Control signals
AI = "AI"
AO = "AO"
BI = "BI"
BO = "BO"
PCA = "PCA" # Program counter advance
PCI = "PCI"
PCO = "PCO"
MR = "MR"
MW = "MW"
ARI = "ARI"
IRI = "IRI"
IR4 = "IR4" # Low 4 bits of instruction register onto bus
APC = "APC" # ar <- pc
# ALU selector
E0 = "E0" # ALU out
ES0 = "ES0"
ES1 = "ES1"
ES2 = "ES2"
ES3 = "ES3"

# Control ROM
control = bytearray( 1024 )

# Machine state outside CPU
ram = bytearray( 256 )

class CPU:

    def __init__( self ):
        self.pc = 0
        self.ar = 0
        self.ir = 0
        self.a = 0
        self.b = 0
        self.c = 0
        # Not a register. We put this here for error checking
        self.bus = None

    def step( self ):
        ctrl = control[ self.c * 512 + 2*self.ir ]
        self._rising_edge( ctrl )
        self._falling_edge( ctrl )
        ctrl = control[ self.c * 512 + 2*self.ir + 1 ]
        self._rising_edge( ctrl )
        self._falling_edge( ctrl )

    def _set_bus( self ):
        self.bus = None
        if AO in ctrl:
            self._bus( self.a )
        if BO in ctrl:
            self._bus( self.b )
        if PCO in ctrl:
            self._bus( self.pc )
        if MR in ctrl:
            self._bus( self.ram[ self.ar ] )
        if IR4 in ctrl:
            self._bus( self.ir & 0x0f )

    def _bus( self, value ):
        if self.bus is None:
            self.bus = value
        else:
            raise ValueError

    def _rising_edge( self, ctrl ):
        if PCA in ctrl:
            self.pc = self.pc + 1
        if PCI in ctrl:
            self.pc = self.bus
            if PCA in ctrl:
                raise ValueError
        if IRI in ctrl:
            self.ir = self.bus

    def _falling_edge( self, ctrl ):
        if APC in ctrl:
            self.pc = self.ar
        if ARI in ctrl:
            self.ar = self.bus
        if AI in ctrl:
            self.a = self.bus
        if BI in ctrl:
            self.b = self.bus

