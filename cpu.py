#! /usr/bin/python

# Idea: an 8-bit processor just powerful enough to implement
# an interpreter for itself. 

class State:

    def __init__( self ):
        self.belt = [0] * 4
        self.pc = 0
        self.flags = set()
        self.mem = [0] * 32

    def __str__( self ):
        return "Belt: %s\n  PC: %s\nFlags: %s\nMem: %s" % ( self.belt, self.pc, self.belt, self.mem )

    def push( self, imm ):
        def go():
            self._push( imm )
        return self._wrap( go )

    def load( self, disp ):
        """
        Flags unaffected
        """
        def go():
            self._push( mem[address( self.belt[0], disp )] )
        return self._wrap( go )

    def store( self, disp ):
        """
        Flags unaffected
        01 tt ss ff
        """
        def go():
            mem[address( self.belt[0], disp )] = self.belt[0]
        return self._wrap( go )

    def dup( self ):
        def go():
            self._push( self.belt[0] )
        return self._wrap( go )

    def revolve( self, n ):
        def go():
            belt = self.belt
            self.belt = [belt[ n ]] + belt[ 0:n ] + belt[ n+1: ]
        return self._wrap( go )

    def inc( self, imm ):
        def go():
            self._push( self._alu_sum( self.belt[ 0 ], imm, 0 ) )
        return self._wrap( go )

    def add( self ):
        """
        T = T + S + C
        """
        def go():
            self._push( self._alu_sum( self.belt[ 0 ], self.belt[ 1 ], 0 ) )
        return self._wrap( go )

    def adc( self ):
        def go():
            carry_in = 'c' in self.flags
            self._push( self._alu_sum( self.belt[ 0 ], self.belt[ 1 ], carry_in ) )
        return self._wrap( go )

    def neg( self, treg ):
        """
        Sets Z flag. C unaffected
        T = 256-T & 255
        """
        def go():
            self.belt[ 0 ] = self._setZ( 256 - self.belt[ 0 ] )
        return self._wrap( go )

    def lsr( self, bits3 ):
        """
        Logical shift right
        Sets Z flag. C unaffected
        T = T >>> bits3
        """
        def go():
            self.belt[ 0 ] = self._setZ( self.belt[ 0 ] >> bits3 )
        return self._wrap( go )

    def shl( self, treg, bits3 ):
        """
        Sets Z flag. C unaffected
        T = T << bits3
        """
        def go():
            self.belt[ 0 ] = self._setZ( self.belt[ 0 ] << bits3 )
        return self._wrap( go )

    def jmp( self, offset ):
        def go() :
            self.pc += offset
        return self._wrap( go )

    def jc( self, offset ):
        def go() :
            if 'c' in self.flags:
                self.pc += offset
        return self._wrap( go )

    def jnc( self, offset ):
        def go() :
            if not 'c' in self.flags:
                self.pc += offset
        return self._wrap( go )

    def jz( self, offset ):
        def go() :
            if 'z' in self.flags:
                self.pc += offset
        return self._wrap( go )

    def jnz( self, offset ):
        def go() :
            if not 'z' in self.flags:
                self.pc += offset
        return self._wrap( go )

    def _wrap( self, function ):
        def wrapped():
            self.pc = ( self.pc + 1 ) & 255
            function()
        return wrapped

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
        # Add back and forth
        state.add(),
        # Loop
        state.jnc( -2 ),
        # Result
        state.revolve( 1 )
    ]
    while state.pc < len( fibonacci ):
        instr = fibonacci[ state.pc ]
        instr()
        print( str(state) )

fib()
