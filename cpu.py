#! /usr/bin/python
from dataclasses import dataclass
from typing import *

# Idea: an 8-bit processor just powerful enough to implement
# an interpreter for itself. 
#
# First three bits of each instruction:
#
# 000 - push
# 001 - load
# 010 - store
# 011 - pick
# 100 - jmp
# 101 - skip (conditional jump forward)
# 110 - opcode-only instructions
# 111 - other

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
        return "Belt: %s\n  PC: %s\nLink: %s\nFlags: %s\nMem: %s" % ( self.belt, self.pc, self.link, self.belt, self.mem )

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

    def load( self, disp ):
        """
        001ddddd

        d = signed 5-bit displacement

        Load contents of [belt[0] + d] onto belt.

        Flags unaffected.
        """
        def go():
            self._push( mem[address( self.belt[0], disp )] )
        return self._wrap( "load", 0x20 + disp, go )

    def store( self, disp ):
        """
        010ddddd

        d = signed 5-bit displacement

        Store belt[1] to [belt[0] + d].

        Flags unaffected.
        """
        def go():
            mem[address( self.belt[0], disp )] = self.belt[0]
        return self._wrap( store, 0x40 + disp, go )

    def pick( self, n ):
        """
        011000nn

        n = unsigned belt index

        Rotate belt items 0..n (inclusive) by one position,
        leaving item 0 at 1, 1 at 2, ... and item n at 0.

        Note that revolve by 0 is a no-op.

        All other instructions starting with 011 are reserved.

        Flags unaffected.
        """
        def go():
            belt = self.belt
            self.belt = [belt[ n ]] + belt[ 0:n ] + belt[ n+1: ]
        return self._wrap( "pick", 0x50 + n, go )

    def dup( self ):
        """
        11000000

        Push belt[0], thereby leaving two copies of it on the belt.

        Flags unaffected.
        """
        def go():
            self._push( self.belt[0] )
        return self._wrap( "dup", 0xc0, go )

    def neg( self ):
        """
        11000001

        Push two's complement of belt[0].

        Sets Z.
        """
        def go():
            self._push(self._setZ( 256 - self.belt[ 0 ] ))
        return self._wrap( "neg", 0xc1, go )

    def add( self ):
        """
        11000010

        Push belt[0] + belt[1].

        Sets Z and C.
        """
        def go():
            self._push( self._alu_sum( self.belt[ 0 ], self.belt[ 1 ], 0 ) )
        return self._wrap( "add", 0xc2, go )

    def adc( self ):
        """
        11000011

        Push belt[0] + belt[1] + C.

        Sets Z and C.
        """
        def go():
            carry_in = 'c' in self.flags
            self._push( self._alu_sum( self.belt[ 0 ], self.belt[ 1 ], carry_in ) )
        return self._wrap( "adc", 0xc3, go )

    def link( self ):
        """
        11000100

        Push link register.

        Flags unaffected.
        """
        def go():
            self._push( self.link )
        return self._wrap( "link", 0xc4, go )

    def wlink( self ):
        """
        11000101

        Write link register from belt[0].

        Flags unaffected.
        """
        def go():
            self.link = self.belt[0]
        return self._wrap( "wlink", 0xc5, go )

    def ret( self ):
        """
        11000110

        Move link register to pc.

        Flags unaffected.
        """
        def go():
            self.pc = self.link
        return self._wrap( "ret", 0xc6, go )

    def halt( self ):
        """
        11011111

        Stop advancing pc.

        Flags unaffected.
        """
        def go():
            self.pc -= 1
            raise StopIteration
        return self._wrap( "halt",0xdf, go )

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

        Note that jmp -1 is like a "halt" busy-loop instruction.

        Flags unaffected.
        """
        def go() :
            self.link = self.pc
            self.pc += offset
        return self._wrap( "jmp", 0x80 + offset, go )

    def snc( self, offset ):
        """
        101000dd

        d = unsigned displacement from instruction after next

        Skip if C clear.

        Flags unaffected.
        """
        def go() :
            if not 'c' in self.flags:
                self.pc += offset + 1
        return self._wrap( "snc", 0xa0 + offset, go )

    def sc( self, offset ):
        """
        101100dd

        d = unsigned displacement from instruction after next

        Skip if C set.

        Flags unaffected.
        """
        def go() :
            if 'c' in self.flags:
                self.pc += offset + 1
        return self._wrap( "sc", 0xb0 + offset, go )

    def snz( self, offset ):
        """
        101010dd

        d = unsigned displacement from instruction after next

        Skip if Z clear.

        Flags unaffected.
        """
        def go() :
            if not 'z' in self.flags:
                self.pc += offset + 1
        return self._wrap( "snz", 0xa8 + offset, go )

    def sz( self, offset ):
        """
        101110dd

        d = unsigned displacement from instruction after next

        Skip if Z set.

        Flags unaffected.
        """
        def go() :
            if 'z' in self.flags:
                self.pc += offset + 1
        return self._wrap( "sz", 0xb8 + offset, go )

    def _wrap( self, name, encoding, handler ):
        def wrapped():
            self.pc = ( self.pc + 1 ) & 255
            handler()
        return Instruction( name, encoding, wrapped )

    def _alu_sum( self, left, right, carry_in ):
        result = (left&255)+ (right&255)+ carry_in
        if result == 0:
            self.flags = {'z'}
        elif result <= 255:
            self.flags = set()
        elif result == 256:
            self.flags = {'c','z'}
            result = 0
        else:
            self.flags = {'c'}
            result = result & 255
        return result

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
        state.pick( 1 ),
        state.halt()
    ]
    def fib_binary():
        for instr in fibonacci:
            yield instr.encoding
    binary = bytearray( fib_binary() )
    print(binary)
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

fib()
