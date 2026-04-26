# ==========================================
# CHAPTER 18 SPECIFIC COMPONENTS
# ==========================================
from src.utils import *

class FrequencyDivider:
    """
    Divides a clock frequency by 2.
    It connects the Q_bar output directly back into the Data input. 
    Every time the clock ticks (rising edge), the flip-flop loads its own opposite state.
    """
    def __init__(self):
        self.flipflop = EdgeTriggeredDTypeFlipFlop()

    def getQ(self):
        return self.flipflop.getQ()
        
    def getQ_bar(self):
        return self.flipflop.getQ_bar()

    def __call__(self, clk):
        # Feed Q_bar back into Data
        data = self.flipflop.getQ_bar()
        q, q_bar = self.flipflop([data, clk])
        return q, q_bar

class NBitsFrequencyDivider:
    """
    A Ripple Counter (Up-Counter) made by chaining Frequency Dividers.
    The Q_bar of one flip-flop acts as the Clock for the next flip-flop.
    This is used to build the Seconds, Minutes, and Hours counters.
    """
    def __init__(self, nbits):
        self.nbits = nbits
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
    
    def getQ(self):
        # Reverse the list so the Most Significant Bit (MSB) is at index 0
        return list(reversed([ff.getQ() for ff in self.flipflops]))

    def getQ_bar(self):
        return list(reversed([ff.getQ_bar() for ff in self.flipflops]))

    def __call__(self, clk=0):
        current_clk = clk
        qs = []
        for flipflop in self.flipflops:
            data = flipflop.getQ_bar()
            q, q_bar = flipflop([data, current_clk])
            qs.append(q)
            # The Q_bar of this flip-flop becomes the clock for the next one!
            current_clk = q_bar
            
        return list(reversed(qs))


class Counter0_9:
    """
    Simulates a Modulo-10 (Decade) Ripple Counter.
    Counts from 0 to 9 in binary. When it hits 10 (Binary: 1010), 
    the AND gate detects Q3=1 and Q1=1, triggering an asynchronous clear back to 0.
    """
    def __init__(self):
        self.nbits = 4
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
        self.and_gate = AND()

    def getQs(self):
        qs = [ff.getQ() for ff in self.flipflops]
        return list(reversed(qs))
    
    def __call__(self, clk=0):
        # current_clk = clk 
        # The hardware stabilization loop
        while True:
            old_qs = [ff.getQ() for ff in self.flipflops]

            # Clear when we hit 10 (1010). Q3 == 1 and Q1 == 1.
            q1 = self.flipflops[1].getQ()
            q3 = self.flipflops[3].getQ()
            clear_wire = self.and_gate([q3, q1])

            # NOTE (Hardware Physics): 
            # current_clk MUST be reset to the external clk inside this loop!
            # If placed outside, the loop will accidentally feed the Q_bar from 
            # the last flip-flop back into the first flip-flop, creating a 
            # "circular wire" race condition and accidental clock ticks.
            current_clk = clk
            for ff in self.flipflops:
                data = ff.getQ_bar()
                q, q_bar = ff([data, current_clk, 0, clear_wire])
                current_clk = q_bar

            new_qs = [ff.getQ() for ff in self.flipflops]
            if old_qs == new_qs:
                break
        # Return with MSB on the left for easy reading
        return list(reversed(new_qs))

class Counter0_5:
    """
    Simulates a Modulo-6 Ripple Counter.
    Counts from 0 to 5 in binary. When it hits 6 (Binary: 0110),
    the AND gate detects Q2=1 and Q1=1, triggering an asynchronous clear back to 0.
    Used for the "tens" digit of the seconds and minutes.
    """
    def __init__(self):
        self.nbits = 3
        self.flipflops = [EdgeTriggeredDTypeFlipFlopWithPresetAndClear() for _ in range(self.nbits)]
        self.and_gate = AND()
        
    def getQs(self):
        qs = [ff.getQ() for ff in self.flipflops]
        return list(reversed(qs))
        
    def __call__(self, clk=0):
        while True:
            old_qs = [ff.getQ() for ff in self.flipflops]

            # Clear when we hit 6 (110). Q2 == 1 and Q1 == 1.
            q1 = self.flipflops[1].getQ()
            q2 = self.flipflops[2].getQ()
            clear_wire = self.and_gate([q2, q1])

            current_clk = clk
            for ff in self.flipflops:
                data = ff.getQ_bar()
                q, q_bar = ff([data, current_clk, 0, clear_wire])
                current_clk = q_bar

            new_qs = [ff.getQ() for ff in self.flipflops]
            if old_qs == new_qs:
                break

        return list(reversed(new_qs))

class SecondTimer:
    """
    Combines a Modulo-10 and Modulo-6 counter to count from 00 to 59 seconds.
    The Modulo-6 counter is clocked by the falling edge of the Modulo-10 counter.
    """
    def __init__(self):
        self.decade_counter_6 = Counter0_5()
        self.decade_counter_10 = Counter0_9()
        self.nand_gate = NAND()

    def getBitsOfLow(self):
        return self.decade_counter_10.getQs()

    def getBitsOfHigh(self):
        return self.decade_counter_6.getQs()
    
    def __call__(self, clk=0):
        bits_of_digit10 = self.decade_counter_10(clk)
        clk_of_digit6 = self.nand_gate([bits_of_digit10[0], bits_of_digit10[-1]])
        bits_of_digit6 = self.decade_counter_6(clk_of_digit6)
        return bits_of_digit6, bits_of_digit10

class MinuteTimer:
    """
    Combines a Modulo-10 and Modulo-6 counter to count from 00 to 59 minutes.
    Behaves exactly like the SecondTimer.
    """
    def __init__(self):
        self.decade_counter_6 = Counter0_5()
        self.decade_counter_10 = Counter0_9()
        self.nand_gate = NAND()

    def getBitsOfLow(self):
        return self.decade_counter_10.getQs()

    def getBitsOfHigh(self):
        return self.decade_counter_6.getQs()
    
    def __call__(self, clk=0):
        bits_of_digit10 = self.decade_counter_10(clk)
        clk_of_digit6 = self.nand_gate([bits_of_digit10[0], bits_of_digit10[-1]])
        bits_of_digit6 = self.decade_counter_6(clk_of_digit6)
        return bits_of_digit6, bits_of_digit10

class HourTimer:
    """
    Simulates a 12-Hour Counter (0 to 11).
    Uses complex clearing logic: 
    - Clears the low digit when it hits 10.
    - Clears the entire clock when the total time hits 12.
    """
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
        while True:
            old_qs = [ff.getQ() for ff in self.flipflops]
  
            q1 = self.flipflops[1].getQ()
            q3 = self.flipflops[3].getQ()
            q4 = self.flipflops[4].getQ()
            
            clear_10 = self.and_gate_10([q3, q1])
            clear_12 = self.and_gate_12([q4, q1])
            clear_low_digit = self.or_gate([clear_12, clear_10])

            q0 = self.flipflops[0].getQ()
            clk_of_hour_high_digit = self.nand_gate([q0, q3])
            
            current_clk = clk
            
            for ff in self.flipflops[:-1]:
                data = ff.getQ_bar()
                q, q_bar = ff([data, current_clk, 0, clear_low_digit])
                current_clk = q_bar

            data_high = self.flipflops[-1].getQ_bar()
            self.flipflops[-1]([data_high, clk_of_hour_high_digit, 0, clear_12])
            
            new_qs = [ff.getQ() for ff in self.flipflops]
            if old_qs == new_qs:
                break
                
        return list(reversed(new_qs))
    
class HourMinuteSecondTimer:
    """
    A complete digital clock combining hours, minutes, seconds, and an AM/PM flip-flop.
    
    Architecture:
    It uses a ripple-carry design. The rollover of the seconds clocks the minutes, 
    the rollover of the minutes clocks the hours, and the 11-to-12 transition clocks the AM/PM.
    
    Manual Override:
    Includes XOR gates on the clock lines. By toggling the XOR input (0 -> 1 -> 0), 
    we can artificially inject a clock pulse into a specific tier without waiting 
    for the previous tier to roll over.
    """
    def __init__(self):
        self.hour_timer = HourTimer()
        self.minute_timer = MinuteTimer()
        self.second_timer = SecondTimer()
        
        # NAND gates detect the "max" state of a tier to generate a cascading clock pulse
        self.nand_gate_min_sec = NAND()
        self.nand_gate_hour_min = NAND()
        self.nand_gate_pm_am = NAND()
        
        # A toggle flip-flop to store AM (0) or PM (1)
        self.am_pm_memory = EdgeTriggeredDTypeFlipFlopWithPresetAndClear()

        # XOR gates act as clock pulse injectors for the manual override buttons
        self.switch_sec = XOR()
        self.switch_min = XOR()
        self.switch_hour = XOR()

    def _evaluate_circuit(self, clk=0, sw_sec=0, sw_min=0, sw_hr=0):
        """
        Simulates the continuous flow of electricity through the entire clock circuit.
        Instead of duplicating the routing logic, this single method evaluates the 
        cascade from right (seconds) to left (AM/PM).
        """
        # 1. SECONDS TIER: Clocked by main oscillator OR manual second switch
        sec_clk = self.switch_sec([sw_sec, clk])
        bits_tens_sec, bits_ones_sec = self.second_timer(sec_clk)
        
        # 2. MINUTES TIER: Clocked by seconds rollover OR manual minute switch
        ripple_to_min = self.nand_gate_min_sec([bits_tens_sec[0], bits_tens_sec[-1]])
        min_clk = self.switch_min([sw_min, ripple_to_min])
        bits_tens_min, bits_ones_min = self.minute_timer(min_clk)
        
        # 3. HOURS TIER: Clocked by minutes rollover OR manual hour switch
        ripple_to_hour = self.nand_gate_hour_min([bits_tens_min[0], bits_tens_min[-1]])
        hour_clk = self.switch_hour([sw_hr, ripple_to_hour])
        bits_hour = self.hour_timer(hour_clk)
        bits_tens_hour, bits_ones_hour = [bits_hour[0]], bits_hour[1:] 
        
        # 4. AM/PM TIER: Clocked by the 11 -> 12 hour transition
        ripple_to_ampm = self.nand_gate_pm_am([bits_tens_hour[0], bits_ones_hour[-1]])
        current_am_pm_state = self.am_pm_memory.getQ_bar()
        am_pm_q, _ = self.am_pm_memory([current_am_pm_state, ripple_to_ampm, 0, 0])
        
        return am_pm_q, bits_tens_hour, bits_ones_hour, bits_tens_min, bits_ones_min, bits_tens_sec, bits_ones_sec

    def update_hour(self, hour_stride):
        """Simulates manually pressing the 'Set Hour' button."""
        for _ in range(hour_stride):
            # Press button (Rising edge injected into the XOR gate)
            self._evaluate_circuit(sw_hr=1)
            # Release button (Falling edge injected into the XOR gate)
            self._evaluate_circuit(sw_hr=0)

    def update_minute(self, minute_stride):
        """Simulates manually pressing the 'Set Minute' button."""
        for _ in range(minute_stride):
            # Press button
            self._evaluate_circuit(sw_min=1)
            # Release button
            self._evaluate_circuit(sw_min=0)

    def update_second(self, second_stride, clk=0):
        """Simulates manually pressing the 'Set Second' button."""
        for _ in range(second_stride):
            # Press button 
            self._evaluate_circuit(clk=clk, sw_sec=1)
            # Release button 
            self._evaluate_circuit(clk=clk, sw_sec=0)
            
    def __call__(self, clk=0):
        """
        Executes one standard hardware tick from the main oscillator.
        All manual switches are unpressed (0).
        """
        return self._evaluate_circuit(clk=clk, sw_sec=0, sw_min=0, sw_hr=0)

# ==========================================
# TESTS
# ==========================================

def test_frequency_divider():
    my_oscillator = Oscillator()
    my_freq_divider = FrequencyDivider()

    # init state of the gloden clock and divider
    previous_clock_state = -1
    golden_clock_state = 0
    golden_q = 0
    for tick in range(1, 11):
        assert golden_clock_state == my_oscillator.level(), f"At tick {tick}, expected clock state {golden_clock_state} but got {my_oscillator.level()}"
        
        # Run the hardware simulation
        my_freq_divider(my_oscillator.level())
        if previous_clock_state == 0 and golden_clock_state == 1:  # Only toggle the expected output on the rising edge of the clock
            golden_q = 1 - golden_q

        assert golden_q == my_freq_divider.getQ(), f"At tick {tick}, expected divided output {golden_q} but got {my_freq_divider.getQ()}"

        previous_clock_state = golden_clock_state
        my_oscillator.tick()  # Move to the next clock state for the next iteration
        golden_clock_state = 1 - golden_clock_state  # Toggle the expected clock state for the next tick

def test_nbits_frequency_divider():
    my_oscillator = Oscillator()
    nbits = 3
    my_nbits_freq_divider = NBitsFrequencyDivider(nbits)

    # init state of the gloden clock and divider
    previous_clock_state = -1
    golden_clock_state = 0
    golden_qs = [0] * nbits
    golden_value = 0   
    for tick in range(1, 50):
        assert golden_clock_state == my_oscillator.level(), f"At tick {tick}, expected clock state {golden_clock_state} but got {my_oscillator.level()}"
        
        # Run the hardware simulation
        my_nbits_freq_divider(my_oscillator.level())
        if previous_clock_state == 0 and golden_clock_state == 1:  # Only toggle the expected output on the rising edge of the clock
            golden_value = (golden_value + 1) % (2 ** nbits)
            golden_qs = int_to_nbit_list(golden_value, nbits)

        assert golden_qs == my_nbits_freq_divider.getQ(), f"At tick {tick}, expected divided outputs {golden_qs} but got {my_nbits_freq_divider.getQ()}"
        # print(f"Tick {tick}: Clock={golden_clock_state}, Golden Qs={golden_qs}, Divider Qs={my_nbits_freq_divider.getQ()}")
        previous_clock_state = golden_clock_state
        my_oscillator.tick()  # Move to the next clock state for the next iteration
        golden_clock_state = 1 - golden_clock_state  # Toggle the expected clock state for the next tick

def test_counter0_9():
    my_oscillator = Oscillator()
    nbits = 4
    my_counter = Counter0_9()
    
    previous_clock_state = -1
    golden_clock_state = 0
    golden_qs = [0] * nbits
    golden_value = 0
    
    for clk in range(20):
        assert golden_clock_state == my_oscillator.level(), f"At clock {clk}, expected clock state {golden_clock_state}"
        my_counter(my_oscillator.level())
        
        if previous_clock_state == 0 and golden_clock_state == 1:
            golden_value = (golden_value + 1) % 10
            golden_qs = int_to_nbit_list(golden_value, nbits)

        actual_val = int(''.join(str(bit) for bit in my_counter.getQs()))
        assert golden_qs == my_counter.getQs(), f"At clock {clk}, expected {golden_value} but got {actual_val}"
        
        previous_clock_state = golden_clock_state
        my_oscillator.tick()
        golden_clock_state = 1 - golden_clock_state

def test_counter0_5():
    my_oscillator = Oscillator()
    nbits = 3
    my_counter = Counter0_5()
    
    previous_clock_state = -1
    golden_clock_state = 0
    golden_qs = [0] * nbits
    golden_value = 0
    
    for clk in range(20):
        assert golden_clock_state == my_oscillator.level(), f"At clock {clk}, expected clock state {golden_clock_state}"
        my_counter(my_oscillator.level())
        
        if previous_clock_state == 0 and golden_clock_state == 1:
            golden_value = (golden_value + 1) % 6
            golden_qs = int_to_nbit_list(golden_value, nbits)

        actual_val = int(''.join(str(bit) for bit in my_counter.getQs()))
        assert golden_qs == my_counter.getQs(), f"At clock {clk}, expected {golden_value} but got {actual_val}"
        
        previous_clock_state = golden_clock_state
        my_oscillator.tick()
        golden_clock_state = 1 - golden_clock_state

def test_second_timer():
    my_oscillator = Oscillator()
    my_second_timer = SecondTimer()
    
    previous_clock_state = -1
    golden_clock_state = 0
    golden_lower_qs = [0] * 4
    golden_upper_qs = [0] * 3
    golden_value = 0

    for clk in range(120): # Simulate 2 minutes
        assert golden_clock_state == my_oscillator.level(), f"Expected clock {golden_clock_state}"
        my_second_timer(my_oscillator.level())
        
        if previous_clock_state == 0 and golden_clock_state == 1:
            golden_value = (golden_value + 1) % 60
            golden_lower_qs = int_to_nbit_list(golden_value % 10, 4)
            golden_upper_qs = int_to_nbit_list(golden_value // 10, 3)
            
        assert golden_lower_qs == my_second_timer.getBitsOfLow(), "Second lower bits failed"
        assert golden_upper_qs == my_second_timer.getBitsOfHigh(), "Second upper bits failed"
        
        previous_clock_state = golden_clock_state
        my_oscillator.tick()
        golden_clock_state = 1 - golden_clock_state

def test_minute_timer():
    my_oscillator = Oscillator()
    my_minute_timer = MinuteTimer()
    
    previous_clock_state = -1
    golden_clock_state = 0
    golden_lower_qs = [0] * 4
    golden_upper_qs = [0] * 3
    golden_value = 0

    for clk in range(120): 
        assert golden_clock_state == my_oscillator.level()
        my_minute_timer(my_oscillator.level())
        
        if previous_clock_state == 0 and golden_clock_state == 1:
            golden_value = (golden_value + 1) % 60
            golden_lower_qs = int_to_nbit_list(golden_value % 10, 4)
            golden_upper_qs = int_to_nbit_list(golden_value // 10, 3)
            
        assert golden_lower_qs == my_minute_timer.getBitsOfLow(), "Minute lower bits failed"
        assert golden_upper_qs == my_minute_timer.getBitsOfHigh(), "Minute upper bits failed"
        
        previous_clock_state = golden_clock_state
        my_oscillator.tick()
        golden_clock_state = 1 - golden_clock_state

def test_hour_timer():
    my_oscillator = Oscillator()
    my_hour_timer = HourTimer()
    
    previous_clock_state = -1
    golden_clock_state = 0
    golden_lower_qs = [0] * 4
    golden_upper_qs = [0] * 1
    golden_value = 0

    for clk in range(48): # Simulate 2 days
        assert golden_clock_state == my_oscillator.level()
        my_hour_timer(my_oscillator.level())
        
        if previous_clock_state == 0 and golden_clock_state == 1:
            golden_value = (golden_value + 1) % 12
            golden_lower_qs = int_to_nbit_list(golden_value % 10, 4)
            golden_upper_qs = int_to_nbit_list(golden_value // 10, 1)
            
        Qs = my_hour_timer.getQs()
        assert golden_lower_qs == list(Qs[1:5]), "Hour lower bits failed"
        assert golden_upper_qs == [Qs[0]], "Hour upper bit failed"
        
        previous_clock_state = golden_clock_state
        my_oscillator.tick()
        golden_clock_state = 1 - golden_clock_state

def test_hour_minute_second_timer():
    my_oscillator = Oscillator()
    my_timer = HourMinuteSecondTimer()
    
    previous_clock_state = -1
    golden_clock_state = 0
    
    golden_seconds_value = 0
    golden_minutes_value = 0
    golden_hours_value = 0
    golden_is_am = True

    for clk in range(7200): # Simulate 1 hour
        assert golden_clock_state == my_oscillator.level()
        
        am_pm_q, bits_tens_hour, bits_ones_hour, bits_tens_min, bits_ones_min, bits_tens_sec, bits_ones_sec = my_timer(my_oscillator.level())
        
        if previous_clock_state == 0 and golden_clock_state == 1:
            golden_seconds_value = (golden_seconds_value + 1) % 60
            if golden_seconds_value == 0:
                golden_minutes_value = (golden_minutes_value + 1) % 60
                if golden_minutes_value == 0:
                    golden_hours_value = (golden_hours_value + 1) % 12
                    if golden_hours_value == 0:
                        golden_is_am = not golden_is_am
                        
            golden_seconds_lower_qs = int_to_nbit_list(golden_seconds_value % 10, 4)
            golden_seconds_upper_qs = int_to_nbit_list(golden_seconds_value // 10, 3)
            golden_minutes_lower_qs = int_to_nbit_list(golden_minutes_value % 10, 4)
            golden_minutes_upper_qs = int_to_nbit_list(golden_minutes_value // 10, 3)
            golden_hours_lower_qs = int_to_nbit_list(golden_hours_value % 10, 4)
            golden_hours_upper_qs = int_to_nbit_list(golden_hours_value // 10, 1)
            golden_am_pm_q = [0] if golden_is_am else [1]
            
            assert golden_seconds_lower_qs == bits_ones_sec
            assert golden_seconds_upper_qs == bits_tens_sec
            assert golden_minutes_lower_qs == bits_ones_min
            assert golden_minutes_upper_qs == bits_tens_min
            assert golden_hours_lower_qs == bits_ones_hour
            assert golden_hours_upper_qs == bits_tens_hour
            assert golden_am_pm_q == [am_pm_q]
            
        previous_clock_state = golden_clock_state
        my_oscillator.tick()
        golden_clock_state = 1 - golden_clock_state

def test_digital_clock_extreme_edge_cases():
    """
    Time travel to edge cases and verify the cascades.
    """
    clock = HourMinuteSecondTimer()
    
    # Tick clock once to get to rising edge before manual updates
    am_pm, t_hr, o_hr, t_min, o_min, t_sec, o_sec = clock(0)

    # --- Edge Case 1: The 11:59:59 to 12:00:00 Cascade ---
    clock.update_hour(11)
    clock.update_minute(59)
    clock.update_second(59)
    
    am_pm, t_hr, o_hr, t_min, o_min, t_sec, o_sec = clock(0)
    assert am_pm == 0, "Expected AM (0)"
    assert bit_list_to_int(t_hr, False) * 10 + bit_list_to_int(o_hr, False) == 11
    assert bit_list_to_int(t_min, False) * 10 + bit_list_to_int(o_min, False) == 59
    assert bit_list_to_int(t_sec, False) * 10 + bit_list_to_int(o_sec, False) == 59

    # Add exactly 1 second. This ripples through everything!
    clock.update_second(1)
    
    am_pm, t_hr, o_hr, t_min, o_min, t_sec, o_sec = clock(0)
    assert am_pm == 1, "Expected PM (1)"
    assert bit_list_to_int(t_hr, False) * 10 + bit_list_to_int(o_hr, False) == 0
    assert bit_list_to_int(t_min, False) * 10 + bit_list_to_int(o_min, False) == 0
    assert bit_list_to_int(t_sec, False) * 10 + bit_list_to_int(o_sec, False) == 0

    # --- Edge Case 2: The 24-Hour Wrap Around ---
    clock.update_hour(12)
    am_pm, t_hr, o_hr, t_min, o_min, t_sec, o_sec = clock(0)
    
    assert am_pm == 0, "Expected AM (0)"
    assert bit_list_to_int(t_hr, False) * 10 + bit_list_to_int(o_hr, False) == 0
    assert bit_list_to_int(t_min, False) * 10 + bit_list_to_int(o_min, False) == 0
    assert bit_list_to_int(t_sec, False) * 10 + bit_list_to_int(o_sec, False) == 0

if __name__ == "__main__":
    test_frequency_divider()
    test_nbits_frequency_divider()
    test_counter0_9()
    test_counter0_5()
    test_second_timer()
    test_minute_timer()
    test_hour_timer()
    test_hour_minute_second_timer()
    test_digital_clock_extreme_edge_cases()
