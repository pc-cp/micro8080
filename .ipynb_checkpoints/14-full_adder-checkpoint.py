# The Basic Gates
class AND:
    def __init__(self, nin=2):
        self.nin = nin

    def __call__(self, x):
        assert len(x) == self.nin, f"Expected {self.nin} inputs"
        result = x[0]
        # Chain bitwise AND over all inputs
        for val in x[1:]:
            result &= val
        return result

class OR:
    def __init__(self, nin=2):
        self.nin = nin

    def __call__(self, x):
        assert len(x) == self.nin, f"Expected {self.nin} inputs"
        result = x[0]
        # Chain bitwise OR over all inputs
        for val in x[1:]:
            result |= val
        return result

class Inverter:
    """The NOT gate, It strictly takes 1 input."""
    def __init__(self):
        self.nin = 1

    def __call__(self, x):
        assert len(x) == self.nin, "Inverter takes exactly 1 input"
        # If 1, return 0. If 0, return 1.
        return 1 - x[0]

# Composing Complex Gates
class NAND:
    def __init__(self, nin=2):
        self.nin = nin
        # NAND is just an AND gate followed by an Inverter
        self.and_gate = AND(nin)
        self.inverter = Inverter()

    def __call__(self, x):
        # x -> and -> invert -> out
        return self.inverter([self.and_gate(x)])

class NOR:
    def __init__(self, nin=2):
        self.nin = nin
        # NOR is just an OR gate followed by an Inverter
        self.or_gate = OR(nin)
        self.inverter = Inverter()

    def __call__(self, x):
        # x -> or -> invert -> out
        return self.inverter([self.or_gate(x)])

# Composing XOR gate use OR, NAND and AND gate
class XOR:
    def __init__(self):
        self.nin = 2

        self.or_gate = OR(self.nin)
        self.nand_gate = NAND(self.nin)
        self.and_gate = AND(self.nin)

    def __call__(self, x):
        assert len(x) == self.nin, "XOR takes exactly 2 inputs"
        # x -> or -> o1
        # x -> nand -> o2
        # and(o1, o2) -> out
        o1 = self.or_gate(x)
        o2 = self.nand_gate(x)
        return self.and_gate([o1, o2])

class HalfAdder:
    def __init__(self):
        self.nin = 2
        # The two components we need
        self.xor_gate = XOR()
        self.and_gate = AND(self.nin)

    def __call__(self, x):
        assert len(x) == self.nin, "Half Adder takes exactly 2 inputs"
        # Calculate Sum and Carry
        final_sum = self.xor_gate(x)
        final_carry = self.and_gate(x)

        # Return them as a tuple
        return final_carry, final_sum


class FullAdder:
    def __init__(self):
        self.nin = 3 # # Carry-In, A, and B

        # A full adder is literally just two half adders and an OR gate
        self.ha1 = HalfAdder()
        self.ha2 = HalfAdder()
        self.or_gate = OR(2)

    def __call__(self, x):
        # Carry-In, A, and B
        if len(x) == self.nin:
            carry_in, a, b = x[0], x[1], x[2]
        else:
            carry_in = 0
            a, b = x[0], x[1]

        # First Half-Adder adds A and B
        carry1, sum1 = self.ha1([a, b])

        # Second Half-Adder adds previous sum and the Carry-In
        carry2, final_sum = self.ha2([carry_in, sum1])

        # The OR gate catches the carry from either Half-Adder
        final_carry = self.or_gate([carry2, carry1])

        # Return them as a tuple
        return final_carry, final_sum

class NBitAdderWithCarryOut:
    def __init__(self, nbits):
        self.nbits = nbits # Carry_In, A, and B
        # Instantiate 'n' Full Adders
        self.fulladders = [FullAdder() for _ in range(self.nbits)]

    def __call__(self, x, y, last_carry_in=0):
        assert len(x) == self.nbits and len(y) == self.nbits, f"Inputs must be {self.nbits} bits long"
        final_sums = []
        final_carrys = [last_carry_in]

        # Iterate backwards: start from the far right and move left
        for idx in reversed(range(self.nbits)):
            carry_in = final_carrys[0]
            a = x[idx]
            b = y[idx]
            
            # Run the Full Adder for this column
            carry_out, sum_out = self.fulladders[idx]([carry_in, a, b])
            
            final_carrys = [carry_out] + final_carrys
            final_sums = [sum_out] + final_sums
        # The final carry out of the MSB is still sitting at index 0
        return final_carrys[0], final_sums

def int_to_8bit_list(num):
    """Converts an integer to a 8-bit list with MSB at index 0."""
    # format(num, '08b') automatically converts to binary and pads to 8 bits
    bin_str = format(num, '08b')
    return [int(bit) for bit in bin_str]

def int_to_16bit_list(num):
    """Converts an integer to a 16-bit list with MSB at index 0."""
    # format(num, '016b') automatically converts to binary and pads to 16 bits
    bin_str = format(num, '016b')
    return [int(bit) for bit in bin_str]

def bit_list_to_int(bit_list):
    """Converts a bit list (MSB at index 0) back to a standard integer."""
    bin_str = "".join(str(bit) for bit in bit_list)
    return int(bin_str, 2)

