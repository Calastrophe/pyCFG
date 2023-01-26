from itertools import count
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field, astuple, asdict

class JumpType(Enum):
    NO_JUMP = 0
    ABSOLUTE_JUMP = 1
    CONDITIONAL_JUMP = 2

@dataclass(slots=True, frozen=True)
class Instruction:
    name: str
    operand: str = ""
    jump: JumpType = JumpType.NO_JUMP

    ## This could be removed as most types have formatting implemented.
    def __post_init__(self):
        ##https://stackoverflow.com/questions/58992252/how-to-enforce-dataclass-fields-types
        given_args = asdict(self)
        for (name, field_type) in self.__annotations__.items():
            if not isinstance(given_args[name], field_type):
                current_type = type(given_args[name])
                raise TypeError(f"The field `{name}` was assigned by `{current_type}` instead of `{field_type}`")

@dataclass(slots=True, unsafe_hash=True)
class CFGNode:
    start: int
    # https://stackoverflow.com/questions/71195208/creating-a-unique-id-in-a-python-dataclass
    __id: int = field(default_factory=count().__next__, init=False)
    __block: dict[int, Instruction] = field(default_factory=dict, compare=False, init=False)

    def add_instruction(self, addr: int, instruction: Instruction):
        assert(isinstance(instruction, Instruction) == True) ## You have to provide an instruction instance.
        assert((addr > self.start) == True) ## You can't go backwards, unless you are jumping!
        self.__block[addr] = astuple(instruction)

    @property
    def end(self): ## Get the last key of the block and convert to int
        return int(self.addresses[-1])

    @property
    def addresses(self):
        return self.__block.keys()

    @property
    def instructions(self):
        return self.__block.items()

    ## Generate a string representation for the GUI.
    def __str__(self):
        ret_string = ""
        for address in self.__block:
            retrieved_instruction = self.__block[address]
            ret_string += f"{hex(address) : <16} {retrieved_instruction[0] :<12} {retrieved_instruction[1]:<12}\n"
        return ret_string


class DirectedGraph:
    def __init__(self, entry_point:int):
        self._curr_node: CFGNode = CFGNode(entry_point)
        self._nodes = {}
        self.add_node(self._curr_node)

    ## edges: list[CFGNode] = DirectedGraph[node]
    def __getitem__(self, key) -> CFGNode:
        return self._nodes[key]

    ## DirectedGraph[node] = edges
    def __setitem__(self, node: CFGNode, edges: Optional[ list[CFGNode] ]=None):
        edges = [] if edges is None else edges
        self._nodes[node] = edges

    @property
    def nodes(self):
        return self._nodes.keys()

    def add_node(self, node:CFGNode, edges: Optional[ list[CFGNode] ]=None):
        assert(isinstance(node, CFGNode) == True)
        edges = [] if edges is None else edges
        self._nodes.setdefault(node, edges)

    def add_edge(self, node:CFGNode, edge:CFGNode):
        self._nodes[node].append(edge)

    def query_nodes(self, address) -> Optional[CFGNode]:
        for node in self.nodes():
            if node.start == address:
                return node
        return None

    ## Underlying actual .dot file generation
    def generate_dot(self, fn:str):
        pass
        

" The control flow graph requires to know the entry point which it will start the nodes from. "
class pyCFG():
    def __init__(self, entry_point: int):
        self.__CFG = DirectedGraph(entry_point)


    """ The given instruction is executed and mapped into the control flow graph into its rightful node. """
    """ This is the meat and potatoes of the control flow mapping. As instructions actually act on the graph. """
    def execute(self, program_counter:int , instruction: Instruction):
        current_node = self.__current_node__
        ## Branching logic with the use of _curr_node
        if program_counter not in current_node.addresses or instruction.jump: ## Jumps are always re-evaluated
            match instruction.jump:
                case JumpType.NO_JUMP:
                    current_node.add_instruction(program_counter, instruction)
                case JumpType.CONDITIONAL_JUMP:
                    ## Create two blocks for successful and unsuccessful
                    pass
                case JumpType.ABSOLUTE_JUMP:
                    pass
        pass

    """ View the generated .dot with pySide6 """
    def view(self):
        pass

    def __nodes__(self):
        return self.__CFG.nodes

    @property
    def __current_node__(self):
        return self.__CFG._curr_node



# Creating our own .dot file generation

if __name__ == "__main__":
    test_graph = pyCFG(0)
    test_graph.execute(1, Instruction("LOAD", "1"))
    test_graph.execute(2, Instruction("PUSH", "1"))
    test_graph.execute(3, Instruction("STORE", "1"))
    iter = test_graph.__nodes__()
    for node in iter:
        print(node)
    # Handle loop case of a block
