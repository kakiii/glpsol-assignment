import os
import re


def run_glpsol():
    os.system("glpsol --lp 1.lp -o output.txt")
    with open("output.txt", "r") as outputfile:
        opt_value = None
        for line in outputfile.readlines():
            if "Objective" in line:
                opt_value = float((re.findall("[0-9]+[,.]*[0-9]*", line))[0])
            if "PRIMAL SOLUTION IS INFEASIBLE" in line:
                opt_value = None
    if opt_value is None:
        raise Exception("LP is unsolvable.")
    return opt_value


graph = {
    1: [2, 3, 5],
    2: [1, 7, 8],
    3: [1, 4, 9],
    4: [3, 5, 9],
    5: [1, 4, 6],
    6: [5, 7, 10],
    7: [2, 6, 8],
    8: [2, 7, 12],
    9: [3, 4, 11],
    10: [6, 11, 12],
    11: [9, 10, 12],
    12: [8, 10, 11]
}

properties = {
    "Q": {
        "cost": 100,
        "product": {
            "G": 200,
            "D": 75
        },
    },
    "M": {
        "prices": {
            "G": 150,
            "D": 200,
            "J": 1000
        }
    },
    "F": {
        "cost": 300,
        "product": {
            "J": 60,
        },
        "demand": {
            "G": 70,
            "D": 20,
        }
    }
}

indices = {
    "F": [4, 7, 10],
    "Q": [1, 2, 3, 8, 9, 11, 12],
    "M": [5, 6],
}

items = ["G", "D", "J"]

LIMIT = 165
MAX_ENERGY = 850


def produce_problem():
    with open("1.lp", "w") as f:
        f.write("Maximize\n")
        for index in indices['M']:
            for neighbor in graph[index]:
                if neighbor in indices['F']:
                    for prod in properties['F']['product']:
                        f.write(
                            f"+ {properties['M']['prices'][prod]} {prod}_{neighbor}_{index}")
                    for prod in properties['F']['demand']:
                        f.write(
                            f"+ {properties['M']['prices'][prod]} {prod}_{neighbor}_{index}")
                elif neighbor in indices['Q']:
                    for prod in properties['Q']['product']:
                        f.write(
                            f"+ {properties['M']['prices'][prod]} {prod}_{neighbor}_{index}")
        f.write(f"\nSubject To\n")
        # flow constraints

        for node, neighbors in graph.items():
            for neighbor in neighbors:
                for item in items:
                    f.write(f"+ {item}_{node}_{neighbor} ")
                    f.write(f"+ {item}_{neighbor}_{node} ")
                f.write(f"<={LIMIT}\n")

        # energy constraints
        for node, neighbors in graph.items():


if __name__ == "__main__":
    produce_problem()
