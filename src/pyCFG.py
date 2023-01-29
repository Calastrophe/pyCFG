from itertools import count
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field, astuple, asdict
from tone_generator import pluck
import pygame
from pygame.mixer import pre_init
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
class CFGNode:
    start: int
    # https://stackoverflow.com/questions/71195208/creating-a-unique-id-in-a-python-dataclass
    __id: int = field(default_factory=count().__next__, init=False)
    __block: dict[int, Instruction | Jump] = field(default_factory=dict, compare=False, init=False)

    def add_instruction(self, addr: int, instr_or_jmp: Instruction | Jump):
        assert(isinstance(instr_or_jmp, Instruction | Jump) == True) ## You have to provide a instruction or jump instance.
        self.__block[addr] = astuple(instr_or_jmp)

    @property
    def end(self): ## Get the last key of the block and convert to int
        return int(self.addresses[-1])

    @property
    def addresses(self):
        return self.__block.keys()

    @property
    def instructions(self):
        return self.__block.items()

    @property
    def id(self):
        return self.__id

    ## The string representation of the node for debugging.
    def __str__(self):
        ret_string = ""
        for address in self.__block:
            retrieved: Instruction | Jump = self.__block[address]
            ret_string += f"{hex(address) : <16} {retrieved[0] :<12} {retrieved[1]:<12}\n"
        return ret_string

    ## The  
    def __repr__(self):
        ret_string = ""
        for address in self.__block:
            retrieved: Instruction | Jump = self.__block[address]
            try:
                ret_string += f"{hex(address)}   {retrieved[0]}   {hex(retrieved[1])}\\n"
            except:
                ret_string += f"{hex(address)}   {retrieved[0]}   {retrieved[1]}\\n"
        return ret_string


class DirectedGraph:
    def __init__(self, entry_point:int):
        self._curr_node: CFGNode = CFGNode(entry_point)
        # self._previous_node: CFGNode = None
        self._nodes: dict[CFGNode, list[CFGNode(CFGNode, int)]] = {}
        self.add_node(self._curr_node)

    ## edges: list[CFGNode] = DirectedGraph[node]
    def __getitem__(self, key) -> CFGNode:
        return self._nodes[key]

    ## DirectedGraph[node] = edges
    def __setitem__(self, node: CFGNode, edges: Optional[ list[tuple[CFGNode, int]] ]=None):
        edges = [] if edges is None else edges
        self._nodes[node] = edges

    """ Iterating in reverse to see if we might have already explored a node is faster, if such node exists. """
    @property
    def nodes(self):
        return self._nodes.keys().__reversed__()

    def add_node(self, node:CFGNode, edges: Optional[ list[tuple[CFGNode, int]] ]=None):
        assert(isinstance(node, CFGNode) == True)
        edges = [] if edges is None else edges
        self._nodes.setdefault(node, edges)

    def add_edge(self, node:CFGNode, edge:CFGNode):
        cfgnode_tuple: tuple(CFGNode, int) = self.query_edges(node, edge)
        if not cfgnode_tuple:
            self._nodes[node].append((edge, 1))
        else:
            cfgnode_tuple = (cfgnode_tuple[0], cfgnode_tuple[1]+1)

    def query_edges(self, node: CFGNode, target_edge: CFGNode) -> Optional[tuple[CFGNode, int]]:
        for edge_tuple in self._nodes[node]:
            if edge_tuple[0] == target_edge:
                return edge_tuple
        return None

    def query_nodes(self, address) -> Optional[CFGNode]:
        for node in self.nodes:
            if node.start == address:
                return node
        return None

    def edges_to_string(self, edges: list[ tuple[CFGNode, int]] ) -> tuple[str, str]:
        for (edge, amount_of_visits) in edges:
            yield (f'node_{edge.start}', f'[label="{amount_of_visits}"]')

            
    def generate_dot(self):
        with open("output.dot", "w") as fd:
            fd.write("digraph pyCFG {\n")
            for node in self._nodes:
                instruction_block: str = repr(node)
                if instruction_block:
                    fd.write(f'\tnode_{node.start} [shape = box][label="{instruction_block}"][penwidth=2][fontname = "Comic Sans MS"]\n')
                else:
                    fd.write(f'\tnode_{node.start} [shape=box][label="Unexplored"][color="webmaroon"][penwidth=2][fontname = "Comic Sans MS"]\n')
            fd.write("\n")
            for node in self._nodes:
                fail = True
                for (edge_string, visits_label) in self.edges_to_string(self._nodes[node]):
                    if fail:
                        if len(self._nodes[node]) == 2:
                            fd.write(f'\tnode_{node.start} -> {{{edge_string}}} {visits_label}[color="red"]\n')
                            fail = False
                        else:
                            fd.write(f'\tnode_{node.start} -> {{{edge_string}}} {visits_label}[color="blue"]\n')
                    else:
                        fd.write(f'\tnode_{node.start} -> {{{edge_string}}} {visits_label}[color="green"]\n')
            fd.write("}\n")


" The control flow graph requires to know the entry point which it will start the nodes from. "
class pyCFG:
    def __init__(self, entry_point: int):
        self.__CFG = DirectedGraph(entry_point)
        # pre_init(44100, -16, 1, 1024) Add back if visual representation is supplied in time
        # pygame.init()

    """ The given instruction is executed and mapped into the control flow graph into its rightful node. """
    """ This is the meat and potatoes of the control flow mapping. As instructions actually act on the graph. """
    def execute(self, program_counter:int, instr_or_jmp: Instruction | Jump):
        # pluck(((program_counter*8) % 5000)+500)
        if isinstance(instr_or_jmp, Instruction):
            if program_counter not in self.__CFG._curr_node.addresses:
                self.__CFG._curr_node.add_instruction(program_counter, instr_or_jmp)
        else:
            self.__match_jump(program_counter, instr_or_jmp)

    def __match_jump(self, program_counter:int, jump: Jump):
        assert(isinstance(jump, Jump) == True)
        match jump.jump_type:
            case JumpType.JMP:
                potential_node = self.__CFG.query_nodes(jump.success_address)
                next_node = potential_node if potential_node else CFGNode(jump.success_address)
                self.__CFG._curr_node.add_instruction(program_counter, jump)
                if not potential_node:
                    self.__CFG.add_node(next_node)
                if next_node not in self.__CFG._nodes[self.__CFG._curr_node]:
                    self.__CFG.add_edge(self.__CFG._curr_node, next_node)
                self.__CFG._curr_node = next_node
            case JumpType.JCC_TAKEN:
                target_address = jump.success_address
                potential_node = self.__CFG.query_nodes(target_address)
                next_node = potential_node if potential_node else CFGNode(target_address)
                potential_fail_node = self.__CFG.query_nodes(jump.failure_address)
                fail_node = potential_fail_node if potential_fail_node else CFGNode(jump.failure_address)
                if not potential_fail_node:
                    self.__CFG.add_node(fail_node)
                    self.__CFG.add_edge(self.__CFG._curr_node, fail_node)
                if not potential_node: ## We have made a new node
                    self.__CFG._curr_node.add_instruction(program_counter, jump)
                    self.__CFG.add_node(next_node)
                    self.__CFG.add_edge(self.__CFG._curr_node, next_node)
                self.__CFG._curr_node = next_node
            case JumpType.JCC_NOT_TAKEN:
                target_address = jump.failure_address
                potential_node = self.__CFG.query_nodes(target_address)
                next_node = potential_node if potential_node else CFGNode(target_address)
                potential_fail_node = self.__CFG.query_nodes(jump.success_address)
                fail_node = potential_fail_node if potential_fail_node else CFGNode(jump.success_address)
                if not potential_node: ## We have made a new node
                    self.__CFG._curr_node.add_instruction(program_counter, jump)
                    self.__CFG.add_node(next_node)
                    self.__CFG.add_edge(self.__CFG._curr_node, next_node)
                if not potential_fail_node:
                    self.__CFG.add_node(fail_node)
                    self.__CFG.add_edge(self.__CFG._curr_node, fail_node)
                self.__CFG._curr_node = next_node


    
    """ View the generated .dot with pySide6 """
    def png(self, output_name):
        self.__CFG.generate_dot()
        subprocess.run(f'dot -Tpng -Gdpi=300 output.dot -o {output_name}.png', shell=True)
        os.remove('output.dot')

    def __nodes__(self):
        return self.__CFG.nodes


# Creating our own .dot file generation

if __name__ == "__main__":
    test_graph = pyCFG(0)
    new_node = CFGNode(3)
    test_graph.execute(1, Instruction("LOAD"))
    test_graph.execute(2, Instruction("PUSH", "1"))
    test_graph.execute(3, Instruction("STORE", "1"))
    test_graph.execute(4, Jump("JMP", 5, JumpType.JMP))
    test_graph.execute(5, Instruction("PUSH", "1"))
    test_graph.execute(6, Jump("JMPZ", 7, JumpType.JCC_TAKEN, 12))
    test_graph.execute(7, Instruction("PUSH", "1"))
    for node in test_graph.__nodes__():
        print(node)
    test_graph.png('weeee')
    # Handle loop case of a block
