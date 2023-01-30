# What is pythonCFG?
It is an easy-to-use library to implement control flow graph generation in your emulator.

All that is required is to wrap your instruction set around the two classes Instruction or Jump.



# Downloading the library
If you wish to download the library and use it, you must install Graphviz and add it to your PATH at install.

https://graphviz.org/download/

After installing Graphviz, you can use pip to install the library for use in your own emulator.

``pip install pythonCFG``

# Using the library
Assuming you have an emulator which contains some pseudocode such as...
``emulator.execute(instruction)``

You will take this instruction and wrap it into a Instruction or Jump class.
An instruction can optionally take an operand, but requires a name.

A jump requires a name and "success_address" (operand) for all types of JumpType. A failure address is needed in the case of a JCC.

Some psuedocode to simulate this is...

```py
match instruction:
      case INC:
            Instruction("INC")
            
      case JUMP:
            Jump("JUMP", 0x30, JumpType.JMP) ## NOTE: A failure address is not needed as this is an absolute jump!
            ## NOTE: You will need to dynamically determine what your success_address and failure_address.
            
      case CONDITIONAL_JUMP:
            Jump("COND", 0x30, JumpType.JCC_TAKEN, 0x20) ## NOTE: A failure address is needed as this is conditional.
```

After matching your instruction set into an Instruction or Jump, you will need to execute this instruction in the graph.
Some pseudocode after you've matched your instruction set with its respective operands.
```py
    class Emulator:
        def __init__(self):
              ## OTHER ARGUMENTS ARE IMPLEMENTATION SPECIFIC
              self.graph = pyCFG(0) ## Import this class and set your entry point address ( in this case 0 ).
              
        def execute(self, instruction):
              self.graph.execute( matched_instruction(instruction) ) 
              ## We are assuming you have correctly determined operands in matched_instruction.
              
        def output(self):
              self.graph.png("some_output.png") # Returns an image of the control flow graph.
```
