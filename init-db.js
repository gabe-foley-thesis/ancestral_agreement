db = db.getSiblingDB("ancestral_agreement_forever");
db.data_store.drop();



data_store = DataStore(
    session_token='44',
    data=data,
    names=['Small example 1', 'Small example 2'],
    age_order=['N0, N1', 'N2', 'N3', 'N4'],
    ages= [0, 0.0215755, 0.215755, 0.05201, 0.05899],
    child_order=['N0, N1', 'N2', 'N3', 'N4'],
    child_count=[6,3,3,2,2],
    node_dict= {N0: "N0", N1: "N1", N2: "N2", N3: "N3", N4: "N4"},
    tree_path="aa/static/uploads/test_ancestors_6.nwk",
)
data_store.save()



// db.data_store.insertOne([
//     {
//         "id": 1,
//         "name": "Lion",
//         "type": "wild"
//     },
//     {
//         "id": 2,
//         "name": "Cow",
//         "type": "domestic"
//     },
//     {
//         "id": 3,
//         "name": "Tiger",
//         "type": "wild"
//     },
// ]);
//
//
//
