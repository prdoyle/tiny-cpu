# TinyCPU
A 8-bit cpu just barely capable of simulating itself.

_You're going to want to look at `cpu.py`. The rest of the files are secondary._

The main program is `cpu.py`. It contains:
- An assembler
- A disassembler
- An emulator written in Python
- An emulator written in TinyCPU assembly code
- Fibonacci written in TinyCPU assembly code
- Some unit tests

When executed, it runs the interpreter running the interpreter running Fibonacci.

## Architecture

All registers are 8 bits.
- PC - program counter
- RA - Accumulator register
- RB - Auxiliary register (used as an array index and a second ALU operand)
- PA - Pointer accumulator (used to compute addresses of things)
- PB - Pointer base (kind of like the `this` pointer in an object-oriented language)
- LR - Link register (holds the return address from a subroutine call, or the entry point of a loop)
- Also, there is a carry flag

There are 17 instructions that accept a 4-bit immediate value `n`.
The majority of them seem to be oriented around memory addressing.
Well over half the instructions are for loading, storing, or manipulating pointers.
An for example: `LBF` stands for "Load Base Field" and copies the data at address [PB + n] to RA.

Here are the 17 instructions that accept a 4-bit immediate value `n`:
- `IMM` - _Immediate_: loads `n` into RA
- `LAF` - _Load A Field_: loads [PA + n] into RA
- `LBF` - _Load B Field_: loads [PB + n] into RA
- `LAE` - _Load A Element_: loads [PA + RB + n] into RA
- `SAF` - _Store A Field_: stores RA into [PA + n]
- `SAE` - _Store A Element_: stores RA into [PA + RB + n]
- `SBF` - _Store B Field_: stores RA into [PB + n]
- `PAF` - _Pointer-load A Field_: loads [PA + n] into PA
- `PBF` - _Pointer-load B Field_: loads [PB + n] into PA
- `SPBF` - _Store Pointer B Field_: stores PA into [PB + n]
- `SCC` - _Skip if Carry Clear_: add n to PC if carry flag is 0
- `SCS` - _Skip if Carry Set_: add n to PC if carry flag is 1
- `AP` - _Advance Pointer_: add n to PA (0 <= n <= 3)
- `JBF` - _Jump to B Field_: loads [PB + n] into PC (4 <= n <= 15)
- `CALL` - Like `JBF` but also sets LR to the address immediately after the `CALL` instruction
- `LINK` - _Set link register_: set LR to PC + n (0 <= n <= 3)
- `CLE` - _Carry if less or equal_: set the carry flag if RA <= n (0 <= n <= 3)

There are a couple dozen instructions with implicit operands. Some notable ones:
- `RX` - _Register exchange_: swap RA and RB
- `RET` - _Return to link register_: copy LR to PC

Some highlights:
- `LINK 0` is useful to mark the entry point of a loop. A subsequent `RET` can then branch back to the entry point.
- `LINK 1` is useful to record the return address, thereby turning a jump into a call.

## Fibonacci example

```
        IMM     1       # RA = 1; second element of the Fibonacci sequence
        RA2B            # RB = RA; first element
        LINK    0       # Mark top of loop
        ADD             # RA = RA+RB
        SCS     2       # Leave the loop by skipping two instructions once we overflow RA
        RX              # Swap RA & RB
        ADD             # RA = RA+RB
        RET             # End of loop
        HALT
```

## Metacircular interpreter

The interpreter begins with PB pointing to a 16-byte data structure containing the state of the simulated registers, plus a collection of useful address vectors.
The layout can be seen in cpu.py [here](https://github.com/prdoyle/tiny-cpu/blob/master/cpu.py#L426).

The main loop reads the instruction indicated by PC, then uses `SPLIT` to separate the high four and low four bits. The high four bits are used to index into an array of "handlers", and the low four bits are passed as an operand to the handler.

With only 256 bytes available, space is very tight. For the interpreter to run itself requires two copies of the interpreter state, for a total of 32 bytes, plus room to store the program being interpreted&mdash;Fibonacci is 8 bytes. This leaves only 216 bytes for the handler code to implement 35 different instructions, which is only 6 bytes per handler; and one of those bytes must return to the main loop!

To make this all fit required two pairs of handlers to share code:
- `SCC` branches into the middle of `SCS` because they have four instructions in common; and
- `JBF` is actually inside `CALL` because they are identical aside from their effect on `LR`.

There is also a very handy common subroutine `PREP_ALU_REGS` which loads RA, RB, and the carry flag with their simulated counterparts.
This permits a lot of ALU instructions to be implemented simply by _executing the instruction itself_.

For example, `ADD` is implemented in three instructions as follows:

```
        CALL    V_ALU   # PREP_ALU_REGS
        ADD             # The instruction itself
        JBF     V_CFRA  # Store carry flag and RA into simulated state structure
```

Ten instructions are implemented in a similar economical fashion, including `HALT`, which uses `PREP_ALU_REGS` to propagate the computation result from the simulation state into the actual CPU registers before terminating.
