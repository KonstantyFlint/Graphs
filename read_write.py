import random


def make_path(start: int, stop_inclusive: int):
    return [(i, i + 1, random.randint(1, 10)) for i in range(start, stop_inclusive)] + [(1, start, 1),
                                                                                        (stop_inclusive, 1000, 1)]


def make_problem():
    out = []
    for i in range(5):
        out += make_path((i + 1) * 100, (i + 1) * 100 + random.randint(5, 10))
    return out


def write_problem():
    problem = make_problem()
    with open("generated_problem.txt", "w") as file:
        for (a, b, l) in problem:
            file.write(f"{a}, {b}, {l}\n")


def read_problem(name):
    out = []
    with open(name) as file:
        for line in file.readlines():
            x, y, z = line.split(", ")
            out.append((int(x), int(y), int(z)))
    return out
