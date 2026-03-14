import sys
sys.path.append("../src")
from utils import Oscillator, FrequencyDivider, NBitsFrequencyDivider, Counter0_9, Counter0_5
from utils import SecondTimer, MinuteTimer, HourTimer, HourMinuteSecondTimer
from utils import int_to_nbit_list, bit_list_to_int

def test_frequency_divider():
    my_oscillator = Oscillator()
    my_freq_divider = FrequencyDivider()

    # init state of the gloden clock and divider
    previous_clock_state = -1
    golden_clock_state = 0
    gloden_q = 0
    for tick in range(1, 11):
        assert golden_clock_state == my_oscillator.level(), f"At tick {tick}, expected clock state {golden_clock_state} but got {my_oscillator.level()}"
        
        # Run the hardware simulation
        my_freq_divider(my_oscillator.level())
        if previous_clock_state == 0 and golden_clock_state == 1:  # Only toggle the expected output on the rising edge of the clock
            gloden_q = 1 - gloden_q

        assert gloden_q == my_freq_divider.getQ(), f"At tick {tick}, expected divided output {gloden_q} but got {my_freq_divider.getQ()}"

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

# test_nbits_frequency_divider()

def test_counter0_9():
    my_oscillator = Oscillator()
    nbits = 4
    my_counter = Counter0_9()
    
    previous_clock_state = -1
    golden_clock_state = 0
    golden_qs = [0] * nbits
    golden_value = 0
    for clk in range(20):
        assert golden_clock_state == my_oscillator.level(), f"At clock {clk}, expected clock state {golden_clock_state} but got {my_oscillator.level()}"
        my_counter(my_oscillator.level())
        if previous_clock_state == 0 and golden_clock_state == 1:  # Only increment the expected counter value on the rising edge of the clock
            golden_value = (golden_value + 1) % 10
            golden_qs = int_to_nbit_list(golden_value, nbits)

        assert golden_qs == my_counter.getQs(), f"At clock {clk}, expected counter value {golden_value} but got {int(''.join(str(bit) for bit in my_counter.getQs()))}"
        previous_clock_state = golden_clock_state
        my_oscillator.tick()  # Move to the next clock state for the next iteration
        golden_clock_state = 1 - golden_clock_state  # Toggle the expected clock state for

def test_counter0_5():
    my_oscillator = Oscillator()
    nbits = 3
    my_counter = Counter0_5()
    
    previous_clock_state = -1
    golden_clock_state = 0
    golden_qs = [0] * nbits
    golden_value = 0
    for clk in range(20):
        assert golden_clock_state == my_oscillator.level(), f"At clock {clk}, expected clock state {golden_clock_state} but got {my_oscillator.level()}"
        my_counter(my_oscillator.level())
        if previous_clock_state == 0 and golden_clock_state == 1:  # Only increment the expected counter value on the rising edge of the clock
            golden_value = (golden_value + 1) % 6
            golden_qs = int_to_nbit_list(golden_value, nbits)

        assert golden_qs == my_counter.getQs(), f"At clock {clk}, expected counter value {golden_value} but got {int(''.join(str(bit) for bit in my_counter.getQs()))}"
        previous_clock_state = golden_clock_state
        my_oscillator.tick()  # Move to the next clock state for the next iteration
        golden_clock_state = 1 - golden_clock_state  # Toggle the expected clock state for

def test_second_timer():
    my_oscillator = Oscillator()
    my_second_timer = SecondTimer()
    
    previous_clock_state = -1
    golden_clock_state = 0
    golden_lower_qs = [0] * 4  # Lower 4 bits for seconds (0-9)
    golden_upper_qs = [0] * 3  # Upper 3 bits for tens of seconds (0-5)
    golden_value = 0

    for clk in range(120):  # Simulate 120 clock ticks (2 minutes)
        assert golden_clock_state == my_oscillator.level(), f"At clock {clk}, expected clock state {golden_clock_state} but got {my_oscillator.level()}"
        my_second_timer(my_oscillator.level())
        if previous_clock_state == 0 and golden_clock_state == 1:  # Only increment the expected timer value on the rising edge of the clock
            golden_value = (golden_value + 1) % 60
            golden_lower_qs = int_to_nbit_list(golden_value % 10, 4)
            golden_upper_qs = int_to_nbit_list(golden_value // 10, 3)
        # print(f"At clock {clk}, expected value {golden_value}, got {bit_list_to_int(my_second_timer.getBitsOfHigh(), False)}{bit_list_to_int(my_second_timer.getBitsOfLow(), False)}")
        assert golden_lower_qs == my_second_timer.getBitsOfLow(), f"At clock {clk}, expected second timer value {golden_lower_qs} but got {my_second_timer.getBitsOfLow()}"
        assert golden_upper_qs == my_second_timer.getBitsOfHigh(), f"At clock {clk}, expected second timer value {golden_upper_qs} but got {my_second_timer.getBitsOfHigh()}"
        previous_clock_state = golden_clock_state
        my_oscillator.tick()  # Move to the next clock state for the next iteration
        golden_clock_state = 1 - golden_clock_state  # Toggle the expected clock state for
# test_second_timer()

def test_minute_timer():
    my_oscillator = Oscillator()
    my_minute_timer = MinuteTimer()
    
    previous_clock_state = -1
    golden_clock_state = 0
    golden_lower_qs = [0] * 4  # Lower 4 bits for minutes (0-9)
    golden_upper_qs = [0] * 3  # Upper 3 bits for tens of minutes (0-5)
    golden_value = 0

    for clk in range(120):  # Simulate 120 clock ticks (2 minutes)
        assert golden_clock_state == my_oscillator.level(), f"At clock {clk}, expected clock state {golden_clock_state} but got {my_oscillator.level()}"
        my_minute_timer(my_oscillator.level())
        if previous_clock_state == 0 and golden_clock_state == 1:  # Only increment the expected timer value on the rising edge of the clock
            golden_value = (golden_value + 1) % 60
            golden_lower_qs = int_to_nbit_list(golden_value % 10, 4)
            golden_upper_qs = int_to_nbit_list(golden_value // 10, 3)
        assert golden_lower_qs == my_minute_timer.getBitsOfLow(), f"At clock {clk}, expected minute timer value {golden_lower_qs} but got {my_minute_timer.getBitsOfLow()}"
        assert golden_upper_qs == my_minute_timer.getBitsOfHigh(), f"At clock {clk}, expected minute timer value {golden_upper_qs} but got {my_minute_timer.getBitsOfHigh()}"
        previous_clock_state = golden_clock_state
        my_oscillator.tick()  # Move to the next clock state for the next iteration
        golden_clock_state = 1 - golden_clock_state  # Toggle the expected clock state for

def test_hour_timer():
    my_oscillator = Oscillator()
    my_hour_timer = HourTimer()
    
    previous_clock_state = -1
    golden_clock_state = 0
    golden_lower_qs = [0] * 4  # Lower 4 bits for hours (0-9)
    golden_upper_qs = [0] * 1  # Upper 1 bits for tens of hours (0-1)
    golden_value = 0

    for clk in range(48):  # Simulate 48 clock ticks (2 days)
        assert golden_clock_state == my_oscillator.level(), f"At clock {clk}, expected clock state {golden_clock_state} but got {my_oscillator.level()}"
        my_hour_timer(my_oscillator.level())
        if previous_clock_state == 0 and golden_clock_state == 1:  # Only increment the expected timer value on the rising edge of the clock
            golden_value = (golden_value + 1) % 12
            golden_lower_qs = int_to_nbit_list(golden_value % 10, 4)
            golden_upper_qs = int_to_nbit_list(golden_value // 10, 1)
        Qs = my_hour_timer.getQs()
        assert golden_lower_qs == list(Qs[1:5]), f"At clock {clk}, expected hour timer value {golden_lower_qs} but got {list(Qs[1:5])}"
        assert golden_upper_qs == [Qs[0]], f"At clock {clk}, expected hour timer value {golden_upper_qs} but got {[Qs[0]]}"
        previous_clock_state = golden_clock_state
        my_oscillator.tick()  # Move to the next clock state for the next iteration
        golden_clock_state = 1 - golden_clock_state  # Toggle the expected clock state for

def test_hour_minute_second_timer():
    my_oscillator = Oscillator()
    my_timer = HourMinuteSecondTimer()
    
    previous_clock_state = -1
    golden_clock_state = 0
    golden_seconds_lower_qs = [0] * 4  # Lower 4 bits for seconds (0-9)
    golden_seconds_upper_qs = [0] * 3  # Upper 3 bits for tens of seconds (0-5)
    golden_minutes_lower_qs = [0] * 4  # Lower 4 bits for minutes (0-9)
    golden_minutes_upper_qs = [0] * 3  # Upper 3 bits for tens of minutes (0-5)
    golden_hours_lower_qs = [0] * 4  # Lower 4 bits for hours (0-9)
    golden_hours_upper_qs = [0] * 1  # Upper 1 bit for tens of hours (0-1)
    golden_am_pm_q = [0] * 1  # 1 bit for AM/PM
    golden_seconds_value = 0
    golden_minutes_value = 0
    golden_hours_value = 0
    golden_is_am = True

    for clk in range(7200):  # Simulate 7200 clock ticks (1 hours)
        assert golden_clock_state == my_oscillator.level(), f"At clock {clk}, expected clock state {golden_clock_state} but got {my_oscillator.level()}"
        am_pm_q, bits_tens_hour, bits_ones_hour, bits_tens_min, bits_ones_min, bits_tens_sec, bits_ones_sec = my_timer(my_oscillator.level())
        if previous_clock_state == 0 and golden_clock_state == 1:  # Only increment the expected timer value on the rising edge of the clock
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
        assert golden_seconds_lower_qs == bits_ones_sec, f"At clock {clk}, expected seconds lower bits {golden_seconds_lower_qs} but got {bits_ones_sec}"
        assert golden_seconds_upper_qs == bits_tens_sec, f"At clock {clk}, expected seconds upper bits {golden_seconds_upper_qs} but got {bits_tens_sec}"
        assert golden_minutes_lower_qs == bits_ones_min, f"At clock {clk}, expected minutes lower bits {golden_minutes_lower_qs} but got {bits_ones_min}"
        assert golden_minutes_upper_qs == bits_tens_min, f"At clock {clk}, expected minutes upper bits {golden_minutes_upper_qs} but got {bits_tens_min}"
        assert golden_hours_lower_qs == bits_ones_hour, f"At clock {clk}, expected hours lower bits {golden_hours_lower_qs} but got {bits_ones_hour}"
        assert golden_hours_upper_qs == bits_tens_hour, f"At clock {clk}, expected hours upper bits {golden_hours_upper_qs} but got {bits_tens_hour}"
        assert golden_am_pm_q == [am_pm_q], f"At clock {clk}, expected AM/PM bit {golden_am_pm_q} but got {[am_pm_q]}"
        previous_clock_state = golden_clock_state
        my_oscillator.tick()  # Move to the next clock state for the next iteration
        golden_clock_state = 1 - golden_clock_state  # Toggle the expected clock state for the next iteration

# ==========================================
# 2. TIME-TRAVEL STRESS TESTING (Testing Edge Cases)
# ==========================================
def test_digital_clock_extreme_edge_cases():
    """
    Instead of ticking the clock 86,400 times manually, we use your brilliant 
    update_* methods to 'time travel' to edge cases and verify the cascades.
    """
    clock = HourMinuteSecondTimer()
    # because we use edge triggered flip-flops, we need to make sure we are on the rising edge 
    # of the clock before we update the time, otherwise the updates won't take effect until the 
    # next rising edge, which will mess up our testing. 
    # So we will tick the clock once to get to the rising edge before we start updating the time.
    am_pm, t_hr, o_hr, t_min, o_min, t_sec, o_sec = clock(0)
    # print(am_pm, t_hr, o_hr, t_min, o_min, t_sec, o_sec)

    # --- Edge Case 1: The 11:59:59 to 12:00:00 Cascade ---
    # Fast forward to 11:59:59 AM
    clock.update_hour(11)
    clock.update_minute(59)
    clock.update_second(59)
    
    # Verify we are at 11:59:59 AM (am_pm == 0)
    am_pm, t_hr, o_hr, t_min, o_min, t_sec, o_sec = clock(0)
    assert am_pm == 0, f"Expected AM (0) but got {am_pm}"
    # this is BCD not binary, so we need to convert the tens and ones separately and then combine them
    assert bit_list_to_int(t_hr, signed=False) * 10 + bit_list_to_int(o_hr, signed=False) == 11, f"Expected hour 11 but got {bit_list_to_int(t_hr, signed=False) * 10 + bit_list_to_int(o_hr, signed=False)}"
    assert bit_list_to_int(t_min, signed=False) * 10 + bit_list_to_int(o_min, signed=False) == 59, f"Expected minute 59 but got {bit_list_to_int(t_min, signed=False) * 10 + bit_list_to_int(o_min, signed=False)}"
    assert bit_list_to_int(t_sec, signed=False) * 10 + bit_list_to_int(o_sec, signed=False) == 59, f"Expected second 59 but got {bit_list_to_int(t_sec, signed=False) * 10 + bit_list_to_int(o_sec, signed=False)}"

    # THE STRESS TEST: Add exactly 1 second. 
    # This must ripple through all 3 tiers of timers and the AM/PM flip-flop!
    clock.update_second(1)
    
    am_pm, t_hr, o_hr, t_min, o_min, t_sec, o_sec = clock(0)
    assert am_pm == 1, f"Expected PM (1) but got {am_pm}"
    assert bit_list_to_int(t_hr, signed=False) * 10 + bit_list_to_int(o_hr, signed=False) == 0, f"Expected hour 0 but got {bit_list_to_int(t_hr, signed=False) * 10 + bit_list_to_int(o_hr, signed=False)}"
    assert bit_list_to_int(t_min, signed=False) * 10 + bit_list_to_int(o_min, signed=False) == 0, f"Expected minute 0 but got {bit_list_to_int(t_min, signed=False) * 10 + bit_list_to_int(o_min, signed=False)}"
    assert bit_list_to_int(t_sec, signed=False) * 10 + bit_list_to_int(o_sec, signed=False) == 0, f"Expected second 0 but got {bit_list_to_int(t_sec, signed=False) * 10 + bit_list_to_int(o_sec, signed=False)}"

    # --- Edge Case 2: The 24-Hour Wrap Around ---
    # From 12:00:00 PM, add exactly 12 hours. It should become 12:00:00 AM.
    clock.update_hour(12)
    am_pm, t_hr, o_hr, t_min, o_min, t_sec, o_sec = clock(0)
    
    assert am_pm == 0, f"Expected AM (0) but got {am_pm}"
    assert bit_list_to_int(t_hr, signed=False) * 10 + bit_list_to_int(o_hr, signed=False) == 0, f"Expected hour 0 but got {bit_list_to_int(t_hr, signed=False) * 10 + bit_list_to_int(o_hr, signed=False)}"
    assert bit_list_to_int(t_min, signed=False) * 10 + bit_list_to_int(o_min, signed=False) == 0, f"Expected minute 0 but got {bit_list_to_int(t_min, signed=False) * 10 + bit_list_to_int(o_min, signed=False)}"
    assert bit_list_to_int(t_sec, signed=False) * 10 + bit_list_to_int(o_sec, signed=False) == 0, f"Expected second 0 but got {bit_list_to_int(t_sec, signed=False) * 10 + bit_list_to_int(o_sec, signed=False)}"
