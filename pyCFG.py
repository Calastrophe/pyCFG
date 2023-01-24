from itertools import count
from typing import Dict, Optional
from dataclasses import dataclass, field

@dataclass(slots=True, frozen=True)
class Instruction:
    name: str
    operand: Optional[str]
    absolute_jmp: bool = False
    conditional_jmp: bool = False

@dataclass(slots=True, unsafe_hash=True)
class CFGNode:
    start: int
    # https://stackoverflow.com/questions/71195208/creating-a-unique-id-in-a-python-dataclass
    __id: int = field(default_factory=count().__next__, init=False)
    __block: Dict[int, Instruction] = field(default_factory=dict, compare=False, init=False)

    def add_instruction(self, addr, instruction):
        assert(isinstance(instruction, Instruction) == True)
        self._block.update({addr, instruction})

    @property
    def end(self): ## Get the last key of the block and convert to int
        return int(self._block.keys()[-1])

    ## Generate a string representation for the GUI.
    def __str__(self):
        return ""

class DirectedGraph:
    def __init__(self, initial_nodes: Optional[ Dict[ CFGNode, list[CFGNode] ] ]=None):
        self._nodes = {} if initial_nodes is None else initial_nodes

    ## edges: list[CFGNode] = DirectedGraph[node]
    def __getitem__(self, key) -> CFGNode:
        return self._nodes[key]

    ## DirectedGraph[node] = edges
    def __setitem__(self, node: CFGNode, edges: Optional[ list[CFGNode] ]=None):
        edges = [] if edges is None else edges
        self._nodes[node] = edges

    def nodes(self):
        return self._nodes.keys()

    def add_node(self, node:CFGNode, edges: Optional[ list[CFGNode] ]=None):
        assert(isinstance(node, CFGNode) == True)
        edges = [] if edges is None else edges
        self._nodes.setdefault(node, edges)

    def add_edge(self, node:CFGNode, edge:CFGNode):
        self._nodes[node].append(edge)

        

if __name__ == "__main__":
    test_graph = DirectedGraph()
    test_node = CFGNode(0)
    tester = CFGNode(0)
    test_node_two = CFGNode(3)
    test_graph.add_node(test_node)
    test_graph.add_node(test_node_two)
    test_graph.add_edge(test_node, test_node_two)
    print(test_graph[test_node])
    print(test_graph[test_node_two])
    # Handle loop case of a block
