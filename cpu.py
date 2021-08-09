#! /usr/bin/python

# Idea: an 8-bit processor just powerful enough to implement
# an interpreter for itself. 

PC = 3 # Program counter is register 3

class State:

    def __init__( self ):
        self.mem = [0] * 32
        self.regs = [0, 0, 0, 0]
        self.flags = set()

    def __str__( self ):
        return "Flags: %s\nRegs: %s\n Mem: %s" % ( self.flags, self.regs, self.mem )

    def load( self, treg, sreg, u2 ):
        """
        Flags unaffected
        00 tt ss ff
        """
        def go():
            self.regs[ treg ] = mem[address( self.regs[ sreg ], u2 )]
        return self._wrap( go )

    def store( self, treg, u2, sreg ):
        """
        Flags unaffected
        01 tt ss ff
        """
        def go():
            mem[address( self.regs[ treg ], u2 )] = self.self.regs[ sreg ]
        return self._wrap( go )

    def add( self, treg, sreg ):
        """
        T = T + S + C
        """
        def go():
            self.regs[ treg ] = self._alu_sum( self.regs[ treg ], self.regs[ sreg ] )
        return self._wrap( go )

    def dec( self, treg, u3 ):
        """
        Flags unaffected
        T = T - u3
        """
        def go() :
            self.regs[ treg ] = ( 256 + self.regs[ treg ] - u3 ) & 255
        return self._wrap( go )

    def neg( self, treg ):
        """
        Sets Z flag. C unaffected
        T = 256-T & 255
        """
        def go():
            self.regs[ treg ] = self._setZ( 256 - self.regs[ treg ] )
        return self._wrap( go )

    def lsr( self, treg, bits3 ):
        """
        Logical shift right
        Sets Z flag. C unaffected
        T = T >>> bits3
        """
        def go():
            self.regs[ treg ] = self._setZ( self.regs[ treg ] >> bits3 )
        return self._wrap( go )

    def shl( self, treg, bits3 ):
        """
        Sets Z flag. C unaffected
        T = T << bits3
        """
        def go():
            self.regs[ treg ] = self._setZ( self.regs[ treg ] << bits3 )
        return self._wrap( go )

    def _wrap( self, function ):
        def wrapped():
            self.regs[ PC ] = ( self.regs[ PC ] + 1 ) & 255
            function()
            # Do we want a zero register? Can we afford one?
            #self.regs[ 0 ] = 0
        return wrapped

    def _alu_sum( self, left, right ):
        carry_in = 'c' in self.flags
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

def address( base, u2 ):
    return ( base + (u2 & 3) ) & 255

def main():
    state = State()
    state.mem[31] = 1
    fibonacci = [
        # Initialize
        state.dec( 1, 1 ),
        state.neg( 1 ),
        state.dec( 2, 1 ),
        state.neg( 2 ),
        # Add back and forth
        state.add( 1, 2 ),
        state.add( 2, 1 ),
        # Loop
        state.dec( PC, 3 )
    ]
    for n in range( 1, 10 ):
        instr = fibonacci[ state.regs[PC] ]
        instr()
        print( str(state) )

main()
