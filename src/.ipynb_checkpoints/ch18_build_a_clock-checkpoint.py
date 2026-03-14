import sys
sys.path.append("../src")

from utils import *

class Counter0_9:
    """A module-10 Ripple Counter that counts from 0 to 9 and resets. """
    def __init__(self,):
        self.nbits = 4
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
        self.and_gate = AND()

    def getQs(self):
        qs = [ff.getQ() for ff in self.flipflops]
        return list(reversed(qs))
    
    def __call__(self, clk = 0):
        # The hardware stabilization loop
        while True:
            # 1. Take a snapshot of the current state of the ff
            old_qs = [ff.getQ() for ff in self.flipflops]

            # 2. Wire up the Async Clear
            # ff[0] is Q0 (LSB), ff[1] is Q1, ff[2] is Q2, ff[3] is Q3 (MSB)
            # We want to clear when we hit 10 (Binary: 1010). 
            # This happens when Q3 == 1 and Q1 == 1.
            q1 = self.flipflops[1].getQ()
            q3 = self.flipflops[3].getQ()
            clear_wire = self.and_gate([q3, q1])

            # 3. Propagate the clock and data through the ripple chain
            current_clk = clk
            for ff in self.flipflops:
                data = ff.getQ_bar()
                # Pass Data, Clock, Preset(0), and our dynamic Clear wire!
                q, q_bar = ff([data, current_clk, 0, clear_wire])
                current_clk = q_bar

            # 4. Read the new state
            new_qs = [ff.getQ() for ff in self.flipflops]

            # 5. If the electrons have settled and nothing changed, break!
            if old_qs == new_qs:
                break

        # Return with MSB on the left for easy reading
        return list(reversed(new_qs))

class Counter0_5:
    """A module-6 Ripple Counter that counts from 0 to 5 and resets. """
    def __init__(self,):
        self.nbits = 3
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
        self.and_gate = AND()
        
    def getQs(self):
        qs = [ff.getQ() for ff in self.flipflops]
        return list(reversed(qs))
        
    def __call__(self, clk = 0):
        # when the while loop runs a second time, it means
        # the circuit hasn't settled yet, but we are still
        # inside the exact same moment in time.
        # By putting current_clk = clk inside the top of 
        # the while loop, you ensure that every time you
        # re-calculate the ripple chain, you are correctly
        # starting from the external physical pin,
        # rather than accidentally passing the baton in a circle.
        # current_clk = clk

        
        # The hardware stabilization loop
        while True:
            # 1. Take a snapshot of the current state of the ff
            old_qs = [ff.getQ() for ff in self.flipflops]

            # 2. Wire up the Async Clear
            # ff[0] is Q0 (LSB), ff[1] is Q1, ff[2] is Q2(MSB)
            # We want to clear when we hit 6 (Binary: 110). 
            # This happens when Q2 == 1 and Q1 == 1.
            q1 = self.flipflops[1].getQ()
            q2 = self.flipflops[2].getQ()
            clear_wire = self.and_gate([q2, q1])

            # 3. Propagate the clock and data through the ripple chain
            current_clk = clk
            for ff in self.flipflops:
                data = ff.getQ_bar()
                # Pass Data, Clock, Preset(0), and our dynamic Clear wire!
                q, q_bar = ff([data, current_clk, 0, clear_wire])
                current_clk = q_bar

            # 4. Read the new state
            new_qs = [ff.getQ() for ff in self.flipflops]

            # 5. If the electrons have settled and nothing changed, break!
            if old_qs == new_qs:
                break
            # else:
            #     print(list(reversed(old_qs)))
            #     print(list(reversed(new_qs)))
            # 5 -> 0
            # [1, 0, 1] 5
            # [1, 1, 0] 6
            # [1, 1, 0] 6
            # [0, 0, 0] 0

        # Return with MSB on the left for easy reading
        return list(reversed(new_qs))

class SecondTimer:
    def __init__(self):
        self.decade_counter_6 = Counter0_5()
        self.decade_counter_10 = Counter0_9()
        self.nand_gate = NAND()

    def getBitsOfLow(self):
        bits_of_low = self.decade_counter_10.getQs()
        return bits_of_low

    def getBitsOfHigh(self):
        bits_of_high = self.decade_counter_6.getQs()
        return bits_of_high
    
    def __call__(self, clk = 0):
        bits_of_digit10 = self.decade_counter_10(clk)
        clk_of_digit6 = self.nand_gate([bits_of_digit10[0], bits_of_digit10[-1]])
        bits_of_digit6 = self.decade_counter_6(clk_of_digit6)
        return bits_of_digit6, bits_of_digit10

class MinuteTimer:
    def __init__(self):
        self.decade_counter_6 = Counter0_5()
        self.decade_counter_10 = Counter0_9()
        self.nand_gate = NAND()

    def getBitsOfLow(self):
        bits_of_low = self.decade_counter_10.getQs()
        return bits_of_low

    def getBitsOfHigh(self):
        bits_of_high = self.decade_counter_6.getQs()
        return bits_of_high
    
    def __call__(self, clk = 0):
        bits_of_digit10 = self.decade_counter_10(clk)
        clk_of_digit6 = self.nand_gate([bits_of_digit10[0], bits_of_digit10[-1]])
        bits_of_digit6 = self.decade_counter_6(clk_of_digit6)
        return bits_of_digit6, bits_of_digit10

class HourTimer:
    def __init__(self):
        self.nbits = 5        
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
                
        self.nand_gate = NAND()
        self.and_gate_10 = AND(2) # Detects the 10
        self.and_gate_12 = AND(2) # Detects the 12
        
        self.or_gate = OR(2)

    def getQs(self):
        qs = [ff.getQ() for ff in self.flipflops]
        return list(reversed(qs))
    
    def __call__(self, clk=0):
        # The hardware stabilization loop
        while True:
            # 1. Take a snapshot of the current state of the ff
            old_qs = [ff.getQ() for ff in self.flipflops]
  
            # 2. Wire up the Async Clear
            q1 = self.flipflops[1].getQ()
            q3 = self.flipflops[3].getQ()
            q4 = self.flipflops[4].getQ()
            
            # Clear 1: When low digit hits 10 (q3=1, q1=1)
            clear_10 = self.and_gate_10([q3, q1])

            # Clear 2: When total time hits 12 (q4=1, q1=1). NO INVERTER NEEDED!
            clear_12 = self.and_gate_12([q4, q1])
            
            # The low digit must clear if it hits 10 OR if the whole clock hits 12
            clear_low_digit = self.or_gate([clear_12, clear_10])

            # The cascading clock for the High Digit (Triggers when low digit hits 10)
            q0 = self.flipflops[0].getQ()
            clk_of_hour_high_digit = self.nand_gate([q0, q3])
            
            # 3. Propagate the clock and data through the ripple chain
            current_clk = clk
            
            # Tick the low digit (bits 0 to 3)
            for ff in self.flipflops[:-1]:
                data = ff.getQ_bar()
                q, q_bar = ff([data, current_clk, 0, clear_low_digit])
                current_clk = q_bar

            # Tick the high digit (bit 4)
            data_high = self.flipflops[-1].getQ_bar()
            self.flipflops[-1]([data_high, clk_of_hour_high_digit, 0, clear_12])
            
            # 4. Read the new state
            new_qs = [ff.getQ() for ff in self.flipflops]

            # 5. If the electrons have settled and nothing changed, break!
            if old_qs == new_qs:
                break
                
        # Return with MSB on the left for easy reading
        return list(reversed(new_qs))

class HourMinuteSecondTimer:
    # adding switches to set the time manually(hour and minute and second)
    def __init__(self):
        self.hour_timer = HourTimer()
        self.minute_timer = MinuteTimer()
        self.second_timer = SecondTimer()
        self.nand_gate_min_sec = NAND()
        
        self.nand_gate_hour_min = NAND()
        self.nand_gate_pm_am = NAND()
        # A toggle flip-flop to store AM (0) or PM (1)
        self.am_pm_memory = EdgeTriggeredDTypeFlipFlopWithPresetAndClear()

        self.switch_sec = XOR()
        self.switch_min = XOR()
        self.switch_hour = XOR()

    def update_hour(self, hour_stride):
        for _ in range(hour_stride):
            bits_tens_min = self.minute_timer.getBitsOfHigh()
            clk_of_hour = self.nand_gate_hour_min([bits_tens_min[0], bits_tens_min[-1]])
            for switch in [1, 1]:
                clk_of_hour = self.switch_hour([switch, clk_of_hour])
                bits_hour = self.hour_timer(clk_of_hour)
                bits_tens_hour, bits_ones_hour = [bits_hour[0]], bits_hour[1:] # The 1-bit high digit, The 4-bit low digit        
                
                clk_of_am_pm = self.nand_gate_pm_am([bits_tens_hour[0], bits_ones_hour[-1]])
                current_am_pm_state = self.am_pm_memory.getQ_bar()
                am_pm_q, _ = self.am_pm_memory([current_am_pm_state, clk_of_am_pm, 0, 0])

    def update_minute(self, minute_stride):
        for _ in range(minute_stride):
            bits_tens_sec = self.second_timer.getBitsOfHigh()
            clk_of_min = self.nand_gate_min_sec([bits_tens_sec[0], bits_tens_sec[-1]])
            for switch in [1, 1]:
                clk_of_min = self.switch_min([switch, clk_of_min])
                bits_tens_min, bits_ones_min = self.minute_timer(clk_of_min)
                
                clk_of_hour = self.nand_gate_hour_min([bits_tens_min[0], bits_tens_min[-1]])
                clk_of_hour = self.switch_hour([0, clk_of_hour])
                bits_hour = self.hour_timer(clk_of_hour)
                bits_tens_hour, bits_ones_hour = [bits_hour[0]], bits_hour[1:] # The 1-bit high digit, The 4-bit low digit
                
                clk_of_am_pm = self.nand_gate_pm_am([bits_tens_hour[0], bits_ones_hour[-1]])
                current_am_pm_state = self.am_pm_memory.getQ_bar()
                am_pm_q, _ = self.am_pm_memory([current_am_pm_state, clk_of_am_pm, 0, 0])

    def update_second(self, second_stride, clk = 0):
        for _ in range(second_stride):
            for switch in [1, 1]:
                clk = self.switch_sec([switch, clk])
                bits_tens_sec, bits_ones_sec = self.second_timer(clk)
                clk_of_min = self.nand_gate_min_sec([bits_tens_sec[0], bits_tens_sec[-1]])
                clk_of_min = self.switch_min([0, clk_of_min])
                bits_tens_min, bits_ones_min = self.minute_timer(clk_of_min)
                
                clk_of_hour = self.nand_gate_hour_min([bits_tens_min[0], bits_tens_min[-1]])
                clk_of_hour = self.switch_hour([0, clk_of_hour])
                bits_hour = self.hour_timer(clk_of_hour)
                bits_tens_hour, bits_ones_hour = [bits_hour[0]], bits_hour[1:] # The 1-bit high digit, The 4-bit low digit
                
                clk_of_am_pm = self.nand_gate_pm_am([bits_tens_hour[0], bits_ones_hour[-1]])
                current_am_pm_state = self.am_pm_memory.getQ_bar()
                am_pm_q, _ = self.am_pm_memory([current_am_pm_state, clk_of_am_pm, 0, 0])
            
    def __call__(self, clk = 0):
        # bits_tens_min, bits_ones_min, bits_tens_sec, bits_ones_sec = self.min_sec_timer(clk)
        clk = self.switch_sec([0, clk])
        bits_tens_sec, bits_ones_sec = self.second_timer(clk)
        clk_of_min = self.nand_gate_min_sec([bits_tens_sec[0], bits_tens_sec[-1]])
        clk_of_min = self.switch_min([0, clk_of_min])
        bits_tens_min, bits_ones_min = self.minute_timer(clk_of_min)
        
        clk_of_hour = self.nand_gate_hour_min([bits_tens_min[0], bits_tens_min[-1]])
        clk_of_hour = self.switch_hour([0, clk_of_hour])
        bits_hour = self.hour_timer(clk_of_hour)
        bits_tens_hour, bits_ones_hour = [bits_hour[0]], bits_hour[1:] # The 1-bit high digit, The 4-bit low digit
        
        clk_of_am_pm = self.nand_gate_pm_am([bits_tens_hour[0], bits_ones_hour[-1]])
        current_am_pm_state = self.am_pm_memory.getQ_bar()
        am_pm_q, _ = self.am_pm_memory([current_am_pm_state, clk_of_am_pm, 0, 0])
        
        return am_pm_q, bits_tens_hour, bits_ones_hour, bits_tens_min, bits_ones_min, bits_tens_sec, bits_ones_sec



