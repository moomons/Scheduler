import networkx as nx
import numpy as np
from collections import defaultdict

def test():
    # dict_2d = defaultdict(dict)
    dict_2d = defaultdict(lambda: defaultdict(lambda: 0))
    print dict_2d['00:01']['00:02']
    print dict_2d

    A = np.array([[0, 1, 0, 0],
                  [0, 0, 1, 0],
                  [0, 0, 0, 1],
                  [0, 0, 0, 0]])

    G = nx.from_numpy_matrix(A, create_using=nx.DiGraph())
    print(nx.dijkstra_path(G, 0, 3))
    # Ref: https://networkx.readthedocs.org/en/stable/reference/generated/networkx.algorithms.shortest_paths.weighted.dijkstra_path.html


# BUGGY!
def dijkstra_dict2d(graph, start, end):
    D = {}  # Final distances dict
    P = {}  # Predecessor dict

    for node in graph.keys():
        D[node] = -1.0  # Vertices are unreachable
        P[node] = ""
    D[start] = 0.0  # The start vertex needs no move
    unseen_nodes = graph.keys()  # All nodes are unseen

    while len(unseen_nodes) > 0:
        shortest = None
        node = ''
        for temp_node in unseen_nodes:
            if shortest is None:
                shortest = D[temp_node]
                node = temp_node
            elif D[temp_node] < shortest:
                shortest = D[temp_node]
                node = temp_node
        unseen_nodes.remove(node)
        for child_node, child_value in graph[node].items():
            if D[child_node] < D[node] + child_value:
                D[child_node] = D[node] + child_value
                P[child_node] = node
    path = []
    node = end
    while not (node == start):
        if path.count(node) == 0:
            path.insert(0, node)  # Insert the predecessor of the current node
            node = P[node]  # The current node becomes its predecessor
        else:
            break
    path.insert(0, start)  # Finally, insert the start vertex
    return path
    # Ref: http://stackoverflow.com/questions/14864020/will-my-dicts-of-dicts-work-for-this-dijkstras-algorithm
