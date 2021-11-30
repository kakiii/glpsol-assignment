import os
import re
from copy import deepcopy


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
        # for every market
        for index in indices['M']:
            # every neighbor to the market
            for neighbor in graph[index]:
                # if the neighbor is a factory
                if neighbor in indices['F']:
                    # then for every product produced by the factory
                    # actually, there is only one product produced by the factory(jewelry)
                    for prod in properties['F']['product']:
                        # write the total price of the product
                        f.write(
                            f"+ {properties['M']['prices'][prod]} {prod}_{neighbor}_{index}")
                    # besides, the factory can output raw materials directly
                    for prod in properties['F']['demand']:
                        f.write(
                            f"+ {properties['M']['prices'][prod]} {prod}_{neighbor}_{index}")
                # if the neighbor is a quarry
                elif neighbor in indices['Q']:
                    # then for every product produced by the quarry
                    # it can be sold to the market directly
                    for prod in properties['Q']['product']:
                        f.write(
                            f"+ {properties['M']['prices'][prod]} {prod}_{neighbor}_{index}")
        f.write(f"\nSubject To\n")
        # flow constraints
        graph_copy = deepcopy(graph)
        for node, neighbors in graph_copy.items():
            for neighbor in neighbors:
                for item in items:
                    f.write(f"+ {item}_{node}_{neighbor} ")
                    f.write(f"+ {item}_{neighbor}_{node} ")
                    if node in graph_copy[neighbor]:
                        graph_copy[neighbor].remove(node)
                f.write(f"<={LIMIT}\n")
        # factory and quarry efficiency constraints
        for prod,prod_value in properties['F']['product'].items():
            for index in indices['F']:
                for neighbor in graph[index]:
                    f.write(f"+ {prod}_{index}_{neighbor} ")
                f.write(f"<= {prod_value}\n")
        for prod,prod_value in properties['Q']['product'].items():
            for index in indices['Q']:
                for neighbor in graph[index]:
                    f.write(f"+ {prod}_{index}_{neighbor} ")
                f.write(f"<= {prod_value}\n")
        # for factory: jewelry:gold:diamond=60:70:20
        for item,item_value in properties['F']['demand'].items():
            for prod, prod_value in properties['F']['product'].items():
                for index in indices['F']:
                    for neighbor in graph[index]:
                        f.write(f"+ {item_value} {prod}_{index}_{neighbor} ")
                        f.write(f"+ {prod_value} {item}_{index}_{neighbor} ")
                        f.write(f"- {prod_value} {item}_{neighbor}_{index} ")
                    f.write("=0\n")
        # for quarry: gold:diamond=200:75
        q_products = [[key,val] for key,val in properties['Q']['product'].items()]
        print(q_products)
        for prod in q_products:
            for prod_next in q_products[1:]:
                if prod != prod_next:
                    for index in indices['Q']:
                        for neighbor in graph[index]:
                            f.write(f"+ {prod[1]} {prod_next[0]}_{index}_{neighbor} ")
                            # f.write(f"+ {prod_next[1]} {prod[0]}_{index}_{neighbor} ")
                            f.write(f"- {prod_next[1]} {prod[0]}_{neighbor}_{index} ")
                        f.write("=0\n")
        # energy constraints, total energy <= MAX_ENERGY
        


if __name__ == "__main__":
    produce_problem()
    #print(graph)
