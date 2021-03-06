from Bio import Phylo
from ete3 import PhyloTree
import numpy as np
import plotly.graph_objs as go
import ipywidgets as ipw
import empet_tree
import os


# tree = Phylo.read(os.getcwd() + '/files/bcl.xml', 'phyloxml')
tree = Phylo.read(os.getcwd() + "/files/test_ancestors_6.nwk", "newick")
phylo_tree = PhyloTree(os.getcwd() + "/files/test_ancestors_6.nwk", format=1)

# tree = Phylo.read(os.getcwd() + '/files/GRASP_ancestors_6.nwk', 'newick')
# phylo_tree = PhyloTree(os.getcwd() + '/files/GRASP_ancestors_6.nwk', format=1)

xnodes, ynodes, xlines, ylines, xarc, yarc = empet_tree.get_circular_tree_data(
    tree, order="preorder", start_leaf="last"
)

tooltip = []
colour = []
idx = 0
tree_nodes = {}
for clade in tree.get_nonterminals(order="preorder"):
    tree_nodes[clade.name] = idx

    if clade.name and clade.confidence and clade.branch_length:
        # tooltip.append(f"id: {clade.id}<br>name: {clade.name}<br>branch-length: {clade.branch_length} <br>confidence: {int(clade.confidence.value)}")
        colour.append[clade.confidence.value]
    elif (
        clade.name is None
        and clade.branch_length is not None
        and clade.confidence is not None
    ):
        colour.append(clade.confidence.value)
        # tooltip.append(f"id: {clade.id}<br>branch-length: {clade.branch_length}<br>confidence: {int(clade.confidence.value)}")
    elif clade.name and clade.branch_length and clade.confidence is None:
        tooltip.append(f"name: {clade.name}<br>branch-length: {clade.branch_length}")
        colour.append("green")
    else:
        tooltip.append(f"name: {clade.name}<br>")
        colour.append("green")
    idx += 1

size = [9 if c != -1 else 7 for c in colour]

# pl_colorscale = [[0.0, 'rgb(10,10,150)'],  # color for leafs that haven't associated a confidence
#                  [0.001, 'rgb(10,10,150)'],
#                  [0.001, 'rgb(214, 47, 38)'],  # in fact the colorscale starts here
#                  [0.1, 'rgb(214, 47, 38)'],
#                  [0.2, 'rgb(244, 109, 67)'],
#                  [0.3, 'rgb(252, 172, 96)'],
#                  [0.4, 'rgb(254, 224, 139)'],
#                  [0.5, 'rgb(254, 254, 189)'],
#                  [0.6, 'rgb(217, 239, 139)'],
#                  [0.7, 'rgb(164, 216, 105)'],
#                  [0.8, 'rgb(102, 189, 99)'],
#                  [0.9, 'rgb(63, 170, 89)'],
#                  [1.0, 'rgb(25, 151, 79)']]

pl_colorscale = [
    [0.0, "pink"],  # color for leafs that haven't associated a confidence
    [0.001, "rgb(10,10,150)"],
    [0.001, "rgb(214, 47, 38)"],  # in fact the colorscale starts here
    [0.1, "rgb(214, 47, 38)"],
    [0.2, "rgb(244, 109, 67)"],
    [0.3, "rgb(252, 172, 96)"],
    [0.4, "rgb(254, 224, 139)"],
    [0.5, "rgb(254, 254, 189)"],
    [0.6, "rgb(217, 239, 139)"],
    [0.7, "rgb(164, 216, 105)"],
    [0.8, "rgb(102, 189, 99)"],
    [0.9, "green"],
    [1.0, "orange"],
]

trace_nodes = dict(
    type="scatter",
    x=xnodes,
    y=ynodes,
    mode="markers",
    marker=dict(color=colour, size=size, colorscale=pl_colorscale),
    text=tooltip,
    hoverinfo="text",
    opacity=1,
)

trace_radial_lines = dict(
    type="scatter",
    x=xlines,
    y=ylines,
    mode="lines",
    line=dict(color="rgb(20,20,20)", width=1),
    hoverinfo="none",
)

trace_arcs = dict(
    type="scatter",
    x=xarc,
    y=yarc,
    mode="lines",
    line=dict(color="rgb(20,20,20)", width=1, shape="spline"),
    hoverinfo="none",
)

layout = dict(
    title="Phylogenetic Tree",
    font=dict(family="Balto", size=14),
    height=800,
    width=850,
    autosize=True,
    showlegend=False,
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
    hovermode="closest",
    clickmode="event+select",
    plot_bgcolor="rgb(245,245,245)",
)
