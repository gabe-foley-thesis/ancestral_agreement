"""AncestralAgreementPlots show the level of agreement between two ancestral data sets"""

import numpy as np
import plotly.graph_objs as go
from dash import dcc
from ete3 import PhyloTree

class AncestralAgreementPlot:
    node_dict = {}
    node_colours = []
    random_x = []
    random_y = []
    data = [
        go.Scattergl(
            x=random_x,
            y=random_y,
            text='',
            mode="markers",
            marker=dict(
                size=12,
                color=node_colours,
                symbol="circle",
                line=dict(
                    width=2,
                ),
            ),
        )
    ]

    layout = go.Layout(
        title="Ancestral Agreement Plot",  # Graph title
        xaxis=dict(title="Evolutionary age"),  # x-axis label
        yaxis=dict(title="Molecular weight"),  # y-axis label
        hovermode="closest",  # handles multiple points landing on the same vertical
        clickmode="event+select",
        dragmode="select",
    )

    aa_plot = dcc.Graph(
        id="ancestral_agreement_plot",
        clear_on_unhover=True,
        config={
            "doubleClick": "reset+autosize",
            # 'modeBarButtonsToRemove': ['select2d', 'lasso2d']
        },
        figure=go.FigureWidget(data=data, layout=layout),
    )
    np.random.seed(42)
    random_x = []
    random_y = []

    def __init__(self, tree_path):
        """
        Create an AncestralAgreementPlot
        :param str tree_path: The location of the treefile to build the AncestralAgreementPlot from
        """
        self.node_colours = []
        self.node_dict = {}
        self.node_names = []

        if tree_path:

            # Load the tree
            phylo_tree = PhyloTree(tree_path, format=1)
            count = 0

            # Name the ancestor nodes and create an entry for the node colour for each ancestor
            for node in phylo_tree.traverse():
                if not node.is_leaf():
                    self.node_dict[node.name] = count
                    self.node_names.append(node.name)
                    self.node_colours.append("green")
                    count += 1

        print ('init called')
        print (self.node_names)

    active_node = None

    def generate_plot(self,
                      metric1,
                      metric2,
                      name1,
                      name2,
                      data_len,
                      count,
                      count_order,
                      metric_lims,
                      metric_name,
                      order_name,
                      highlight_nodes
                      ):

        if len(metric1) != len(metric2):
            raise ValueError("m1 does not have the same length as m2.")
        if metric_lims < 0:
            raise ValueError("sd_limit ({}) is less than 0.".format(metric_lims))

        means = np.mean([metric1, metric2], axis=0)
        diffs = metric1 - metric2
        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs, axis=0)

        if metric_lims > 0:
            half_ylim = (1.5 * metric_lims) * std_diff

            limit_of_agreement = metric_lims * std_diff
            lower = mean_diff - limit_of_agreement
            upper = mean_diff + limit_of_agreement

        nodes = go.Scattergl(
            x=count,
            y=diffs,
            text=self.node_names,
            mode="markers",
            name="Node agreement",
            marker=dict(  # change the marker style
                size=12,
                color=highlight_nodes,
                symbol="circle",
                line=dict(
                    width=2,
                ),
            ),
        )
        lower = go.Scattergl(
            x=[0, 170],
            y=[lower] * data_len,
            mode="lines+text",
            name="-SD 1.96",
            text=["", "", "Text F"],
            textposition="bottom center",
            line=dict(shape="vhv"),
        )
        upper = go.Scattergl(
            x=[0, 170],
            y=[upper] * data_len,
            mode="lines+text",
            name="+SD 1.96",
            text=["", "", "Text F"],
            textposition="bottom center",
            line=dict(shape="vhv"),
        )

        data = [nodes, upper, lower]

        layout = go.Layout(
            title=name1 + " " + name2,  # Graph title
            xaxis=dict(title=order_name),  # x-axis label
            yaxis=dict(title=metric_name),  # y-axis label
            hovermode="closest",  # handles multiple points landing on the same vertical
            clickmode="event+select",
            dragmode="select",
        )
        return (data, layout)

    def get_node_names(self):
        print ('lets return them ')
        print (self.node_names)
        return self.node_names

    def update_plot(self, highlight_nodes):
        """
        Update the plot by highlighting certain nodes
        :param list highlight_nodes: The list of nodes to highlight
        """
        traces = []
        traces.append(
            go.Scattergl(
                x=self.random_x,
                y=self.random_y,
                text=self.node_names,
                mode="markers",
                marker=dict(  # change the marker style
                    size=12,
                    color=highlight_nodes,
                    symbol="circle",
                    line=dict(
                        width=2,
                    ),
                ),
            )
        )

        return traces
