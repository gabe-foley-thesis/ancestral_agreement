import datetime
import os
import random
import string
import time
import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
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

# Set the upload folders
UPLOAD_FOLDER = "aa/static/uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

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

dataset_names = ["Refresh page to view example data", "Refresh page to view example data"]


# print ("Loading example data")

print (os.getcwd())
print (os.listdir())


# Load sample data 
curr_tree_plot = TreePlot("./aa/files/test_ancestors_6.nwk")
curr_aa_plot = ancestral_agreement_plot.AncestralAgreementPlot("./aa/files/test_ancestors_6.nwk")


# curr_tree_plot = TreePlot(tree_path=None)
# curr_aa_plot = ancestral_agreement_plot.AncestralAgreementPlot(tree_path=None)


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

    print ('Update aa storage')
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

    # If user navigates directly to /dash/ then no data is generated and we should serve the example data
    if session.get("data_generated") is None:
        example_token = 'VDGX14L1N2E9VJHAJ7CI'
        session["data_generated"] = example_token

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



    if session.get("data_generated") is None or None in (first_dataset, second_dataset):
        raise PreventUpdate

    print ('data generated is ')
    print (session.get("data_generated"))

    if session.get("data_generated") is not None:
        curr_data = DataStore.objects().get(session_token=session["data_generated"])

    curr_tree_plot = TreePlot(curr_data.tree_path)

    print ('and here')

    print (master_data)


    traces = []

    if not master_data:
        highlight_nodes = ["green" for x in curr_tree_plot.colour]


    else:


        highlight_nodes = curr_tree_plot.colour[:]

        print ('highlight nodes is')
        print (highlight_nodes)

        print ('node names in aa plot are')

        print ('curr aa plot is ')
        print (curr_aa_plot)

        print (curr_aa_plot.get_node_names())

        for node_name in master_data:

            if node_name in curr_aa_plot.node_names:

                print ('it was tehre')

                # Update the selected node to be a different colour
                highlight_nodes[curr_tree_plot.tree_nodes[node_name]] = "red"


            else:
                print ('no good')
                raise PreventUpdate


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

    if first_dataset == "Refresh page to view example data" or second_dataset == "Refresh page to view example data":
        raise PreventUpdate



    if session.get("data_generated") is None:
        raise PreventUpdate

    if session.get("data_generated") is not None:
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

    current_data = DataStore.objects().get(session_token=str(session["data_generated"].strip()))

    if order.strip() == "Evolutionary age":
        count = current_data.ages
        suffix = ""
        count_order = current_data.age_order
    else:
        suffix = "_Child_order"
        count = current_data.child_count
        count_order = current_data.child_order


    metric1 = np.array(current_data.data[first_dataset][metric.strip() + suffix])
    metric2 = np.array(current_data.data[second_dataset][metric.strip() + suffix])

    print ("Calling generate plot")


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

        current_data = DataStore.objects().get(session_token=session["data_generated"])
        dataset_names = current_data.names
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

    # When user navigates to the index page we clear the generated data token
    if session.get("data_generated") is not None:
        session.pop('data_generated')
        print ('popped it')


    form = UploadForm()
    if request.method == "POST":

        if len(request.files) < 4:
            return render_template(
                "index.html", form=form, error="Enter at least two datasets"
            )

        names = get_names(request.form)
        saved_files = save_files(request.files)
        trees, tree_path = get_input(saved_files)
        data = ancestral_agreement.run_ancestral_agreement(trees, names)

        # Get the order of nodes from first tree according to both evolutionary age and child order
        age_order, ages = ancestral_agreement.get_age_order_and_ages(trees[0])
        child_order, child_count = ancestral_agreement.get_child_order_and_child_count(
            trees[0]
        )

        # Get a dictionary that relates the nodes in the first tree to the second tree
        node_dict = ancestral_agreement.map_nodes_between_trees(trees[0], trees[1])

        print ('tree path is')
        print (tree_path)

        # Make a random session token to use as a unique key for storing information in the database
        session_token = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=20)
        )

        session["data_generated"] = session_token

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

        return redirect(url_for("/dash/"))

    elif request.method == "GET":
        return render_template("index.html", form=form)



def get_names(form):
    """
    Take the upload form, and extract the names given by the user
    :param form:
    :return:
    """
    names = []
    for idx in range(
            0, int(len(form) - 1)
    ):  # Magic number 1 corrects for csrf_token stored in the form
        # print(idx)
        # print(form["input[new" + str(idx) + "][name]"])
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
        print ('Saving')
        print ('hekki firax')
        print (os.getcwd())

        print (app.config["UPLOAD_FOLDER"])


        filename = secure_filename(file.filename)
        print (filename)
        print (os.getcwd())
        print (os.listdir())
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        path_dict[path] = filename

    return path_dict


def get_input(uploads):
    """ Build the tree based on the tree and alignment provided"""
    trees = []

    for idx in range(0, int(len(uploads) / 2)):

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

        trees.append(tree)

    return trees, tree_path


if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000)

