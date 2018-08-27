import networkx as nx

from nose.tools import assert_raises

from textworld.generator.graph_networks import InvalidConstraint
from textworld.generator.graph_networks import relative_2d_constraint_layout


def test_relative_2d_constraint_layout():
    # Generate a graph similar to 
    # C -------- D
    # |          |
    # |  G - F - E
    # |
    # A -------- B
    # |
    # |          J
    # |          |
    # H -------- I
    G = nx.Graph()
    G.add_nodes_from(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'])
    G.add_edges_from([('A', 'B'), ('A', 'C'), ('C', 'D'), ('D', 'E'), ('F', 'E'), ('F', 'G'),
                      ('A', 'H'), ('H', 'I'), ('I', 'J')])
    
    constraints = [('B', 'east', 'A'), ('C', 'north', 'A'),
                   ('D', 'east', 'C'), ('E', 'south', 'D'),
                   ('E', 'east', 'F'), ('G', 'west', 'F'),
                   ('A', 'north', 'H'), ('I', 'east', 'H'),
                   ('J', 'north', 'I')]
    
    expected_pos = {'A': (0, 0), 'B': (3, 0), 'C': (0, 2), 'H': (0, -2), 
                    'D': (3, 2), 'I': (3, -2), 'E': (3, 1), 'J': (3, -1), 
                    'F': (2, 1), 'G': (1, 1)}
    pos = relative_2d_constraint_layout(G, constraints)
    assert expected_pos, pos

    # Uncomment the following to visualize.
    # import matplotlib.pyplot as plt
    # nx.draw(G, pos=pos, labels=dict(zip(G.nodes(),G.nodes())))
    # plt.show()

    # Multiple constraints for a node with the same relation.
    G = nx.Graph()
    G.add_nodes_from(['A', 'B', 'C'])
    G.add_edges_from([('A', 'B'), ('A', 'C')])
    constraints = [('B', 'north', 'A'), ('A', 'south', 'C')]
    assert_raises(InvalidConstraint, relative_2d_constraint_layout, G, constraints)
    