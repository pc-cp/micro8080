from src.utils import *

class RAM_8_1:
    """
    An 8x1 Memory Chip (8 words, 1 bit per word).
    Combines the Decoder, the Memory Cells, and the Selector to build
    a fully functional, addressable memory block.
    """
    def __init__(self):
        self.capacity = 8  # 8 words
        self.word_size = 1  # 1 bit per word

        self.decoder = Decoder_3_8()
        self.memory_cells = [NBitsMemory(self.word_size) for _ in range(self.capacity)]  # 8 words of 1 bit each
        self.selector = Selector_8_1()

    def __call__(self, address, data_in, write):
        assert len(address) == 3, "Address must be 3 bits long"
        assert len(data_in) == self.word_size, f"Data input must be {self.word_size} bits long"
        assert write in [0, 1], "Write signal must be 0 or 1"
        
        # Use the decoder to determine which memory cell to write to
        write_lines = self.decoder(address, write)
        for i in range(self.capacity):
            self.memory_cells[i](data_in, write_lines[i])  # Write data to the selected memory cell

    def read(self, address):
        # Read from all memory cells and use the selector to get the output from the selected cell
        out_from_memory = [cell.read()[0] for cell in self.memory_cells]
        return self.selector(address, out_from_memory)

class RAM_8_8:
    """
    An 8x8 Memory Chip (8 Bytes total).
    Wires eight 8x1 RAM chips in parallel to allow reading/writing full 8-bit bytes.
    """
    def __init__(self, word_size=8):
        self.capacity = 8  # 8 words
        self.word_size = word_size
        self.ram_8_1_cells = [RAM_8_1() for _ in range(self.word_size)]
        
    def __call__(self, address, data_in, write):
        assert len(address) == 3, "Address must be 3 bits"
        assert len(data_in) == self.word_size, f"Data must be {self.word_size} bits"
        assert write in [0, 1], "Write signal must be 0 or 1"

        for bit in range(self.word_size):
            self.ram_8_1_cells[bit](address, [data_in[bit]], write)  # Write each bit to the selected memory cell

    def read(self, address):
        bits = []
        for bit in range(self.word_size):
            bits = bits + self.ram_8_1_cells[bit].read(address)
        return bits
    

def test_decoder_3_8_isolation():
    """Proves the decoder NEVER lights up more than one wire at a time."""
    decoder = Decoder_3_8()

    # Address 5 (101)
    out = decoder([1, 0, 1], enable=1)
    assert sum(out) == 1, "FATAL: Decoder lit up multiple wires! Short circuit!"
    assert out[5] == 1, "Decoder sent the signal to the wrong memory bank."

    # Address 1 (001)
    out = decoder([0, 0, 1], enable=1)
    assert sum(out) == 1, "FATAL: Decoder lit up multiple wires! Short circuit!"
    assert out[1] == 1, "Decoder sent the signal to the wrong memory bank."

    # Write Enable Shielding
    out_disabled = decoder([1, 0, 1], enable=0)
    assert sum(out_disabled) == 0, "FATAL: Decoder leaked signal when Enable was 0!"

def test_ram_8_1_logic():
    """Proves an 8x1 memory block protects data and prevents crosstalk."""
    ram = RAM_8_1()
    address = [0, 1, 1] # Address 3

    # 1. Basic Write
    ram(address, [1], write=1)
    assert ram.read(address) == [1], "Failed to write 1."

    # 2. Ghost Write (Protects against Write=0)
    ram(address, [0], write=0)
    assert ram.read(address) == [1], "GHOST WRITE: Memory overwrote data while WE=0!"

    # 3. Crosstalk Test (Alternating patterns)
    addresses = [[(i >> 2) & 1, (i >> 1) & 1, i & 1] for i in range(8)]
    for i, addr in enumerate(addresses):
        ram(addr, [i % 2], write=1)
        
    for i, addr in enumerate(addresses):
        expected_bit = i % 2
        actual_bit = ram.read(addr)[0]
        assert actual_bit == expected_bit, f"CROSSTALK at address {addr}."

def test_ram_8_8_crosstalk():
    """Fills all 8 bytes of memory with unique patterns to verify column/row isolation."""
    ram = RAM_8_8()
    addresses = [[(i >> 2) & 1, (i >> 1) & 1, i & 1] for i in range(8)]
    
    # 8 highly distinct 8-bit patterns
    patterns = [
        [0,0,0,0,0,0,0,0], [1,1,1,1,1,1,1,1], [1,0,1,0,1,0,1,0], [0,1,0,1,0,1,0,1],
        [1,1,0,0,1,1,0,0], [0,0,1,1,0,0,1,1], [1,1,1,1,0,0,0,0], [0,0,0,0,1,1,1,1]
    ]
    
    for addr, data in zip(addresses, patterns):
        ram(addr, data, write=1)
        
    for addr, expected_data in zip(addresses, patterns):
        out = ram.read(addr)
        assert out == expected_data, f"Crosstalk at address {addr}! Expected {expected_data}, got {out}"

def test_ram_16_8_fatigue():
    """Rapidly flips every single bit in a specific byte to ensure latches don't lock up."""
    ram = RAM_16_8()
    addr = [0, 1, 0, 1] # Address 5
    
    pattern1 = [1, 1, 1, 1, 0, 0, 0, 0]
    pattern2 = [0, 0, 0, 0, 1, 1, 1, 1]
    
    for i in range(50):
        data = pattern1 if i % 2 == 0 else pattern2
        ram(addr, data, write=1)
        out = ram.read(addr)
        assert out == data, f"Fatigue failure on write cycle {i}. Bits stuck!"

def test_ram_64kb_boundaries_and_routing():
    """Tests writing to extreme boundaries and ensures Chip Select logic routing works."""
    ram = RAM_64KB()
    data_zeros = [0] * 8

    # 1. Extreme Boundaries
    addr_first = [0] * 16
    data_first = [1, 0, 1, 0, 1, 0, 1, 0]
    
    addr_last = [1] * 16
    data_last = [0, 1, 0, 1, 0, 1, 0, 1]
    
    ram(addr_first, data_first, write=1)
    ram(addr_last, data_last, write=1)
    
    assert ram.read(addr_first) == data_first, "Failed to read Address 0x0000"
    assert ram.read(addr_last) == data_last, "Failed to read Address 0xFFFF"
    
    # 2. Tri-State Buffer Isolation
    assert ram.read(addr_first, enable=0) == data_zeros, "Buffer leaked signal when disabled!"
    assert ram.read(addr_last, enable=0) == data_zeros, "Buffer leaked signal when disabled!"

    # 3. Chip Select Crosstalk (Testing addresses across vastly different memory chips)
    addr_A = [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,1,0,1] # Chip 0
    data_A = [1, 1, 0, 0, 0, 0, 1, 1]
    
    addr_B = [0,0,0,0, 0,0,0,0, 0,0,0,1, 0,1,0,1] # Chip 1
    data_B = [0, 0, 1, 1, 1, 1, 0, 0]
    
    addr_C = [1,1,1,1, 1,1,1,1, 1,1,1,1, 0,1,0,1] # Chip 4095
    data_C = [1, 1, 1, 1, 1, 1, 1, 1]
    
    ram(addr_A, data_A, write=1)
    ram(addr_B, data_B, write=1)
    ram(addr_C, data_C, write=1)
    
    assert ram.read(addr_A) == data_A, "Crosstalk corrupted Chip 0"
    assert ram.read(addr_B) == data_B, "Crosstalk corrupted Chip 1"
    assert ram.read(addr_C) == data_C, "Crosstalk corrupted Chip 4095"

if __name__ == "__main__":
    test_decoder_3_8_isolation()
    test_ram_8_1_logic()
    test_ram_8_8_crosstalk()
    test_ram_16_8_fatigue()
    test_ram_64kb_boundaries_and_routing()