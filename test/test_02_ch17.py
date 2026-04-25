from src.utils import *

def test_oscillator():
    my_oscillator = Oscillator()
    assert my_oscillator.level() == 0, "Oscillator should start at 0"
    
    my_oscillator.tick()
    assert my_oscillator.level() == 1, "Oscillator should toggle to 1"
    
    my_oscillator.tick()
    assert my_oscillator.level() == 0, "Oscillator should toggle back to 0"
    
    my_oscillator.tick()
    assert my_oscillator.level() == 1, "Oscillator should toggle back to 1"

def test_reset_set_flip_flop():
    my_flipflop = ResetSetFlipFlop()
    
    # 1. Reset
    my_flipflop([1, 0]) # R=1, S=0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Reset should set Q=0, Q_bar=1"
    
    # 2. Hold
    my_flipflop([0, 0]) # R=0, S=0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain Q=0"
    
    # 3. Set
    my_flipflop([0, 1]) # R=0, S=1
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Set should set Q=1, Q_bar=0"
    
    # 4. Hold
    my_flipflop([0, 0]) # R=0, S=0
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Hold should maintain Q=1"

def test_level_triggered_d_type_flip_flop():
    my_flipflop = LevelTriggeredDTypeFlipFlop()
    
    # Initial D=0, CLK=0
    my_flipflop([0, 0]) 
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Start state Q=0"
    
    # D changes to 1, but CLK is 0. It should HOLD.
    my_flipflop([1, 0]) 
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold state: Clock is low, ignores D=1"
    
    # CLK goes high (1). It should CAPTURE D.
    my_flipflop([1, 1]) 
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Capture state: Clock is high, copies D=1"
    
    # CLK goes low (0). It should HOLD.
    my_flipflop([0, 0]) 
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Hold state: Clock went low, memory retains 1"

def test_level_triggered_d_type_flip_flop_with_clear():
    my_flipflop = LevelTriggeredDTypeFlipFlopWithClear()
    
    # Set it to 1 first
    my_flipflop([1, 1, 0]) # D=1, CLK=1, CLR=0
    assert my_flipflop.getQ() == 1, "Capture D=1"
    
    # Test Clear pin while Clock is low
    my_flipflop([1, 0, 1]) # D=1, CLK=0, CLR=1
    assert my_flipflop.getQ() == 0, "Clear pin must force Q=0 asynchronously"
    
    # Set back to 1
    my_flipflop([1, 1, 0]) 
    assert my_flipflop.getQ() == 1
    
    # Test Clear pin while Clock is high (Conflict test)
    my_flipflop([1, 1, 1]) # D=1, CLK=1, CLR=1
    assert my_flipflop.getQ() == 0, "Clear pin must overpower the Data pin"

def test_edge_triggered_d_type_flip_flop():
    my_flipflop = EdgeTriggeredDTypeFlipFlop()
    my_flipflop([0, 0])
    # 1. Setup: D=1, CLK=0 (Hold)
    my_flipflop([1, 0])
    assert my_flipflop.getQ() == 0, "Clock is low, ignores D=1"
    
    # 2. Rising Edge: CLK goes 0 -> 1 (Capture)
    my_flipflop([1, 1])
    assert my_flipflop.getQ() == 1, "Rising Edge: Captures D=1"
    
    # 3. Change Data while CLK is High (Should Ignore!)
    my_flipflop([0, 1])
    assert my_flipflop.getQ() == 1, "Clock is steady high, no rising edge. Must ignore D=0"
    
    # 4. Falling Edge: CLK goes 1 -> 0 (Should Ignore!)
    my_flipflop([0, 0])
    assert my_flipflop.getQ() == 1, "Falling Edge: Must ignore D=0 and hold Q=1"
    
    # 5. Next Rising Edge: CLK goes 0 -> 1 (Capture)
    my_flipflop([0, 1])
    assert my_flipflop.getQ() == 0, "Rising Edge: Captures D=0"

    my_flipflop([1, 0])
    my_flipflop([1, 1])
    # now q is 1
    my_flipflop([0, 0])
    my_flipflop([1, 1])
    assert my_flipflop.getQ() == 0, "Rising Edge: Captures D when last clock is 0"

def test_edge_triggered_d_type_flip_flop_with_preset_and_clear():
    my_flipflop = EdgeTriggeredDTypeFlipFlopWithPresetAndClear()
    # NOTE: The "Setup Time" / Priming the Clock
    # In real silicon, an edge-triggered flip-flop triggers on the TRANSITION (0 -> 1).
    # When we power on the simulation, the internal latches need to see a stable Low (0) 
    # clock first to open their input gates and prepare the internal wires. 
    # If we start immediately with CLK=1, there is no "rising edge", just a static high, 
    # and the data will be ignored.
    # NOTE: The "Setup Time" / Priming the Clock
    my_flipflop([0, 0, 0, 0]) # D=0, CLK=0, PRE=0, CLR=0
    assert my_flipflop.getQ() == 0, "Initial power-on state"

    # Test 1: Basic Rising Edge Capture
    # Test 1: Basic Rising Edge Capture (Strict Hardware Adherence)
    my_flipflop([1, 0, 0, 0]) # D=1, CLK=0 (Setup Time: Prime the latches)
    my_flipflop([1, 1, 0, 0]) # D=1, CLK=1 (0->1 transition: Capture!)
    assert my_flipflop.getQ() == 1, "Rising edge captures D=1"

    # Test 2: Data changes while Clock is HIGH (Should be ignored)
    my_flipflop([0, 1, 0, 0]) # D changes to 0, CLK remains 1
    assert my_flipflop.getQ() == 1, "Clock is steady high. Must ignore D=0 and hold Q=1"

    # Test 3: Falling Edge (Clock drops, state holds)
    my_flipflop([1, 0, 0, 0]) # D=1, CLK goes 1->0
    assert my_flipflop.getQ() == 1, "Falling edge. Must hold Q=1"

    # Test 4: Setup Time (Data changes to 0 while Clock is LOW)
    # The master latches prepare to read a 0, but the output doesn't change yet.
    my_flipflop([0, 0, 0, 0]) # D changes to 0, CLK remains 0
    assert my_flipflop.getQ() == 1, "Clock is steady low. Must ignore D=0 and hold Q=1"

    # Test 5: Rising Edge (Data is held steady at 0 while Clock rises)
    my_flipflop([0, 1, 0, 0]) # D remains 0, CLK goes 0->1
    assert my_flipflop.getQ() == 0, "Rising edge captures the D=0 that was set up"

    # Test 6: Setup Time again (Data changes to 1 while Clock is LOW)
    my_flipflop([0, 0, 0, 0]) # First drop the clock
    my_flipflop([1, 0, 0, 0]) # Now change Data to 1
    assert my_flipflop.getQ() == 0, "Clock is steady low. Must ignore D=1 and hold Q=0"

    # Test 7: Rising Edge captures the new 1
    my_flipflop([1, 1, 0, 0]) # D remains 1, CLK goes 0->1
    assert my_flipflop.getQ() == 1, "Rising edge captures the D=1 that was set up"

    # Test 8: Clock goes low, holds state
    my_flipflop([1, 0, 0, 0]) # D=1, CLK=0
    assert my_flipflop.getQ() == 1, "Clock went low. State holds at Q=1."

    # Test 9: New Rising Edge
    my_flipflop([1, 1, 0, 0]) # D=1, CLK=1 (0->1)
    assert my_flipflop.getQ() == 1, "New rising edge. Captures D=1."

    # Test 10: Asynchronous Preset while Clock is LOW
    my_flipflop([0, 0, 1, 0]) # D=0, CLK=0, PRE=1, CLR=0
    assert my_flipflop.getQ() == 1, "Preset pin forces Q=1 asynchronously while clock is low"

    # Test 11: Drop Preset, state should hold
    my_flipflop([0, 0, 0, 0]) # D=0, CLK=0, PRE=0, CLR=0
    assert my_flipflop.getQ() == 1, "Dropped preset. State holds at Q=1."

    # Test 12: Asynchronous Preset while Clock is HIGH
    my_flipflop([0, 1, 0, 0]) # First, let's capture a 0 (CLK 0->1)
    assert my_flipflop.getQ() == 0, "Captured D=0"
    
    my_flipflop([0, 1, 1, 0]) # Now apply Preset while CLK is still high
    assert my_flipflop.getQ() == 1, "Preset pin forces Q=1 asynchronously even when clock is high"

    # Test 13: Asynchronous Clear while Clock is HIGH
    # First, let's capture a 1 so we have something to clear
    my_flipflop([1, 0, 0, 0]) # Setup: Drop clock to 0
    my_flipflop([1, 1, 0, 0]) # Rising Edge (0->1) captures D=1
    assert my_flipflop.getQ() == 1, "Captured D=1"

    # Now, while the clock remains steady at 1, hit the Clear pin!
    my_flipflop([1, 1, 0, 1]) 
    assert my_flipflop.getQ() == 0, "Clear pin forces Q=0 asynchronously even when clock is steady high"

    # Test 14: Drop Clear, state should hold at 0
    my_flipflop([1, 1, 0, 0]) # D=1, CLK=1, PRE=0, CLR=0
    assert my_flipflop.getQ() == 0, "Dropped clear. State holds at Q=0."

    my_flipflop([0, 0, 0, 0])
    my_flipflop([0, 1, 0, 0]) 

    my_flipflop([0, 0, 0, 0]) 
    my_flipflop([1, 1, 0, 0]) 
    assert my_flipflop.getQ() == 0, "FF2 clock triggers this gate to lock out FF1."
    
    # my_flipflop([1, 0, 0, 0]) 
    # my_flipflop([1, 1, 0, 0]) 

    my_flipflop([1, 0, 0, 0]) 
    my_flipflop([0, 1, 0, 0]) 
    assert my_flipflop.getQ() == 1, "FF2 clock triggers this gate to lock out FF1."
    

def test_nbits_accumulator():
    nbits = 8  # Use 8 bits to allow for larger math testing
    my_accumulator = NBitsAccumulator(nbits)
    
    # 1. Test Hardware Clear
    my_accumulator.clear()
    assert bit_list_to_int(my_accumulator.get_register(), signed=True) == 0, "Clear should reset hardware to 0"
    
    # 2. Add a sequence of numbers: 5 + 10 + (-3) = 12
    nums_to_add = [5, 10, -3] 
    inputs_sequence = [int_to_nbit_list(num, nbits) for num in nums_to_add]
    
    my_accumulator(inputs_sequence)
    
    result_bits = my_accumulator.get_register()
    total = bit_list_to_int(result_bits, signed=True)
    assert total == sum(nums_to_add), f"Expected total {sum(nums_to_add)} but got {total}"
    
    # 3. Add one more number to current state: 12 + 20 = 32
    my_accumulator([int_to_nbit_list(20, nbits)])
    total = bit_list_to_int(my_accumulator.get_register(), signed=True)
    assert total == 32, f"Expected total 32 but got {total}"

if __name__ == "__main__":
    test_oscillator()
    test_reset_set_flip_flop()
    test_level_triggered_d_type_flip_flop()
    test_level_triggered_d_type_flip_flop_with_clear()
    test_edge_triggered_d_type_flip_flop()
    test_edge_triggered_d_type_flip_flop_with_preset_and_clear()
    test_nbits_accumulator()