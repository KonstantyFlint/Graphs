from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

from read_write import read_problem
from nodes import Node, Manager


@dataclass(frozen=True)
class PartialPathLeft:
    sender: int
    length: int


@dataclass(frozen=True)
class PartialPathRight:
    sender: int
    length: int


@dataclass(frozen=True)
class FullPath:
    sender: int
    length: int


class StartLeft:
    pass


class StartRight:
    pass


MessageT = PartialPathLeft | PartialPathRight | FullPath | StartLeft | StartRight


@dataclass
class GraphProblem:
    edges: List[Tuple[int, int, int]]
    start: int
    end: int


@dataclass
class NodeState:
    global_best: Optional[int]
    path_left: Optional[int]
    node_left: Optional[int]
    path_right: Optional[int]
    node_right: Optional[int]
    neighbour_distances: Dict[int, int]

    @property
    def full_path(self):
        if None in (self.path_left, self.path_right):
            return None
        return self.path_left + self.path_right


class GraphNode(Node[NodeState, MessageT]):

    def is_better_than_best(self):
        state = self.state
        if state.global_best is None:
            return True
        if state.path_left is not None and state.path_left > state.global_best:
            return False
        if state.path_right is not None and state.path_right > state.global_best:
            return False
        if state.full_path is not None and state.full_path > state.global_best:
            return False
        return True

    def append_distance(self, neighbour: int, length: int):
        return self.state.neighbour_distances[neighbour] + length

    def update_path_left(self, sender: int, new_length: int):
        got_better = False
        state = self.state
        new_length = self.append_distance(sender, new_length)
        if state.path_left is None or state.path_left > new_length:
            state.path_left = new_length
            state.node_left = sender
            got_better = True
        self.state = state
        return got_better

    def update_path_right(self, sender: int, new_length: int):
        got_better = False
        state = self.state
        new_length = self.append_distance(sender, new_length)
        if state.path_right is None or state.path_right > new_length:
            state.path_right = new_length
            state.node_right = sender
            got_better = True
        self.state = state
        return got_better

    def update_global_best(self, new_length):
        state = self.state
        if state.global_best is None or state.global_best > new_length:
            state.global_best = new_length
        self.state = state

    def process(self, state: NodeState, messages: List[MessageT]) -> (NodeState, List[MessageT], List[MessageT]):
        neighbour_messages: List[MessageT] = []
        global_messages: List[MessageT] = []

        for message in messages:
            match message:
                case StartLeft():
                    self.state.path_left = 0
                    neighbour_messages.append(
                        PartialPathLeft(self.index, self.state.path_left)
                    )
                case StartRight():
                    self.state.path_right = 0
                    neighbour_messages.append(
                        PartialPathRight(self.index, self.state.path_right)
                    )
                case PartialPathLeft(sender, length):
                    if self.update_path_left(sender, length):
                        neighbour_messages.append(
                            PartialPathLeft(self.index, self.state.path_left)
                        )
                case PartialPathRight(sender, length):
                    if self.update_path_right(sender, length):
                        neighbour_messages.append(
                            PartialPathRight(self.index, self.state.path_right)
                        )
                case FullPath(_, length):
                    self.update_global_best(length)
                case _:
                    raise RuntimeError("unsupported message")

        if not self.is_better_than_best():
            return state, [], []

        if state.full_path is not None and (state.global_best is None or state.global_best > state.full_path):
            global_messages.append(
                FullPath(self.index, self.state.full_path)
            )
        return state, neighbour_messages, global_messages


class GraphManager(Manager[GraphProblem, NodeState, MessageT]):


    def collect_output(self):
        path = []
        for node in self.nodes:
            if node.state.full_path is not None:
                if not path or path[0].state.full_path > node.state.full_path:
                    path = [node]
        while path[0].state.node_left is not None:
            path = [self.node_map[path[0].state.node_left]] + path
        while path[-1].state.node_right is not None:
            path = path + [self.node_map[path[-1].state.node_right]]
        return [p.index for p in path]

    def make_nodes(self, problem: GraphProblem) -> List[Node[NodeState, MessageT]]:
        def make_node(index: int):
            state = NodeState(
                None,
                None,
                None,
                None,
                None,
                dict()
            )
            initial_messages = []
            if index == problem.start:
                initial_messages.append(StartLeft())
            if index == problem.end:
                initial_messages.append(StartRight())
            return GraphNode(index, state, initial_messages, [])

        indexes = set()
        for (x, y, _) in problem.edges:
            indexes.add(x)
            indexes.add(y)
        nodes = {index: make_node(index) for index in indexes}
        for (x, y, length) in problem.edges:
            left = nodes[x]
            right = nodes[y]
            left.neighbours.append(right)
            left.state.neighbour_distances[right.index] = length
            right.neighbours.append(left)
            right.state.neighbour_distances[left.index] = length

        return list(nodes.values())
