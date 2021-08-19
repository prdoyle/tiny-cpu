#! /usr/bin/env python3

from unittest import TestCase
import sys

def debug(*args, **kwargs):
    if True:
        print(*args, file=sys.stdout, **kwargs)

def ff(n):
    return n & 0xff

class Assembler:

    def __init__( self, ram ):
        self.ram = ram
        self.loc = 0

    def emit( self, n ):
        self.ram[ self.loc ] = n
        self.loc += 1

    def imm( self, n ): self.emit( 0x00 + n )
    def lbf( self, n ): self.emit( 0x10 + n )
    def lae( self, n ): self.emit( 0x20 + n )
    def laf( self, n ): self.emit( 0x30 + n )
    def spbf( self, n ): self.emit( 0x40 + n )
    def sbf( self, n ): self.emit( 0x50 + n )
    def sae( self, n ): self.emit( 0x60 + n )
    def saf( self, n ): self.emit( 0x70 + n )
    def scc( self, n ): self.emit( 0x80 + n )
    def scs( self, n ): self.emit( 0x90 + n )
    def ap( self, n ): self.emit( 0xc0 + n )
    def pbf( self, n ): self.emit( 0xd0 + n )
    def pae( self, n ): self.emit( 0xe0 + n )
    def paf( self, n ): self.emit( 0xf0 + n )
    def link( self, n ): self.emit( 0xa0 + n )
    def px( self ): self.emit( 0xa4 )
    def plx( self ): self.emit( 0xa5 )
    def sbc( self ): self.emit( 0xa6 )
    def sub( self ): self.emit( 0xa7 )
    def c2a( self ): self.emit( 0xa8 )
    def rx( self ): self.emit( 0xa9 )
    def ax( self ): self.emit( 0xaa )
    def ra2b( self ): self.emit( 0xab )
    def adc( self ): self.emit( 0xac )
    def add( self ): self.emit( 0xad )
    def padd( self ): self.emit( 0xae )
    def cl( self, n ): self.emit( 0xb0 + n )
    def ret( self ): self.emit( 0xb4 )
    def cleb( self ): self.emit( 0xb5 )
    def clebc( self ): self.emit( 0xb6 )
    def clb( self ): self.emit( 0xb7 )
    def p2r( self ): self.emit( 0xb8 )
    def pb2a( self ): self.emit( 0xba )
    def jp( self ): self.emit( 0xbc )
    def halt( self ): self.emit( 0xbd )
    def lsr( self ): self.emit( 0xbe )
    def split( self ): self.emit( 0xbf )
    def data( self, n ): self.emit( n )

def decode( instr, consumer ):
    main_handlers = [
        lambda n: consumer.imm( n ),
        lambda n: consumer.lbf( n ),
        lambda n: consumer.lae( n ),
        lambda n: consumer.laf( n ),

	lambda n: consumer.spbf( n ),
	lambda n: consumer.sbf( n ),
	lambda n: consumer.sae( n ),
	lambda n: consumer.saf( n ),

	lambda n: consumer.scc( n ),
	lambda n: consumer.scs( n ),
	lambda n: ax_handlers[ n ]( n ),
	lambda n: bx_handlers[ n ]( n ),

	lambda n: consumer.ap( n ),
	lambda n: consumer.pbf( n ),
	lambda n: consumer.pae( n ),
	lambda n: consumer.paf( n ),
    ]
    ax_handlers = [
	lambda n: consumer.link( n ),
	lambda n: consumer.link( n ),
	lambda n: consumer.link( n ),
	lambda n: consumer.link( n ),

	lambda n: consumer.px(),
	lambda n: consumer.plx(),
	lambda n: consumer.sbc(),
	lambda n: consumer.sub(),

	lambda n: consumer.c2a(),
	lambda n: consumer.rx(),
	lambda n: consumer.ax(),
	lambda n: consumer.ra2b(),

	lambda n: consumer.adc(),
	lambda n: consumer.add(),
	lambda n: consumer.padd(),
	lambda n: consumer.data( instr ),
    ]
    bx_handlers = [
	lambda n: consumer.cl( n ),
	lambda n: consumer.cl( n ),
	lambda n: consumer.cl( n ),
	lambda n: consumer.cl( n ),

	lambda n: consumer.ret(),
	lambda n: consumer.cleb(),
	lambda n: consumer.clebc(),
	lambda n: consumer.clb(),

	lambda n: consumer.p2r(),
	lambda n: consumer.data( instr ),
	lambda n: consumer.pb2a(),
	lambda n: consumer.data( instr ),

	lambda n: consumer.jp(),
	lambda n: consumer.halt(),
	lambda n: consumer.lsr(),
	lambda n: consumer.split(),
    ]
    hi4 = ff( instr ) >> 4
    lo4 = instr & 0x0F
    main_handlers[ hi4 ]( lo4 )

class Interpreter:

    def __init__( self, ram ):
        self.ram = ram
        self.pc = 0x10
        self.ra = 0
        self.rb = 0
        self.pa = 0
        self.pb = 0
        self.lr = 0
        self.cf = 0
        self.halted = False

    def step( self ):
        if not self.halted:
            instr = self.ram[ self.pc ]
            self.debug()
            debug( "Execute opcode %02x" % instr )
            decode( instr, self )
        return not self.halted

    def debug( self ):
        v = vars( self ).copy()
        del v["ram"]
        for k in list( v.keys() ):
            if k[0] == "_":
                del v[k]
        debug( "| state=%s" % ( v ) )

    # Helpers

    def _next( self ):
        self.pc = ff( self.pc+1 )

    def _bf( self, n ):
        return ff( self.pb + n )

    def _ae( self, n ):
        return ff( self.pa + self.rb + n )

    def _af( self, n ):
        return ff( self.pa + n )

    # Handlers

    def imm( self, n ):
        self._next()
        self.ra = ff( n )

    def lbf( self, n ):
        self._next()
        self.ra = self.ram[ self._bf(n) ]

    def lae( self, n ):
        self._next()
        self.ra = self.ram[ self._ae(n) ]

    def laf( self, n ):
        self._next()
        self.ra = self.ram[ self._af(n) ]

    def spbf( self, n ):
        self._next()
        self.ram[ self._bf(n) ] = self.pa

    def sbf( self, n ):
        self._next()
        self.ram[ self._bf(n) ] = self.ra

    def sae( self, n ):
        self._next()
        self.ram[ self._ae(n) ] = self.ra

    def saf( self, n ):
        self._next()
        self.ram[ self._af(n) ] = self.ra

    def scc( self, n ):
        self._next()
        if not self.cf:
            self.pc = ff( self.pc + n )

    def scs( self, n ):
        self._next()
        if self.cf:
            self.pc = ff( self.pc + n )

    def ap( self, n ):
        self._next()
        self.pa = ff( self.pa + n )

    def pbf( self, n ):
        self._next()
        self.pa = self.ram[ self._bf(n) ]

    def pae( self, n ):
        self._next()
        self.pa = self.ram[ self._ae(n) ]

    def paf( self, n ):
        self._next()
        self.pa = self.ram[ self._af(n) ]

    def link( self, n ):
        self._next()
        self.lr = ff( self.pc + n )

    def px( self ):
        self._next()
        ( self.pa, self.pb ) = ( self.pb, self.pa )

    def plx( self ):
        self._next()
        ( self.pa, self.lr ) = ( self.lr, self.pa )

    def sbc( self ):
        self._next()
        result = ( self.ra + (~self.rb) + self.cf ) & 0x1ff
        self.ra = ff( result )
        self.cf = result >> 8

    def sub( self ):
        self._next()
        result = ( self.ra + (~self.rb) + 1 ) & 0x1ff
        self.ra = ff( result )
        self.cf = result >> 8

    def c2a( self ):
        self._next()
        self.ra = self.cf

    def rx( self ):
        self._next()
        ( self.ra, self.rb ) = ( self.rb, self.ra )

    def ax( self ):
        self._next()
        ( self.pa, self.pb ) = ( self.pb, self.pa )

    def ra2b( self ):
        self._next()
        self.rb = self.ra

    def adc( self ):
        self._next()
        result = ( self.ra + self.rb + self.cf ) & 0x1ff
        self.ra = ff( result )
        self.cf = result >> 8

    def add( self ):
        self._next()
        result = ( self.ra + self.rb ) & 0x1ff
        self.ra = ff( result )
        self.cf = result >> 8

    def padd( self ):
        self._next()
        result = ( self.pa + self.rb ) & 0x1ff
        self.pa = ff( result )

    def cl( self, n ):
        self._next()
        result = ( self.ra + (~n) + 1 ) & 0x1ff
        self.cf = result >> 8

    def ret( self ):
        self.pc = self.lr

    def cleb( self ):
        self._next()
        result = ( self.ra + (~self.rb) ) & 0x1ff
        self.cf = result >> 8

    def clebc( self ): # SBC but discard result
        self._next()
        result = ( self.ra + (~self.rb) + self.cf ) & 0x1ff
        self.cf = result >> 8

    def clb( self ): # SUB but discard result
        self._next()
        result = ( self.ra + (~self.rb) + 1 ) & 0x1ff
        self.cf = result >> 8

    def p2r( self ):
        self._next()
        self.ra = self.pa

    def pb2a( self ):
        self._next()
        self.pa = self.pb

    def jp( self ):
        self.pc = self.pa

    def halt( self ):
        self.halted = True

    def lsr( self ):
        d = self.rb
        if d >= 8:
            d = d-8
            self.ra = ff( self.ra << d )
        else:
            self.ra = ff( self.ra >> d )

    def split( self ):
        self._next()
        self.rb = self.ra & 0x0F
        self.ra = self.ra >> 4

    def data( self, n ):
        raise ValueError("Unimplemented opcode: %x" % n )

def generate_fib( asm ):
    asm.imm( 1 )
    asm.ra2b()
    asm.link( 0 )
    asm.add()
    asm.scs( 2 )
    asm.rx()
    asm.ret()
    asm.halt()

def generate_all( asm ):
    for b in range(256):
        asm.data( b )

def generate_meta_interpreter( asm ):
    R_PC = 0
    R_RA = 1
    R_RB = 2
    R_PA = 3
    R_PB = 4
    R_LR = 5
    R_CF = 6

    H_MAIN = 9
    H_AX   = 0xA
    H_BX   = 0xB

    V_MAIN  = 12
    V_RET   = 13
    V ALU   = 14
    V_CARRY = 15

    asm.loc = 0x20

    MAIN_LOOP = asm.loc
    asm.pbf( R_PC )
    asm.laf( 0 )         # Load instruction
    asm.ap( 1 )
    asm.spbf( R_PC )     # Advance PC

    asm.split()
    asm.rx()             # RA = lo4, RB = hi4
    asm.pbf( H_MAIN )
    asm.pae( 0 )         # PA = handler
    asm.rx()             # RA = hi4, RB = lo4
    asm.link( 1 )
    asm.jp()
    MAIN_RETURN = asm.loc
    asm.pbf( V_MAIN )
    asm.jp()

    PREP_ALU_REGS = asm.loc
    asm.lbf( R_CF )
    asm.rx()
    asm.imm( 0 )
    asm.clb()            # CF loaded
    asm.lbf( R_RB )
    asm.rx()
    asm.lbf( R_RA )      # RA and RB loaded
    asm.ret()

    SET_CARRY_AND_RETURN = asm.loc
    asm.c2a()
    asm.sbf( R_CF )
    asm.pbf( V_RET )
    asm.jp()

    ## Opcode implementations

    O_IMM = asm.loc
    asm.sbf( R_RA )
    asm.ret()

    O_LBF = asm.loc
    asm.pbf( R_PB )
    asm.pae( 0 )
    asm.spbf( R_RA )
    asm.ret()

    O_LAE = asm.loc
    asm.lbf( R_PA )
    asm.add()
    asm.rx()             # RB is PA+imm4
    asm.pbf( R_RB )      # PA is RB
    asm.pae( 0 )         # PA is [PA+RB+imm4]
    asm.spbf( R_RA )
    asm.ret()

    O_LAF = asm.loc
    asm.pbf( R_PA )
    asm.pae( 0 )
    asm.spbf( R_RA )
    asm.ret()

    O_SPBF = asm.loc
    asm.pbf( R_PB )
    asm.lbf( R_PA )      # RA is PA
    asm.sae( 0 )         # Store to [PB + imm4]
    asm.ret()

    O_SBF = asm.loc
    asm.pbf( R_PB )
    asm.lbf( R_RA )      # RA is RA
    asm.sae( 0 )         # Store to [PB + imm4]
    asm.ret()

    O_SAE = asm.loc
    asm.lbf( R_PA )
    asm.add()
    asm.rx()             # RB is PA+imm4
    asm.pbf( R_RB )      # PA is RB
    asm.lbf( R_RA )
    asm.sae( 0 )         # Store to [PA+RB+imm4]
    asm.ret()

    O_SAF = asm.loc
    asm.pbf( R_PA )
    asm.lbf( R_RA )      # RA is RA
    asm.sae( 0 )         # Store to [PA + imm4]
    asm.ret()


class RoundTripTest( TestCase ):
    
    def test( self ):
        for initializer in [ generate_fib, generate_all ]:
            with self.subTest(initializer=initializer.__name__):
                original = bytearray( 256 )
                asm = Assembler( original )
                initializer( asm )
                dup = bytearray( 256 )
                asm = Assembler( dup )
                for byte in original:
                    decode( byte, asm )
                self.assertEqual( original, dup )

def main():
    ram = bytearray( 256 )
    asm = Assembler( ram )
    asm.loc = 0x10
    generate_fib( asm )
    interpreter = Interpreter( ram )
    while interpreter.step():
        pass

if __name__ == "__main__":
    main()
