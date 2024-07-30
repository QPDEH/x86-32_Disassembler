#Program by QPDEH, see https://github.com/QPDEH
#Sources - https://github.com/QPDEH/x86-32_Disassembler

regs16 = ["AX", "CX", "DX", "BX", "SP", "BP", "SI", "DI"]
regs32 = ["EAX", "ECX", "EDX", "EBX", "ESP", "EBP", "ESI", "EDI"]
regs16w0 = ["AL", "CL", "DL", "BL", "AH", "CH", "DH", "BH"]
regs16w1 = regs16
regs32w0 = regs16w0
regs32w1 = regs32


tipical_op_masc32 = 0b1111_1000_0000_0000
tipical_imdata_masc32 = 0b1111_1100_0011_1000_0000_0000

masc_8_of_16 = 0b1111_1111_0000_0000
masc_16_of_24 = 0b1111_1111_1111_1111_0000_0000
masc_15_of_16 = 0b1111_1111_1111_1110

mrm_16_bit = ["BX", "BX", "BP", "BP", "SI", "DI", "BP", "BX"]

mrm_32_bit_mod_op = [0, 1, 4]

prefix_bytes = (0xf0, 0xf2, 0xf3, 0x67, 0x66, 0x26, 0x2e, 0x36, 0x3e, 0x64, 0x65, 0x0f)

default_operand_size = 4#bytes
prefix_op_operand_size = 2#bytes

change_segment_regs_prefs = (0x26, 0x2e, 0x36, 0x3e, 0x64, 0x65)

nnn_byte_cmd = ["ADD", "OR", "ADC", "SBB", "AND", "SUB", "XOR", "CMP"]
sreg2_table = ["ES", "CS", "SS", "DS"]
sreg3_table = ["ES", "CS", "SS", "DS", "FS", "GS"]

tttn_table = ["O", "NO", "B", "NB", "E", "NE", "BE", "NBE",
              "S", "NS", "P", "NP", "L", "NL", "LE", "NLE"]

control_regs = ["CR0", None, "CR2", "CR3", "CR4"]
debug_regs = ["DR0", "DR1", "DR2", "DR3", "DR4", "DR5", "DR6", "DR7"]
nnn_0xff_byte_cmd = ["INC", "DEC", "CALL", "CALL", "JMP", "JMP", "PUSH"]
nnn_0xc0_byte_cmd = ["ROL", "ROR", "RCL", "RCR", "SHL", "SHR", None, "SAR"]
nnn_0xf6_byte_cmd = ["TEST", None, "NOT", "NEG", "MUL", "IMUL", "DIV", "IDIV"]
fpu_0xd8_byte_cmd = ["FADD", "FMUL", "FCOM", "FCOMP", "FSUB", "FSUBR", "FDIV", "FDIVR"]
fpu_0xdd_byte_cmd = ["FLD", "FISTTP", "FST", "FSTP", "FRSTOR", None, "FSAVE", "FSTW"]
fpu_0xdb_byte_cmd = ["FILD", "FISTTP", "FIST", "FISTP", None, "FLD", None, "FSTP"]
