#! /usr/bin/env python3

from unittest import TestCase
import sys

def debug(*args, **kwargs):
    if True:
        print(*args, file=sys.stdout, **kwargs)

### Control signals
# Out to bus - 74238?
AO = "AO"
DPO = "DPO"
PCO = "PCO"
MR = "MR"
EO = "EO" # ALU out
SO = "SO" # Shifter out
IR4O = "IR4O" # Low 4 bits of instruction register onto bus
LO = "LO" # Link register out
# In from bus - 74238?
AI = "AI"
BI = "BI"
DPI = "DPI"
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
EDP = "EDP" # First input is data pointer
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
    # SD # Store direct via pointer
    for n in range(16):
        encode( 0x10+n, 1, { ARI, EO, EDP, EI4, ES0,ES3 })  # AR  := DP+ir4
        encode( 0x10+n, 2, { MW, AO   })                    # mem := A
    # SI # Store indirect (store A to address loaded via pointer)
    for n in range(16):
        encode( 0x20+n, 1, { ARI, EO, EDP, EI4, ES0,ES3 })  # AR  := DP+ir4
        encode( 0x20+n, 2, { ARI, MR   })                   # AR := mem
        encode( 0x20+n, 3, { MW, AO   })                    # mem := A
    # LD # Load direct via pointer
    for n in range(16):
        encode( 0x30+n, 1, { ARI, EO, EDP, EI4, ES0,ES3 })  # AR := DP+ir4
        encode( 0x30+n, 2, { AI, MR   })                    # A  := mem
    # LI # Load indirect (load A from address loaded via pointer)
    for n in range(16):
        encode( 0x40+n, 1, { ARI, EO, EDP, EI4, ES0,ES3 })  # AR := DP+ir4
        encode( 0x40+n, 2, { ARI, MR   })                   # AR := mem
        encode( 0x40+n, 3, { AI, MR   })                    # A  := mem
    # SH # Bitwise shift
    for n in range(16):
        encode( 0x50+n, 1, { AI, SO, EI4 })        # A  := shifter output of A and ir4
    # JV # Jump virtual (load PC from [DP+n] save return address)
    for n in range(16):
        encode( 0x60+n, 1, { ARI, EO, EDP, EI4, ES0,ES3 })  # AR := DP+ir4
        encode( 0x60+n, 2, { PCI, MR   })                   # PC := mem
    # JT # Jump table (PC = [DP + n + B])
    for n in range(16):
        encode( 0x70+n, 1, { PCI, EO, EDP,      ES0,ES3 })  # PC := DP+B // temp storage
        encode( 0x70+n, 2, { ARI, EO, EPC, EI4, ES0,ES3 })  # AR := PC+ir4
        encode( 0x70+n, 3, { PCI, MR   })                   # DP := mem
    # DPE # Dereference pointer to element (DP = [DP + n + B])
    for n in range(16):
        encode( 0xe0+n, 1, { DPI, EO, EDP,      ES0,ES3 })  # DP := DP+B
        encode( 0xe0+n, 2, { ARI, EO, EDP, EI4, ES0,ES3 })  # AR := DP+ir4
        encode( 0xe0+n, 3, { DPI, MR   })                   # DP := mem
    # DPF # Dereference pointer to field (DP = [DP+n])
    for n in range(16):
        encode( 0xf0+n, 1, { ARI, EO, EDP, EI4, ES0,ES3 })  # AR := DP+ir4
        encode( 0xf0+n, 2, { DPI, MR   })                   # DP := mem
    # ADD
    encode( 0xa0, 1, { AI, EO, EA, ES0, ES3, CI })      # A := A + B; set carry
    # ADC
    encode( 0xa1, 1, { AI, EO, EA, ES0, ES3, CI, EC })  # A := A + B + C; set carry
    # SBC
    encode( 0xa3, 1, { AI, EO, EA, ES2,ES1, CI, EC })  # A := A + C - B; set carry (0 = borrow)
    # LINKn
    for n in range(4):
        encode( 0xb0+n, 1, { LI, EO, EPC, EI4, ES0, ES3  }) # link := PC + ir4
    # RET
    encode( 0xb4, 1, { PCI, LO })  # PC := link
    # C2A
    encode( 0xb5, 1, { AI, EO, EA, EM,ES3,ES1,ES0, CI}) # A := 0 + C
    # A2DP
    encode( 0xb8, 1, { DPI, AO })
    # DP2A
    encode( 0xb9, 1, { AI, DPO })
    # A2B
    encode( 0xba, 1, { BI, AO })
    # XCHG
    encode( 0xbb, 1, { BI, EO, EA, EM, ES0, ES3 })  # B := A ^ B
    encode( 0xbb, 2, { AI, EO, EA, EM, ES0, ES3 })  # A := A ^ B
    encode( 0xbb, 3, { BI, EO, EA, EM, ES0, ES3 })  # B := A ^ B
    # SPLIT -- NOTE this opcode must end with "F" because it's used as a mask
    encode( 0xbf, 1, { BI, EO, EA, EI4, EM,ES3,ES1,ES0 })  # B := A & 0x0F
    encode( 0xbf, 2, { AI, EO, EA,      EM,ES2,ES1     })  # A := A ^ B
    # L2A
    encode( 0xbe, 1, { AI, LO })
    # A2L
    encode( 0xbc, 1, { LI, AO })
    # HALT
    encode( 0xbd, 1, { H } )
    # Skip if carry clear
    for n in range(16):
        encode( 0xc0+n, 1, { PCI, EO, EPC, EI4, ES0, ES3  }) # PC := PC + ir4
    # Skip if carry set
    for n in range(16):
        encode( 0xd0+n, 1, { PCI, EO, EPC, EI4, ES0, ES3  }) # PC := PC + ir4

    # Now copy everything for carry set
    half = len( control ) // 2
    for i in range( half ):
        control[ half + i ] = control[ i ]
    # Clear out appropriate conditional instructions
    for n in range(16):
        put_control( 0xd0+n, 1, set() )
        put_control( 0x1c0+n, 1, set() )

init_control()

# Machine state outside CPU
ram = bytearray( 256 )

class ArchitectedRegisters:

    def __init__( self ):
        # Architected regs
        self.pc = 0x10  # Program counter
        self.a = 0      # Accumulator reg
        self.b = 0      # B reg
        self.dp = 0     # Data pointer
        self.carry = 0
        self.lr = 0
        # Just so we can tell when we're done
        self.halted = False

    def _debug( self ):
        v = vars( self ).copy()
        v["ram"] = "..."
        for k in list( v.keys() ):
            if k[0] == "_":
                del v[k]
        debug( "| state=%s" % ( v ) )

class CPU(ArchitectedRegisters):

    def __init__( self ):
        super().__init__()
        # Internal regs
        self.ar = 0     # Address reg
        self.ir = 0     # Instruction reg
        self.lr = 9     # Link reg
        # Not a register. We put this here for error checking
        self.bus = None

    def step( self ):
        debug( "Step instruction=%x" % ( self.ram[ self.pc ] ) )
        for cycle in range(4):
            ctrl = control[ self.carry * 1024 + 4*self.ir + cycle ]
            if cycle == 0:
                ctrl.add( APC )
            elif cycle == 1:
                ctrl.add( PCA )
            self._debug()
            debug( "%d: ctrl = %s" % ( cycle, ctrl ) )
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
        if SO in ctrl:
            self._bus( self._shifter( ctrl ) )

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
        if DPI in ctrl:
            self.dp = self.bus
        if PCI in ctrl:
            self.pc = self.bus
        if MW in ctrl:
            self.mem[ self.ar ] = self.bus

    def _alu_first_operand( self, ctrl ):
        if EA in ctrl:
            return self.a
        if EDP in ctrl:
            return self.dp
        if EPC in ctrl:
            return self.pc
        raise ValueError

    def _alu_second_operand( self, ctrl ):
        if EI4 in ctrl:
            return self.ir & 0x0f
        else:
            return self.b

    def _74181( self, ctrl ):
        s = ( (ES3 in ctrl) * 8
            + (ES2 in ctrl) * 4
            + (ES1 in ctrl) * 2
            + (ES0 in ctrl) * 1
        )
        a = self._alu_first_operand( ctrl )
        b = self._alu_second_operand( ctrl )
        return _74181_logic( a, b, s, (EM in ctrl), (EC in ctrl) and self.carry )

    def _shifter( self, ctrl ):
        a = self._alu_first_operand( ctrl )
        b = self._alu_second_operand( ctrl )
        if b & 0x80: # Left
            result = a << (b & 0x07)
        else: # Right
            result = a >> (b & 0x07)
        return result & 0xff

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

    def sd( self, d ):
        self._emit( 0x10 + d )

    def si( self, d ):
        self._emit( 0x20 + d )

    def ld( self, d ):
        self._emit( 0x30 + d )

    def li( self, d ):
        self._emit( 0x40 + d )

    def lsl( self, d ):
        self._emit( 0x50 + d )

    def lsr( self, d ):
        self._emit( 0x58 + d )

    def jv( self, d ):
        self._emit( 0x60 + d )

    def jt( self, d ):
        self._emit( 0x70 + d )

    def add( self ):
        self._emit( 0xa0 )

    def adc( self ):
        self._emit( 0xa1 )

    def sbc( self ):
        self._emit( 0xa3 )

    def a2dp( self ):
        self._emit( 0xb8 )

    def dp2a( self ):
        self._emit( 0xb9 )

    def a2b( self ):
        self._emit( 0xba )

    def xchg( self ):
        self._emit( 0xbb )

    def l2a( self ):
        self._emit( 0xbe )

    def a2l( self ):
        self._emit( 0xbc )

    def split( self ):
        self._emit( 0xbf )

    def ret( self ):
        self._emit( 0xb4 )

    def c2a( self ):
        self._emit( 0xb5 )

    def link( self, n ):
        assert 0 <= n < 4
        self._emit( 0xb0 + n )

    def halt( self ):
        self._emit( 0xbd )

    def scc( self, d ):
        self._emit( 0xc0 + d )

    def scs( self, d ):
        self._emit( 0xd0 + d )

    def dpe( self, d ):
        self._emit( 0xe0 + d )

    def dpf( self, d ):
        self._emit( 0xf0 + d )

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
        #self.cpu = CPU()
        self.cpu = Interpreter()
        self.ram = bytearray( 256 )
        self.cpu.ram = self.ram
        self.asm = Assembler( self.ram )
        self.asm.loc = 16

    def test_split( self ):
        for a in [0x00, 0x5a, 0xa5, 0xef, 0xfe]:
            with self.subTest(a=a):
                self.cpu.a = a
                self.cpu.pc = 16
                self.asm.loc = 16
                self.asm.split()
                self.cpu.step()
                self.assertEqual( a & 0xf0, self.cpu.a )
                self.assertEqual( a & 0x0f, self.cpu.b )

    def test_sbc( self ):
        for a in [0, 1, 2, 253, 254, 255]:
            for b in [0, 1, 2, 253, 254, 255]:
                for carry in [0,1]:
                    with self.subTest(a=a,b=b,carry=carry):
                        self.cpu.a = a
                        self.cpu.b = b
                        self.cpu.carry = carry
                        self.cpu.pc = 16
                        self.asm.loc = 16
                        self.asm.sbc()
                        self.cpu.step()
                        expected = (a - b - 1 + carry) & 0x1ff
                        self.assertEqual( expected & 0xff, self.cpu.a )
                        self.assertEqual( expected >> 8, self.cpu.carry )

    def _fib( self ):
        self.asm.imm( 1 )
        self.asm.a2b()
        self.asm.imm( 1 )
        self.asm.link( 0 )
        self.asm.xchg()
        self.asm.add()
        self.asm.scs( 1 )
        self.asm.ret()
        self.asm.halt()

    def _meta_interpreter( self ):
        # Data fields from DP=0
        F_PC = 0
        F_A  = 1
        F_B  = 2
        F_DP = 3
        F_CARRY  = 4
        F_HALTED = 5
        F_MAIN_LOOP = 8
        F_HANDLERS_MAIN = 9
        F_HANDLERS_AX = 10
        F_HANDLERS_BX = 11

        ### CODE ###
        self.asm.loc = 0x10

        MAIN_LOOP = self.asm.loc
        # Fetch
        self.asm.li( PC )
        # Call handler
        self.asm.split()
        self.asm.lsr( 4 )
        self.asm.xchg()   # A = lo4, B = hi4
        self.asm.df( F_HANDLERS_MAIN )
        self.asm.link( 1 )
        self.asm.jt( 0 )
        # Reset DP and loop
        self.asm.imm( 0 )
        self.asm.a2dp()
        self.asm.jv( MAIN_LOOP )
        ## Data
        self.ram[ F_PC ] = MAIN_LOOP
        self.ram[ F_MAIN_LOOP ] = MAIN_LOOP
        self.ram[ F_HANDLERS_MAIN ] = 0x20
        self.ram[ F_HANDLERS_AX ] = 0x30
        self.ram[ F_HANDLERS_BX ] = 0x40

        H_IMM = self.asm.loc
        self.asm.sd( F_A )
        self.asm.ret()

        H_A2B = self.asm.loc
        self.asm.imm( 0 )
        self.asm.a2dp()
        self.asm.ld( F_A )
        self.asm.sd( F_B )
        self.asm.ret()

        H_LINK = self.asm.loc
        self.asm.xchg()
        self.asm.imm( 0 )
        self.asm.a2dp()
        self.asm.ld( F_PC )
        self.asm.add()
        self.asm.sd( F_LR )
        self.asm.ret()

        H_XCHG = self.asm.loc
        self.asm.imm( 0 )
        self.asm.a2dp()
        self.asm.ld( F_A )
        self.asm.xchg()
        self.asm.ld( F_B )
        self.asm.st( F_A )
        self.asm.xchg()
        self.asm.st( F_B )
        self.asm.ret()

        H_ADD = self.asm.loc
        self.asm.imm( 0 )
        self.asm.a2dp()
        self.asm.ld( F_A )
        self.asm.xchg()
        self.asm.ld( F_B )
        self.asm.add()
        self.asm.st( F_A )
        self.asm.c2a()
        self.asm.st( F_CARRY )
        self.asm.ret()

        H_ADC = self.asm.loc
        self.asm.imm( 0 )
        self.asm.a2dp()
        self.asm.ld( F_A )
        self.asm.xchg()
        self.asm.ld( F_B )
        self.asm.add()
        self.asm.ld( F_C )
        self.asm.adc()
        self.asm.st( F_A )
        self.asm.c2a()
        self.asm.st( F_CARRY )
        self.asm.ret()

        H_SCS = self.asm.loc
        self.asm.imm( 0 )
        self.asm.a2dp()
        self.asm.ld( F_C )
        self.asm.xchg()
        self.asm.ld( F_PC )
        self.asm.adc()
        self.asm.ret()

        H_SD = self.asm.loc
        H_SI = self.asm.loc
        H_LD = self.asm.loc
        H_LI = self.asm.loc
        H_SH = self.asm.loc
        H_JV = self.asm.loc
        H_JT = self.asm.loc
        H_BX = self.asm.loc
        H_SCC = self.asm.loc
        H_DPE = self.asm.loc
        H_DPF = self.asm.loc
        H_A2DP = self.asm.loc
        H_DP2A = self.asm.loc
        H_L2A = self.asm.loc
        H_A2L = self.asm.loc
        H_SPLIT = self.asm.loc
        H_RET = self.asm.loc
        H_JDP = self.asm.loc
        H_HALT = self.asm.loc
        # Not yet implemented
        self.asm.halt()

        AX_TABLE = self.asm.loc
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()
        self.asm.halt()

        H_OPCODES_AX = self.asm.loc
        self.asm.imm( 0 )
        self.asm.a2dp()
        self.asm.xchg()   # B = lo4
        self.asm.df( F_HANDLERS_AX )
        self.asm.jt( 0 )

        BX_TABLE = self.asm.loc
        self.asm.imm( H_LINK )
        self.asm.imm( H_LINK )
        self.asm.imm( H_LINK )
        self.asm.imm( H_LINK )
        self.asm.imm( H_RET )
        self.asm.imm( H_C2A )
        self.asm.imm( H_ADD )
        self.asm.imm( H_ADC )
        self.asm.imm( H_A2DP )
        self.asm.imm( H_DP2A )
        self.asm.imm( H_A2B )
        self.asm.imm( H_XCHG )
        self.asm.imm( H_A2L )
        self.asm.imm( H_HALT )
        self.asm.imm( H_L2A )
        self.asm.imm( H_SPLIT )

        H_OPCODES_BX = self.asm.loc
        self.asm.imm( 0 )
        self.asm.a2dp()
        self.asm.xchg()   # B = lo4
        self.asm.df( F_HANDLERS_BX )
        self.asm.jt( 0 )

    def _execute( self ):
        while not self.cpu.halted:
            self.cpu.step()

class Interpreter(ArchitectedRegisters):
    """Like CPU but closer to what the software will look like, rather than the hardware"""

    def __init__( self ):
        super().__init__()
        # TODO: Virtualize memory
        self._handlers_main = [
            self._imm,
            self._sd,
            self._si,
            self._ld,

            self._li,
            self._sh,
            self._jv,
            self._jt,

            self._UNDEF,
            self._UNDEF,
            self._ax,
            self._bx,

            self._scc,
            self._scs,
            self._dpe,
            self._dpf,
        ]
        self._handlers_ax = [
            self._add,
            self._adc,
            self._UNDEF,
            self._sbc,

            self._UNDEF,
            self._UNDEF,
            self._UNDEF,
            self._UNDEF,

            self._UNDEF,
            self._UNDEF,
            self._UNDEF,
            self._UNDEF,

            self._UNDEF,
            self._UNDEF,
            self._UNDEF,
            self._UNDEF,
        ]
        self._handlers_bx = [
            self._link,
            self._link,
            self._link,
            self._link,

            self._ret,
            self._c2a,
            self._UNDEF,
            self._UNDEF,

            self._a2dp,
            self._dp2a,
            self._a2b,
            self._xchg,

            self._a2l,
            self._halt,
            self._l2a,
            self._split,
        ]

    def step( self ):
        debug( "Step instruction=%x" % ( self.ram[ self.pc ] ) )
        self._debug()
        dp = self._handlers_main
        instr = self.ram[ self.pc ]
        self.pc += 1
        hi4 = instr >> 4
        lo4 = instr & 0x0f
        dp[ hi4 ]( lo4 )

    def _imm( self, lo4 ):
        self.a = lo4

    def _sd( self, lo4 ):
        self.ram[ self.dp + lo4 ] = self.a

    def _si( self, lo4 ):
        addr = self.ram[ self.dp + lo4 ]
        ram[ addr ] = self.a

    def _ld( self, lo4 ):
        self.a = self.ram[ self.dp + lo4 ]

    def _li( self, lo4 ):
        addr = self.ram[ self.dp + lo4 ]
        self.a = ram[ addr ]

    def _sh( self, lo4 ):
        distance = lo4 - 8
        if distance < 0:
            self.a = self.a << (-distance)
        else:
            self.a = self.a >> distance

    def _jv( self, lo4 ):
        addr = self.ram[ self.dp + lo4 ]
        self.pc = self.ram[ addr ]

    def _jt( self, lo4 ):
        addr = self.ram[ self.dp + self.b ]
        self.pc = self.ram[ addr ]

    def _ax( self, lo4 ):
        dp = self._handlers_ax
        dp[ lo4 ]( lo4 )

    def _bx( self, lo4 ):
        dp = self._handlers_bx
        dp[ lo4 ]( lo4 )

    def _scc( self, lo4 ):
        if not self.c:
            self.pc += lo4

    def _scs( self, lo4 ):
        if self.carry:
            self.pc += lo4

    def _dpe( self, lo4 ):
        self.dp = self.ram[ self.dp + self.b + lo4 ]

    def _dpf( self, lo4 ):
        self.dp = self.ram[ self.dp + lo4 ]

    def _a2dp( self, lo4 ):
        self.dp = self.a

    def _dp2a( self, lo4 ):
        self.a = self.dp

    def _a2b( self, lo4 ):
        self.b = self.a

    def _xchg( self, lo4 ):
        temp = self.a
        self.a = self.b
        self.b = temp

    def _l2a( self, lo4 ):
        self.a = self.lr

    def _a2l( self, lo4 ):
        self.lr = self.a

    def _split( self, lo4 ):
        self.b = self.a & 0x0f
        self.a = self.a ^ self.b

    def _add( self, lo4 ):
        result = self.a + self.b
        self.a = result & 0xff
        self.carry = result >> 8

    def _adc( self, lo4 ):
        result = self.a + self.b + c
        self.a = result & 0xff
        self.carry = result >> 8

    def _sbc( self, lo4 ):
        result = (self.a - self.b - 1 + self.carry) & 0x1ff
        self.a = result & 0xff
        self.carry = result >> 8

    def _link( self, lo4 ):
        self.lr = self.pc + lo4

    def _ret( self, lo4 ):
        self.pc = self.lr

    def _c2a( self, lo4 ):
        self.a = self.carry

    def _halt( self, lo4 ):
        self.halted = True

    def _UNDEF( self, lo4 ):
        raise ValueError( "No handler for %x" % lo4 )

def main():
    t = TestMath()
    t.setUp()
    t._fib()
    t._execute()

main()
