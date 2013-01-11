"""
--------------------------------------------------------------------------------------------------
Jason Wilkin
assem.py
12/15/2012

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

--------------------------------------------------------------------------------------------------
"""

import sys

# Globals:

# Each flag bit is defined 
Nbit = 32
Ibit = 16
Xbit = 8
Bbit = 4
Pbit = 2
Ebit = 1

# Tracks the BASE value when used with the BASE directive
BASE = None
# Tracks current line in input file for outputing error messages
CurLine = 0

# Each mnemonic has a record indicating (0) whether it's an instruction 
# or a directive, (2) how long of an instruction, (3) its opcode, (4) a list
# describing its operands.

Mnemonics = {'START' : ['D'],
             'BASE'  : ['D'],
             'NOBASE': ['D'],
             'STL'   : ['I',3,0x14,['m']],
             'RMO'   : ['I',2,0xAC,['r','r']],
             'ADD'   : ['I',3,0x18,['m']],
             'J'     : ['I',3,0x3C,['m']],
             'LDA'   : ['I',3,0x00,['m']],
             'STA'   : ['I',3,0x0C,['m']],
             'JSUB'  : ['I',3,0x48,['m']],
             'JEQ'   : ['I',3,0x30,['m']],
             'SUB'   : ['I',3,0x1C,['m']],
             'MULR'  : ['I',2,0x98,['r','r']],
             'LDL'   : ['I',3,0x08,['m']],
             'RSUB'  : ['I',3,0x4C,['m']],
             'ADDF'  : ['I',3,0x18,['m']],
             'ADDR'  : ['I',2,0x90,['r','r']],
             'AND'   : ['I',3,0x40,['m']],
             'CLEAR' : ['I',2,0xB4,['r']],
             'COMP'  : ['I',3,0x28,['m']],
             'COMPF' : ['I',3,0x88,['m']],
             'COMPR' : ['I',2,0xA0,['r','r']],
             'DIV'   : ['I',3,0x24,['m']],
             'DIVF'  : ['I',3,0x64,['m']],
             'DIVR'  : ['I',2,0x9C,['r','r']],
             'FIX'   : ['I',1,0xC4,[]],
             'FLOAT' : ['I',1,0xC0,[]],
             'HIO'   : ['I',1,0xF4,[]],
             'JGT'   : ['I',3,0x34,['m']],
             'JLT'   : ['I',3,0x38,['m']],
             'LDB'   : ['I',3,0x68,['m']],
             'LDCH'  : ['I',3,0x50,['m']],
             'LDF'   : ['I',3,0x70,['m']],
             'LDL'   : ['I',3,0x08,['m']],
             'LDS'   : ['I',3,0x6C,['m']],
             'LDT'   : ['I',3,0x74,['m']],
             'LDX'   : ['I',3,0x04,['m']],
             'LPS'   : ['I',3,0xD0,['m']],
             'MUL'   : ['I',3,0x20,['m']],
             'MULF'  : ['I',3,0x60,['m']],
             'NORM'  : ['I',1,0xC8,[]],
             'OR'    : ['I',3,0x44,['m']],
             'RD'    : ['I',3,0xD8,['m']],
             'SHIFTL': ['I',2,0xA4,['r','n']],
             'SHIFTR': ['I',2,0xA8,['r','n']],
             'SIO'   : ['I',1,0xF0,[]],
             'SSK'   : ['I',3,0xEC,['m']],
             'STB'   : ['I',3,0x78,['m']],
             'STCH'  : ['I',3,0x54,['m']],
             'STF'   : ['I',3,0x80,['m']],
             'STI'   : ['I',3,0xD4,['m']],
             'STS'   : ['I',3,0x7C,['m']],
             'STSW'  : ['I',3,0xE8,['m']],
             'STT'   : ['I',3,0x84,['m']],
             'STX'   : ['I',3,0x10,['m']],
             'SUBF'  : ['I',3,0x5C,['m']],
             'SUBR'  : ['I',2,0x94,['r','r']],
             'SVC'   : ['I',2,0xB0,['n']],
             'TD'    : ['I',3,0xE0,['m']],
             'TIO'   : ['I',1,0xF8,[]],
             'TIX'   : ['I',3,0x2C,['m']],
             'TIXR'  : ['I',2,0xB8,['r']],
             'WD'    : ['I',3,0xDC,['m']]
             }


# Dictionary of defined symbols and their values
Symtab = {}

# Dictionary of registers and their values in bit strings
RegisterNumbers = {'A' : "0000", 
                   'X' : "0001",
                   'L' : "0010",
                   'B' : "0011",
                   'S' : "0100",
                   'T' : "0101",
                   'PC' : "1000", 
                   'SW' : "1001"}


def isspace(c):
    """ Returns true iff c is a space character, false otherwise """
    return c == ' ' or c =='\t' or c == '\n'


def readFile(fname):
    """ returns a list of strings: lines from the file named fname"""
    return [line[:-1] for line in open(fname).readlines()]


def isCommentLine(line):
    """ returns true iff line begins with a dot (.) """
    return line[:1] == '.'
    
def hasLabel(line):
    """ return true iff line begins with an ALPHA character """
    return line[:1].isalpha()

def isExtended(mnemonic):
    """ return true iff this mnemonic begins with a '+' """
    return mnemonic[:1] == '+'

def baseMnemonic(mnemonic):
    """ return the mnemonic with any leading + stripped off """
    if isExtended(mnemonic):
        return mnemonic[1:]
    else:
        return mnemonic


def assembledLength(mnemonic,operands):
    """ Return the number of bytes required for the assembly of 
        the given instruction. """

    if mnemonic in ["START","END","BASE","NOBASE"]:
        return 0
    elif mnemonic == "RESB":
        if operands[0] == 'X':
            return int(makeLiteral(operands), 16)               # Return number of hex bytes
        elif operands[0] == 'C':
            error("RESB does not support character opperands")
        else:
            return int(operands)                                # Return number of decimal bytes
    elif mnemonic == "RESW":
        if operands[0] == 'X':
            return int(makeLiteral(operands), 16) * 3           # Return number of hex words
        elif operands[0] == 'C':
            error("RESW does not support character opperands")
        else:
            return int(operands) * 3                            # Return number of decimal words

    elif mnemonic == "WORD":
        return 3

    elif mnemonic == "BYTE":
        return len(makeLiteral(operands))/2                     # Return number of bytes

    else:
        lookup = Mnemonics[baseMnemonic(mnemonic)]              # list of information on the mnemonic
        if isExtended(mnemonic):
            return int(lookup[1]) + 1
        else:
            return int(lookup[1])



def oppositeBit(b):
    """ b is a single char, 0 or 1.  return the other. """
    if b == '1':
        return '0'
    else:
        return '1'

def bitStr2Comp(bitstring):
    """ compute and return the 2's complement of bitstring """

    bitList = list(bitstring)
    length = len(bitList)
    broke = 0
    for i in range(length):                          # Not each bit
        bitList[i] = oppositeBit(bitList[i])           
    for i in range(length):                          # Add one to the flipped bit string
        if bitList[length-(i+1)] == '0':
            bitList[length-(i+1)] = '1'
            broke = 1
            break
        else:
            bitList[length-(i+1)] = '0'
            
    if broke == 0:
        return '1' + "".join(bitList)               # Account for extra carry
    else:
        return "".join(bitList)


def toBitString(val,length=24):
    """Build and return a bit string of the given length.  
       val is a signed integer"""

    bits = '{:b}'.format(val)                       # Convert int to bit string

    if val < 0:
        bits = bitStr2Comp(bits[1:])

    if len(bits) < length:                          # Add leading 0s or 1s
        if val >= 0:
            return '0'*(length-len(bits)) + bits
        else:
            return '1'*(length-len(bits)) + bits

    else:
        return bits
    
def bitStr2Hex(bitstring):
    """ Recursively returns a hex representation of a bit string. """
    hexStr = "0123456789ABCDEF"
    if len(bitstring) == 0:
        return ""
    elif len(bitstring) >= 4:
        return bitStr2Hex(bitstring[:-4]) + hexStr[int(("0b" + bitstring[-4:]),2)]
    else:
        return hexStr[int(("0b" + bitstring),2)]


def makeLiteral(string):
    """ string is C'CCCCCC...' or (hex) X'HHHHHH....'.
        Return a string of hexadecimal... """
    if string[0] == 'X':
        return string[2:-1]             # Return hexadecimal string
    else:
        Revstring = string[2:-1][::-1]  # slice the characters and reverse string for conversion
        bitStr = ""
        for i in range(len(Revstring)):
            bitStr = toBitString((ord(Revstring[i])), 8) + bitStr   # Convert each char to bit string
        return bitStr2Hex(bitStr)


def printSymtab():
    """ Symtab is sorted and printed nicely """
    sortedTable = sorted(Symtab, key=Symtab.__getitem__)    # Sorts Symtab
    print
    for i in range(len(sortedTable)):
        print " "*(10-len(sortedTable[i])), sortedTable[i]+": %05X"%(Symtab.get(sortedTable[i]))

def registerNumber(reg):
   """reg is a string, return its number """
   return RegisterNumbers[reg]


def makeInstruction(mnemonic,operands,curloc):
    """ Prepend with 0 to a given length """
    global BASE

    if mnemonic in ['START','RESB','RESW','END']:           # Return empty string for directives
            return ""

    elif mnemonic == 'BASE':                # Return empty string and set base value
        BASE = Symtab[operands]
        return ""

    elif mnemonic == 'NOBASE':              # Clear base value and return empty string
        BASE = None
        return ""


    elif mnemonic == 'WORD':                # Convert word operand to hexstring
        if operands[0] in ['X','C']:
            return makeLiteral(operands)
        else:
            return bitStr2Hex(toBitString(int(operands)))

    elif mnemonic == 'BYTE':                # Convert byte operand to hexstring
        if operands[0] in ['X','C']:
            return makeLiteral(operands)
        else:
            return bitStr2Hex(toBitString(int(operands),len(operands) * 2))


    length = assembledLength(mnemonic,operands)     # length is instruction format
    instrBits = toBitString(Mnemonics[baseMnemonic(mnemonic)][2],8)     # instrBits will be a bitstring of the instructions

    if baseMnemonic(mnemonic) == "RSUB":       # Special check for RSUB
        if mnemonic[0] == '+':
            instrBits = instrBits[0:6]+toBitString(Nbit+Ibit+Ebit,6)+toBitString(0,20)
        else:
            instrBits = instrBits[0:6]+toBitString(Nbit+Ibit,6)+toBitString(0,12)
        return bitStr2Hex(instrBits)

    # ------- Format 1 -------
    if length==1:
        pass

    # ------- Format 2 -------
    elif length==2:
        lookup = Mnemonics[baseMnemonic(mnemonic)]
        if mnemonic == "SVC":                               # Special check for SVC
            if int(operands) >= 0 and int(operands) < 16:
                instrBits = instrBits + toBitString(int(operands),4) + '0000'
            else:
                error("SVC operand n must be of format 0 <= n < 16")
        elif lookup[3] == ['r']:
            instrBits = instrBits + registerNumber(operands) + '0000'
        elif lookup[3] == ['r','r']:
            ops = operands.split(',')
            r1 = registerNumber(ops[0])
            r2 = registerNumber(ops[1])
            if int(r1,2) < 16 and int(r1,2) >= 0 and int(r2,2) < 16 and int(r2,2) >= 0:
                instrBits = instrBits + r1 + r2
            else:
                error(mnemonic + " operands r1,r2 must be of format 0 <= r1,r2 < 16")
        else:
            ops = operands.split(',')
            r = registerNumber(ops[0])
            n = int(ops[1])
            if n < 17 and n > 0 and int(r,2) < 16 and int(r,2) >= 0:
                instrBits = instrBits + r + toBitString(n-1,4)
            else:
                error(mnemonic + " operand n must be of format 0 < n < 17 and operand r must be of format 0 <= r < 16.")
    

    # ------- Format 3 -------       
    elif length==3:

        if operands[0] == '#' and not isSymbol(baseOperand(operands)):
            instrBits = instrBits[0:6]+toBitString(setFlags(operands,mnemonic),6)+toBitString(int(mOperandValue(operands)),12)
            
        else:
            Opval = int(mOperandValue(baseOperand(operands)))
            PCTA = Opval - curloc
            if PCTA >= -2048 and PCTA <= 2047:
                # PC relative
                instrBits = instrBits[0:6]+toBitString((setFlags(operands,mnemonic)+Pbit),6)+toBitString(PCTA,12)
            else:
                if BASE == None:
                    error("No BASE was delcared. Attemping to check for base relative addressing.")
                else:
                    BTA = Opval - BASE
                    if BTA >= 0 and BTA <= 4095:
                        # Base relative
                        instrBits = instrBits[0:6]+toBitString((setFlags(operands,mnemonic)+Bbit),6)+toBitString(BTA,12)
                    else:
                        # ERROR
                        error("CANNOT USE PC OR BASE RELATIVE ADDRESSING.")
     
    # ------- Format 4 -------               
    else:
        instrBits = instrBits[0:6]+toBitString(setFlags(operands,mnemonic),6)+toBitString(int(mOperandValue(baseOperand(operands))),20)

    return bitStr2Hex(instrBits)

def baseOperand(string):
    """ return string with any leading @ or # stripped off """
    if string[-2:]==',X':
        string = string[:-2]
    if string[0] == '@' or string[0] == '#':
        return string[1:]
    else:
        return string

def mOperandValue(op):
    """ op is a basic memory operand, perhaps a symbol. Return its value, 
        from Symtab if necessary """
    baseop = baseOperand(op)
    if isSymbol(baseop):
        return Symtab[baseop]
    else:
        return baseop

def setFlags(op, mnemonic):
    """ return flag bits """       
    flags = 0
    if op[0] == '#':        # Immediate addressing
        flags += Ibit

    elif op[0] == "@":      # iNdirect addressing
        flags += Nbit
    if isExtended(mnemonic):    # Extended addressing
        flags += Ebit
    if op[-2:] == ",X" and ((flags & Nbit) or (flags & Ibit)):      
        error("Indexed addressing is used with Immediate or Indirect addressing.")
    elif op[-2:] == ",X":       # indeXed addressing
        flags += Xbit
    if not (flags & (Nbit+Ibit)):  # Simple addressing
        flags += Nbit+Ibit

    return flags

def isSymbol(string):
    """ return True iff string is a key in Symtab """
    return string in Symtab.keys()

def error(msg):
    """ print msg and abort the program """
    print
    print "Error on line %d:"%(CurLine)
    print msg
    sys.exit(-1)


def main():
    # ---------- PASS 1 ----------
    curloc = 0                          # Current address
    lines = readFile(sys.argv[1])
    for line in lines:
        if isCommentLine(line):
            continue
        label = ""
        lmo = line.split()

        if len(lmo) == 1:                           # Continue to calcuate curloc to determine symbol values
            curloc+=assembledLength(lmo[0],0)
        else:
            if hasLabel(line):      # Need to add label to Symtab
                if len(lmo) < 3:
                    label = lmo[0]
                    mnemonic = lmo[1]
                    operands = ""
                else:
                    label,mnemonic,operands = lmo[0],lmo[1],lmo[2]
                if isSymbol(label):
                    error("Symbol " + label + " is duplicately-defined.")
                else:
                    Symtab[label] = curloc         # Add label to the symbol table with current curloc value
            else:
                mnemonic,operands = lmo[0],lmo[1]
            curloc+=assembledLength(mnemonic,operands)

    printSymtab()
    print


    # ---------- PASS 2 ----------
    curloc = 0
    for line in lines:
        global CurLine              # Tracks current line in program for error messages
        CurLine+=1
        if isCommentLine(line):
            print "\t",line
            continue

        label = ""              # Initialize/reset parts to be processed after each line
        operands = ""
        instruction = ""
        mnemonic = ""
        lmo = line.split()
                
        if len(lmo) == 1:       # No label and no operands
            instruction = makeInstruction(lmo[0],"#0",(curloc+assembledLength(lmo[0],operands)))
            print "%05X\t%s\t%s\t\t%s"%(curloc,label,lmo[0],instruction)
            curloc+=assembledLength(lmo[0],0)

        else:
            if hasLabel(line):
                if len(lmo) < 3:        # Label and no operands
                    label = lmo[0]
                    mnemonic = lmo[1]
                else:
                    label,mnemonic,operands = lmo[0],lmo[1],lmo[2]
            else:
                mnemonic,operands = lmo[0],lmo[1]

            nextLoc = curloc+assembledLength(mnemonic,operands)     # Process next address for makeInstruction
            instruction = makeInstruction(mnemonic,operands,(nextLoc))
            if mnemonic in ["START","END","BASE","NOBASE"]:
                print "\t%s\t%s\t%s\t%s"%(label,mnemonic,operands,instruction)
            else:
                print "%05X\t%s\t%s\t%s\t%s"%(curloc,label,mnemonic,operands,instruction)
            curloc=nextLoc

main()
