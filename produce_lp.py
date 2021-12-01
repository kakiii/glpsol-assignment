import os
import re
from copy import deepcopy
import time
import ast

def run_glpsol():
    # for step 1 use a.lp
    os.system("glpsol --lp template.lp -o output_1.txt")
    with open("output_1.txt", "r") as outputfile:
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
        "energy": 100,
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
        "energy": 300,
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

FLOW_CONSTRAINT = 165
MAX_ENERGY = 850
NODE_NUM = 12
BUILDING_TYPES = list(indices.keys())


def write_problem(indices=indices):
    MARKET_FLAG = False
    with open("template.lp", "w") as f:
        f.write("Maximize\n")
        # for every market
        if indices['M'] and len(indices['M'])!=NODE_NUM:
            for index in indices['M']:
                # every neighbor to the market
                for neighbor in graph[index]:
                    for item in items:
                        if neighbor not in indices['M']:
                            f.write(
                                f"- {properties['M']['prices'][item]} {item}_{index}_{neighbor}")
                            f.write(
                                f"+ {properties['M']['prices'][item]} {item}_{neighbor}_{index}")
        else:
            MARKET_FLAG = True
            f.write("a_0\n")
        f.write(f"\nSubject To\n\n")
        if MARKET_FLAG:
            f.write("a_0=0\n")
        # flow constraints
        f.write("\\flow constraints\n")
        graph_copy = deepcopy(graph)
        for node, neighbors in graph_copy.items():
            for neighbor in neighbors:
                for item in items:
                    f.write(f"+ {item}_{node}_{neighbor} ")
                    f.write(f"+ {item}_{neighbor}_{node} ")
                    if node in graph_copy[neighbor]:
                        graph_copy[neighbor].remove(node)
                f.write(f"<={FLOW_CONSTRAINT}\n")
        f.write("\n")

        # factory and quarry efficiency constraints
        f.write("\\factories and quarries efficiency constraints\n")
        for prod, prod_value in properties['F']['product'].items():
            for index in indices['F']:
                for neighbor in graph[index]:
                    f.write(f"+ {prod}_{index}_{neighbor} ")
                    f.write(f"- {prod}_{neighbor}_{index} ")
                f.write(f"<= {prod_value}\n")
        for prod, prod_value in properties['Q']['product'].items():
            for index in indices['Q']:
                for neighbor in graph[index]:
                    f.write(f"+ {prod}_{index}_{neighbor} ")
                    f.write(f"- {prod}_{neighbor}_{index} ")
                f.write(f"<= {prod_value}\n")
        f.write("\n")

        # for factory: jewelry:gold:diamond=60:70:20
        f.write("\\for factory: jewelry:gold:diamond=60:70:20\n")
        for item, item_value in properties['F']['demand'].items():
            for prod, prod_value in properties['F']['product'].items():
                for index in indices['F']:
                    for neighbor in graph[index]:
                        f.write(f"+ {item_value} {prod}_{index}_{neighbor} ")
                        f.write(f"- {item_value} {prod}_{neighbor}_{index} ")
                        f.write(f"+ {prod_value} {item}_{index}_{neighbor} ")
                        f.write(f"- {prod_value} {item}_{neighbor}_{index} ")
                    f.write("=0\n")
        f.write("\n")

        # for quarry: gold:diamond=200:75
        f.write("\\for quarry: gold:diamond=200:75\n")
        q_products = [[key, val]
                      for key, val in properties['Q']['product'].items()]
        #print(q_products)
        for prod in q_products:
            for prod_next in q_products[1:]:
                if prod != prod_next:
                    for index in indices['Q']:
                        for neighbor in graph[index]:
                            f.write(
                                f"+ {prod[1]} {prod_next[0]}_{index}_{neighbor} ")
                            # f.write(f"+ {prod_next[1]} {prod[0]}_{index}_{neighbor} ")
                            f.write(
                                f"- {prod[1]} {prod_next[0]}_{neighbor}_{index} ")
                            f.write(
                                f"- {prod_next[1]} {prod[0]}_{index}_{neighbor} ")
                            f.write(
                                f"+ {prod_next[1]} {prod[0]}_{neighbor}_{index} ")
                        f.write("=0\n")
        f.write("\n")

        # factory consumes gold and diamond
        f.write("\\factory consumes gold and diamond\n")
        for demand, demand_value in properties['F']['demand'].items():
            for index in indices['F']:
                for neighbor in graph[index]:
                    f.write(f"- {demand}_{index}_{neighbor} ")
                    f.write(f"+ {demand}_{neighbor}_{index} ")
                f.write(">=0\n")
        f.write("\n")

        # factory produces jewelry
        f.write("\\factory produces jewelry\n")
        for prod, prod_value in properties['F']['product'].items():
            for index in indices['F']:
                for neighbor in graph[index]:
                    f.write(f"+ {prod}_{index}_{neighbor} ")
                    f.write(f"- {prod}_{neighbor}_{index} ")
                f.write(">=0\n")

        # quarry produces gold and diamond
        f.write("\\quarry produces gold and diamond\n")
        for prod, prod_value in properties['Q']['product'].items():
            for index in indices['Q']:
                for neighbor in graph[index]:
                    f.write(f"+ {prod}_{index}_{neighbor} ")
                    f.write(f"- {prod}_{neighbor}_{index} ")
                f.write(">=0\n")
        f.write("\n")

        # quarry can only transport jewelry
        f.write("\\quarry can only transport jewelry\n")
        for index in indices['Q']:
            for neighbor in graph[index]:
                f.write(f"+ J_{index}_{neighbor} ")
                f.write(f"- J_{neighbor}_{index} ")
            f.write("= 0\n")
        f.write("\n")

        # convert jewelry produced to energy
        f.write("\\convert jewelry produced to energy\n")
        prod, prod_value = list(properties['F']['product'].items())[0]
        for index in indices['F']:
            for neighbor in graph[index]:
                f.write(
                    f"+ {properties['F']['energy']} {prod}_{index}_{neighbor} ")
                f.write(
                    f"- {properties['F']['energy']} {prod}_{neighbor}_{index} ")
            f.write(f"- {prod_value} E_{index} = 0\n")
        f.write("\n")

        # convert gold produced to energy
        f.write("\\convert gold produced to energy\n")
        prod, prod_value = list(properties['Q']['product'].items())[0]
        for index in indices['Q']:
            for neighbor in graph[index]:
                f.write(
                    f"+ {properties['Q']['energy']} {prod}_{index}_{neighbor} ")
                f.write(
                    f"- {properties['Q']['energy']} {prod}_{neighbor}_{index} ")
            f.write(f"- {prod_value} E_{index} = 0\n")
        f.write("\n")

        # energy constraints, total energy <= MAX_ENERGY
        f.write("\\energy constraints, total energy <= MAX_ENERGY\n")
        for num in range(1, NODE_NUM+1):
            f.write(f"+ E_{num} ")
        f.write(f"<={MAX_ENERGY}\n")
        f.write("\n")

        # market input >= output
        f.write("\\market input >= output\n")
        for index in indices['M']:
            for neighbor in graph[index]:
                for item in items:
                    f.write(f"- {item}_{index}_{neighbor} ")
                    f.write(f"+ {item}_{neighbor}_{index} ")
            f.write(">=0\n")

        # Bounds
        f.write("Bounds\n")
        for index in graph:
            for neighbor in graph[index]:
                for item in items:
                    f.write(f"{item}_{index}_{neighbor}>=0\n")
        f.write("\n")

        f.write("END\n")


def permute_placements():
    # with open("placements.txt", "w") as f:
    #     for permutation in mapdistr(NODE_NUM, 3):
    #         f.write(f"{permutation}\n")
    # flag = True
    all_values = []
    indices = {key: [] for key in properties.keys()}
    count = 0
    for permutation in mapdistr(NODE_NUM, 3):
        for index,building in enumerate(indices.keys()):
            indices[building]=permutation[index]
        # print(indices)
        # if count <= 5:
        write_problem(indices)
        with open("results.txt", "a") as f:
            val = run_glpsol()
            all_values.append(val)
            f.write(f"{count}: {val} {indices}\n")
            count+=1
    
def mapdistr(K, N):
    for x in range(N**K):
        t = x
        l = [[] for _ in range(N)]
        for i in range(K):
            id = t % N
            t = t // N   #integer division
            l[id].append(i+1)
        yield l

def find_max_value():
    all_values = []
    all_placements = []
    with open('results.txt',"r") as f:
        for line in f.readlines():
            line = line.strip()
            val  = re.search(r'(\d): (\d+\.\d+) (.+)',line).group(1,2,3)
            all_values.append(float(val[1]))
            # print(val[2])
            all_placements.append(ast.literal_eval(val[2]))
        # print(val)
    # print(all_placements)
    # print(all_values.index(max(all_values)),max(all_values))
    max_value, max_value_index = max(all_values), all_values.index(max(all_values))
    max_placement = all_placements[max_value_index]
    print(max_value,max_value_index, max_placement)
    write_problem(max_placement)
    run_glpsol()

    

    

if __name__ == "__main__":
    start_time = time.time()
    # write_problem()
    # print(run_glpsol())
    # permute_placements()
    find_max_value()
    print(f"--- {round(time.time() - start_time,2)} seconds ---")
    
