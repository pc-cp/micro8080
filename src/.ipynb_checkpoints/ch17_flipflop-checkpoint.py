# import sys
# sys.path.append("../src")

from utils import *

class Oscillator:
    """ A simple system clock that alternates between 0 and 1. """
    def __init__(self):
        self.state = 0

    def level(self):
        return self.state
        
    def tick(self):
        # Time moves forward one step!
        self.state = 1 - self.state
        return self.state

class RS_FlipFlop_V1:
    def __init__(self):
        self.nin = 2
        self.nor_gate1 = NOR()
        self.nor_gate2 = NOR()
        self.q = 0
        self.q_bar = 1 - self.q

    def getQ(self):
        return self.q

    def getQ_bar(self):
        return self.q_bar
    
    def __call__(self, x):
        assert len(x) == self.nin, "RS_FlipFlop takes exactly 2 inputs"
        r, s = x
        # 1. Q -> Q_bar -> Q
        # correct
        # self.q_bar = self.nor_gate2([self.q, s])
        # self.q = self.nor_gate1([self.q_bar, r])

        # 2. Q_bar -> Q -> Q_bar (- -> Q)
        # error
        # (PengChen:) because you evaluated Q first,
        # it didn't know that Q-bar was about to change!
        # Q evaluated using the "old" reality.
        # self.q = self.nor_gate1([self.q_bar, r])
        # self.q_bar = self.nor_gate2([self.q, s])

        # 3. iterate until stable
        while True:
            new_q = self.nor_gate1([r, self.q_bar])
            new_q_bar = self.nor_gate2([s, self.q])
            
            if new_q == self.q and new_q_bar == self.q_bar:
                break

            self.q = new_q
            self.q_bar = new_q_bar
        
        return self.q, self.q_bar

class Level_Triggered_D_Latch_V1:
    def __init__(self):
        self.nin = 2
        self.invert = Inverter()
        
        # Solder TWO physical AND gates to our board!
        self.and_gate1 = AND()
        self.and_gate2 = AND()
        
        self.rs_flipflop = RS_FlipFlop_V1()

    def getQ(self):
        return self.rs_flipflop.getQ()

    def getQ_bar(self):
        return self.rs_flipflop.getQ_bar()
    
    def __call__(self, x):
        assert len(x) == self.nin, f"Expected {self.nin} inputs"
        data, clock = x[0], x[1]

        # Wire 1: Invert the Data
        not_data = self.invert([data])

        # Wire 2: The Reset pin (R) gets AND(NOT Data, Clock)
        r_wire = self.and_gate1([not_data, clock])

        # Wire 3: The Set pin (S) gets AND(Data, Clock)
        s_wire = self.and_gate2([data, clock])

        # Feed the R and S wires into our stabilized RS Flip-Flop
        q, q_bar = self.rs_flipflop([r_wire, s_wire])

        return q, q_bar
        
class Level_Triggered_D_Latch_V2:
    def __init__(self):
        self.nin = 3 # data, clk, clr
        self.invert_data = Inverter()
        self.invert_clr = Inverter() # added to protect the set pin
        
        # Solder TWO physical AND gates to our board!
        self.and_gate_r = AND(2)
        self.and_gate_s = AND(3) # upgraded to 3 inputs
        self.or_gate = OR()
        
        self.rs_flipflop = RS_FlipFlop_V1()

    def getQ(self):
        return self.rs_flipflop.getQ()

    def getQ_bar(self):
        return self.rs_flipflop.getQ_bar()
    
    def __call__(self, x):
        assert len(x) in (self.nin, self.nin - 1), f"Expected {self.nin} or {self.nin - 1} inputs"
        if len(x) == self.nin:
            data, clock, clr = x
        else:
            data, clock = x
            clr = 0
            
        not_data = self.invert_data([data])
        not_clr = self.invert_clr([clr])
            
        # Wire 1: The Reset pin (R) gets OR(Clr, AND(NOT Data, Clock))
        and_r = self.and_gate_r([not_data, clock])
        r_wire = self.or_gate([clr, and_r])

        # Wire 2: The Set pin (S) gets AND(Data, Clock, NOT Clr)
        s_wire = self.and_gate_s([data, clock, not_clr])

        # Feed the R and S wires into our stabilized RS Flip-Flop
        q, q_bar = self.rs_flipflop([r_wire, s_wire])

        return q, q_bar

class nBitLevelTriggeredDLatch:
    def __init__(self, nbits):
        self.nbits = nbits
        # Solder 'n' D-Latches onto the board side-by-side
        self.level_d_latchs = [Level_Triggered_D_Latch_V2() for _ in range(self.nbits)]

    # We separate the data bus (a list) from the clock (a single bit)
    def __call__(self, datas, clk):
        assert len(datas) == self.nbits, f"Data bus must be {self.nbits} bits long"
        
        qs = []
        
        # Parallel processing! No rippling required.
        for idx in range(self.nbits):
            # Fetch the latch for this specific bit, and pass its data and the shared clock
            q, q_bar = self.level_d_latchs[idx]([datas[idx], clk])
            qs.append(q)
            
        return qs

# A circuit that open like a door (Level-Triggered) is 
# called a Latch.
# A circuit that only triggers on the clock's
# transition (Edge-Triggered) is called
# a Flip-Flop.
class Edge_Triggered_D_Flip_Flop_V1:
    def __init__(self):
        self.nin = 2

        self.level_d_latchs_stage1 = Level_Triggered_D_Latch_V1()
        self.level_d_latchs_stage2 = Level_Triggered_D_Latch_V1()
        self.invert1 = Inverter()
        # self.q, self.q_bar = 0, 1

    def getQ(self):
        return self.level_d_latchs_stage2.getQ()

    def getQ_bar(self):
        return self.level_d_latchs_stage2.getQ_bar()
        
    def __call__(self, x):
        assert len(x) == self.nin, f"Expected {self.nin} inputs"
        data, clock = x[0], x[1]

        # Wire 1: Invert the Clk
        not_clk = self.invert1([clock])

        # Wire 2: get Q and Q_bar from stage1
        q1, q_bar1 = self.level_d_latchs_stage1([data, not_clk])

        # Wire 3: get Q and Q_bar from stage2
        q2, q_bar2 = self.level_d_latchs_stage2([q1, clock])
        return q2, q_bar2

class RS_FlipFlop_V2:
    def __init__(self):
        # Edge-Triggered D-Type Flip-Flop with Clear and Preset (page 238)
        self.nin = 4 # r0, r1, s0, s1
        self.rs_flipflop = RS_FlipFlop_V1()
        self.or_gate1 = OR()
        self.or_gate2 = OR()

    def getQ(self):
        return self.rs_flipflop.getQ()

    def getQ_bar(self):
        return self.rs_flipflop.getQ_bar()
    
    def __call__(self, x):
        assert len(x) == self.nin, f"RS_FlipFlop takes exactly {self.nin} inputs"
        r0, r1, s0, s1 = x
        r = self.or_gate1([r0, r1])
        s = self.or_gate2([s0, s1])

        q, q_bar = self.rs_flipflop([r, s])
        return q, q_bar

class Edge_Triggered_D_Flip_Flop_V2:
    def __init__(self):
        self.nin = 4
        self.rs_flipflop1 = RS_FlipFlop_V2()
        self.rs_flipflop2 = RS_FlipFlop_V2()
        self.rs_flipflop3 = RS_FlipFlop_V2()
        self.invert1 = Inverter()
        
    def getQ(self):
        return self.rs_flipflop3.getQ()

    def getQ_bar(self):
        return self.rs_flipflop3.getQ_bar()
        
    def __call__(self, x):
        assert len(x) in (self.nin, self.nin-2), f"Expected {self.nin} inputs"
        if len(x) == self.nin:
            data, clock, preset, clear = x
        else:
            data, clock = x
            preset, clear = 0, 0

        not_clk = self.invert1([clock])
        while True:
            # 1. Take a snapshot of the current reality
            old_q1, old_q_bar1 = self.rs_flipflop1.getQ(), self.rs_flipflop1.getQ_bar()
            old_q2, old_q_bar2 = self.rs_flipflop2.getQ(), self.rs_flipflop2.getQ_bar()
            old_q3, old_q_bar3 = self.rs_flipflop3.getQ(), self.rs_flipflop3.getQ_bar()

            # 2. Let the electrons flow through all the wires
            self.rs_flipflop1([self.rs_flipflop2.getQ_bar(), not_clk, data, preset])
            self.rs_flipflop2([clear, self.rs_flipflop1.getQ_bar(), preset, not_clk])
            q3, q_bar3 = self.rs_flipflop3([clear, self.rs_flipflop2.getQ_bar(), self.rs_flipflop1.getQ(), preset])    

            # 3. Did the electrons change anything? If no, the circuit is stable!
            if (old_q1 == self.rs_flipflop1.getQ() and old_q_bar1 == self.rs_flipflop1.getQ_bar() and 
                old_q2 == self.rs_flipflop2.getQ() and old_q_bar2 == self.rs_flipflop2.getQ_bar() and 
                old_q3 == self.rs_flipflop3.getQ() and old_q_bar3 == self.rs_flipflop3.getQ_bar()):
                break;
        
        return q3, q_bar3

class nBit_Edge_Triggered_Register:
    def __init__(self, nbits):
        self.nbits = nbits
        
        # Solder 'n' Edge-Triggered D-Flip-Flops onto the board side-by-side
        self.flip_flops = [Edge_Triggered_D_Flip_Flop_V2() for _ in range(self.nbits)]

    def __call__(self, datas, clk):
        assert len(datas) == self.nbits, f"Data bus must be {self.nbits} bits long"
        
        qs = []
        
        # Parallel processing! All bits lock in at the exact same time.
        for idx in range(self.nbits):
            q, q_bar = self.flip_flops[idx]([datas[idx], clk])
            qs.append(q)
            
        return qs

class nBitAccumulatorV1:
    def __init__(self, nbits):
        self.nbits = nbits
        self.adder = nBit_Adder_with_two_complement(self.nbits)
        self.register = nBit_Edge_Triggered_Register(self.nbits)
        # At boot-up, the memory holds all zeros
        self.current_memory = [0 for _ in range(self.nbits)]

    def __call__(self, inputs_sequence):
        # We process a list of binary numbers, simulating time passing
        for data_in in inputs_sequence:
            assert len(data_in) == self.nbits , f"Data bus must be {self.nbits} bits long"
            # 1. The adder adds the incoming number to the CURRENT memory
            overflow, carry, sum_bits = self.adder(data_in, self.current_memory)

            # 2. Manually toggle the clock (Press the "Add" button)
            self.register(sum_bits, 0)
            # RISING EDGE: Button goes down (Clk=1). The register locks in the new sum
            self.current_memory = self.register(sum_bits, 1)
            # Button goes back up (Clk = 0)
            self.register(sum_bits, 0)
        # Return whatever the register is holding at the very end
        return self.current_memory

    def clear(self):
        """
        Clears the accumulator using pure hardward math.
        Adds the Two's complement of the current memory to itself.
        X + NOT(X) + 1 = 0
        """
        my_inverter = Inverter()

        inverted_memory = [my_inverter([bit]) for bit in self.current_memory]
        overflow, carry, sum_bits = self.adder(inverted_memory, self.current_memory, last_carry_in=1)

        # 2. Manually toggle the clock (Press the "Add" button)
        self.register(sum_bits, 0)
        # RISING EDGE: Button goes down (Clk=1). The register locks in the new sum
        self.current_memory = self.register(sum_bits, 1)
        # Button goes back up (Clk = 0)
        self.register(sum_bits, 0)        

class Frequency_Divider:
    def __init__(self):
        self.nin = 2
        # init self.state = 0
        self.oscillator = Oscillator() 
        self.flipflop = Edge_Triggered_D_Flip_Flop_V1()

        
    def __call__(self):
        clk = self.oscillator.level()
        self.oscillator.tick()
        data = self.flipflop.getQ_bar()

        q, q_bar = self.flipflop([data, clk])
        return q, q_bar

class nBitsRippleCounter:
    def __init__(self, nbits):
        self.nbits = nbits
        self.flipflops = [Edge_Triggered_D_Flip_Flop_V2() for _ in range(self.nbits)]

    def __call__(self, clk = 0):
        current_clk = clk
        qs = []
        for flipflop in self.flipflops:
            data = flipflop.getQ_bar()
            q, q_bar = flipflop([data, current_clk])
            qs.append(q)
            current_clk = q_bar
        # MSB is on the left
        return list(reversed(qs))

# 1. Power on the System Clock and the 4-Bit Counter
system_clock = Oscillator()
counter4 = nBitsRippleCounter(4)

print("Tick | CLK | Q3 Q2 Q1 Q0 | Decimal")
print("-" * 36)

# 2. Run the simulation for 34 ticks to watch it count 0 to 15, and wrap around
for tick in range(1, 35):
    # Tap the clock wire to see its state
    clk_signal = system_clock.level()
    
    # Run the counter hardware using the current clock signal
    q_bits = counter4(clk_signal)
    
    # Read the binary list into a human decimal number
    decimal_val = bit_list_to_int(q_bits, signed=False)
    
    # Print the state
    print(f" {tick:2}  |  {clk_signal}  |  {q_bits[0]}  {q_bits[1]}  {q_bits[2]}  {q_bits[3]}  |   {decimal_val:2}")
    
    # Tick the clock forward for the next loop iteration
    system_clock.tick()