#Program by QPDEH, see https://github.com/QPDEH
#Sources - https://github.com/QPDEH/x86-32_Disassembler

from defines import *

with open(".text", "rb") as source:
    data = source.read()
index = 0
length = len(data)

def fill_to_2(str_):
    return "0" * (2-len(str_))+str_

def get_byte():
    global index
    index += 1
    return data[index-1]

def get_mod(mrm_byte):
    return mrm_byte >> 6

def get_mrm_args(mrm_byte):
    return mrm_byte // 8 % 8, mrm_byte % 8

def get_operand_size(has_0x66_prefix):
    return prefix_op_operand_size if has_0x66_prefix else default_operand_size

def get_operand_size_w(has_0x66_prefix, w):
    if not w: return 1
    return prefix_op_operand_size if has_0x66_prefix else default_operand_size

def get_regs_table(has_0x66_prefix, w):
    if w is None:
        return regs16 if has_0x66_prefix else regs32
    else:
        if has_0x66_prefix:
            return regs16w1 if w else regs16w0
        else:
            return regs32w1 if w else regs32w0

def decode_immediate_data(operand_size):
    out = 0
    for i in range(operand_size):
        out += (get_byte() << (i * 8))  # bc little endian
    return out

def decode_mrm_byte(has_0x66_prefix, regs_table):
    returned = []
    mrm_byte = get_byte()
    mod = get_mod(mrm_byte)
    if mod == 0b11:
        reg1, reg2 = get_mrm_args(mrm_byte)
        returned.append(regs_table[reg1])
        returned.append(regs_table[reg2])
    else:
        reg, rm = get_mrm_args(mrm_byte)
        temp_args = [] # f'[{"+".join(temp_args)}]'
        if has_0x66_prefix:
            #16 bit
            disp = decode_immediate_data(mod)
            if rm == 0b110 and not mod:
                disp = decode_immediate_data(2)
            else:
                temp_args.append(mrm_16_bit[rm])
            if not rm // 4:
                temp_args.append("DI" if rm % 2 else "SI")
            if mod or (rm == 0b110 and not mod):
                temp_args.append(str(disp))
        else:
            #32 bit
            if rm != 0b100:
                disp = decode_immediate_data(mrm_32_bit_mod_op[mod])
                if rm == 0b101 and not mod:
                    disp = decode_immediate_data(4)
                else:
                    temp_args.append(regs32[rm])
                if mod or (rm == 0b101 and not mod):
                    temp_args.append(str(disp))
            else:
                #sib byte
                sib_byte = get_byte()
                scale = get_mod(sib_byte)
                index, base = get_mrm_args(sib_byte)
                disp = decode_immediate_data(mrm_32_bit_mod_op[mod])
                if base == 0b101 and not mod:
                    disp = decode_immediate_data(4)
                else:
                    temp_args.append(regs32[base])
                if index != 0b100:
                    temp_args.append(f"{2**scale}*{regs32[index]}")
                if mod or (base == 0b101 and not mod):
                    temp_args.append(str(disp))
                        
        returned.append(regs_table[reg])
        returned.append(f"[{'+'.join(temp_args)}]")
    return returned

def read_command():
    global index, file
    def tipical_operation_no_1():
        nonlocal args, has_0x66_prefix
        w = opcode % 2
        regs_table = get_regs_table(has_0x66_prefix, w)
        if not opcode // 4 % 2:
            is_intel_notation = opcode // 2 % 2
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0] if is_intel_notation else temp[1])
            args.append(temp[1] if is_intel_notation else temp[0])
        else:
            #immediate to AL, AX, or EAX
            operand_size = get_operand_size_w(has_0x66_prefix, w)
            args.append(regs_table[0])
            args.append(str(decode_immediate_data(operand_size)))

    def tipical_operation_no_2():
        reg = opcode % 8
        regs_table = get_regs_table(has_0x66_prefix, None)
        args.append(regs_table[reg])
    
    has_lock_prefix = False  # 0xf0 LOCK
    has_rep_prefix  = False  # 0xf2, 0xf3 REP
    has_0x67_prefix = False  # change addr size
    has_0x66_prefix = False  # change operand size
    replace_default_seg_with = None
    is_extended_opcode = False
    opcode = None

    command = ""
    args = []  # ",".join(args)
    
    while opcode is None:
        byte = get_byte()
        if byte == 0xf0:
            has_lock_prefix = True
        elif byte in (0xf2, 0xf3):
            has_rep_prefix = True
        elif byte == 0x67:
            has_0x67_prefix = True
        elif byte == 0x66:
            has_0x66_prefix = True
        elif byte in change_segment_regs_prefs:
            replace_default_seg_with = byte
        elif byte == 0xf1:
            raise Exception("Undocumented")
        elif byte == 0x0f:
            is_extended_opcode = True
        else:
            opcode = byte
    if not is_extended_opcode:
        #0x00-0x05
        if (opcode & 0b1111_1000) == 0:
            command = "ADD"
            tipical_operation_no_1()
        #?
        elif (opcode & 0b1110_0111) == 0b0000_0110:
            command = "PUSH"
            args.append(sreg2_table[opcode // 8 % 4])
        elif (opcode & 0b1110_0111) == 0b0000_0111:
            #CS impossible
            command = "POP"
            args.append(sreg2_table[opcode // 8 % 4])
        #0x08-0x0d
        elif (opcode & 0b1111_1000) == 0b0000_1000:
            command = "OR"
            tipical_operation_no_1()
        #0x10-0x15
        elif (opcode & 0b1111_1000) == 0b0001_0000:
            command = "ADC"
            tipical_operation_no_1()
        #0x18-0x1d
        elif (opcode & 0b1111_1000) == 0b0001_1000:
            command = "SBB"
            tipical_operation_no_1()
        #0x20-0x25
        elif (opcode & 0b1111_1000) == 0b0010_0000:
            command = "AND"
            tipical_operation_no_1()
        #0x27
        elif opcode == 0b0010_0111:
            command = "DAA"
        #0x28-0x2d
        elif (opcode & 0b1111_1000) == 0b0010_1000:
            command = "SUB"
            tipical_operation_no_1()
        #0x2f
        elif opcode == 0b0010_1111:
            command = "DAS"
        #0x30-0x35
        elif (opcode & 0b1111_1000) == 0b0011_0000:
            command = "XOR"
            tipical_operation_no_1()
        #0x37
        elif opcode == 0b0011_0111:
            command = "AAA"
        #0x38-3d
        elif (opcode & 0b1111_1000) == 0b0011_1000:
            command = "CMP"
            tipical_operation_no_1()
        #0x3f
        elif opcode == 0b0011_1111:
            command = "AAS"
        #0x40-0x47
        elif (opcode & 0b1111_1000) == 0b0100_0000:
            command = "INC"
            tipical_operation_no_2()
        #0x48-0x4f
        elif (opcode & 0b1111_1000) == 0b0100_1000:
            command = "DEC"
            tipical_operation_no_2()
        #0x50-0x57
        elif (opcode & 0b1111_1000) == 0b0101_0000:
            command = "PUSH"
            tipical_operation_no_2()
        #0x58-0x5f
        elif (opcode & 0b1111_1000) == 0b0101_1000:
            command = "POP"
            tipical_operation_no_2()
        #0x60
        elif opcode == 0b0110_0000:
            command = "PUSHA"
        #0x61
        elif opcode == 0b0110_0001:
            command = "POPA"
        #0x62
        elif opcode == 0b0110_0010:
            command = "BOUND"
            mrm_byte = get_byte()
            regs_table = get_regs_table(has_0x66_prefix, None)
            
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0x63
        elif opcode == 0b0110_0011:
            command = "ARPL"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0x68, 0x6a
        elif (opcode & 0b1111_1101) == 0b0110_1000:
            command = "PUSH"
            s = opcode // 2 % 2
            operand_size = get_operand_size_w(has_0x66_prefix, not s)
            args.append(str(decode_immediate_data(operand_size)))
        #0x69, 0x6b
        elif (opcode & 0b1111_1101) == 0b0110_1001:
            command = "IMUL"
            s = opcode // 2 % 2
            operand_size = get_operand_size_w(has_0x66_prefix, not s)
            args.append(str(decode_immediate_data(operand_size)))
        #0x6c-0x6f
        #TODO
        #0x70-0x7f
        elif (opcode & 0b1111_0000) == 0b0111_0000:
            command = "J" + tttn_table[opcode % 16]
            addr_byte = get_byte()
            args.append("["+str(addr_byte)+"]")
        #0x80-0x83
        elif (opcode & 0b1111_1100) == 0b1000_0000:
            w = opcode % 2
            s = opcode // 2 % 2
            operand_size = 1
            if opcode & 0b11 == 0b1:
                operand_size = get_operand_size(has_0x66_prefix)
            regs_table = get_regs_table(has_0x66_prefix, w)
            mrm_byte = get_byte()
            index-=1
            temp = decode_mrm_byte(0, regs_table)
            command = nnn_byte_cmd[get_mrm_args(mrm_byte)[0]]
            args.append(temp[1])
            args.append(str(decode_immediate_data(operand_size)))
        #0x84-0x85
        elif (opcode & 0b1111_1110) == 0b1000_0100:
            command = "TEST"
            w = opcode % 2
            regs_table = get_regs_table(has_0x66_prefix, w)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0x86-0x87
        elif (opcode & 0b1111_1110) == 0b1000_0110:
            command = "XCHG"
            w = opcode % 2
            regs_table = get_regs_table(has_0x66_prefix, w)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0x88-0x8b
        elif (opcode & 0b1111_1100) == 0b1000_1000:
            command = "MOV"
            is_intel_notation = opcode // 2 % 2
            w = opcode % 2
            regs_table = get_regs_table(has_0x66_prefix, w)
            temp = decode_mrm_byte(0, regs_table)
            args.append(temp[0] if is_intel_notation else temp[1])
            args.append(temp[1] if is_intel_notation else temp[0])
        #0x8c,0x8e
        elif (opcode & 0b1111_1101) == 0b1000_1100:
            command = "MOV"
            regs_table = get_regs_table(has_0x66_prefix, None)
            is_intel_notation = opcode // 2 % 2
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0] if is_intel_notation else temp[1])
            args.append(temp[1] if is_intel_notation else temp[0])

        #0x8d
        elif opcode == 0b1000_1101:
            command = "LEA"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0x8f
        elif opcode == 0b1000_1111:
            command = "POP"
            mrm_byte = get_byte()
            mod = get_mod(mrm_byte)
            mrm_args = get_mrm_args(mrm_byte)
            index -=1
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66, regs_table)
            args.append(temp[1])
        #0x90
        elif opcode == 0b1001_0000:
            #Exchange eax with eax
            command = "NOP"
        #0x90-0x97
        elif (opcode & 0b1111_1000) == 0b1001_0000:
            command = "XCHG"
            regs_table = get_regs_table(has_0x66_prefix, None)
            args.append(regs_table[opcode % 8])
            args.append(regs_table[0])
        #0x98
        elif opcode == 0b1001_1000:
            command = "CBW"  # aka CWDE
        #0x99
        elif opcode == 0b1001_1001:
            command = "CDQ"  # aka CWD
        #0x9a
        elif opcode == 0b1001_1010:
            command = "CALL"
            operand_size = get_operand_size(has_0x66_prefix) + 2
            addr_bytes = decode_immediate_data(operand_size)
            args.append(str(addr_bytes))
        #0x9b
        elif opcode == 0b1001_1011:
            command = "WAIT"
        #0x9c
        elif opcode == 0b1001_1100:
            command = "PUSHF"
        #0x9d
        elif opcode == 0b1001_1101:
            command = "POPF"
        #0x9e
        elif opcode == 0b1001_1110:
            command = "SAHF"
        #0x9f
        elif opcode == 0b1001_1111:
            command = "LAHF"
        #0xa0-0xa3
        elif (opcode & 0b1111_1100) == 0b1010_0000:
            command = "MOV"
            args_order = opcode // 2 % 2
            w = opcode % 2
            regs_table = get_regs_table(has_0x66_prefix, w)
            operand_size = get_operand_size(has_0x66_prefix)
            addr_bytes = decode_immediate_data(operand_size)
            args.append("["+str(addr_bytes)+"]" if args_order else regs_table[0])
            args.append(regs_table[0] if args_order else "["+str(addr_bytes)+"]")
        #0xa4-0xa5
        elif (opcode & 0b1111_1110) == 0b1010_0100:
            command = "MOVS"
            #TODO
        #0xa6-0xa7
        elif (opcode & 0b1111_1110) == 0b1010_0110:
            command = "CMPS"
            #TODO
        #0xa8-0xa9
        elif (opcode & 0b1111_1110) == 0b1010_1000:
            command = "TEST"
            w = opcode % 2
            operand_size = get_operand_size_w(has_0x66_prefix, w)
            regs_table = get_regs_table(has_0x66_prefix, w)
            args.append(regs_table[0])
            args.append(str(decode_immediate_data(operand_size)))
        #0xaa-0xab
        elif (opcode & 0b1111_1110) == 0b1010_1010:
            command = "STOS"
        #0xac-0xad
        elif (opcode & 0b1111_1110) == 0b1010_1100:
            command = "LODS"
        #0xae-0xaf
        elif (opcode & 0b1111_1110) == 0b1010_1110:
            command = "SCAS"
        #0xb0-bf
        elif (opcode & 0b1111_0000) == 0b1011_0000:
            command = "MOV"
            w = opcode // 16 % 2
            reg = opcode % 8
            operand_size = get_operand_size_w(has_0x66_prefix, w)
            regs_table = get_regs_table(has_0x66_prefix, w)
            args.append(regs_table[reg])
            args.append(str(decode_immediate_data(operand_size)))
        #0xc0-0xc1
        elif (opcode & 0b1111_1110) == 0b1100_0000:
            w = opcode % 2
            operand_size = 1
            regs_table = get_regs_table(has_0x66_prefix, w)
            mrm_byte = get_byte()
            index-=1
            temp = decode_mrm_byte(0, regs_table)
            command = nnn_0xc0_byte_cmd[get_mrm_args(mrm_byte)[0]]
            args.append(temp[1])
            args.append(str(decode_immediate_data(operand_size)))
        #0xc2-0xc3
        elif (opcode & 0b1111_1110) == 0b1100_0010:
            command = "RET"
            if not opcode % 2:
                args.append(str(decode_immediate_data(2)))
        #0xc4
        elif opcode == 0b1100_0100:
            command = "LES"
            regs_table = get_regs_table(has_0x66_prefix, None)
            mrm_byte = get_byte()
            mod = get_mod(mrm_byte)
            mrm_args = get_mrm_args(mrm_byte)
            args.append(regs_table[mrm_args[0]])
            args.append(str(mrm_args[1]))#TODO
        #0xc5
        elif opcode == 0b1100_0101:
            command = "LDS"
            regs_table = get_regs_table(has_0x66_prefix, None)
            mrm_byte = get_byte()
            mod = get_mod(mrm_byte)
            mrm_args = get_mrm_args(mrm_byte)
            args.append(regs_table[mrm_args[0]])
            args.append(str(mrm_args[1]))#TODO
        #0xc6-0xc7
        elif (opcode & 0b1111_1110) == 0b1100_0110:
            command = "MOV"
            w = opcode % 2
            regs_table = get_regs_table(has_0x66_prefix, w)
            operand_size = get_operand_size_w(has_0x66_prefix, w)
            args.append(decode_mrm_byte(has_0x66_prefix, regs_table)[1])
            args.append(str(decode_immediate_data(operand_size)))
        #0xc8
        elif opcode == 0b1100_1000:
            command = "ENTER"
            args.append(str(decode_immediate_data(2)))
            args.append(str(decode_immediate_data(1)))
        #0xc9
        elif opcode == 0b1100_1001:
            command = "LEAVE"
        #0xca
        elif opcode == 0b1100_1010:
            command = "RET"
            args.append(str(decode_immediate_data(2)))
        #0xcb
        elif opcode == 0b1100_1011:
            command = "RET"
        #0xcc
        elif opcode == 0b1100_1100:
            command = "INT"
            args.append("3")
        #0xcd
        elif opcode == 0b1100_1101:
            command = "INT"
            args.append(str(decode_immediate_data(2)))
        #0xce
        elif opcode == 0b1100_1110:
            command = "INTO"
        #0xcf
        elif opcode == 0b1100_1111:
            command = "IRET"
        #0xd0-0xd3
        elif (opcode & 0b1111_1100) == 0b1101_0000:
            w = opcode % 2
            regs_table = get_regs_table(has_0x66_prefix, w)
            mrm_byte = get_byte()
            index-=1
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            command = nnn_0xc0_byte_cmd[get_mrm_args(mrm_byte)[0]]
            args.append(temp[1])
            if opcode // 2 % 2:
                args.append("CL")
            else:
                args.append("1")
        #0xd4
        elif opcode == 0b1101_0100:
            sbyte = get_byte()
            command = "AAM"
        #0xd5
        elif opcode == 0b1101_0101:
            sbyte = get_byte()
            command = "AAD"
        #0xd6
        elif opcode == 0b1101_0110:
            command = "SALC"
        #0xd7
        elif opcode == 0b1101_0111:
            command = "XLAT"
        #fpu commands 0xd8-0xdf
        #0xd8
##        elif opcode == 0b1101_1000:
##            nnn_byte = get_byte()
##            mod = get_mod(nnn_byte)
##            nnn_args = get_mrm_args(nnn_byte)
##            command = fpu_0xd8_byte_cmd[nnn_args[0]]
##            if mod == 0b11:
##                args.append("ST(0)")
##                args.append(f"ST({opcode % 8})")
        #0xdb
        elif opcode == 0b1101_1011:
            nnn_byte = get_byte()
            optype = get_mrm_args(nnn_byte)[0]
            index-=1
            if get_mod(nnn_byte) != 0b11:
                command = fpu_0xdb_byte_cmd[optype]
            else:
                pass
            temp = decode_mrm_byte(has_0x66_prefix, get_regs_table(has_0x66_prefix, None))
            args.append(temp[1])
        #0xdd
        elif opcode == 0b1101_1101:
            nnn_byte = get_byte()
            optype = get_mrm_args(nnn_byte)[0]
            index-=1
            if get_mod(nnn_byte) != 0x11:
                command = fpu_0xdd_byte_cmd[optype]
            else:
                pass
            temp = decode_mrm_byte(has_0x66_prefix, get_regs_table(has_0x66_prefix, None))
            args.append(temp[1])
        #else
        elif (opcode & 0b1111_1000) == 0b1101_1000:
            command = "ESC"
            get_byte()
        #0xe0
        elif opcode == 0b1110_0000:
            command = "LOOPNE"
            args.append(str(decode_immediate_data(1)))
        #0xe1
        elif opcode == 0b1110_0001:
            command = "LOOPE"
            args.append(str(decode_immediate_data(1)))
        #0xe2
        elif opcode == 0b1110_0010:
            command = "LOOP"
            args.append(str(decode_immediate_data(1)))
        #0xe3
        elif opcode == 0b1110_0011:
            command = "JCXZ"
            args.append(str(decode_immediate_data(1)))
        #0xe4-0xe5,0xe8-0xe9
        elif (opcode & 0b1111_0110) == 0b1110_0100:
            command = "IN"
            w = opcode % 2
            regs_table = get_regs_table(has_0x66_prefix, w)
            args.append(regs_table[0])
            if not opcode // 8 % 2:
                args.append(str(decode_immediate_data(1)))
            else:
                args.append("DX")
        #0xe6-0xe7,0xea-0xeb
        elif (opcode & 0b1111_0110) == 0b1110_0110:
            command = "OUT"
            w = opcode % 2
            regs_table = get_regs_table(has_0x66_prefix, w)
            if not opcode // 8 % 2:
                args.append(str(decode_immediate_data(1)))
            else:
                args.append("DX")
            args.append(regs_table[0])
        #0xe8
        elif opcode == 0b1110_1000:
            command = "CALL"
            operand_size = get_operand_size(has_0x66_prefix)
            args.append("["+str(decode_immediate_data(operand_size))+"]")
        #0xe9
        elif opcode == 0b1110_1001:
            command = "JMP"
            operand_size = get_operand_size(has_0x66_prefix)
            args.append("["+str(decode_immediate_data(operand_size))+"]")
        #0xea
        elif opcode == 0b1110_1010:
            command = "JMP"
            operand_size = get_operand_size(has_0x66_prefix) + 2
            args.append("["+str(decode_immediate_data(operand_size))+"]")
        #0xeb
        elif opcode == 0b1110_1011:
            command = "JMP"
            args.append("["+str(decode_immediate_data(1))+"]")
        #prefixes 0xf0-0xf3
        #0xf4
        elif opcode == 0b1111_0100:
            command = "HLT"
        #0xf5
        elif opcode == 0b1111_0101:
            command = "CMC"
        #0xf6-0xf7
        elif (opcode & 0b1111_1110) == 0b1111_0110:
            w = opcode % 2
            mrm_byte = get_byte()
            optype = get_mrm_args(mrm_byte)[0]
            command = nnn_0xf6_byte_cmd[optype]
            regs_table = get_regs_table(has_0x66_prefix, w)
            index-=1
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[1])
            if not optype:
                args.append(str(
                    decode_immediate_data(get_operand_size_w(has_0x66_prefix, w))
                ))
        #0xf8
        elif opcode == 0b1111_1000:
            command = "CLC"
        #0xf9
        elif opcode == 0b1111_1001:
            command = "STC"
        #0xfa
        elif opcode == 0b1111_1010:
            command = "CLI"
        #0xfb
        elif opcode == 0b1111_1011:
            command = "STI"
        #0xfc
        elif opcode == 0b1111_1100:
            command = "CLD"
        #0xfd
        elif opcode == 0b1111_1101:
            command = "STD"
        #0xfe-0xff
        elif (opcode & 0b1111_1110) == 0b1111_1110:
            regs_table = get_regs_table(has_0x66_prefix, None)
            mrm_byte = get_byte()
            optype = get_mrm_args(mrm_byte)[0]
            index-=1
            temp = decode_mrm_byte(0, regs_table)
            command = nnn_0xff_byte_cmd[optype]
            args.append(temp[1])
        else:
            raise Exception(f"Unknown opcode: {hex(opcode)}")
    else:
        #0x00
        #TODO
        #0x01
        #TODO
        #0x02
        if opcode == 0b0000_0010:
            command = "LAR"
            temp = decode_mrm_byte()
            args.append(temp[0])
            args.append(temp[1])
        #0x03
        elif opcode == 0b0000_0011:
            command = "LSL"
            temp = decode_mrm_byte()
            args.append(temp[0])
            args.append(temp[1])
        #0x06
        elif opcode == 0b0000_0110:
            command = "CLTS"
        #0x08
        elif opcode == 0b0000_1000:
            command = "INVD"
        #0x09
        elif opcode == 0b0000_1001:
            command = "WBINVD"
        #?
        elif (opcode & 0b1111_1101) == 0b0010_0000:
            command = "MOV"
            is_intel_notation = opcode // 2 % 2
            regs_table = get_regs_table(has_0x66_prefix, None)
            creg, reg, = get_mrm_args(get_byte)
            args.append(control_regs[creg] if is_intel_notation else regs_table[reg])
            args.append(regs_table[reg] if is_intel_notation else control_regs[creg])
        #?
        elif (opcode & 0b1111_1101) == 0b0010_0001:
            command = "MOV"
            is_intel_notation = opcode // 2 % 2
            regs_table = get_regs_table(has_0x66_prefix, None)
            creg, reg, = get_mrm_args(get_byte)
            args.append(debug_regs[creg] if is_intel_notation else regs_table[reg])
            args.append(regs_table[reg] if is_intel_notation else debug_regs[creg])
        #0x80-0x8f
        elif (opcode & 0b1111_0000) == 0b1000_0000:
            command = "J" + tttn_table[opcode % 16]
            operand_size = get_operand_size(has_0x66_prefix)
            args.append("["+str(decode_immediate_data(operand_size))+"]")
        #0x90-0x9f
        elif (opcode & 0b1111_0000) == 0b1001_0000:
            command = "SET" + tttn_table[opcode % 16]
            temp = decode_mrm_byte(has_0x66_prefix, get_regs_table(has_0x66_prefix, None))
            args.append(temp[1])
        #0xa0
        elif opcode == 0b1010_0000:
            command = "PUSH"
            args.append("FS")
        #0xa1
        elif opcode == 0b1010_0001:
            command = "POP"
            args.append("FS")
        #0xa8
        elif opcode == 0b1010_1000:
            command = "PUSH"
            args.append("GS")
        #0xa9
        elif opcode == 0b1010_1001:
            command = "POP"
            args.append("GS")
        #0xa3
        elif opcode == 0b1010_0011:
            command = "BT"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xab
        elif opcode == 0b1010_1011:
            command = "BTS"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xa4-0xa5
        elif (opcode & 0b1111_1110) == 0b1010_0100:
            command = "SHLD"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
            if not opcode % 2:
                args.append(str(get_byte()))
            else:
                args.append("CL")
        #0xb0-0xb1
        elif (opcode & 0b1111_1110) == 0b1011_0000:
            command = "CMPXCHG"
            w = opcode % 2
            regs_table = get_regs_table(has_0x66_prefix, w)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xac-0xad
        elif (opcode & 0b1111_1110) == 0b1010_1100:
            command = "SHRD"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
            if not opcode % 2:
                args.append(str(get_byte()))
        #0xaf
        elif opcode == 0b1010_1111:
            command = "IMUL"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xb2
        elif opcode == 0b1011_0010:
            command = "LSS"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xb3
        elif opcode == 0b1011_0011:
            command = "BTR"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xb4
        elif opcode == 0b1011_0100:
            command = "LFS"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xb5
        elif opcode == 0b1011_0101:
            command = "LGS"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xb6-0xb7
        elif (opcode & 0b1111_1110) == 0b1011_0110:
            command = "MOVZX"
            w = opcode % 2
            regs_table = get_regs_table(has_0x66_prefix, w)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xba
        #TODO
        #0xbb
        elif opcode == 0b1011_1011:
            command = "BTC"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xbc
        elif opcode == 0b1011_1100:
            command = "BSF"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xbd
        elif opcode == 0b1011_1101:
            command = "BSR"
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xbe-0xbf
        elif (opcode & 0b1111_1110) == 0b1011_1110:
            command = "MOVSX"
            w = opcode % 2
            regs_table = get_regs_table(has_0x66_prefix, w)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xc0-0xc1
        elif (opcode & 0b1111_1110) == 0b1100_0000:
            command = "XADD"
            w = opcode % 2
            regs_table = get_regs_table(has_0x66_prefix, w)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        #0xc8-0xcf
        elif (opcode & 0b1111_1000) == 0b1100_1000:
            command = "BSWAP"
            _, reg = get_mrm_args(opcode)
            regs_table = get_regs_table(has_0x66_prefix, None)
            args.append(regs_table[reg])
        #0x40-0x4f
        elif (opcode & 0b1111_0000) == 0b0100_0000:
            command = "CMOV" + tttn_table[opcode % 16]
            regs_table = get_regs_table(has_0x66_prefix, None)
            temp = decode_mrm_byte(has_0x66_prefix, regs_table)
            args.append(temp[0])
            args.append(temp[1])
        else:
            raise Exception(f"Unknown opcode: {hex(opcode)}")
    
    end_index = index
    out = ""
    if True:
        out += "".join(list(map(lambda x: fill_to_2(hex(x)[2:]), data[start_index: end_index]))) + " "
    if has_lock_prefix:
        out += "LOCK "
    if has_rep_prefix:
        out += "REP "
    out += command
    if args:
        out += " " + ", ".join(args)
    file.write(out + "\n")

file = open("a.asm", "w+")
file.write("")
plain_print = False
while index < length:
    start_index = index
    if not plain_print:
        try:
            read_command()
        except Exception as ex:
            print(type(ex).__name__, ex)
            file.write("".join(list(map(lambda x: fill_to_2(hex(x)[2:]), data[start_index: index]))))
            plain_print = True
    else:
        file.write(hex(get_byte())[2:])
file.close()
        
