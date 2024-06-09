from collections import defaultdict
from typing import TypeVar, Generic, List, Self, Dict

Problem = TypeVar("Problem")
State = TypeVar("State")
Message = TypeVar("Message")


class Node(Generic[State, Message]):

    def __init__(self, index: int, initial_state: State, initial_messages: List[Message], neighbours: List[Self]):
        self.index = index
        self.neighbours = neighbours
        self.state = initial_state
        self.messages_in = initial_messages
        self._messages_to_neighbours = []
        self._messages_to_all = []

    def __repr__(self):
        return (f"Node(index={self.index}, "
                f"state={self.state}, "
                f"messages_in={self.messages_in}, "
                f"neighbours={[neighbour.index for neighbour in self.neighbours]})")

    def process(self, state: State, messages: List[Message]) -> (State, List[Message], List[Message]):
        # returns the new state, messages to the neighbours and global messages
        raise NotImplementedError()

    def step(self):
        self._messages_to_neighbours = []
        self._messages_to_all = []
        if len(self.messages_in) == 0:
            return False
        (
            self.state,
            self._messages_to_neighbours,
            self._messages_to_all
        ) = self.process(self.state, self.messages_in)

        self.messages_in = []
        return True


class Manager(Generic[Problem, State, Message]):

    def __init__(self, problem: Problem):
        self.nodes = self.make_nodes(problem)
        self.node_map = {node.index: node for node in self.nodes}

    def make_nodes(self, problem: Problem) -> List[Node[State, Message]]:
        raise NotImplementedError()

    def collect_output(self):
        raise NotImplementedError()

    def _collect_messages(self) -> Dict[int, List[Message]]:
        global_messages: List[Message] = []
        messages: Dict[int, List[Message]] = defaultdict(list)
        for node in self.nodes:
            global_messages = global_messages + node._messages_to_all
            for neighbour in node.neighbours:
                messages[neighbour.index] = messages[neighbour.index] + node._messages_to_neighbours
        for index, msg in messages.items():
            messages[index] = msg + global_messages

        return messages

    def step(self):
        messages = self._collect_messages()
        for node in self.nodes:
            node.messages_in = node.messages_in + messages[node.index]
        moved = [node.step() for node in self.nodes]
        return any(moved)

    def solve(self):
        while self.step():
            pass
        return self.collect_output()
