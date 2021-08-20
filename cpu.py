#! /usr/bin/env python3

from unittest import TestCase
import sys

def debug(*args, **kwargs):
    if True:
        print(*args, file=sys.stdout, **kwargs)

def ff(n):
    return n & 0xff

def dump_ram( ram ):
    debug( "".join([ "%02x"%n for n in range(16) ]) )
    debug( ram.hex( "\n", 16 ) )

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
    def ap( self, n ): self.emit( 0xc0 + n ) # Same as jbf
    def jbf( self, n ): self.emit( 0xc0 + n ) # Same as ap
    def pbf( self, n ): self.emit( 0xd0 + n )
    def pae( self, n ): self.emit( 0xe0 + n )
    def call( self, n ): self.emit( 0xf0 + n )

    def link( self, n ): self.emit( 0xa0 + n )
    def padd( self ): self.emit( 0xa3 )
    def adc( self ): self.emit( 0xa4 )
    def add( self ): self.emit( 0xa5 )
    def sbc( self ): self.emit( 0xa6 )
    def sub( self ): self.emit( 0xa7 )
    def c2a( self ): self.emit( 0xa8 )
    def rx( self ): self.emit( 0xa9 )
    def ax( self ): self.emit( 0xaa )
    def ra2b( self ): self.emit( 0xab )

    def cle( self, n ): self.emit( 0xb0 + n )
    def ret( self ): self.emit( 0xb4 )
    def cleb( self ): self.emit( 0xb5 )
    def clebc( self ): self.emit( 0xb6 )
    def clb( self ): self.emit( 0xb7 )
    def p2r( self ): self.emit( 0xb8 )
    def lsr( self ): self.emit( 0xb9 )
    def pb2a( self ): self.emit( 0xba )
    def split( self ): self.emit( 0xbb )
    def jp( self ): self.emit( 0xbc )
    def halt( self ): self.emit( 0xbd )
    def data( self, n ): self.emit( n )

class Disassembler:

    def __init__( self ):
        pass

    def _format( self, opcode, operand=None ):
        if operand == None:
            result = f"{ opcode.upper() }"
        else:
            result = f"{ opcode.upper() } { operand }"
        return result

    def imm( self, n ): return self._format( "imm", n )
    def lbf( self, n ): return self._format( "lbf", n )
    def lae( self, n ): return self._format( "lae", n )
    def laf( self, n ): return self._format( "laf", n )
    def spbf( self, n ): return self._format( "spbf", n )
    def sbf( self, n ): return self._format( "sbf", n )
    def sae( self, n ): return self._format( "sae", n )
    def saf( self, n ): return self._format( "saf", n )
    def scc( self, n ): return self._format( "scc", n )
    def scs( self, n ): return self._format( "scs", n )
    def ap( self, n ): return self._format( "ap", n )
    def jbf( self, n ): return self._format( "jbf", n )
    def pbf( self, n ): return self._format( "pbf", n )
    def pae( self, n ): return self._format( "pae", n )
    def call( self, n ): return self._format( "call", n )

    def link( self, n ): return self._format( "link", n )
    def adc( self ): return self._format( "adc" )
    def add( self ): return self._format( "add" )
    def sbc( self ): return self._format( "sbc" )
    def sub( self ): return self._format( "sub" )
    def c2a( self ): return self._format( "c2a" )
    def rx( self ): return self._format( "rx" )
    def ax( self ): return self._format( "ax" )
    def ra2b( self ): return self._format( "ra2b" )
    def padd( self ): return self._format( "padd" )

    def cle( self, n ): return self._format( "cle", n )
    def ret( self ): return self._format( "ret" )
    def cleb( self ): return self._format( "cleb" )
    def clebc( self ): return self._format( "clebc" )
    def clb( self ): return self._format( "clb" )
    def p2r( self ): return self._format( "p2r" )
    def lsr( self ): return self._format( "lsr" )
    def pb2a( self ): return self._format( "pb2a" )
    def split( self ): return self._format( "split" )
    def jp( self ): return self._format( "jp" )
    def halt( self ): return self._format( "halt" )
    def data( self, n ): return self._format( "data", n )

def decode( instr, consumer ):
    def ap_or_jbf( n ):
        if n <= 2:
            consumer.ap( n )
        else:
            consumer.jbf( n )

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

	lambda n: ap_or_jbf( n ),
	lambda n: consumer.pbf( n ),
	lambda n: consumer.pae( n ),
	lambda n: consumer.call( n ),
    ]
    ax_handlers = [
	lambda n: consumer.link( n ),
	lambda n: consumer.link( n ),
	lambda n: consumer.link( n ),
	lambda n: consumer.padd(),

	lambda n: consumer.adc(),
	lambda n: consumer.add(),
	lambda n: consumer.sbc(),
	lambda n: consumer.sub(),

	lambda n: consumer.c2a(),
	lambda n: consumer.rx(),
	lambda n: consumer.ax(),
	lambda n: consumer.ra2b(),

	lambda n: consumer.data( instr ),
	lambda n: consumer.data( instr ),
	lambda n: consumer.data( instr ),
	lambda n: consumer.data( instr ),
    ]
    bx_handlers = [
	lambda n: consumer.cle( n ),
	lambda n: consumer.cle( n ),
	lambda n: consumer.cle( n ),
	lambda n: consumer.cle( n ),

	lambda n: consumer.ret(),
	lambda n: consumer.cleb(),
	lambda n: consumer.clebc(),
	lambda n: consumer.clb(),

	lambda n: consumer.p2r(),
	lambda n: consumer.lsr(),
	lambda n: consumer.pb2a(),
	lambda n: consumer.split(),

	lambda n: consumer.jp(),
	lambda n: consumer.halt(),
	lambda n: consumer.data( instr ),
	lambda n: consumer.data( instr ),
    ]
    hi4 = ff( instr ) >> 4
    lo4 = instr & 0x0F
    return main_handlers[ hi4 ]( lo4 )

class Interpreter:

    def __init__( self, ram, start_pc ):
        self.ram = ram
        self.pc = start_pc
        self.ra = 0
        self.rb = 0
        self.pa = 0
        self.pb = 0
        self.lr = 0
        self.cf = 0
        self.halted = False
        self._disassembler = Disassembler()

    def step( self ):
        if not self.halted:
            instr = self.ram[ self.pc ]
            self.debug()
            debug( "Execute opcode %02x: %s" % ( instr, decode( instr, self._disassembler ) ) )
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
        raise ValueError("LAE is not implemented!")
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

    def jbf( self, n ):
        self._next()
        self.pc = self.ram[ self._bf(n) ]

    def pbf( self, n ):
        self._next()
        self.pa = self.ram[ self._bf(n) ]

    def pae( self, n ):
        self._next()
        self.pa = self.ram[ self._ae(n) ]

    def call( self, n ): # Same as link(1);jbf(n)
        self.lr = ff( self.pc + 1 ) # After the call
        self.pc = self.ram[ self._bf(n) ]

    def link( self, n ):
        self._next()
        self.lr = ff( self.pc + n )

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

    def padd( self ):
        self._next()
        result = ( self.pa + self.rb ) & 0x1ff
        self.pa = ff( result )

    def cle( self, n ):
        self._next()
        result = ( self.ra + (~n) ) & 0x1ff
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

    def lsr( self ):
        d = self.rb
        if d >= 8:
            d = d-8
            self.ra = ff( self.ra << d )
        else:
            self.ra = ff( self.ra >> d )

    def pb2a( self ):
        self._next()
        self.pa = self.pb

    def split( self ):
        self._next()
        self.rb = self.ra >> 4
        self.ra = self.ra & 0x0F

    def jp( self ):
        self.pc = self.pa

    def halt( self ):
        self.halted = True

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
    ## Data field offsets from pb

    R_PC = 0
    R_RA = 1
    R_RB = 2
    R_PA = 3
    R_PB = 4
    R_LR = 5
    R_CF = 6

    H_MAIN = 8
    H_AX   = 9
    H_BX   = 10

    V_MAIN  = 11
    V_ALU   = 12
    V_CFRA  = 13
    V_CARRY = 14

    ## Entry point

    asm.loc = 0x18 # CHEESE

    MAIN_LOOP = asm.loc
    asm.pbf( R_PC )
    asm.laf( 0 )         # Load instruction
    asm.ap( 1 )
    asm.spbf( R_PC )     # Advance PC

    asm.split()          # RA = lo4, RB = hi4
    asm.pbf( H_MAIN )
    asm.pae( 0 )         # PA = handler
    asm.rx()             # RA = hi4, RB = lo4
    asm.link( 1 )
    asm.jp()
    MAIN_RETURN = asm.loc
    asm.jbf( V_MAIN )

    PREP_ALU_REGS = asm.loc
    asm.lbf( R_CF )
    asm.rx()
    asm.imm( 0 )
    asm.clb()            # CF loaded
    asm.lbf( R_RB )
    asm.rx()
    asm.lbf( R_RA )      # RA and RB loaded
    asm.ret()

    SET_CARRY_AND_RA_THEN_RETURN = asm.loc
    asm.sbf( R_RA )
    SET_CARRY_THEN_RETURN = asm.loc
    asm.c2a()
    asm.sbf( R_CF )
    asm.jbf( V_MAIN )

    ## Macros

    def EXCHANGE( r1, r2 ):
        asm.lbf( r1 )
        asm.pbf( r2 )
        asm.spbf( r1 )
        asm.sbf( r2 )

    def PREP_ALU():
        """Call PREP_ALU_REGS to get ra, rb, and cf fields into actual registers"""
        #asm.pbf( V_ALU )
        #asm.link( 1 )
        #asm.jp()
        asm.call( V_ALU )

    ## Opcode handlers

    O_IMM = asm.loc
    asm.rx()
    asm.sbf( R_RA )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_IMM", O_IMM, asm.loc - O_IMM ) )

    O_LBF = asm.loc
    asm.pbf( R_PB )
    asm.pae( 0 )
    asm.spbf( R_RA )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_LBF", O_LBF, asm.loc - O_LBF ) )

    O_LAE = asm.loc
    # CHEAT! Save the bytes for an instruction we're not using
    if True:
        asm.halt()
    else:
        asm.lbf( R_PA )
        asm.add()
        asm.rx()             # RB is PA+imm4
        asm.pbf( R_RB )      # PA is RB
        asm.pae( 0 )         # PA is [PA+RB+imm4]
        asm.spbf( R_RA )
        asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_LAE", O_LAE, asm.loc - O_LAE ) )

    O_LAF = asm.loc
    asm.pbf( R_PA )
    asm.pae( 0 )
    asm.spbf( R_RA )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_LAF", O_LAF, asm.loc - O_LAF ) )

    O_SPBF = asm.loc
    asm.pbf( R_PB )
    asm.lbf( R_PA )      # RA is PA
    asm.sae( 0 )         # Store to [PB + imm4]
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_SPBF", O_SPBF, asm.loc - O_SPBF ) )

    O_SBF = asm.loc
    asm.pbf( R_PB )
    asm.lbf( R_RA )      # RA is RA
    asm.sae( 0 )         # Store to [PB + imm4]
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_SBF", O_SBF, asm.loc - O_SBF ) )

    O_SAE = asm.loc
    asm.lbf( R_PA )
    asm.add()
    asm.rx()             # RB is PA+imm4
    asm.pbf( R_RB )      # PA is RB
    asm.lbf( R_RA )
    asm.sae( 0 )         # Store to [PA+RB+imm4]
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_SAE", O_SAE, asm.loc - O_SAE ) )

    O_SAF = asm.loc
    asm.pbf( R_PA )
    asm.lbf( R_RA )      # RA is RA
    asm.sae( 0 )         # Store to [PA + imm4]
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_SAF", O_SAF, asm.loc - O_SAF ) )

    O_SCC = asm.loc
    asm.lbf( R_CF )
    asm.cle( 0 )         # CF is ~CF
    asm.scc( 3 )         # So confusing
    asm.pbf( R_PC )
    asm.padd()
    asm.spbf( R_PC )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_SCC", O_SCC, asm.loc - O_SCC ) )

    O_SCS = asm.loc
    asm.lbf( R_CF )
    asm.cle( 0 )         # CF is ~CF
    asm.scs( 3 )         # So confusing
    asm.pbf( R_PC )
    asm.padd()
    asm.spbf( R_PC )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_SCS", O_SCS, asm.loc - O_SCS ) )

    AX_TRAMPOLINE = asm.loc
    asm.pbf( H_AX )
    asm.pae( 0 )
    asm.jp()
    debug( "%s\t%02x\t%d bytes" % ( "AX_TRAMPOLINE", AX_TRAMPOLINE, asm.loc - AX_TRAMPOLINE ) )

    BX_TRAMPOLINE = asm.loc
    asm.pbf( H_BX )
    asm.pae( 0 )
    asm.jp()
    debug( "%s\t%02x\t%d bytes" % ( "BX_TRAMPOLINE", BX_TRAMPOLINE, asm.loc - BX_TRAMPOLINE ) )

    O_AP_JBF = asm.loc
    asm.cle( 3 )
    asm.scs( 4 )
    # JBF
    asm.pbf( R_PB )
    asm.pae( 0 )         # PA is [PB+imm4]
    asm.spbf( R_PC )
    asm.ret()
    # AP
    asm.pbf( R_PA )
    asm.padd()
    asm.spbf( R_PA )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_AP_JBF", O_AP_JBF, asm.loc - O_AP_JBF ) )

    O_PBF = asm.loc
    asm.pbf( R_PB )
    asm.pae( 0 )         # PA is [PB+imm4]
    asm.spbf( R_PA )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_PBF", O_PBF, asm.loc - O_PBF ) )

    O_PAE = asm.loc
    asm.lbf( R_PA )
    asm.add()
    asm.rx()             # RB is PA+imm4
    asm.pbf( R_RB )      # PA is RB
    asm.pae( 0 )         # PA is [PA+RB+imm4]
    asm.spbf( R_PA )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_PAE", O_PAE, asm.loc - O_PAE ) )

    O_CALL = asm.loc
    asm.lbf( R_PC )
    asm.sbf( R_LR )
    asm.pbf( R_PB )
    asm.pae( 0 )
    asm.spbf( R_PC )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_CALL", O_CALL, asm.loc - O_CALL ) )

    O_LINK = asm.loc
    asm.lbf( R_PC )
    asm.add()
    asm.sbf( R_LR )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_LINK", O_LINK, asm.loc - O_LINK ) )

    O_SBC = asm.loc
    PREP_ALU()
    asm.sbc()
    asm.jbf( V_CFRA )
    debug( "%s\t%02x\t%d bytes" % ( "O_SBC", O_SBC, asm.loc - O_SBC ) )

    O_SUB = asm.loc
    PREP_ALU()
    asm.sub()
    asm.jbf( V_CFRA )
    debug( "%s\t%02x\t%d bytes" % ( "O_SUB", O_SUB, asm.loc - O_SUB ) )

    O_C2A = asm.loc
    asm.lbf( R_CF )
    asm.sbf( R_RA )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_C2A", O_C2A, asm.loc - O_C2A ) )

    O_RX = asm.loc
    EXCHANGE( R_RA, R_RB )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_RX", O_RX, asm.loc - O_RX ) )

    O_AX = asm.loc
    EXCHANGE( R_PA, R_RA )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_AX", O_AX, asm.loc - O_AX ) )

    O_RA2B = asm.loc
    asm.lbf( R_RA )
    asm.sbf( R_RB )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_RA2B", O_RA2B, asm.loc - O_RA2B ) )

    O_ADC = asm.loc
    PREP_ALU()
    asm.adc()
    asm.jbf( V_CFRA )
    debug( "%s\t%02x\t%d bytes" % ( "O_ADC", O_ADC, asm.loc - O_ADC ) )

    O_ADD = asm.loc
    PREP_ALU()
    asm.add()
    asm.jbf( V_CFRA )
    debug( "%s\t%02x\t%d bytes" % ( "O_ADD", O_ADD, asm.loc - O_ADD ) )

    O_PADD = asm.loc
    asm.lbf( R_RB )
    asm.rx()
    asm.lbf( R_PA )
    asm.add()
    asm.sbf( R_PA )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_PADD", O_PADD, asm.loc - O_PADD ) )

    O_CLE = asm.loc
    asm.lbf( R_RA )
    asm.cleb()           # B contains the imm4
    asm.jbf( V_CARRY )
    debug( "%s\t%02x\t%d bytes" % ( "O_CLE", O_CLE, asm.loc - O_CLE ) )

    O_RET = asm.loc
    asm.lbf( R_LR )
    asm.sbf( R_PC )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_RET", O_RET, asm.loc - O_RET ) )

    O_CLEB = asm.loc
    PREP_ALU()
    asm.cleb()
    asm.jbf( V_CARRY )
    debug( "%s\t%02x\t%d bytes" % ( "O_CLEB", O_CLEB, asm.loc - O_CLEB ) )

    O_CLEBC = asm.loc
    PREP_ALU()
    asm.clebc()
    asm.jbf( V_CARRY )
    debug( "%s\t%02x\t%d bytes" % ( "O_CLEBC", O_CLEBC, asm.loc - O_CLEBC ) )

    O_CLB = asm.loc
    PREP_ALU()
    asm.clb()
    asm.jbf( V_CARRY )
    debug( "%s\t%02x\t%d bytes" % ( "O_CLB", O_CLB, asm.loc - O_CLB ) )

    O_P2R = asm.loc
    asm.lbf( R_PA )
    asm.sbf( R_RA )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_P2R", O_P2R, asm.loc - O_P2R ) )

    O_PB2A = asm.loc
    asm.lbf( R_PB )
    asm.sbf( R_PA )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_PB2A", O_PB2A, asm.loc - O_PB2A ) )

    O_JP = asm.loc
    asm.lbf( R_PA )
    asm.sbf( R_PC )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_JP", O_JP, asm.loc - O_JP ) )

    O_HALT = asm.loc
    asm.halt()
    debug( "%s\t%02x\t%d bytes" % ( "O_HALT", O_HALT, asm.loc - O_HALT ) )

    O_LSR = asm.loc
    PREP_ALU()
    asm.lsr()
    asm.sbf( R_RA )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_LSR", O_LSR, asm.loc - O_LSR ) )

    O_SPLIT = asm.loc
    PREP_ALU()
    asm.split()
    asm.sbf( R_RA )
    asm.rx()
    asm.sbf( R_RB )
    asm.ret()
    debug( "%s\t%02x\t%d bytes" % ( "O_SPLIT", O_SPLIT, asm.loc - O_SPLIT ) )

    if asm.loc > 0xd0:
        dump_ram( asm.ram )
        raise ValueError( "Code is too big. asm.loc = %d %02x" % ( asm.loc, asm.loc ) )

    ## Handler tables

    MAIN_HANDLERS = asm.loc
    asm.data( O_IMM )
    asm.data( O_LBF )
    asm.data( O_LAE )
    asm.data( O_LAF )

    asm.data( O_SPBF )
    asm.data( O_SBF )
    asm.data( O_SAE )
    asm.data( O_SAF )

    asm.data( O_SCC )
    asm.data( O_SCS )
    asm.data( AX_TRAMPOLINE )
    asm.data( BX_TRAMPOLINE )

    asm.data( O_AP_JBF )
    asm.data( O_PBF )
    asm.data( O_PAE )
    asm.data( O_CALL )

    AX_HANDLERS = asm.loc
    asm.data( O_LINK )
    asm.data( O_LINK )
    asm.data( O_LINK )
    asm.data( O_PADD )

    asm.data( O_ADC )
    asm.data( O_ADD )
    asm.data( O_SBC )
    asm.data( O_SUB )

    asm.data( O_C2A )
    asm.data( O_RX )
    asm.data( O_AX )
    asm.data( O_RA2B )

    BX_HANDLERS = asm.loc
    asm.data( O_CLE )
    asm.data( O_CLE )
    asm.data( O_CLE )
    asm.data( O_CLE )

    asm.data( O_RET )
    asm.data( O_CLEB )
    asm.data( O_CLEBC )
    asm.data( O_CLB )

    asm.data( O_P2R )
    asm.data( O_LSR )
    asm.data( O_PB2A )
    asm.data( O_SPLIT )

    asm.data( O_JP )
    asm.data( O_HALT )

    # Initial state

    BASE_ADDR = 0x00
    asm.loc = BASE_ADDR + R_PC
    asm.data( 0x10 )
    asm.loc = BASE_ADDR + H_MAIN
    asm.data( MAIN_HANDLERS )
    asm.loc = BASE_ADDR + H_AX
    asm.data( AX_HANDLERS )
    asm.loc = BASE_ADDR + H_BX
    asm.data( BX_HANDLERS )
    asm.loc = BASE_ADDR + V_MAIN
    asm.data( MAIN_LOOP )
    asm.loc = BASE_ADDR + V_ALU
    asm.data( PREP_ALU_REGS )
    asm.loc = BASE_ADDR + V_CFRA
    asm.data( SET_CARRY_AND_RA_THEN_RETURN )
    asm.loc = BASE_ADDR + V_CARRY
    asm.data( SET_CARRY_THEN_RETURN )

class RoundTripTest( TestCase ):

    def test( self ):
        for initializer in [ generate_fib, generate_all, generate_meta_interpreter ]:
            with self.subTest(initializer=initializer.__name__):
                original = bytearray( 256 )
                asm = Assembler( original )
                initializer( asm )
                dup = bytearray( 256 )
                asm = Assembler( dup )
                for byte in original:
                    decode( byte, asm )
                self.assertEqual( original, dup )

def interpret_fib():
    ram = bytearray( 256 )
    asm = Assembler( ram )
    asm.loc = 0x10
    generate_fib( asm )
    interpreter = Interpreter( ram, 0x10 )
    while interpreter.step():
        pass

def assemble_meta_interpreter():
    ram = bytearray( 256 )
    asm = Assembler( ram )
    generate_meta_interpreter( asm )
    asm.loc = 0x10
    generate_fib( asm )
    dump_ram( ram )
    return asm

def main():
    asm = assemble_meta_interpreter()
    interpreter = Interpreter( asm.ram, 0x18 )
    for step in range(1,1200):
        debug( f'--## Step {step} ##--' )
        dump_ram( asm.ram )
        if not interpreter.step():
            break
    dump_ram( asm.ram )

if __name__ == "__main__":
    main()
