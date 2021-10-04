import fasta
from Bio.Seq import Seq
from itertools import combinations
import re
import numpy as np
import Bio.SeqUtils
import atchleyIndex
import bland_altman
import pandas as pd
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from SimilarNodeFinder.src.tree_object import TreeObject
from SimilarNodeFinder.src.tree_controller import TreeController
from collections import defaultdict


def get_similar_nodes(treepath1, treepath2):
    similar_nodes = {}
    tree1 = TreeObject(treepath1)
    tree2 = TreeObject(treepath2)
    tree_controller = TreeController()
    matching_labels = tree_controller.get_similar_nodes_between_trees(
        tree1, tree2, False
    )
    for label, node in matching_labels.items():
        similar_nodes[label.strip()] = node.get_label().strip()
    return similar_nodes


def pare_down_similar_nodes(reference, other):
    pared_down_similar_nodes = {}
    for ref in reference.values():
        if ref in pared_down_similar_nodes:
            print("ALREADY IN THERE ", ref)
        pared_down_similar_nodes[ref] = other[ref]

    return pared_down_similar_nodes


def getRemovedSeqs(tree1, tree2):
    removedSeqs = [x.name for x in tree1 if x.name not in tree2]
    removedSeqs2 = [x.name for x in tree2 if x.name not in tree1]

    if len(removedSeqs) > 0 and len(removedSeqs2) > 0:
        raise RuntimeError(
            "There are unique sequences in each tree. One tree should be a subset of the other"
        )

    if len(removedSeqs) > 0:
        return removedSeqs
    elif len(removedSeqs2) > 0:
        return removedSeqs2
    else:
        raise RuntimeError("These trees contained the same sequences")

    return removedSeqs


def get_node_to_leaf_dict(tree):
    leaves = tree.get_cached_content()
    node2leaf = {}

    for n in tree.traverse():
        if len(leaves[n]) > 1:
            leaf_names = [x.name for x in leaves[n]]
            node2leaf[n] = leaf_names

    return node2leaf


def get_leaf_to_node_dict(tree):

    leaves = tree.get_cached_content()
    leaf2node = {}

    for n in tree.traverse():
        if len(leaves[n]) > 1:
            leaf_names = [x.name for x in leaves[n]]
            leaf2node[repr(sorted(leaf_names))] = n

    return leaf2node


def clean_paml_tree(tree, outpath=None):

    regex = re.compile("\d*[_]")

    for node in tree:
        node.name = node.name.split(re.search(regex, node.name).group(0))[1]
    if outpath:
        tree.write(outfile=outpath)
    return tree


def correct_fastml_seqs_to_n0(fastml_ancestors, outpath=None):
    """
    Take a set of FastML sequences including ancestors and change them so that N1 becomes N0, N2 becomes N1, etc...
    This puts them in line with the GRASP labelling and allows for us to use GRASP labelled trees instead of FastML
    labelled trees
    :param fastml_ancestors: The set of FastML ancestors to change
    :param outpath: Path to write the corrected sequences to
    :return:
    """

    for x in fastml_ancestors:
        if (
            len(x.name) < 5
        ):  # Just in case the sequence file still contains the extant sequences
            oldname = x.name
            node = oldname.split("N")[1]
            newname = "N" + str(int(node) - 1)
            x.id = newname
            x.name = newname
            x.description = newname

    records = [x for x in fastml_ancestors]

    record_dict = {}

    for x in records:
        record_dict[x.name] = x

    if outpath:
        fasta.write_fasta(records=records, filename=outpath)

    return record_dict


def map_nodes_between_trees(tree1, tree2, removedSeqs=[]):
    """
    Given two trees with identical topology (or where one is a subset of another larger tree) but potentially
    differently labelled internal nodes - create a mapping from tree1's to tree2's internal nodes
    :param tree1: First
    :param tree2:
    :param removedSeqs: Optional list of sequences not found in the smaller tree
    :return: Dictionary mapping tree1's internal nodes to tree2
    """
    nodeDict = {}
    if len(tree1) >= len(tree2):
        larger = tree1
        smaller = tree2
    else:
        larger = tree2
        smaller = tree1

    larger_dict = get_node_to_leaf_dict(larger)
    smaller_dict = get_leaf_to_node_dict(smaller)

    for node, leaf_names in larger_dict.items():

        removed_names = [x for x in leaf_names if x not in removedSeqs]

        if (
            removed_names in larger_dict.values()
            and len(removed_names) < len(leaf_names)
            or len(removed_names) == 1
        ):
            pass
        else:
            leaves = repr(sorted(removed_names))

            nodeDict[node.name] = smaller_dict[leaves].name

    return nodeDict


def get_age_order_and_ages(tree, rev=False):
    """
    Return a tuple with two lists, one of internal nodes in evolutionary age from root ancestor, and one of
    the actual ages associated with each internal node
    :param tree: The tree for which we want to generate the lists
    :param rev: Whether or not to reverse the order of the nodes and ages
    :return: A tuple with two lists - node names and evolutionary ages in the specified order
    """
    age_order = []
    ages = []
    node_dist = {}

    # Get all the distances
    for node in tree.traverse("postorder"):
        if not node.is_leaf():
            node_dist[node.name] = node.get_distance(tree.get_tree_root())

    # Create a sorted list of distances
    for node in sorted(node_dist, key=node_dist.get, reverse=rev):
        age_order.append(node)
        ages.append(node_dist[node])

    return age_order, ages


def get_child_order_and_child_count(tree, rev=True):
    """
    Return a tuple with two lists, one of internal nodes in order of number of children, and one of
    the actual number of children associated with each internal node
    :param tree: The tree for which we want to generate the lists
    :param rev: Whether or not to reverse the order of the nodes and child number
    :return: A tuple with two lists - node names and child numbers in the specified order
    """
    child_order = []
    child_count = []
    node_count = {}

    nodes = tree.get_cached_content()
    for n in tree.traverse():
        if len(nodes[n]) > 1:
            node_count[n.name] = len(nodes[n])

    for node in sorted(node_count, key=node_count.get, reverse=rev):
        child_order.append(node)
        child_count.append(node_count[node])

    return child_order, child_count


def quantify_seq(tree, atchleyNames):
    """
    Take two trees and return a list of tuples containing the quantified representations of the sequences at internal
     nodes in a given order.
    :param tree1: The first tree containing sequences at internal nodes
    :param atchleyNames: A list of atchley indexes to compute
    :return: A list of tuples with quantified representations of the sequences in the given node order for each metric
    """

    seq = []
    weight = []
    iso = []
    instab = []
    gravy = []
    results = {}

    if atchleyNames:
        for atchley in atchleyNames:
            exec(atchley + "= []")
    for curr in tree.traverse():
        if not curr.is_leaf():
            analysed_seq = ProteinAnalysis(str(curr.sequence).replace("-", ""))
            seq.append(str(curr.sequence).replace("-", ""))
            weight.append(float("%0.2f" % analysed_seq.molecular_weight()))
            iso.append(analysed_seq.isoelectric_point())
            instab.append(analysed_seq.instability_index())
            gravy.append(analysed_seq.gravy())

            if atchleyNames:
                for atchley in atchleyNames:
                    exec(
                        atchley
                        + ".append(atchleyIndex.get_atchley_index_for_seq(str(curr.sequence).replace('-',''),'"
                        + atchley
                        + "'))"
                    )

        results["Sequence"] = seq
        results["Molecular weight"] = weight
        results["Isoelectric point"] = iso
        results["Instability index"] = instab
        results["Grand average of hydropathicity"] = gravy

        if atchleyNames:
            for atchley in atchleyNames:
                exec("results['" + atchley + "'] =" + atchley)

    return results


def map_internal_gap_patterns(seqs_gaps, seqs_wo_gaps, outpath=None, gaps2wo=None):
    """
    Take a set of sequences representing internal nodes with gaps, a set of internal nodes without gaps and a dictionary
    mapping the internal nodes from one to another and add a gap pattern to the sequences without gaps consistent with
    the sequences with gaps

    :param seqs_gaps: Set of sequences with gaps
    :param seqs_wo_gaps: Set of sequences without gaps
    :param gaps2wo: Dictionary mapping the internal nodes between the sequence sets
    :param outpath: Where to write the sequence set with the newly added gaps to
    :return: The records with new internal gap patterns
    """
    # Make a mapping of the nodes from the sequence set with gaps to the sequence set without

    updated_seqs = []

    for x in seqs_gaps:
        if len(x) < 5 and x.startswith("N"):
            updated_joint = ""

            if gaps2wo != None:
                seq_to_change = seqs_wo_gaps[gaps2wo[x]].seq
            else:
                seq_to_change = seqs_wo_gaps[x].seq

            for pos in zip(seqs_gaps[x].seq, seq_to_change):

                if pos[0] == "-":
                    updated_joint += "-"
                else:
                    updated_joint += pos[1]

            if gaps2wo != None:
                seqs_wo_gaps[gaps2wo[x]].seq = Seq(updated_joint)
            else:
                seqs_wo_gaps[x].seq = Seq(updated_joint)

    results = [x for x in seqs_wo_gaps.values()]

    for x in results:
        if x.name == "699":
            print("And now it is")
            print(x)
    if outpath:
        fasta.write_fasta(records=results, filename=outpath)

    return results


def get_metric_lims(metrics):
    """
    Calculate what the y-lim should be for a plot by considering all of the trees we'll be comparing for the same metric
    :param metrics: A dictionary relating a pair of trees to a dictionary containing the metrics and scores
    :return: A dictionary relating a metric to the highest absolute score
    """

    # Just grab the first set of metrics to make a metric limit dictionary
    metric_list = list(metrics.values())
    metric_lims = dict.fromkeys(metric_list[0])
    for k in metric_lims:
        metric_lims[k] = 0

    for method, metrics in metrics.items():
        for metric, vals in metrics.items():
            diffs = vals[0] - vals[1]
            limit = abs(max(diffs, key=np.abs))
            if metric_lims[metric] < limit:
                metric_lims[metric] = limit

    return metric_lims


def generate_ancestral_agreement_plot(
    tree_metrics, counts, count_order, data_name, data_len, metric_lims, x_axis
):

    for name, metrics in tree_metrics.items():
        name1 = name[0]
        name2 = name[1]

        for metric_name, vals in metrics.items():
            metric1 = vals[0]
            metric2 = vals[1]

            if metric_lims:
                y_lim = metric_lims[metric_name] + (metric_lims[metric_name] / 2)
            else:
                y_lim = None

            bland_altman_ages = bland_altman.bland_altman_plot(
                metric1,
                metric2,
                ages=counts,
                point_labels=count_order,
                title="%s vs %s predictions for %s %s (%s sequences)"
                % (name1, name2, metric_name.replace("_", " "), data_name, data_len),
                y_lim=y_lim,
                x_axis=x_axis,
            )
            fig = bland_altman_ages.get_figure()
            fig.savefig("%s %s vs %s_%s.png" % (data_name, name1, name2, metric_name))


def run_ancestral_agreement(
    trees,
    names=None,
    nodeDict=None,
    skip=(),
    data_name="",
    sort_age=True,
    sort_child=False,
    atchleyNames=["Polarity"],
):
    if names == None:
        names = [x[0] for x in enumerate(trees)]

    if len(trees) != len(names):
        raise RuntimeError("Please provide a name for each set")

    data_len = len(trees[0]) - 1

    data = [x for x in zip(names, trees)]

    age_order, ages = get_age_order_and_ages(trees[0])
    child_order, child_count = get_child_order_and_child_count(trees[0])

    child_indexes = [child_order.index(x) for pos, x in enumerate(age_order)]

    print(f"Here is the age order {age_order} and ages is {ages}")
    print(f"Here is the child order {child_order} and count is {child_count}")

    print("here is child indexes ", child_indexes)

    data_frame = pd.DataFrame()
    quantified_data = {}
    master_data = defaultdict(list)
    for dataset in data:
        # Get all of the quantified versions of ancestral sequences
        quantified_seqs = quantify_seq(dataset[1], atchleyNames)
        quantified_child_order_seqs = {}

        for metric, values in quantified_seqs.items():
            quantified_child_order_seqs[metric + "_Child_order"] = [
                values[x] for x in child_indexes
            ]

        print("quantified seqs is ")
        print(quantified_seqs)
        joined_data = dict(
            list(quantified_seqs.items()) + list(quantified_child_order_seqs.items())
        )
        quantified_data[dataset[0]] = joined_data

    print("her eis quantified ")
    print(quantified_data)

    return quantified_data

    # for k, v in quantified_seq.items():
    #     master_data[k] += v
    #     print(dataset[0], k, v)
    #     if k in data_frame:
    #         data

    #     perm = combinations(data, 2)

    #     tree_age_dict = {}
    #     tree_child_dict = {}

    #     for i in list(perm):
    #         name1 = i[0][0]
    #         name2 = i[1][0]
    #         tree1 = i[0][1]
    #         tree2 = i[1][1]
    #         if (name1, name2) not in skip and (name2, name1) not in skip:

    #             if nodeDict == None:

    #                 nodeDict = map_nodes_between_trees(tree1, tree2)

    #             age_order, ages = get_age_order_and_ages(tree1)
    #             child_order, child_count = get_child_order_and_child_count(tree1)

    #             if sort_age:
    #                 metrics_by_age = quantify_seqs(tree1, tree2, age_order, nodeDict, atchleyNames=atchleyNames)
    #                 tree_age_dict[(name1, name2)] = metrics_by_age

    #             if sort_child:
    #                 metrics_by_child_count = quantify_seqs(tree1, tree2, child_order, nodeDict,atchleyNames=atchleyNames)
    #                 tree_child_dict[(name1, name2)] = metrics_by_child_count

    #     if sort_age:
    #         age_metric_lims = get_metric_lims(tree_age_dict)
    #         generate_ancestral_agreement_plot(tree_age_dict, ages, age_order, data_name, data_len, age_metric_lims,
    #                                            "Evolutionary age")

    #     if sort_child:
    #         child_metric_lims = get_metric_lims(tree_child_dict)
    #         generate_ancestral_agreement_plot(tree_child_dict, child_count, child_order, data_name, data_len,
    #                                       child_metric_lims, "Number of child nodes")
