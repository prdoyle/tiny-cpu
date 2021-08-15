#! /usr/bin/env python3

import unittest

X = 'X' # transitioning
Z = 'Z' # high impedance

def combine2( signal1, signal2 ):
    if signal1 == signal2:
        return signal1
    elif signal1 == Z:
        return signal2
    elif signal2 == Z:
        return signal1
    else:
        raise ValueError

def combine( *signals ):
    return reduce( combine2, signals, X )

class TestCombine2( unittest.TestCase ):

    def test_0Z( self ):
        self._check_combine2( 0, 0, Z )

    def test_00( self ):
        self._check_combine2( 0, 0, 0 )

    def test_1Z( self ):
        self._check_combine2( 1, 1, Z )

    def test_11( self ):
        self._check_combine2( 1, 1, 1 )

    def test_XZ( self ):
        self._check_combine2( X, X, Z )

    def test_XX( self ):
        self._check_combine2( X, X, X )

    def test_ZZ( self ):
        self._check_combine2( Z, Z, Z )

    def test_01( self ):
        self._invalid_combine2( 0, 1 )

    def test_0X( self ):
        self._invalid_combine2( 0, X )

    def test_1X( self ):
        self._invalid_combine2( 1, X )

    def _check_combine2( self, expected, arg1, arg2 ):
        self.assertEqual( expected, combine2( arg1, arg2 ) )
        self.assertEqual( expected, combine2( arg2, arg1 ) )

    def _invalid_combine2( self, arg1, arg2 ):
        with self.assertRaises( ValueError ):
            combine2( arg1, arg2 )
        with self.assertRaises( ValueError ):
            combine2( arg2, arg1 )

def not1( in1 ):
    return { 0: 1, 1: 0, X: X, Z: X }[ in1 ]

def nand2( in1, in2 ):
    if in1 == 0 or in2 == 0:
        return 1
    elif in1 == in2 == 1:
        return 0
    else:
        return X

def nor2( in1, in2 ):
    if in1 == 1 or in2 == 1:
        return 0
    elif in1 == in2 == 0:
        return 1
    else:
        return X

def xor2( in1, in2 ):
    if in1 == 0:
        return not1( in2 )
    elif in2 == 0:
        return not1( in1 )
    else:
        return X

def and2( in1, in2 ):
    return not1( nand2(in1,in2) )

def or2( in1, in2 ):
    return not1( nor2(in1,in2) )

def xnor2( in1, in2 ):
    return not1( xor2(in1,in2) )

def Component1( f ):
    def result( in1 ):
        return f( in1() )
    return result

def Component2( f ):
    def result( in1, in2 ):
        return f( in1(), in2() )
    return result

And2  = Component2( and2 )
Or2   = Component2( or2 )
Nand2 = Component2( nand2 )
Nor2  = Component2( nor2 )
Xor2  = Component2( xor2 )
Xnor2 = Component2( xnor2 )

