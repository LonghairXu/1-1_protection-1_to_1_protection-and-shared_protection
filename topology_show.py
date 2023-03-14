import json
import networkx as nx
import matplotlib.pyplot as plt

# load the graph from the json file
with open('IT_21.json', 'r') as f:
    graph_data = json.load(f)

# create a directed graph object from the json data
G = nx.DiGraph()

# add nodes to the graph
for node in graph_data['nodes']:
    G.add_node(node['id'], name=node['name'])

# add edges to the graph
for link in graph_data['links']:
    G.add_edge(link['source'], link['target'], weight=link['length'])

# draw the graph
pos = nx.spring_layout(G)
labels = {node['id']: node['name'] for node in graph_data['nodes']}
nx.draw(G, pos, with_labels=True, labels=labels, node_color='lightblue', edge_color='gray', font_size=8, node_size=500)
edge_labels = nx.get_edge_attributes(G,'weight')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
plt.show()
