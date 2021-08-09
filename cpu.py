#! /usr/bin/python

# State
memory = [0] * 256
acc = 0
pc = 0

REG_ACC = 0
REG_PC = 1

def load( reg, addr4 ):
    if reg == REG_ACC:
        acc = memory[ addr4 ]
    else:
        pc = memory[ addr4 ]

def store( reg, addr4 ):
    if reg == REG_ACC:
        memory[ addr4 ] = acc
    else:
        memory[ addr4 ] = pc

def xchg( reg, addr4 ):
    if reg == REG_ACC:
        memory[ addr4 ] = acc
    else:
        memory[ addr4 ] = pc

# High 4 bits of instruction word
LOAD = 0
JABS = 1 # Jump absolute = LOAD to PC
XCHG = 2
JLNK = 3 # Jump and link = XCNG to PC
ADD = 4
JREL = 5 # Jump relative = ADD to PC
REG = 6  # Register-only instructions

# Regs:
# - PC
# - Accumulator
# - Link
# - Flags
# Internal:
# - Instruction
# - B (ALU second operand)

# Want to be ambiguous between call/return vs trace exit
# - No recursion
# - No side-effects in anything architecturally visible
CALL # Add mem to PC; store next PC in link reg
RETL # Return to link reg

# Now, the user can make architecturally-visible side effects if desired
LLNK # Load link reg to acc
SLNK # Store link reg from acc
LFLG # Load flags reg to acc
SFLG # Store flags reg from acc

LOAD # Load acc from mem
STOR # Store acc to mem
ACC  # Set accumulator to immediate
ADD  # Add mem to acc

NEG # Two's complement acc

# Flags
Z # Acc is zero
C # Carry


