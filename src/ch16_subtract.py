# ch16_subtract.py
# include some basic data process function and nBit_Adder_with_two_complement
def int_to_nbit_list(num, nbits=8):
    """
    Converts an integer to an n-bit list using our simulated hardware 
    for Two's Complement (Invert and Add 1).
    """
    abs_val = abs(num)
    bin_str = format(abs_val, f'0{nbits}b')
    bit_list = [int(bit) for bit in bin_str]

    if num >= 0:
        return bit_list

    # --- THE HARDWARE WAY ---
    
    # Step A: Pass the bits through our simulated Inverters
    my_inverter = Inverter()
    inverted_bits = [my_inverter([bit]) for bit in bit_list]

    # Step B: Wire up an adder to add 1
    adder = nBit_Adder(nbits)
    
    # Step B: Add 0, but set the Carry-In pin to 1
    zero_bits = [0 for _ in range(nbits)]
    overflow_carry, final_bits = adder(inverted_bits, zero_bits, last_carry_in=1)
    
    return final_bits
    
# Now you can easily create your 8-bit and 16-bit specific helpers:
def int_to_8bit_list(num):
    return int_to_nbit_list(num, nbits=8)

def int_to_16bit_list(num):
    return int_to_nbit_list(num, nbits=16)

def bit_list_to_int(bit_list, signed=True):
    """Converts a bit list (MSB at index 0) back to a standard integer."""
    bin_str = "".join(str(bit) for bit in bit_list)
    val = int(bin_str, 2)
    
    # If we are treating this as a signed Two's Complement number...
    if signed:
        # Check the Most Significant Bit (Index 0)
        msb = bit_list[0]
        if msb == 1:
            # If MSB is 1, it's negative. We calculate its true negative value.
            # E.g., for 8 bits: val - 2^8 (val - 256)
            val = val - (1 << len(bit_list)) 
            
    return val

class nBit_Adder_with_two_complement:
    def __init__(self, nbits):
        self.nbits = nbits # Carry_In, A, and B
        # Instantiate 'n' Full Adders
        self.fulladders = [FullAdder() for _ in range(self.nbits)]

        # below gate use for overflow
        self.inverter = Inverter()
        # AND gate detects an overflow condition for negative numbers.
        # the sign bit of x and y inputs are both 1 and the sign
        # of the sum is 0.
        self.and_gate = AND(nin=3)
        # NOR gate detects an overflow condition for positive numbers.
        # the sign bit of x and y inputs are both 0 and the sign
        # of the sum is 1.
        self.nor_gate = NOR(nin=3)
        
        self.or_gate = OR(nin=2)
        
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

        # we return third result that reflect overflow use two-complement
        invert_msb_of_final_sum = self.inverter([final_sums[0]])
        msb_of_x = x[0]
        msb_of_y = y[0]

        out_of_and_gate = self.and_gate([invert_msb_of_final_sum, msb_of_x, msb_of_y])
        out_of_nor_gate = self.nor_gate([invert_msb_of_final_sum, msb_of_x, msb_of_y])
        overflow = self.or_gate([out_of_and_gate, out_of_nor_gate])
        
        return overflow, final_carrys[0], final_sums

