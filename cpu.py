#! /usr/bin/python
from dataclasses import dataclass
from typing import *

# Idea: an 8-bit processor just powerful enough to implement
# an interpreter for itself. 
#
# First three bits of each instruction:
#
# 000 (0,1) - push (mnemonic: small numbers represent themselves as literals)
# 001 (2,3) - store (mnemonic: 2 = "to")
# 010 (4,5) - load
# 011 (6,7) - get
# 100 (8,9) - jmp
# 101 (a,b) - opcode-only instructions
# 110 (c,d) - skip (conditional jump forward) (mnemonic: c = "clear")
# 111 (e,f) - other

@dataclass
class Instruction:
    name: str
    encoding: int
    handler: Callable[[], None]

    def __str__( self ):
        return "%s [%02x]" % ( self.name, self.encoding )

class State:

    def __init__( self ):
        self.belt = [0] * 4
        self.pc = 0
        self.link = 0
        self.flags = set()
        self.mem = [0] * 32

    def __str__( self ):
        return "Belt: %s\n  PC: %s\nLink: %s\nFlags: %s\nMem: %s" % ( self.belt, self.pc, self.link, list(self.flags), self.mem )

    def push( self, imm ):
        """
        000iiiii

        i = signed 5-bit immediate

        Push i on the belt, shifting all other entries by 1.

        Flags unaffected.
        """
        def go():
            self._push( imm )
        return self._wrap( "push", 0x00 + imm, go );

    def store( self, disp ):
        """
        001ddddd

        d = signed 5-bit displacement

        Store belt[1] to [belt[0] + d].

        Flags unaffected.
        """
        def go():
            mem[address( self.belt[0], disp )] = self.belt[0]
        return self._wrap( store, 0x20 + disp, go )

    def load( self, disp ):
        """
        010ddddd

        d = signed 5-bit displacement

        Load contents of [belt[0] + d] onto belt.

        Flags unaffected.
        """
        def go():
            self._push( mem[address( self.belt[0], disp )] )
        return self._wrap( "load", 0x40 + disp, go )

    def get( self, n ):
        """
        011000nn

        n = unsigned belt index

        Rotate belt items 0..n (inclusive) down by one position,
        leaving item 0 at 1, 1 at 2, ... and item n at 0.

        Note that get 0 is a no-op.

        All other instructions starting with 0110 are reserved.

        Flags unaffected.
        """
        def go():
            belt = self.belt
            self.belt = [belt[ n ]] + belt[ 0:n ] + belt[ n+1: ]
        return self._wrap( "get", 0x60 + n, go ) # mnemonic: 6 = g = "get"

    def drop( self, n ):
        """
        011100nn

        n = unsigned belt index

        I don't really like this one. The intent was to offer a way to discard
        some belt entries so they don't push more desirable entries off the end
        prematurely. So, for example, you could get a "compare" operation by
        doing a "subtract" that discards the result that would have gone on the
        top of the belt; or you could get a destructive add by overwriting the
        top of the belt instead of pushing. However, this "drop" concept
        happens after the fact, after the damage is done, so there's no way to
        recover that lost item, making this rather pointless.

        Shift items from n+1 upward up by one position,
        leaving item n+1 at n, n+2 at n+1, and so on.
        Items before n are unaffected. Item n is discarded.
        The item at the bottom of the belt is set to zero.

        All other instructions starting with 0111 are reserved.

        Flags unaffected.
        """
        def go():
            del self.belt[ n ]
            self.belt.append( 0xdd )
        return self._wrap( "drop", 0x70 + n, go )

    def dup( self ):
        """
        10110002

        Push belt[0], thereby leaving two copies of it on the belt.

        Flags unaffected.
        """
        def go():
            self._push( self.belt[0] )
        return self._wrap( "dup", 0xb2, go ) # mnemonic: b2 = be two

    def neg( self ):
        """
        10101111

        Push two's complement of belt[0].

        Sets Z.
        """
        def go():
            self._push(self._setZ( 256 - self.belt[ 0 ] ))
        return self._wrap( "neg", 0xaf, go ) # mnemonic: af = arithmetic flip

    def adc( self ):
        """
        10101100

        Push belt[0] + belt[1] + C.

        Sets Z and C.
        """
        def go():
            carry_in = 'c' in self.flags
            self._push( self._alu_sum( self.belt[ 0 ], self.belt[ 1 ], carry_in ) )
        return self._wrap( "adc", 0xac, go ) # mnemonic: ac = add with carry

    def add( self ):
        """
        10101101

        Push belt[0] + belt[1].

        Sets Z and C.
        """
        def go():
            self._push( self._alu_sum( self.belt[ 0 ], self.belt[ 1 ], 0 ) )
        return self._wrap( "add", 0xad, go ) # mnemonic: ad = "add"

    def wlink( self ):
        """
        10100001

        Write link register from belt[0].

        Flags unaffected.
        """
        def go():
            self.link = self.belt[0]
        return self._wrap( "wlink", 0xa1, go ) # mnemonic: a1 = AL = alter link

    def link( self ):
        """
        10110001

        Push link register.

        Flags unaffected.
        """
        def go():
            self._push( self.link )
        return self._wrap( "link", 0xb1, go ) # mnemonic: b1 = BL = belt <= link

    def wflags( self ):
        """
        10101111

        Write flags register from belt[0].

        Flags all affected.
        """
        def go():
            self.link = self.belt[0]
        return self._wrap( "wlink", 0xaf, go ) # mnemonic: af = alter flags

    def flags( self ):
        """
        10111111

        Push flags register.
        C = bit 7
        Z = bit 6

        Flags unaffected.
        """
        def go():
            self._push( self.link )
        return self._wrap( "link", 0xbf, go ) # mnemonic: bf = belt <= flags

    def ret( self ):
        """
        10110100

        Move link register to pc.

        Flags unaffected.
        """
        def go():
            self.pc = self.link
        return self._wrap( "ret", 0xb4, go ) # mnemonic: b4 = before

    def halt( self ):
        """
        10111101

        Stop advancing pc.

        Flags unaffected.
        """
        def go():
            self.pc -= 1
            raise StopIteration
        return self._wrap( "halt",0xbd, go ) # mnemonic: bd = be dormant

    def lsr( self, bits3 ):
        """
        11100sss

        s = unsigned shift distance

        Logical shift right.  Push belt[0] >> s.

        Sets Z.
        """
        def go():
            self._push( self._setZ( self.belt[ 0 ] >> bits3 ) )
        return self._wrap( "lsr", 0xe0 + bits3, go )

    def shl( self, treg, bits3 ):
        """
        11101sss

        s = unsigned shift distance

        Bitwise shift left.  Push belt[0] << s.

        Sets Z.
        """
        def go():
            self._push(self._setZ( self.belt[ 0 ] << bits3 ))
        return self._wrap( "shl", 0xe8 + bits3, go )

    def inc( self, imm ):
        """
        11110iii

        i = signed 3-bit immediate

        Push belt[0] + i.

        Sets Z and C.
        """
        def go():
            self._push( self._alu_sum( self.belt[ 0 ], imm, 0 ) )
        return self._wrap( "inc", 0xf0 + imm, go )

    def jmp( self, offset ):
        """
        100ddddd

        d = signed displacement from following instruction

        Unconditional jump. Sets link register to address of following instruction.

        Note that jmp 0 has no effect but to set the link register,
        and jmp -1 is an endless busy-loop.

        Flags unaffected.
        """
        def go() :
            self.link = self.pc
            self.pc += offset
        return self._wrap( "jmp", 0x80 + offset, go )

    def snc( self, offset ):
        """
        110000dd

        d = unsigned displacement from instruction after next

        Skip if C clear.

        Flags unaffected.
        """
        def go() :
            if not 'c' in self.flags:
                self.pc += offset + 1
        return self._wrap( "snc", 0xc0 + offset, go )

    def sc( self, offset ):
        """
        110100dd

        d = unsigned displacement from instruction after next

        Skip if C set.

        Flags unaffected.
        """
        def go() :
            if 'c' in self.flags:
                self.pc += offset + 1
        return self._wrap( "sc", 0xd0 + offset, go )

    def snz( self, offset ):
        """
        110010dd

        d = unsigned displacement from instruction after next

        Skip if Z clear.

        Flags unaffected.
        """
        def go() :
            if not 'z' in self.flags:
                self.pc += offset + 1
        return self._wrap( "snz", 0xc8 + offset, go )

    def sz( self, offset ):
        """
        110110dd

        d = unsigned displacement from instruction after next

        Skip if Z set.

        Flags unaffected.
        """
        def go() :
            if 'z' in self.flags:
                self.pc += offset + 1
        return self._wrap( "sz", 0xd8 + offset, go )

    def _wrap( self, name, encoding, handler ):
        def wrapped():
            self.pc = ( self.pc + 1 ) & 255
            handler()
        return Instruction( name, encoding, wrapped )

    def _alu_sum( self, left, right, carry_in ):
        result = (left&255)+ (right&255)+ carry_in
        if result >= 256:
            self.flags.add('c')
            result = result & 255
        else:
            self.flags.discard('c')
        return self._setZ( result )

    def _setZ( self, result ):
        result = result & 255
        if result == 0:
            self.flags.add('z')
        else:
            self.flags.discard('z')
        return result

    def _push( self, value ):
        self.belt = [ value ] + self.belt[ :-1 ]

def address( base, disp ):
    return ( base + disp ) & 255

def fib():
    state = State()
    fibonacci = [
        # Initialize
        state.push( 1 ),
        state.push( 1 ),
        # Record loop entry point
        state.jmp( 0 ),
        # Add last two items
        state.add(),
        # Loop
        state.sc( 0 ),
        state.ret(),
        # Result
        state.get( 1 ),
        state.halt()
    ]
    def fib_binary():
        for instr in fibonacci:
            yield instr.encoding
    binary = bytearray( fib_binary() )
    print("Binary: " + binary.hex(" "))
    try:
        while state.pc < len( fibonacci ):
            instr = fibonacci[ state.pc ]
            print( "-- %s --" % instr )
            instr.handler()
            print( str(state) )
            print()
        print("\n== No more instructions ==")
    except StopIteration:
        print("\n== Halted ==")
    assert state.belt[0] == 233

fib()

