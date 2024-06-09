from graph import GraphProblem, GraphManager
from read_write import read_problem

edges = read_problem("generated_problem.txt")
problem = GraphProblem(edges, 1, 1000)
manager = GraphManager(problem)
print(manager.solve())
