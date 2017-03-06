import dis
import operator
import builtins
import sys
import collections


class VirtualMachine:
    def __init__(self):
        self.stack = []
        self.builtins_names = builtins.__dict__

    def popn(self, n):
        if n:
            elements = self.stack[-n:]
            self.stack[-n:] = []
            return elements
        else:
            return []

    def POP_TOP(self):
        self.stack.pop()

    def ROT_TWO(self):
        a, b = self.popn(2)
        self.stack.append(b, a)

    def ROT_THREE(self):
        a, b, c = self.popn(3)
        self.stack.append(c, a, b)

    def DUP_TOP(self):
        self.append(self.stack[-1])

    def DUP_TOP_TWO(self):
        a, b = self.popn(2)
        self.stack.append(a, b, a, b)

    def LOAD_CONST(self, const=None):
        self.stack.append(const)

    def LOAD_FAST(self, name):
        self.stack.append(globals()[name])

    def STORE_FAST(self, name):
        val = self.stack.pop()
        globals()[name] = val

    def DELETE_FAST(self, name):
        del globals()[name]

    def LOAD_NAME(self, name):
        if name in self.builtins_names:
            val = self.builtins_names[name]
            self.stack.append(val)
        else:
            self.stack.append(globals()[name])

    def STORE_NAME(self, name):
        val = self.stack.pop()
        globals()[name] = val

    def DELETE_NAME(self, name):
        del globals()[name]

    def LOAD_GLOBAL(self, name):
        if name in self.builtins_names:
            val = self.builtins_names[name]
            self.stack.append(val)
        else:
            self.stack.append(globals()[name])

    def STORE_GLOBAL(self, name):
        val = self.stack.pop()
        globals()[name] = val

    def DELETE_GLOBAL(self, name):
        del globals()[name]

    def STORE_SUBSCR(self):
        tos2, tos1, tos = self.popn(3)
        tos1[tos] = tos2

    def DELETE_SUBSCR(self):
        tos1, tos = self.popn(2)
        del tos1[tos]

    def CALL_FUNCTION(self, arg):
        return self.call_function(arg, [], {})

    def call_function(self, arg, args, kwargs):
        len_kwargs, len_args = divmod(arg, 256)
        named_args = {}
        for i in range(len_kwargs):
            key, val = self.popn(2)
            named_args[key] = val
        named_args.update(kwargs)
        cortege_args = self.popn(len_args)
        cortege_args.extend(args)
        func = self.stack.pop()
        self.stack.append(func(*cortege_args, **named_args))

    def RETURN_VALUE(self):
        top = self.stack[-1:]
        self.stack.pop()

    def OPERATOR(self, instruction, argument):
        unary_operators = {
            'POSITIVE': operator.pos,
            'NEGATIVE': operator.neg,
            'NOT': operator.not_,
            'CONVERT': repr,
            'INVERT': operator.invert,
        }
        binary_operators = {
            '>': operator.gt,
            '<': operator.lt,
            '<=': operator.le,
            '==': operator.eq,
            '!=': operator.ne,
            '>=': operator.ge,
            'is': operator.is_,
            'is not': operator.is_not,
            'SUBSCR': operator.getitem,
            'LSHIFT': operator.lshift,
            'RSHIFT': operator.rshift,
            'AND': operator.and_,
            'XOR': operator.xor,
            'OR': operator.or_,
            'POWER': pow,
            'MULTIPLY': operator.mul,
            'FLOOR_DIVIDE': operator.floordiv,
            'TRUE_DIVIDE': operator.truediv,
            'MODULO': operator.mod,
            'ADD': operator.add,
            'SUBTRACT': operator.sub,
        }
        if instruction.startswith('UNARY_'):
            op = instruction[6:]
            x = self.popn(1)
            self.stack.append(unary_operators[op](x))
        else:
            if instruction.startswith('BINARY_'):
                op = instruction[7:]
            elif instruction.startswith('INPLACE_'):
                op = instruction[8:]
            else:
                op = argument
            x, y = self.popn(2)
            self.stack.append(binary_operators[op](x, y))

    def LOAD_ATTR(self, attr):
        cur_object = self.stack.pop()
        value = getattr(cur_object, attr)
        self.stack.append(value)

    def STORE_ATTR(self, name):
        value, cur_object = self.popn(2)
        setattr(object, name, value)

    def UNPACK_SEQUENCE(self, count):
        sequence = self.stack.pop()
        for element in reversed(sequence):
            self.stack.append(element)

    def BUILD_SLICE(self, argc):
        if argc == 2:
            x, y = self.popn(2)
            self.stack.append(slice(x, y))
        elif argc == 3:
            x, y, z = self.popn(3)
            self.stack.append(slice(x, y, z))

    def BUILD_LIST(self, count):
        elements = self.popn(count)
        self.stack.append(elements)

    def LIST_APPEND(self, count):
        value = self.stack.pop()
        cur_list = self.stack[-count]
        cur_list.append(value)

    def BUILD_MAP(self, count):
        if count:
            elements = self.popn(count * 2)
            cur = {}
            for i in range(count):
                cur[elements[i]] = elements[i + 1]
            self.stack.append(dict(cur))
        else:
            self.stack.append({})

    def STORE_MAP(self):
        cur_map, value, key = self.popn(3)
        cur_map[key] = value
        self.stack.append(cur_map)

    def MAP_ADD(self, count):
        value, key = self.popn(2)
        cur_map = self.stack[-count]
        cur_map[key] = value

    def BUILD_TUPLE(self, count):
        elements = self.popn(count)
        self.stack.append(tuple(elements))

    def BUILD_SET(self, count):
        elements = self.popn(count)
        self.stack.append(set(elements))

    def SET_ADD(self, count):
        value = self.stack.pop()
        cur_set = self.stack[-count]
        cur_set.add(value)

    def JUMP_IF_TRUE(self, jump):
        val = self.stack[-1]
        if val:
            return False
        else:
            return True

    def JUMP_IF_FALSE(self, jump):
        val = self.stack[-1]
        if not val:
            return False
        else:
            return True

    def POP_JUMP_IF_FALSE(self, jump):
        val = self.stack.pop()
        if not val:
            return False
        else:
            return True

    def POP_JUMP_IF_TRUE(self, jump):
        val = self.stack.pop()
        if val:
            return False
        else:
            return True

    def SETUP_LOOP(self, dest):
        pass

    def CONTINUE_LOOP(sel):
        pass

    def POP_BLOCK(self):
        pass

    def GET_ITER(self):
        self.stack.append(iter(self.stack.pop()))

    def FOR_ITER(self, jump):
        try:
            tos = self.stack[-1]
            self.stack.append(next(tos))
        except StopIteration:
            self.stack.pop()
            return True

    def find_index_to_jump(self, inp_dict, arg):
        values = list(inp_dict.values())
        index = 0
        for i in range(len(values)):
            if values[i][3] == arg:
                return index
            index += 1

    def find_pop_block_ind(self, inp_dict):
        values = list(inp_dict.values())
        index = 0
        for i in range(len(values)):
            if values[i][2] == 'POP_BLOCK':
                return index
            index += 1

    def update_index(self, size, i):
        size -= 1
        i += 1
        return size, i

    def run(self, code, global_names=None, local_names=None):
        instructions = dis.get_instructions(code)
        size = 0
        instr = collections.OrderedDict()
        for instruction in instructions:
            instr[size] = [instruction.opcode, instruction.argval,
                           instruction.opname, instruction.offset]
            size += 1
        i = 0
        start_size = size
        while size:
            argument = instr[i][1]
            instruction_name = instr[i][2]
            operators = ['UNARY_', 'BINARY_',
                         'INPLACE_', 'INPLACE_', 'COMPARE_']
            #if any([instruction_name.startswith(op)
            #        for op in operators]):
            #    self.OPERATOR(instruction_name, argument)
            #    size, i = self.update_index(size, i)
            if instruction_name == 'BREAK_LOOP':
                i = self.find_pop_block_ind(instr)
                size = start_size - i
            elif instruction_name == 'FOR_ITER':
                ans = self.FOR_ITER(argument)
                if ans:
                    i = self.find_pop_block_ind(instr)
                    size = start_size - i
                else:
                    size, i = self.update_index(size, i)
            elif instruction_name in ['JUMP_ABSOLUTE', 'JUMP_FORWARD']:
                i = self.find_index_to_jump(instr, argument)
                size = start_size - i
            elif instruction_name.find('JUMP') != -1:
                bytecode_method = getattr(self, instruction_name)
                ans = bytecode_method(argument)
                if not ans:
                    i = self.find_index_to_jump(instr, argument)
                    size = start_size - i
                else:
                    size, i = self.update_index(size, i)
            else:
                bytecode_method = getattr(self, instruction_name)
                if argument is None:
                    bytecode_method()
                else:
                    bytecode_method(argument)
                size, i = self.update_index(size, i)

if __name__ == "__main__":
    compiled = compile('x = 2; y = 2; print(x + y)', "<stdin>", 'exec')
    VirtualMachine().run(compiled)