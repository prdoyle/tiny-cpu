#! /usr/bin/env python3

from unittest import TestCase
import sys

def debug(*args, **kwargs):
    if True:
        print(*args, file=sys.stdout, **kwargs)

### Control signals
# Out to bus - 74238?
AO = "AO"
PO = "PO"
PCO = "PCO"
MR = "MR"
EO = "EO" # ALU out
SO = "SO" # Shifter out
IR4O = "IR4O" # Low 4 bits of instruction register onto bus
LO = "LO" # Link register out
# In from bus - 74238?
AI = "AI"
BI = "BI"
PI = "PI"
PCI = "PCI"
MW = "MW"
ARI = "ARI"
LI = "LI" # Link register in
# Fetch signals - these can use a 74153
APC = "APC" # ar <- pc and IR from bus - cycle 0
PCA = "PCA" # Program counter advance - cycle 1
# ALU function selector
ES0 = "ES0"
ES1 = "ES1"
ES2 = "ES2"
ES3 = "ES3"
EM  = "EM"
CI  = "CI" # ALU writes carry to C register
# ALU input selector
EA  = "EA" # First input is accumulator
EP  = "EP" # First input is pointer
EPC = "EPC" # First input is program counter
EI4 = "EI4" # ALU (and shifter) reads second operand from low 4 bits of instruction register; otherwise b
EC  = "EC" # ALU reads carry from C register; otherwise zero
# Misc
H   = "H" # Halted

# Control ROM (2k bytes)
control = [set()] * 2048

def put_control( instruction, cycle, flags ):
    global control
    control[ 4*instruction + cycle ] = flags

def encode( instruction, cycle, flags ):
    put_control( instruction, cycle, flags )
    put_control( 256+instruction, cycle, flags )

def init_control():
    global control
    for opcode in range(256):
        encode( opcode, 0, { MR } ) # Fetch instruction from memory
    # IMM # Load immediate
    for n in range(16):
        encode( 0x00+n, 1, { AI, IR4O })
    # ST # Store via pointer
    for n in range(16):
        encode( 0x20+n, 1, { ARI, EO, EP, EI4, ES0,ES3 })  # AR  := P+ir4
        encode( 0x20+n, 2, { MW, AO   })                   # mem := A
    # JV # Jump virtual (load PC via pointer)
    for n in range(16):
        encode( 0x30+n, 1, { LI, PCO })                     # LR := PC
        encode( 0x30+n, 2, { ARI, EO, EP, EI4, ES0,ES3  })  # AR := P+ir4
        encode( 0x30+n, 3, { PCI, MR   })                   # PC := mem
    # LD # Load via pointer
    for n in range(16):
        encode( 0x40+n, 1, { ARI, EO, EP, EI4, ES0,ES3  })  # AR := P+ir4
        encode( 0x40+n, 2, { AI, MR   })                    # A  := mem
    # SH # Bitwise shift
    for n in range(16):
        encode( 0x50+n, 1, { AI, SO, EI4 })        # A  := shifter output of A and ir4
    # A2P
    encode( 0x80, 1, { PI, AO })
    # P2A
    encode( 0x81, 1, { AI, PO })
    # A2B
    encode( 0x82, 1, { BI, AO })
    # XCHG
    encode( 0x83, 1, { BI, EO, EA, EM, ES0, ES3 })  # B := A ^ B
    encode( 0x83, 2, { AI, EO, EA, EM, ES0, ES3 })  # A := A ^ B
    encode( 0x83, 3, { BI, EO, EA, EM, ES0, ES3 })  # B := A ^ B
    # L2A
    encode( 0x84, 1, { AI, LO })
    # A2L
    encode( 0x85, 1, { LI, AO })
    # ADD
    encode( 0xa2, 1, { AI, EO, EA, ES0, ES3, CI })      # A := A + B; set carry
    # ADC
    encode( 0xa3, 1, { AI, EO, EA, ES0, ES3, CI, EC })  # A := A + B + C; set carry
    # LINK
    encode( 0xb3, 1, { LI, PCO })  # link := PC
    # RET
    encode( 0xb4, 1, { PCI, LO })  # PC := link
    # HALT
    encode( 0xbd, 1, { H } )
    # Skip if carry clear
    for n in range(16):
        encode( 0xc0+n, 1, { PCI, EO, EPC, EI4, ES0, ES3  }) # AR := P+ir4
    # Skip if carry set
    for n in range(16):
        encode( 0xd0+n, 1, { PCI, EO, EPC, EI4, ES0, ES3  }) # AR := P+ir4

    # Now copy everything for carry set
    half = len( control ) // 2
    for i in range( half ):
        control[ half + i ] = control[ i ]
    # Clear out appropriate conditional instructions
    for n in range(16):
        put_control( 0xd0+n, 1, set() )
        put_control( 0x1c0+n, 1, set() )

# Machine state outside CPU
ram = bytearray( 256 )

class CPU:

    def __init__( self ):
        # Architected regs
        self.pc = 0x10  # Program counter
        self.a = 0      # Accumulator reg
        self.b = 0      # B reg
        self.p = 0      # Pointer reg
        self.carry = 0
        # Internal regs
        self.ar = 0     # Address reg
        self.ir = 0     # Instruction reg
        self.lr = 9     # Link reg
        # Not a register. We put this here for error checking
        self.bus = None
        # Just so we can tell when we're done
        self.halted = False

    def step( self ):
        for cycle in range(4):
            ctrl = control[ self.carry * 1024 + 4*self.ir + cycle ]
            if cycle == 0:
                ctrl.add( APC )
            elif cycle == 1:
                ctrl.add( PCA )
            debug( "| ctrl: %s" % ctrl )
            self._set_bus( ctrl )
            self._falling_edge( ctrl )
            self._set_bus( ctrl )
            self._rising_edge( ctrl )

    def _set_bus( self, ctrl ):
        self.bus = None
        if AO in ctrl:
            self._bus( self.a )
        if PCO in ctrl:
            self._bus( self.pc )
        if MR in ctrl:
            self._bus( self.ram[ self.ar ] )
        if IR4O in ctrl:
            self._bus( self.ir & 0x0f )
        if LO in ctrl:
            self._bus( self.lr )
        if EO in ctrl:
            self._bus( self._74181( ctrl ) & 0xff )

    def _bus( self, value ):
        if self.bus is None:
            self.bus = value
        else:
            raise ValueError

    def _rising_edge( self, ctrl ):
        if H in ctrl:
            self.halted = True
        elif APC in ctrl: # Note "elif" override
            self.ir = self.bus
        if PCI in ctrl:
            self.pc = self.bus
        elif PCA in ctrl: # Note "elif" override
            self.pc = self.pc + 1

    def _falling_edge( self, ctrl ):
        if APC in ctrl:
            self.ar = self.pc
        if ARI in ctrl:
            self.ar = self.bus
        if LI in ctrl:
            self.lr = self.bus
        if CI in ctrl:
            self.carry = self._74181( ctrl ) >> 8
        # Do these after carry.  Carry depends on them.
        if AI in ctrl:
            self.a = self.bus
        if BI in ctrl:
            self.b = self.bus
        if PI in ctrl:
            self.p = self.bus
        if PCI in ctrl:
            self.pc = self.bus
        if MW in ctrl:
            self.mem[ self.ar ] = self.bus

    def _74181( self, ctrl ):
        s = ( (ES3 in ctrl) * 8
            + (ES2 in ctrl) * 4
            + (ES1 in ctrl) * 2
            + (ES0 in ctrl) * 1
        )
        a = None
        if EA in ctrl:
            a = self.a
        if EP in ctrl:
            a = self.p
        if EPC in ctrl:
            a = self.pc
        if EI4 in ctrl:
            b = self.ir & 0x0f
        else:
            b = self.b
        return _74181_logic( a, b, s, (EM in ctrl), (EC in ctrl) and self.carry )

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def _74181_logic( A, B, s, m, carry ):
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
        result = (carry + {
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
    debug( "| 74181( %02x, %02x, %1x, %s, %s ) = %03x" % ( A, B, s, m, carry, result ) )
    return result

class Assembler():
    
    def __init__( self, ram ):
        self.ram = ram
        self.loc = 0

    def _emit( self, byte ):
        self.ram[ self.loc ] = byte & 0xff
        self.loc += 1

    def imm( self, v ):
        self._emit( v )

    def st( self, d ):
        self._emit( 0x20 + d )

    def jv( self, d ):
        self._emit( 0x30 + d )

    def ld( self, d ):
        self._emit( 0x40 + d )

    def sh( self, d ):
        self._emit( 0x50 + d )

    def a2p( self ):
        self._emit( 0x80 )

    def p2a( self ):
        self._emit( 0x81 )

    def a2b( self ):
        self._emit( 0x82 )

    def xchg( self ):
        self._emit( 0x83 )

    def l2a( self ):
        self._emit( 0x84 )

    def a2l( self ):
        self._emit( 0x85 )

    def add( self ):
        self._emit( 0xa2 )

    def adc( self ):
        self._emit( 0xa3 )

    def link( self ):
        self._emit( 0xb3 )

    def ret( self ):
        self._emit( 0xb4 )

    def halt( self ):
        self._emit( 0xbd )

    def scc( self, d ):
        self._emit( 0xc0 + d )

    def scs( self, d ):
        self._emit( 0xd0 + d )

class Test74181( TestCase ):
    def test_stuff( self ):
        self._check( 200,  70, 130, 1, 0, 0 )
        self._check( 201,  70, 130, 1, 0, 1 )
        self._check( 300, 170, 130, 1, 0, 0 )

    def _check( self, expected, a, b, s, m, carry ):
        result = _74181_logic( a, b, s, m, carry )
        self.assertEqual( expected, result )

class TestMath( TestCase ):
    def setUp( self ):
        self.cpu = CPU()
        self.ram = bytearray( 256 )
        self.cpu.ram = self.ram
        self.asm = Assembler( self.ram )
        self.asm.loc = 16

    def test_fib( self ):
        self.asm.imm( 1 )
        self.asm.a2b()
        self.asm.imm( 1 )
        self.asm.link()
        self.asm.xchg()
        self.asm.add()
        self.asm.scs( 1 )
        self.asm.ret()
        self.asm.halt()
        
        while not self.cpu.halted:
            v = vars( self.cpu ).copy()
            v["ram"] = "..."
            debug( "state=%s" % ( v ) )
            debug( "| i=%x" % ( self.cpu.ram[ self.cpu.pc ] ) )
            self.cpu.step()

init_control()
t = TestMath()
t.setUp()
t.test_fib()

