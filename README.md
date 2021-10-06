# Ancestral Agreement

Ancestral Agreement is a method, inspired by Bland-Altman plots, for comparing the agreement between two sets of predicted biological ancestral sequences.


Each pair of ancestral protein sequences between two sets are converted into quantitative predictions for a range of metrics and the differences between sets are plotted against the evolutionary age of each ancestor. Results are easily interpretable and highlight whether particular methods consistently disagree, whether specific nodes are inconsistently inferred, and specific evolutionary times beyond which methods start to diverge.

<img src="https://raw.githubusercontent.com/gabe-foley-thesis/ancestral_agreement/main/aa/static/images/ancestral_agreement_gui.png" width="800">



# Installation

You can try this out in a docker instance. This will setup the Mongo database and the Flask application.

```
git clone github.com/gabe-foley-thesis/ancestral_agreement
cd ancestral_agreement
docker-compose up
```

You can now open a web browser and go to localhost:5000 - 

This gives you the upload form which you can enter your data into.

If you just want to view the example data then navigate to localhost:5000/dash and it will load automatically

Inputs required are a phylogenetic tree labelled with ancestral node positions (Newick format) and two sets of ancestor sequences from different prediction methods / settings that correspond to the labelled ancestral node positions (FASTA format). 

See /files/test_6_1.aln, test_6_2.aln, and test_6.nwk for the expected format.


# Notes

After you're loaded the files you need to select the data sets you're interested in viewing from the drop down menu.

Currently the phylogenetic tree must be identical for each method.
