Jason Wilkin
12/15/2012
assem.py
========

A SIC/XE assembler written in python

assem.py is a SIX/XE assembler. In pass 1, all symbols are added to Symtab with their appropriate
values. In pass 2, each instruction is calculated using the designated addressing mode
(base-relative, pc-relative, and absolute address, with immediate, simple, and indirect modes)
for each instruction format (1,2,3,4).

The following errors are handled:

    RESB does not support character opperands
    RESW does not support character opperands
    SVC operand n must be of format 0 <= n < 16
    Operands r1,r2 must be of format 0 <= r1,r2 < 16
    Operand n must be of format 0 < n < 17 and operand r must be of format 0 <= r < 16
    No BASE was declared. Attemping to check for base relative addressing
    Cannot use PC or Base relative addressing
    Indexed addressing is used with Immediate or Indirect addressing
    Symbol is duplicately-defined
