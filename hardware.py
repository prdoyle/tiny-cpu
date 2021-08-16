#! /usr/bin/env python3

ram = bytearray( 256 )

R = 'R'
W = 'W'

class RAM:

    def __init__( self ):
        self.contents = bytearray( 256 )
        self.address = None
        self.data_in = None
        self.data_out = None
        self.mode = None

    def clock_lo( self ):
        pass

    def clock_hi( self ):
        if self.mode == R:
            if self.data_in == None:
                self.data_out = self.contents[ self.address ]
            else:
                raise ValueError
        elif self.mode == W:
            if self.data_in == None:
                raise ValueError
            else:
                self.contents[ self.address ] = self.data_in
        else:
            raise ValueError

class CPU:

    def __init__( self, ram ):
        self.ram = ram
        # Architected regs
        self.pc = 0
        self.flags = set()
        self.ra = 0
        self.rb = 0
        # Signals
        self.control = ControlWord()
        self.bus = 0

    def clock_lo( self ):
        if self.control.mw:
            self.ram.mode = W
        elif self.control.mr:
            self.ram.mode = R
        else:
            self.ram.mode = None
        if self.control.pca:
            self.ram.address = self.pc
        if self.control.pci

    def clock_hi( self ):
        pass

class ControlWord():

    def __init__( self ):
        self.mw = False          # Memory Write
        self.mr = False          # Memory Read
        self.pca = False         # PC -> Memory address bus
        self.pci = False         # PC increment

