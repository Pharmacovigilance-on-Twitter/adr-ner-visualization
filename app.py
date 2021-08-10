# app.py
import os
import sys
from flask import Flask, jsonify, request, render_template
import networkx as nx
from bson import json_util, ObjectId
import json
from pymongo import MongoClient #access MongoDB
import itertools
import pandas as pd



app = Flask(__name__)
app._static_folder = os.path.abspath("templates/static")

G = nx.DiGraph()

#Conectar ao MongoDB
def returnDatabase(uri = 'mongodb+srv://db_userTwitter:1QFuElt3ASr5r7Dh@twitter.vw2tu.mongodb.net/myFirstDatabase?retryWrites=true&w=majority',
                   database = 'Twitter'):
    return MongoClient(uri, connectTimeoutMS=300000).get_database(database)

def returnCollection(db, collection = 'CRF'):
    return db.get_collection(collection)

#Criar os nós do grafo
def returnUsers(collection):
    df_user = pd.DataFrame(list(collection.find({'Drug':{'$exists': 'true'}, 'ADR':{'$exists': 'true'}}, {"_id": 0, 'user.id_str': 1, "user.name": 1})))
    df_user['name'] = df_user['user'].apply(lambda cell: cell['name'])
    df_user['user_id'] = df_user['user'].apply(lambda cell: cell['id_str'])
    df_user['group'] = 1
    df_user.drop('user', 1, inplace=True)
    df_user = df_user.drop_duplicates(subset=['user_id'])
    return df_user

def returnReactions(collection):
    df_ADR = pd.DataFrame(list(collection.find({'Drug':{'$exists': 'true'}, 'ADR':{'$exists': 'true'} }, {"_id": 0, "ADR": 1})))
    df_ADR = df_ADR.explode('ADR').drop_duplicates()
    df_ADR.columns = ['descricao']
    df_ADR['tipo'] = 'ADR'
    df_ADR['group'] = 2
    return df_ADR

def returnMedicines(collection):
    df_Drug = pd.DataFrame(list(collection.find({'Drug':{'$exists': 'true'}, 'ADR':{'$exists': 'true'} }, { "_id": 0, "Drug": 1})))
    df_Drug = df_Drug.explode('Drug').drop_duplicates()
    df_Drug.columns = ['descricao']
    df_Drug['tipo'] = 'Drug'
    df_Drug['group'] = 3
    return df_Drug

def returnNodes(users, medicines, reactions):
    frames = [reactions, medicines]
    df_reclamacao = pd.concat(frames).drop_duplicates()
    df_reclamacao['id'] = pd.factorize(df_reclamacao.descricao)[0]
    framesNodes = [users[['user_id','name', 'group']].rename(columns={"user_id": "id", "name": "label"}), 
                   df_reclamacao[['id','descricao', 'group']].rename(columns={"id": "id", "descricao": "label"})]
    df_nodes = pd.concat(framesNodes).drop_duplicates()
    return df_nodes

#Criar as arestas do grafo
def returnUserMedicines(collection):
    df_user_Drug = pd.DataFrame(list(collection.find({'Drug':{'$exists': 'true'}, 
                                                         'ADR':{'$exists': 'true'} }, 
                                                        {'_id': 0, 'Drug': 1, 'user.id_str': 1, 'user.name': 1})))
    df_user_Drug['name'] = df_user_Drug['user'].apply(lambda cell: cell['name'])
    df_user_Drug['user_id'] = df_user_Drug['user'].apply(lambda cell: cell['id_str'])
    df_user_Drug.drop('user', 1, inplace=True)
    df_user_Drug = df_user_Drug.explode('Drug')
    return df_user_Drug

def returnUserReactions(collection):
    df_user_ADR = pd.DataFrame(list(collection.find({'Drug':{'$exists': 'true'}, 
                                                          'ADR':{'$exists': 'true'} }, 
                                                         {'_id': 0, 'ADR': 1, 'user.id_str': 1, 'user.name': 1})))
    df_user_ADR['name'] = df_user_ADR['user'].apply(lambda cell: cell['name'])
    df_user_ADR['user_id'] = df_user_ADR['user'].apply(lambda cell: cell['id_str'])
    df_user_ADR.drop('user', 1, inplace=True)
    df_user_ADR = df_user_ADR.explode('ADR')
    return df_user_ADR

def returnMedicineReaction(collection):
    df_Drug_ADR = pd.DataFrame(list(collection.find({'Drug':{'$exists': 'true'}, 
                                                             'ADR':{'$exists': 'true'}}, 
                                                            {'_id': 0, 'Drug': 1, 'ADR': 1})))
    df_Drug_ADR = df_Drug_ADR.explode('Drug')
    df_Drug_ADR = df_Drug_ADR.explode('ADR')
    return df_Drug_ADR

def returnID(label, dataframe):
    return list(dataframe.loc[dataframe['label'] == label]['id'])[0] 

def returnEdges(user_reactions, medicine_reactions):
    framesEdges = [medicine_reactions[['id_Drug', 'id_ADR']].rename(columns={"id_Drug": "from", "id_ADR": "to"}),
                   user_reactions[['user_id', 'id_ADR']].rename(columns={"id_ADR": "from", "user_id": "to" })]
    return pd.concat(framesEdges).drop_duplicates()

#Criar grafo
def createNodes(nodes):
    nodes_array = []
    for rowindex, row in nodes.iterrows():
        nodes_array.append((row['id'], {'group': row['group'], 'label': row['label']}))
    return nodes_array

def createEdges(edges):
    edges_array = []
    for rowindex, row in edges.iterrows():
        edges_array.append((row['from'], row['to']))
    return edges_array

def createNodesFilter(node_root, nodes_descendants):
    nodes_array = []
    nodes_array.append((node_root, G.nodes[node_root]))    
    for desc in nodes_descendants:
        nodes_array.append((desc, G.nodes[desc]))        
    return nodes_array

def createEdgesFilter(node_root, nodes_descendants):
    edges_array = []
    for desc in nodes_descendants:        
        for path in sorted(nx.all_simple_edge_paths(G, node_root, desc)):
            for p in path:
                edges_array.append(p)
    return edges_array

@app.route('/postmethod', methods = ['POST'])
def post_javascript_data():
    if(G.number_of_nodes() > 0):
        return { 'nodes' : list(G.nodes.data()), 'edges' : list(G.edges())}
        
    uri = "mongodb+srv://db_userTwitter:1QFuElt3ASr5r7Dh@twitter.vw2tu.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
    db = returnDatabase(uri = uri, database = 'Twitter' )
    collection = returnCollection(db, collection = 'CRF')

    #Criar os nós do grafo    
    users = returnUsers(collection)
    reactions = returnReactions(collection)
    medicines = returnMedicines(collection)
    nodes = returnNodes(users, medicines, reactions)

    #Criar as arestas do grafo
    user_medicines = returnUserMedicines(collection)
    user_reactions = returnUserReactions(collection)
    medicine_reactions = returnMedicineReaction(collection)
    user_medicines["id_Drug"] = user_medicines.apply(lambda row: returnID(row["Drug"], nodes), axis=1)
    user_reactions["id_ADR"] = user_reactions.apply(lambda row: returnID(row["ADR"], nodes), axis=1)
    medicine_reactions["id_Drug"] = medicine_reactions.apply(lambda row: returnID(row["Drug"], nodes), axis=1)
    medicine_reactions["id_ADR"] = medicine_reactions.apply(lambda row: returnID(row["ADR"], nodes), axis=1)
    edges = returnEdges(user_reactions, medicine_reactions)


    #Criar grafo (objeto)    
    G.add_nodes_from(createNodes(nodes))  
    G.add_edges_from(createEdges(edges))      

    return { 'nodes' : list(G.nodes.data()), 'edges' : list(G.edges())}
        
@app.route('/postfilter', methods = ['POST'])
def post_javascript_filter():
    node_param = int(request.form['node_param'])    
    descs = nx.descendants(G, int(node_param))    
    nodes = createNodesFilter(node_param, descs)
    edges = createEdgesFilter(node_param, descs)    

    G_Filter = nx.DiGraph()
    G_Filter.add_nodes_from(nodes)  
    G_Filter.add_edges_from(edges)  

    return { 'nodes' : list(G_Filter.nodes.data()), 'edges' : list(G_Filter.edges())}

######## HOME ############
@app.route("/", methods=["GET"])
def index():    
    return render_template('../layouts/index.html')


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(debug=True, threaded=True, port=5000)
