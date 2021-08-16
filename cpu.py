#! /usr/bin/env python3

import unittest

# Control signals
AI = "AI"
AO = "AO"
BI = "BI"
BO = "BO"
CI = "CI" # Carry in
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
EM  = "EM"

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
        self._falling_edge( ctrl )
        self._rising_edge( ctrl )
        ctrl = control[ self.c * 512 + 2*self.ir + 1 ]
        self._falling_edge( ctrl )
        self._rising_edge( ctrl )

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
        if E0 in ctrl:
            self._bus( _74181( ctrl ) & 0xff )

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
        if CI in ctrl:
            self.c = self._74181( ctrl ) >> 8
        # Do these after carry.  Carry depends on them.
        if AI in ctrl:
            self.a = self.bus
        if BI in ctrl:
            self.b = self.bus

    def _74181( self, ctrl ):
        s = ( (ES3 in ctrl) * 8
            + (ES2 in ctrl) * 4
            + (ES1 in ctrl) * 2
            + (ES0 in ctrl) * 1
        )
        return self._74181_logic( self.a, self.b, s, (EM in ctrl), self.c )

def _74181_logic( A, B, s, m, c ):
    """Active high. Returns 9-bit result with high bit = carry out"""
    if m:
        result = {
            0:  ~A,
            1:  ~(A & B),
            2:  (~A) & B,
            3:  0,
            4:  ~(A & B),
            5:  ~B,
            6:   A ^ B,
            7:  A & (~B),
            8:  (~A) | B,
            9:  ~(A ^ B),
            10: B,
            11: A & B,
            12: 1,
            13: A | (~B),
            14: A | B,
            15: A,
        }[s] & 0x1ff
    else:
        AB  = A & B
        AB_ = A & (~B) # Oddly common
        result = (c + {
            0:  A,
            1:  A + B,
            2:  A + (~B),
            3:  -1,
            4:  A + AB_,
            5:  (A+B) + AB_,
            6:  A - B - 1,
            7:  AB_ - 1,
            8:  A + AB,
            9:  A + B,
            10: (A + (~B)) + AB,
            11: AB - 1,
            12: A + A,
            13: (A + B) + A,
            14: (A + (~B)) + A,
            15: A - 1,
        }[s]) & 0x1ff
    return result

class Test74181(unittest.TestCase):
    def test_stuff( self ):
        self._check( 200,  70, 130, 1, 0, 0 )
        self._check( 201,  70, 130, 1, 0, 1 )
        self._check( 300, 170, 130, 1, 0, 0 )

    def _check( self, expected, a, b, s, m, c ):
        result = _74181_logic( a, b, s, m, c )
        self.assertEqual( expected, result )

