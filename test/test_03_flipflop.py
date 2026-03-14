
import sys
sys.path.append("../src")
from utils import Oscillator, ResetSetFlipFlop, ResetSetFlipFlop4Input, LevelTriggeredDTypeFlipFlop, LevelTriggeredDTypeFlipFlopWithClear, NBitLevelTriggeredDTypeFlipFlopWithClear, EdgeTriggeredDTypeFlipFlop, EdgeTriggeredDTypeFlipFlopWithPresetAndClear, NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear, NBitsAccumulator, FrequencyDivider, NBitsFrequencyDivider
from utils import int_to_nbit_list, bit_list_to_int
def test_oscillator():
    my_oscillator = Oscillator()
    assert my_oscillator.level() == 0, "Oscillator should start at 0"
    my_oscillator.tick()
    assert my_oscillator.level() == 1, "Oscillator should toggle to 1"
    my_oscillator.tick()
    assert my_oscillator.level() == 0, "Oscillator should toggle back to 0"

def test_reset_set_flip_flop():
    my_flipflop = ResetSetFlipFlop()
    
    # Test reset
    my_flipflop([0, 0]) # reset = 0, set = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "default state should be q=0 and q_bar=1"
    
    # Test set
    my_flipflop([0, 1]) # reset = 0, set = 1
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Set should set q to 1 and q_bar to 0"
    
    # Test hold (no change)
    my_flipflop([0, 0]) # reset = 0, set = 0 (hold)
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Hold should maintain previous state of q=1 and q_bar=0"

    my_flipflop([1, 0]) # reset = 1, set = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Reset should set q to 0 and q_bar to 1"

    # Test hold (no change)
    my_flipflop([0, 0]) # reset = 0, set = 0 (hold)
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain previous state of q=0 and q_bar=1"

def test_reset_set_flip_flop_4_input():
    my_flipflop = ResetSetFlipFlop4Input()
    
    # Test reset
    my_flipflop([0, 0, 0, 0]) # reset = 0, set = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "default state should be q=0 and q_bar=1"
    
    # Test set
    my_flipflop([0, 0, 0, 1]) # reset = 0, set = 1
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Set should set q to 1 and q_bar to 0"
    
    # Test hold (no change)
    my_flipflop([0, 0, 0, 0]) # reset = 0, set = 0 (hold)
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Hold should maintain previous state of q=1 and q_bar=0"

    my_flipflop([1, 0, 0, 0]) # reset = 1, set = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Reset should set q to 0 and q_bar to 1"

    # Test hold (no change)
    my_flipflop([0, 0, 0, 0]) # reset = 0, set = 0 (hold)
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain previous state of q=0 and q_bar=1"

def test_level_triggered_d_type_flip_flop():
    my_flipflop = LevelTriggeredDTypeFlipFlop()
    
    # Test D=0, CLK=0 (hold)
    my_flipflop([0, 0]) # D = 0, CLK = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain previous state of q=0 and q_bar=1"
    
    # Test D=1, CLK=0 (hold)
    my_flipflop([1, 0]) # D = 1, CLK = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain previous state of q=0 and q_bar=1"
    
    # Test D=1, CLK=1 (capture)
    my_flipflop([1, 1]) # D = 1, CLK = 1
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Capture should set q to D (1) and q_bar to inverse (0)"
    
    # Test D=0, CLK=0 (hold)
    my_flipflop([0, 0]) # D = 0, CLK = 0
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Hold should maintain previous state of q=1 and q_bar=0"
    
    # Test D=0, CLK=1 (capture)
    my_flipflop([0, 1]) # D = 0, CLK = 1
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Capture should set q to D (0) and q_bar to inverse (1)"

    # Test D=0, CLK=1 (capture)
    my_flipflop([0, 0]) # D = 0, CLK = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain previous state of q=0 and q_bar=1"

def test_level_triggered_d_type_flip_flop_with_clear():
    my_flipflop = LevelTriggeredDTypeFlipFlopWithClear()
    
    # Test D=0, CLK=0, CLR=0 (hold)
    my_flipflop([0, 0, 0]) # D = 0, CLK = 0, CLR = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain previous state of q=0 and q_bar=1"
    
    # Test D=1, CLK=0, CLR=0 (hold)
    my_flipflop([1, 0, 0]) # D = 1, CLK = 0, CLR = 0    
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain previous state of q=0 and q_bar=1"
    
    # Test D=1, CLK=1, CLR=0 (capture)
    my_flipflop([1, 1, 0]) # D = 1, CLK = 1, CLR = 0
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Capture should set q to D (1) and q_bar to inverse (0)"
    
    # Test D=0, CLK=0, CLR=0 (hold)
    my_flipflop([0, 0, 0]) # D = 0, CLK = 0, CLR = 0
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Hold should maintain previous state of q=1 and q_bar=0"
    
    # Test D=0, CLK=1, CLR=0 (capture)
    my_flipflop([0, 1, 0]) # D = 0, CLK = 1, CLR = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Capture should set q to D (0) and q_bar to inverse (1)"

    # Test D=0, CLK=0, CLR=0 (hold)
    my_flipflop([0, 0, 0]) # D = 0, CLK = 0, CLR = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain previous state of q=0 and q_bar=1"

    # Test D=0, CLK=1, CLR=1 (capture)
    my_flipflop([0, 1, 1]) # D = 0, CLK = 1, CLR = 1
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Clear should reset q to 0 and q_bar to 1"

    # Test D=0, CLK=1, CLR=1 (capture)
    my_flipflop([1, 1, 1]) # D = 1, CLK = 1, CLR = 1
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Clear should reset q to 0 and q_bar to 1"

def test_nbit_level_triggered_d_type_flip_flop_with_clear():
    nbits = 4
    my_flipflop = NBitLevelTriggeredDTypeFlipFlopWithClear(nbits)
    
    # Test D=0, CLK=0 (hold)
    my_flipflop([0, 0, 0, 0], 0, 0) # D = 0000, CLK = 0, CLR = 0
    assert my_flipflop.getQ() == [0, 0, 0, 0], "Hold should maintain previous state of q=0000"
    
    # Test D=1111, CLK=0 (hold)
    my_flipflop([1, 1, 1, 1], 0, 0) # D = 1111, CLK = 0, CLR = 0
    assert my_flipflop.getQ() == [0, 0, 0, 0], "Hold should maintain previous state of q=0000"
    
    # Test D=1111, CLK=1 (capture)
    my_flipflop([1, 1, 1, 1], 1, 0) # D = 1111, CLK = 1, CLR = 0
    assert my_flipflop.getQ() == [1, 1, 1, 1], "Capture should set q to D (1111)"
    
    # Test D=0000, CLK=0 (hold)
    my_flipflop([0, 0, 0, 0], 0, 0) # D = 0000, CLK = 0, CLR = 0
    assert my_flipflop.getQ() == [1, 1, 1, 1], "Hold should maintain previous state of q=1111"
    
    # Test D=0000, CLK=0, CLR = 1 (clear)
    my_flipflop([0, 1, 0, 1], 1, 1) # D = 0000, CLK = 1, CLR = 1
    assert my_flipflop.getQ() == [0, 0, 0, 0], "Clear should reset q to all zeros"

def test_edge_triggered_d_type_flip_flop():

    my_flipflop = EdgeTriggeredDTypeFlipFlop()
    
    # Test D=0, CLK=0 (hold)
    my_flipflop([0, 0]) # D = 0, CLK = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain previous state of q=0 and q_bar=1"
    
    # Test D=1, CLK=0 (hold)
    my_flipflop([1, 0]) # D = 1, CLK = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain previous state of q=0 and q_bar=1"
    
    # Test D=1, CLK rising edge (capture)
    my_flipflop([1, 1]) # D = 1, CLK = 1
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Capture should set q to D (1) and q_bar to inverse (0)"
    
    # Test D=0, CLK=1 (hold)
    my_flipflop([0, 1]) # D = 0, CLK = 1
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Hold should maintain previous state of q=1 and q_bar=0"
    
    # Test D=0, CLK falling edge (hold)
    my_flipflop([0, 0]) # D = 0, CLK = 0
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Hold should maintain previous state of q=1 and q_bar=0"
    
    # Test D=0, CLK rising edge (capture)
    my_flipflop([0, 1]) # D = 0, CLK = 1
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Capture should set q to D (0) and q_bar to inverse (1)"

def test_edge_triggered_d_type_flip_flop_with_preset_and_clear():
    my_flipflop = EdgeTriggeredDTypeFlipFlopWithPresetAndClear()
    
    # Test D=0, CLK=0, PRE=0, CLR=0 (hold)
    my_flipflop([0, 0, 0, 0]) # D = 0, CLK = 0, PRE = 0, CLR = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain previous state of q=0 and q_bar=1"
    
    # Test D=1, CLK=0, PRE=0, CLR=0 (hold)
    my_flipflop([1, 0, 0, 0]) # D = 1, CLK = 0, PRE = 0, CLR = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Hold should maintain previous state of q=0 and q_bar=1"
    
    # Test D=1, CLK rising edge, PRE=0, CLR=0 (capture)
    my_flipflop([1, 1, 0, 0]) # D = 1, CLK = 1, PRE = 0, CLR = 0
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Capture should set q to D (1) and q_bar to inverse (0)"
    
    # Test D=0, CLK=1, PRE=0, CLR=0 (hold)
    my_flipflop([0, 1, 0, 0]) # D = 0, CLK = 1, PRE = 0, CLR = 0
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Hold should maintain previous state of q=1 and q_bar=0"
    
    # Test D=0, CLK falling edge, PRE=0, CLR=0 (hold)
    my_flipflop([0, 0, 0, 0]) # D = 0, CLK = 0, PRE = 0, CLR = 0
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Hold should maintain previous state of q=1 and q_bar=0"

    # Test D=0, CLK rising edge, PRE=0, CLR=0 (capture)
    my_flipflop([0, 1, 0, 0]) # D = 1, CLK = 1, PRE = 0, CLR = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Capture should set q to D (0) and q_bar to inverse (1)"
    
    # Test D=0, CLK rising edge, PRE=1, CLR=0 (capture)
    my_flipflop([0, 1, 1, 0]) # D = 1, CLK = 1, PRE = 1, CLR = 0
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Preset should set q to 1 and q_bar to 0 regardless of D and CLK"
    
    # Test D=0, CLK falling edge, PRE=0, CLR=0 (hold)
    my_flipflop([0, 0, 0, 0]) # D = 0, CLK = 0, PRE = 0, CLR = 0
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Hold should maintain previous state of q=1 and q_bar=0"

    # Test D=1, CLK rising edge, PRE=0, CLR=1 (clear should override preset)
    my_flipflop([1, 1, 0, 1]) # D = 1, CLK = 1, PRE = 0, CLR = 1
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Clear should set q to 0 and q_bar to 1 regardless of D and CLK"

    # Test D=1, CLK=1, PRE=0, CLR=0 (Hold should maintain preset state since clear is not active)
    my_flipflop([1, 1, 0, 0]) # D = 1, CLK = 1, PRE = 0, CLR = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Clear should set q to 0 and q_bar to 1 regardless of D and CLK"

    # Test D=1, CLK=0, PRE=0, CLR=0 (Hold should maintain preset state since clear is not active)
    my_flipflop([1, 0, 0, 0]) # D = 1, CLK = 0, PRE = 0, CLR = 0
    assert my_flipflop.getQ() == 0 and my_flipflop.getQ_bar() == 1, "Clear should set q to 0 and q_bar to 1 regardless of D and CLK"

    # Test D=1, CLK rising edge, PRE=0, CLR=0 (Capture)
    my_flipflop([1, 1, 0, 0]) # D = 1, CLK = 1, PRE = 0, CLR = 0
    assert my_flipflop.getQ() == 1 and my_flipflop.getQ_bar() == 0, "Capture should set q to D (1) and q_bar to inverse (0)"

def test_nbits_edge_triggered_d_type_flip_flop_with_preset_and_clear():
    nbits = 4
    my_flipflop = NBitsEdgeTriggeredDTypeFlipFlopWithPresetAndClear(nbits)
    
    # Test D=0000, CLK=0 (hold)
    my_flipflop([0, 0, 0, 0], 0) # D = 0000, CLK = 0, PRE = 0000, CLR = 0000
    assert my_flipflop.getQ() == [0, 0, 0, 0], "Hold should maintain previous state of q=0000"
    
    # Test D=1111, CLK=0 (hold)
    my_flipflop([1, 1, 1, 1], 0) # D = 1111, CLK = 0, PRE = 0000, CLR = 0000
    assert my_flipflop.getQ() == [0, 0, 0, 0], "Hold should maintain previous state of q=0000"
    
    # Test D=1111, CLK rising edge (capture)
    my_flipflop([1, 1, 1, 1], 1) # D = 1111, CLK = 1, PRE = 00000 CLR = 00000
    assert my_flipflop.getQ() == [1, 1, 1, 1], "Capture should set q to D (1111)"
    
    # Test D=00000 CLK=1 (hold)
    my_flipflop([0, 0, 0, 0], 1) 
    assert my_flipflop.getQ() == [1 ,1 ,1 ,1], "Hold should maintain previous state of q=11111"
    
    # Test D=00000 CLK= falling edge(hold)
    my_flipflop([0, 0, 0, 0], 0) # D = 00000 CLK= falling edge , PRE=00000 CLR=00000
    assert my_flipflop.getQ() == [1 ,1 ,1 ,1], "Hold should maintain previous state of q=11111"
    
    # Test D=00000 CLK= rising edge (capture)
    my_flipflop([0, 0, 0, 0], 1) # D = 00000 CLK= falling edge , PRE=00000 CLR=00000
    assert my_flipflop.getQ() == [0 ,0 ,0 ,0], "Capture should set q to D (0000)"
    
def test_nbits_accumulator():
    nbits = 4
    my_accumulator = NBitsAccumulator(nbits)
    my_accumulator.clear() # Clear the accumulator to start from 0
    nums_to_add = [1, 2, 3, -14] # We will add these numbers sequentially and check the result after each addition
    inputs_seque = [int_to_nbit_list(num, nbits) for num in nums_to_add]
    # print(inputs_seque)
    my_accumulator(inputs_seque)
    result_bits = my_accumulator.get_register()
    total = bit_list_to_int(result_bits, signed=True)
    assert total == sum(nums_to_add), f"After adding, expected total {sum(nums_to_add)} but got {total}"
