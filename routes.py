import datetime
import os
import random
import string
import time
import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from Bio import Phylo
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from ete3 import PhyloTree
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
)
from flask_bootstrap import Bootstrap
from flask_mongoengine import MongoEngine
from mongoengine import connect
from werkzeug.utils import secure_filename

import ancestral_agreement
import ancestral_agreement_plot
import configs.mongoconfig
from database_models import DataStore
from models import UploadForm

from tree_plot import TreePlot



app = Flask(__name__)
bootstrap = Bootstrap(app)
app_dash = dash.Dash(
    __name__,
    server=app,
    routes_pathname_prefix="/dash/",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

app.config.from_pyfile("configs/mongoconfig.py")

# Connect the database
db = MongoEngine(app)
connect(configs.mongoconfig.MONGODB_DB)

app_dash.scripts.config.serve_locally = True


def parse_contents(contents, filename, date):
    return html.Div(
        [
            html.H5(filename),
            html.H6(datetime.datetime.fromtimestamp(date)),
            # HTML images accept base64 encoded strings in the same format
            # that is supplied by the upload
            html.Img(src=contents),
            html.Hr(),
            html.Div("Raw Content"),
            html.Pre(
                contents[0:200] + "...",
                style={"whiteSpace": "pre-wrap", "wordBreak": "break-all"},
            ),
        ]
    )


_navbar = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(html.Img(src="", height="30px")),
                    dbc.Col(dbc.NavbarBrand("Ancestral Agreement", className="ml-2")),
                ],
                align="center",
                no_gutters=True,
            ),
            href="/",
        ),
        dbc.NavbarToggler(id="navbar-toggler"),
    ],
    color="dark",
    dark=True,
)

dataset_names = ["Data not loaded", "Data not loaded"]


print ("Loading example data")
curr_tree_plot = TreePlot(os.getcwd() + "/files/test_ancestors_6.nwk")
curr_aa_plot = ancestral_agreement_plot.AncestralAgreementPlot(os.getcwd() + '/files/test_ancestors_6.nwk')



app_dash.layout = html.Div(
    [
        _navbar,
        html.Div(
            [
                dcc.Dropdown(
                    id="first_dataset_dropdown",
                    options=[{"label": i, "value": i} for i in dataset_names],
                    value=dataset_names[0],
                ),
                dcc.Dropdown(
                    id="second_dataset_dropdown",
                    options=[{"label": i, "value": i} for i in dataset_names],
                    value=dataset_names[1],
                ),
                dcc.RadioItems(
                    id="metric",
                    options=[
                        {"label": i, "value": i}
                        for i in [
                            " Molecular weight",
                            " Polarity",
                            " Isoelectric point",
                            " Instability index",
                            " Grand average of " "hydropathicity",
                        ]
                    ],
                    value=" Molecular weight",
                    labelStyle={"display": "inline-block", "padding": "5px"},
                ),
                curr_aa_plot.aa_plot,
                dcc.RadioItems(
                    id="order",
                    options=[
                        {"label": i, "value": i} for i in [" Number of child nodes"]
                    ],
                    value=" Number of child nodes",
                    labelStyle={"display": "inline-block", "padding": "5px"},
                ),
            ],
            style={"width": "48%", "display": "inline-block"},
        ),
        html.Div(
            [
                dcc.Graph(
                    id="tree_plot",
                    clear_on_unhover=True,
                    figure=go.FigureWidget(
                        data=[
                            curr_tree_plot.trace_radial_lines,
                            curr_tree_plot.trace_arcs,
                            curr_tree_plot.trace_nodes,
                        ],
                        layout=curr_tree_plot.layout,
                    ),
                )
            ],
            style={"width": "48%", "float": "right", "display": "inline-block"},
        ),
        dcc.Store(id="master_nodes", storage_type="session"),
        dcc.Store(id="aa_hover", storage_type="session"),
        dcc.Store(id="tree_hover", storage_type="session"),
        dcc.Store(id="aa_select", storage_type="session"),
        dcc.Store(id="tree_select", storage_type="session"),
    ],
    style={"padding": 10},
)

app_dash.title = "Ancestral Agreement"


def get_node_name(node):
    if not node:
        return None
    names = []
    for i in range(len(node["points"])):
        if node and "points" in node and "text" in node["points"][i]:
            if "name:" in node["points"][i]["text"]:
                names.append(
                    node["points"][i]["text"].split("<br>")[0].split("name: ")[1]
                )
            else:
                names.append(node["points"][i]["text"])

    if len(names) > 0:
        return names
    else:
        return None


# UPDATE FROM HOVER #


@app_dash.callback(
    Output("aa_hover", "data"),
    [Input(component_id="ancestral_agreement_plot", component_property="hoverData")],
)
def update_aa_storage(data):
    """ Update the nodes hovered over in the Ancestral Agreement plot"""
    return data


@app_dash.callback(
    Output("tree_hover", "data"),
    [Input(component_id="tree_plot", component_property="hoverData")],
)
def update_tree_storage(data):
    """ Update the nodes hovered over in the phylogenetic tree"""
    return get_node_name(data)


# UPDATE FROM SELECTED EVENTS #


@app_dash.callback(
    Output("aa_select", "data"),
    [Input(component_id="ancestral_agreement_plot", component_property="selectedData")],
    [State("aa_select", "data")],
)
def update_aa_storage(aa_data, aa_current):
    """ Update the nodes selected in the Ancestral Agreement plot"""
    node_names = get_node_name(aa_data)
    if node_names == aa_current:
        return []
    return node_names


@app_dash.callback(
    Output("tree_select", "data"),
    [Input(component_id="tree_plot", component_property="selectedData")],
)
def update_tree_storage(data):
    return get_node_name(data)


# UPDATE MASTER LIST #


@app_dash.callback(
    Output("master_nodes", "data"),
    [
        Input("aa_hover", "modified_timestamp"),
        Input("tree_hover", "modified_timestamp"),
        Input("aa_select", "modified_timestamp"),
        Input("tree_select", "modified_timestamp"),
    ],
    [
        State("aa_hover", "data"),
        State("tree_hover", "data"),
        State("aa_select", "data"),
        State("tree_select", "data"),
        State("master_nodes", "data"),
    ],
)
def update_master_div(
        aa_hover_ts,
        tree_hover_ts,
        aa_select_ts,
        tree_select_ts,
        aa_hover_data,
        tree_hover_data,
        aa_select_data,
        tree_select_data,
        master_select_data,
):
    if None in (aa_hover_ts, tree_hover_ts, aa_select_ts, tree_select_ts):
        raise PreventUpdate

    else:
        most_recent = max(aa_hover_ts, tree_hover_ts, aa_select_ts, tree_select_ts)
        latest = None

        if most_recent == aa_hover_ts:

            if aa_hover_data:
                latest = get_node_name(aa_hover_data)
                if aa_select_data:
                    latest += [x for x in aa_select_data if x not in latest]

            if not aa_hover_data:
                latest = aa_select_data

        if most_recent == tree_hover_ts:

            if tree_hover_data:
                latest = tree_hover_data
                if tree_select_data:
                    latest += [x for x in tree_select_data if x not in latest]

            if not tree_hover_data:
                latest = tree_select_data

        if most_recent == aa_select_ts:
            latest = aa_select_data

            return latest

        if most_recent == tree_select_ts:
            latest = tree_select_data

            return latest

        return latest


@app_dash.callback(
    Output(component_id="tree_plot", component_property="figure"),
    [
        Input("master_nodes", "data"),
        Input("first_dataset_dropdown", "value"),
        Input("second_dataset_dropdown", "value"),
        Input("metric", "value"),
    ],
)
def update_tree(master_data, first_dataset, second_dataset, metric):
    print('update tree was called')
    print(master_data)
    print(first_dataset)
    print(second_dataset)
    print(metric)

    print(session.get("data_generated"))

    curr_data = DataStore.objects().get(session_token=session["data_generated"])
    print ('camo damo')

    curr_tree_plot = TreePlot(curr_data.tree_path)

    print('updated tree plot nodes was ')

    if session.get("data_generated") is None or None in (first_dataset, second_dataset):
        raise PreventUpdate
    traces = []

    if not master_data:
        highlight_nodes = ["green" for x in curr_tree_plot.colour]

        print(
            f"I am here and first is {first_dataset} and second is {second_dataset} and metric is {metric}"
        )

    else:

        print('master data was set')
        print(master_data)

        highlight_nodes = curr_tree_plot.colour[:]
        curr = time.time()

        for node_name in master_data:

            if node_name in curr_aa_plot.node_names:

                print (node_name)
                print (curr_tree_plot.tree_nodes)
                print (highlight_nodes)

                # Update the selected node to be a different colour
                highlight_nodes[curr_tree_plot.tree_nodes[node_name]] = "red"

                next = time.time()

            else:
                raise PreventUpdate

        print("Time elapsed was ", next - curr)

    print ('current tree plot is ')
    print (curr_tree_plot)
    print (curr_tree_plot.tree_nodes)

    highlighted_trace_nodes = dict(
        type="scatter",
        x=curr_tree_plot.xnodes,
        y=curr_tree_plot.ynodes,
        mode="markers",
        marker=dict(
            color=highlight_nodes,
            size=curr_tree_plot.size,
            colorscale=curr_tree_plot.pl_colorscale,
        ),
        text=curr_tree_plot.tooltip,
        hoverinfo="text",
        opacity=1,
    )

    traces.append(
        [curr_tree_plot.trace_radial_lines, curr_tree_plot.trace_arcs, highlighted_trace_nodes]
    )

    return go.FigureWidget(
        data=[
            curr_tree_plot.trace_radial_lines,
            curr_tree_plot.trace_arcs,
            highlighted_trace_nodes,
        ],
        layout=curr_tree_plot.layout,
    )


@app_dash.callback(
    Output(component_id="ancestral_agreement_plot", component_property="figure"),
    [
        Input("master_nodes", "data"),
        Input("first_dataset_dropdown", "value"),
        Input("second_dataset_dropdown", "value"),
        Input("metric", "value"),
        Input("order", "value"),
    ],
    [
        State("ancestral_agreement_plot", "relayoutData"),
        State("ancestral_agreement_plot", "figure"),
    ],
)
def update_aa_plot(
        master_nodes,
        first_dataset,
        second_dataset,
        metric,
        order,
        relayout_data,
        aa_layout,
):
    print('here we go')

    if first_dataset == "Data not loaded" or second_dataset == "Data not loaded":
        raise PreventUpdate
    # session["data_generated"] = "560A76BR5L8IE61E5QB7" # cyp2u
    # session["data_generated"] = "CH24A0R3DXLBO1YBO0SD" # small
    # session["data_generated"] = "MGILZ691OLM04XNMAXKA" # latest



    if session.get("data_generated") is None:
        print("no data generated")
        raise PreventUpdate

    curr_data = DataStore.objects().get(session_token=session["data_generated"])
    curr_aa_plot = ancestral_agreement_plot.AncestralAgreementPlot(curr_data.tree_path)

    if not master_nodes:
        highlight_nodes = curr_aa_plot.node_colours[:]

    else:

        highlight_nodes = curr_aa_plot.node_colours[:]

        for node_name in master_nodes:

            if node_name in curr_aa_plot.node_names:

                highlight_nodes[curr_aa_plot.node_dict[node_name]] = "red"

            else:
                raise PreventUpdate

    print('update aa plot called')

    print(session)
    print(session["data_generated"])

    current_data = DataStore.objects().get(session_token=str(session["data_generated"].strip()))

    print('heres da current dict')

    print('and the metric we want is ', metric)

    print('and the order we want is ', order)

    print('and the two datasets we want are ', first_dataset + " " + second_dataset)

    print(current_data)

    print(current_data.data)

    print("order is ", order)

    if order.strip() == "Evolutionary age":
        count = current_data.ages
        suffix = ""
        count_order = current_data.age_order
    else:
        suffix = "_Child_order"
        count = current_data.child_count
        count_order = current_data.child_order

    print('Check values here')

    print(current_data.data.keys())
    print(current_data.data.values())

    print (first_dataset)

    print(current_data.data[first_dataset])

    print (second_dataset)
    print (current_data.data[second_dataset])

    metric1 = np.array(current_data.data[first_dataset][metric.strip() + suffix])
    metric2 = np.array(current_data.data[second_dataset][metric.strip() + suffix])

    print (metric1)

    print (metric2)

    # tree = Phylo.read(os.getcwd() + "/files/test_ancestors_6.nwk", "newick")
    # phylo_tree = PhyloTree(os.getcwd() + "/files/test_ancestors_6.nwk", format=1)
    #
    # # print(phylo_tree)

    # Get the layout for the plot

    print ('highlight nodes')
    print (highlight_nodes)

    current_layout = curr_aa_plot.generate_plot(metric1,
                                           metric2,
                                           first_dataset,
                                           second_dataset,
                                           4,
                                           count,
                                           count_order,
                                           1.96,
                                           metric,
                                           order,
                                           highlight_nodes)

    # Keep the drag mode as whatever the user has selected
    if relayout_data and "dragmode" in relayout_data:
        current_layout[1].dragmode = relayout_data["dragmode"]

    if relayout_data and "xaxis.range[0]" in relayout_data:
        current_layout[1].dragmode = "zoom"

        current_layout[1]["xaxis"]["range"] = [
            relayout_data["xaxis.range[0]"],
            relayout_data["xaxis.range[1]"],
        ]
    if relayout_data and "yaxis.range[0]" in relayout_data:
        current_layout[1]["yaxis"]["range"] = [
            relayout_data["yaxis.range[0]"],
            relayout_data["yaxis.range[1]"],
        ]

    return {"data": current_layout[0], "layout": current_layout[1]}


# Functions for filtering the drop down menus
@app_dash.callback(
    dash.dependencies.Output("first_dataset_dropdown", "options"),
    [dash.dependencies.Input("second_dataset_dropdown", "value")],
)
def set_first_dropdown(exclude):
    if session.get("data_generated") is not None:
        print(session.get("data_generated"))

        current_data = DataStore.objects().get(session_token=session["data_generated"])

        # current_data_frame = pd.DataFrame.from_dict(current_data.data_dict, orient="index")

        # dataset_names = current_data_frame.Name.unique()

        dataset_names = current_data.names

        print(dataset_names)

        return [{"label": i, "value": i} for i in dataset_names if i != exclude]
    else:
        raise PreventUpdate


@app_dash.callback(
    dash.dependencies.Output("second_dataset_dropdown", "options"),
    [dash.dependencies.Input("first_dataset_dropdown", "value")],
)
def set_second_dropdown(exclude):
    if session.get("data_generated") is not None:

        current_data = DataStore.objects().get(session_token=session["data_generated"])

        # current_data_frame = pd.DataFrame.from_dict(current_data.data_dict, orient="index")

        # dataset_names = current_data_frame.Name.unique()

        dataset_names = current_data.names

        return [{"label": i, "value": i} for i in dataset_names if i != exclude]
    else:
        raise PreventUpdate


app.config.update(
    dict(SECRET_KEY="donkeyfacemagicboy", WTF_CSRF_SECRET_KEY="watermelongoldenwitness")
)


@app.route("/", methods=["GET", "POST"])
def index():
    """ Defines the index page of the dash app"""

    form = UploadForm()
    if request.method == "POST":

        if len(request.files) < 4:
            # print ('length too short')
            # print (form)
            return render_template(
                "index.html", form=form, error="Enter at least two datasets"
            )

        names = get_names(request.form)

        # print (names)

        saved_files = save_files(request.files)

        trees, tree_path = get_input(saved_files)


        print("names is {} and trees is {}".format(names, trees))

        data = ancestral_agreement.run_ancestral_agreement(trees, names)

        # Get the order of nodes from first tree according to both evolutionary age and child order
        age_order, ages = ancestral_agreement.get_age_order_and_ages(trees[0])
        child_order, child_count = ancestral_agreement.get_child_order_and_child_count(
            trees[0]
        )

        # Get a dictionary that relates the nodes in the first tree to the second tree
        node_dict = ancestral_agreement.map_nodes_between_trees(trees[0], trees[1])

        # Make a random session token to use as a unique key for storing information in the database
        session_token = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=20)
        )

        print("session token is ", session_token)
        session["data_generated"] = session_token

        # df_dict = data.to_dict('records')
        # string_dict = {}
        # for k, v in df_dict.items():
        #     string_dict[str(k)] = v

        data_store = DataStore(
            session_token=session_token,
            data=data,
            names=names,
            age_order=age_order,
            ages=ages,
            child_order=child_order,
            child_count=child_count,
            node_dict=node_dict,
            tree_path = tree_path
        )
        data_store.save()
        current_data = DataStore.objects().get(session_token=session_token)

        print('hoggles')

        print(current_data)

        # for rec in current_data:
        #     current_data_frame = pd.DataFrame.from_dict(rec.data_dict, orient="index")

        return redirect(url_for("/dash/"))

    elif request.method == "GET":
        return render_template("index.html", form=form)


UPLOAD_FOLDER = os.getcwd() + "/static/uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_names(form):
    """
    Take the upload form, and extract the names given by the user
    :param form:
    :return:
    """
    names = []

    print("getting names")
    print(form)
    print(len(form))
    print(len(form) / 2)
    for idx in range(
            0, int(len(form) - 1)
    ):  # Magic number 1 corrects for csrf_token stored in the form
        print(idx)
        print(form["input[new" + str(idx) + "][name]"])
        names.append(form["input[new" + str(idx) + "][name]"])

    return names


def save_files(uploads):
    """
    Take the FileStorage objects in the input dictionary, save them to the server, and then return the updated mapping
    that maps to their file location
    :param uploads:
    :return:
    """

    path_dict = {}

    for path, file in uploads.items():
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        path_dict[path] = filename

    return path_dict


def get_input(uploads):
    trees = []

    print("uploads here is ", uploads)
    for idx in range(0, int(len(uploads) / 2)):
        print(idx)
        print(uploads["input[new" + str(idx) + "][tree]"])
        print(uploads["input[new" + str(idx) + "][aln]"])

        tree_path = os.path.join(
                app.config["UPLOAD_FOLDER"], uploads["input[new" + str(idx) + "][tree]"])
        aln_path = os.path.join (app.config["UPLOAD_FOLDER"], uploads["input[new" + str(idx) + "][aln]"]
            )

        tree = PhyloTree(
            tree_path,
            alignment=aln_path,
            format=1,
            alg_format="fasta",
        )

        print("made the tree")

        trees.append(tree)

    return trees, tree_path

    #
    # grasp_tree = PhyloTree("./Files/Test/Finals/GRASP_ancestors_6.nwk",
    #                        alignment="./Files/Test/Finals/GRASP_ancestors_6.aln", format=1, alg_format="fasta")


if __name__ == "__main__":
    app.run(debug=True)
