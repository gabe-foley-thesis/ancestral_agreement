from ete3 import PhyloTree
from werkzeug.utils import secure_filename
import os
from routes import app


UPLOAD_FOLDER = os.getcwd() + "/static/uploads/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_names(form):
    """
    Take the upload form, and extract the names given by the user
    :param form:
    :return:
    """
    names = []

    print ('getting names')
    print (form)
    print (len(form))
    print (len(form) / 2)
    for idx in range(0, int(len(form) - 1)): # Magic number 1 corrects for csrf_token stored in the form
        print (idx)
        print (form['input[new' + str(idx) + '][name]'])
        names.append(form['input[new' + str(idx) + '][name]'])

    return names



def save_files(uploads):
    """
    Take the FileStorage objects in the input dictionary, save them to the server, and then return the updated mapping
    that maps to their file location
    :param uploads:
    :return:
    """

    path_dict = {}

    for path,file in uploads.items():

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        path_dict[path] = filename

    return path_dict




def get_input(uploads):
    trees = []


    print ('uploads here is ', uploads)
    for idx in range(0, int(len(uploads) / 2)):
        print (idx)
        print (uploads['input[new' + str(idx) + '][tree]'])
        print (uploads['input[new' + str(idx) +'][aln]'])
        tree = PhyloTree(os.path.join(app.config['UPLOAD_FOLDER'], uploads['input[new' + str(idx) + '][tree]']),
                                      alignment = os.path.join(app.config['UPLOAD_FOLDER'], uploads['input[new' + str(
                                          idx) +
                                                                                          '][aln]']), format=1,
                         alg_format="fasta")

        print ('made the tree')

        trees.append(tree)


    return trees