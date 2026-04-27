# Python Intel 8080 CPU Simulator (Gate-Level)

Welcome! This repository is a Python-based simulation of the classic Intel 8080 CPU architecture. 

Inspired by Charles Petzold's incredible book *Code: The Hidden Language of Computer Hardware and Software (2nd Edition)* and Andrej Karpathy's *micrograd* project, this simulator builds a computer from the ground up. Starting from basic logic gates (AND, OR, NOT), we construct an ALU, Memory, and a Control Unit. 

Currently, this project supports a core subset of the 8080 instruction set. To run a program, you feed it direct machine code (hex/binary), and it will execute the logic cycle by cycle. 

I am still actively learning and building this out. If you spot any bugs, have suggestions, or want to contribute, your feedback is incredibly welcome!

## Supported Instruction Set

Below is the subset of Intel 8080 instructions currently supported by this simulator's Control Unit. 

### Main Operation Codes
| Instruction | Description | Operation Code (Binary) |
| :--- | :--- | :--- |
| `MOV r, r` | Move Register to Register | `0 1 D D D S S S` |
| `MOV r, M` | Move Memory to Register | `0 1 D D D 1 1 0` |
| `MOV M, r` | Move Register to Memory | `0 1 1 1 0 S S S` |
| `HLT` | Halt the CPU | `0 1 1 1 0 1 1 0` |
| `MVI r, data` | Move Immediate to Register | `0 0 D D D 1 1 0` |
| `MVI M, data` | Move Immediate to Memory | `0 0 1 1 0 1 1 0` |
| `ADD, ADC, SUB... r` | Arithmetic/Logic with Register | `1 0 F F F S S S` |
| `ADD, ADC, SUB... M` | Arithmetic/Logic with Memory | `1 0 F F F 1 1 0` |
| `ADI, ACI, SUI... data` | Arithmetic/Logic Immediate | `1 1 F F F 1 1 0` |
| `INX HL` | Increment HL Register Pair | `0 0 1 0 0 0 1 1` |
| `DCX HL` | Decrement HL Register Pair | `0 0 1 0 1 0 1 1` |
| `LDA addr` | Load Accumulator Direct | `0 0 1 1 1 0 1 0` |
| `STA addr` | Store Accumulator Direct | `0 0 1 1 0 0 1 0` |

### Bit Explanations: `DDD`, `SSS`, and `FFF`

The placeholder bits in the table above map to specific Registers and Arithmetic operations.

**Registers (`DDD` = Destination, `SSS` = Source):**
| Binary Code | Register |
| :---: | :--- |
| `000` | **B** |
| `001` | **C** |
| `010` | **D** |
| `011` | **E** |
| `100` | **H** |
| `101` | **L** |
| `110` | **M** (Memory pointed to by `[HL]`) |
| `111` | **A** (Accumulator) |

**ALU Operations (`FFF` = Function):**
| Binary Code | Operation | Instruction Prefix |
| :---: | :--- | :--- |
| `000` | Add | `ADD` / `ADI` |
| `001` | Add with Carry | `ADC` / `ACI` |
| `010` | Subtract | `SUB` / `SUI` |
| `011` | Subtract with Borrow | `SBB` / `SBI` |
| `100` | Bitwise AND | `ANA` / `ANI` |
| `101` | Bitwise XOR | `XRA` / `XRI` |
| `110` | Bitwise OR | `ORA` / `ORI` |
| `111` | Compare | `CMP` / `CPI` |

---

## Example Usage

Here is an example of loading and executing the "Sum Array" program (from Page 377 of *Code*). It calculates the sum of `[1, 2, 3, 4, 5]` and stores the result (`15` or `0x0F`) in RAM.

```python
from utils import CPUSubSet_8080, Oscillator, int_to_16bit_list, bit_list_to_int

cpu = CPUSubSet_8080()
system_tick = Oscillator()
    
program = [
    0x2E, 0x00,       # 0000h: MVI L, 00h
    0x26, 0x10,       # 0002h: MVI H, 10h   (HL is now 1000h)
    0x7E,             # 0004h: MOV A, M     (A = RAM[1000h])
    0x23,             # 0005h: INX HL       (HL = 1001h)
    0x86,             # 0006h: ADD M        (A = A + RAM[1001h])
    0x23,             # 0007h: INX HL
    0x86,             # 0008h: ADD M
    0x23,             # 0009h: INX HL
    0x86,             # 000Ah: ADD M
    0x23,             # 000Bh: INX HL
    0x86,             # 000Ch: ADD M
    0x32, 0x11, 0x00, # 000Dh: STA 0011h    (RAM[0011h] = A)
    0x76              # 0010h: HLT
]

cpu.load_program(program, start_address=0x0000)

# Array of data to sum up
data_values = [0x01, 0x02, 0x03, 0x04, 0x05]
cpu.load_program(data_values, start_address=0x1000)
cpu.reset()

# Run the system clock
for _ in range(1000):
    cpu.tick(system_tick.level())
    system_tick.tick()
    if cpu.current_halt_state == 1:
        break

assert cpu.current_halt_state == 1, "CPU did not halt. Reached max ticks."

# Read result from RAM
result_bits = cpu.ram.read(int_to_16bit_list(0x0011), enable=1)
result_val = bit_list_to_int(result_bits, signed=True)

assert result_val == 15, f"Sum is incorrect. Expected 15, got {result_val}"
print("[       OK ] Sum Array Program (1 + 2 + 3 + 4 + 5 = 15)")
```
Execution Output
The simulator tracks the Program Counter (PC), Address Bus, Data Bus, and the active Opcode exactly as they change during the clock pulses:
```
[ RUN      ] Sum Array Program Test (Page 377)
[PULSE] PC: 0000 | AddrBus: 0000 | DataBus: 2E | Latch 1 (Opcode): 00
[PULSE] PC: 0001 | AddrBus: 0001 | DataBus: 00 | Latch 1 (Opcode): 2E
[PULSE] PC: 0001 | AddrBus: 0001 | DataBus: 00 | Latch 1 (Opcode): 2E
[PULSE] PC: 0002 | AddrBus: 0002 | DataBus: 00 | Latch 1 (Opcode): 2E
[PULSE] PC: 0002 | AddrBus: 0000 | DataBus: 00 | Latch 1 (Opcode): 2E
[PULSE] PC: 0002 | AddrBus: 0002 | DataBus: 26 | Latch 1 (Opcode): 2E
[PULSE] PC: 0003 | AddrBus: 0003 | DataBus: 00 | Latch 1 (Opcode): 26
[PULSE] PC: 0003 | AddrBus: 0003 | DataBus: 10 | Latch 1 (Opcode): 26
[PULSE] PC: 0004 | AddrBus: 0004 | DataBus: 00 | Latch 1 (Opcode): 26
...
[PULSE] PC: 0010 | AddrBus: 0010 | DataBus: 76 | Latch 1 (Opcode): 32
[PULSE] PC: 0011 | AddrBus: 0011 | DataBus: 00 | Latch 1 (Opcode): 76
[       OK ] Sum Array Program (1 + 2 + 3 + 4 + 5 = 15)
```
## Reference:

1. https://codehiddenlanguage.com/Chapter00/

2. [a current list of errata found in the book after publication](https://www.microsoftpressstore.com/content/images/9780137909100/errata/9780137909100Errata012726.doc)

----------------------------
If you find this project interesting, feel free to open an issue or submit a pull request. I'd love to learn together!