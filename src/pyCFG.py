from itertools import count
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field, astuple, asdict
import subprocess
import os


class JumpType(Enum):
    JMP = 1
    JCC_TAKEN = 2
    JCC_NOT_TAKEN = 3

@dataclass(slots=True, frozen=True)
class Instruction:
    name: str
    operand: str = ""

    ## This could be removed as most types have formatting implemented.
    def __post_init__(self):
        ##https://stackoverflow.com/questions/58992252/how-to-enforce-dataclass-fields-types
        given_args = asdict(self)
        for (name, field_type) in self.__annotations__.items():
            if not isinstance(given_args[name], field_type):
                current_type = type(given_args[name])
                raise TypeError(f"The field `{name}` was assigned by `{current_type}` instead of `{field_type}`")

@dataclass(slots=True, frozen=True)
class Jump:
    name: str
    success_address: int
    jump_type: JumpType
    failure_address: Optional[int] = field(default=None) ## Specify if you are doing a conditional jump

    def __post_init__(self):
        ##https://stackoverflow.com/questions/58992252/how-to-enforce-dataclass-fields-types
        given_args = asdict(self)
        if given_args["jump_type"] in [JumpType.JCC_NOT_TAKEN, JumpType.JCC_TAKEN] and given_args["failure_address"] is None:
            raise TypeError(f"The JumpType {given_args['jump_type']} requires a failure address, in addition to the success address.")
        for (name, field_type) in self.__annotations__.items():
            if not isinstance(given_args[name], field_type):
                current_type = type(given_args[name])
                raise TypeError(f"The field `{name}` was assigned by `{current_type}` instead of `{field_type}`")


@dataclass(slots=True, unsafe_hash=True)
class BasicBlock:
    start: int
    # https://stackoverflow.com/questions/71195208/creating-a-unique-id-in-a-python-dataclass
    __id: int = field(default_factory=count().__next__, init=False)
    __block: dict[int, Instruction | Jump] = field(default_factory=dict, compare=False, init=False)
    __edges: dict[int, int] = field(default_factory=dict, compare=False, init=False)

    def add_instruction(self, addr: int, instr_or_jmp: Instruction | Jump):
        assert(isinstance(instr_or_jmp, Instruction | Jump))
        self.__block[addr] = astuple(instr_or_jmp)

    def add_edge(self, edge: int, traversed:bool):
        self.__edges[edge] = self.__edges.get(edge, 0) + traversed

    def edge_strings(self):
        for i, pair in enumerate(self.edges):
            yield (i, pair[0], pair[1])

    @property
    def end(self): 
        return int(self.addresses[-1])

    @property
    def addresses(self):
        return self.__block.keys()
    
    @property
    def edges(self):
        return self.__edges.items()

    @property
    def id(self):
        return self.__id

    def __str__(self):
        ret_string = ""
        for address in self.__block:
            retrieved: Instruction | Jump = self.__block[address]
            ret_string += f"{hex(address) : <16} {retrieved[0] :<12} {retrieved[1]:<12}\n"
        return ret_string

    def __repr__(self):
        ret_string = ""
        for address in self.__block:
            retrieved: Instruction | Jump = self.__block[address]
            try:
                ret_string += f"{hex(address)}   {retrieved[0]}   {hex(retrieved[1])}\\n"
            except:
                ret_string += f"{hex(address)}   {retrieved[0]}   {retrieved[1]}\\n"
        return ret_string


class ControlFlowGraph:
    def __init__(self, entry_point:int):
        self._nodes: list[BasicBlock] = [BasicBlock(entry_point)]
        self._curr_node: BasicBlock = self._nodes[0]
    
    """ Execute a given instruction on the ControlFlowGraph """
    def execute(self, program_counter:int, instruction: Instruction | Jump):
        assert(program_counter >= self._curr_node.start)
        if program_counter not in self._curr_node.addresses:
            self._curr_node.add_instruction(program_counter, instruction)
        if isinstance(instruction, Jump):
            match instruction.jump_type:
                case JumpType.JMP:
                    next_index, next_block = self.__query_block_or_create(instruction.success_address)
                    self._curr_node.add_edge(next_index, True)
                    self._curr_node = next_block
                case JumpType.JCC_TAKEN:
                    fail_index, fail_block = self.__query_block_or_create(instruction.failure_address)
                    self._curr_node.add_edge(fail_index, False)
                    success_index, success_block = self.__query_block_or_create(instruction.success_address)
                    self._curr_node.add_edge(success_index, True)
                    self._curr_node = success_block
                case JumpType.JCC_NOT_TAKEN:
                    fail_index, fail_block = self.__query_block_or_create(instruction.failure_address)
                    self._curr_node.add_edge(fail_index, True)
                    success_index, success_block = self.__query_block_or_create(instruction.success_address)
                    self._curr_node.add_edge(success_index, False)
                    self._curr_node = fail_block

    """ Wrapper for adding nodes to the graph """
    def __add_node(self, node:BasicBlock):
        assert(isinstance(node, BasicBlock))
        self._nodes.append(node)

    """ Queries to see if a block exists, if so, return the block and its index - or create one. """
    def __query_block_or_create(self, start_addr:int) -> tuple[int, BasicBlock]:
        for i, node in enumerate(self.nodes):
            if node.start == start_addr:
                return (i, node)
        index = len(self._nodes)
        self.__add_node(BasicBlock(start_addr))
        return (index, self._nodes[index])

    """ Produces a picture of the current ControlFlowGraph """
    def png(self, output_name: str):
        self.dot()
        subprocess.run(f'dot -Tpng -Gdpi=300 output.dot -o {output_name}.png', shell=True)
        os.remove('output.dot')

    """ Produces a PDF version of the current ControlFlowGraph """
    def pdf(self, output_name: str):
        self.dot()
        subprocess.run(f'dot -Tpdf -Gdpi=300 output.dot -o {output_name}.pdf', shell=True)
        os.remove('output.dot')

    """ Produces a dot file with the name output.dot """
    def dot(self):
        with open("output.dot", "w") as fd:
            fd.write("digraph pyCFG {\n")
            for node in self._nodes:
                instruction_block: str = repr(node)
                box_label = instruction_block if instruction_block else "Unexplored"
                box_color = '[color="webmaroon"]' if box_label == "Unexplored" else '[color="gray0"]'
                fd.write(f'\tnode_{node.start} [shape =box][label="{box_label}"]{box_color}[penwidth=2][fontname = "Comic Sans MS"]\n')
            fd.write("\n")
            for node in self._nodes:
                number_of_edges = len(node.edges)
                for (edge_num, edge_index, edge_traversals) in node.edge_strings():
                    edge_color = "blue" if number_of_edges == 1 else "red" if number_of_edges == 2 and edge_num == 0 else "green"
                    fd.write(f'\tnode_{node.start} -> node_{self._nodes[edge_index].start} [label="{edge_traversals}"][color="{edge_color}"]\n')
            fd.write("}\n")

    @property
    def nodes(self):
        return reversed(self._nodes)