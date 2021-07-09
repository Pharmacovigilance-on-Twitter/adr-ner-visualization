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
def returnDatabase(uri = 'mongodb://...',
                   database = 'twitter'):
    return MongoClient(uri, connectTimeoutMS=300000).get_database(database)

def returnCollection(db, collection = 'allbancos_crf'):
    return db.get_collection(collection)

#Criar os nós do grafo
def returnUsers(collection):
    df_user = pd.DataFrame(list(collection.find({'produto':{'$exists': 'true'}, 'problema':{'$exists': 'true'}}, {"_id": 0, 'user.id_str': 1, "user.name": 1})))
    df_user['name'] = df_user['user'].apply(lambda cell: cell['name'])
    df_user['user_id'] = df_user['user'].apply(lambda cell: cell['id_str'])
    df_user['group'] = 1
    df_user.drop('user', 1, inplace=True)
    df_user = df_user.drop_duplicates(subset=['user_id'])
    return df_user

def returnProblems(collection):
    df_problema = pd.DataFrame(list(collection.find({'produto':{'$exists': 'true'}, 'problema':{'$exists': 'true'} }, {"_id": 0, "problema": 1})))
    df_problema = df_problema.explode('problema').drop_duplicates()
    df_problema.columns = ['descricao']
    df_problema['tipo'] = 'problema'
    df_problema['group'] = 2
    return df_problema

def returnProducts(collection):
    df_produto = pd.DataFrame(list(collection.find({'produto':{'$exists': 'true'}, 'problema':{'$exists': 'true'} }, { "_id": 0, "produto": 1})))
    df_produto = df_produto.explode('produto').drop_duplicates()
    df_produto.columns = ['descricao']
    df_produto['tipo'] = 'produto'
    df_produto['group'] = 3
    return df_produto

def returnNodes(users, products, problems):
    frames = [problems, products]
    df_reclamacao = pd.concat(frames).drop_duplicates()
    df_reclamacao['id'] = pd.factorize(df_reclamacao.descricao)[0]
    framesNodes = [users[['user_id','name', 'group']].rename(columns={"user_id": "id", "name": "label"}), 
                   df_reclamacao[['id','descricao', 'group']].rename(columns={"id": "id", "descricao": "label"})]
    df_nodes = pd.concat(framesNodes).drop_duplicates()
    return df_nodes

#Criar as arestas do grafo
def returnUserProducts(collection):
    df_user_produto = pd.DataFrame(list(collection.find({'produto':{'$exists': 'true'}, 
                                                         'problema':{'$exists': 'true'} }, 
                                                        {'_id': 0, 'produto': 1, 'user.id_str': 1, 'user.name': 1})))
    df_user_produto['name'] = df_user_produto['user'].apply(lambda cell: cell['name'])
    df_user_produto['user_id'] = df_user_produto['user'].apply(lambda cell: cell['id_str'])
    df_user_produto.drop('user', 1, inplace=True)
    df_user_produto = df_user_produto.explode('produto')
    return df_user_produto

def returnUserProblems(collection):
    df_user_problema = pd.DataFrame(list(collection.find({'produto':{'$exists': 'true'}, 
                                                          'problema':{'$exists': 'true'} }, 
                                                         {'_id': 0, 'problema': 1, 'user.id_str': 1, 'user.name': 1})))
    df_user_problema['name'] = df_user_problema['user'].apply(lambda cell: cell['name'])
    df_user_problema['user_id'] = df_user_problema['user'].apply(lambda cell: cell['id_str'])
    df_user_problema.drop('user', 1, inplace=True)
    df_user_problema = df_user_problema.explode('problema')
    return df_user_problema

def returnProductProblem(collection):
    df_produto_problema = pd.DataFrame(list(collection.find({'produto':{'$exists': 'true'}, 
                                                             'problema':{'$exists': 'true'}}, 
                                                            {'_id': 0, 'produto': 1, 'problema': 1})))
    df_produto_problema = df_produto_problema.explode('produto')
    df_produto_problema = df_produto_problema.explode('problema')
    return df_produto_problema

def returnID(label, dataframe):
    return list(dataframe.loc[dataframe['label'] == label]['id'])[0] 

def returnEdges(user_problems, product_problems):
    framesEdges = [product_problems[['id_produto', 'id_problema']].rename(columns={"id_produto": "from", "id_problema": "to"}),
                   user_problems[['user_id', 'id_problema']].rename(columns={"id_problema": "from", "user_id": "to" })]
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
        
    uri = "mongodb://Informe a sua conexão"
    db = returnDatabase(uri = uri, database = 'twitter' )
    collection = returnCollection(db, collection = 'allbancos_crf')

    #Criar os nós do grafo    
    users = returnUsers(collection)
    problems = returnProblems(collection)
    products = returnProducts(collection)
    nodes = returnNodes(users, products, problems)

    #Criar as arestas do grafo
    user_products = returnUserProducts(collection)
    user_problems = returnUserProblems(collection)
    product_problems = returnProductProblem(collection)
    user_products["id_produto"] = user_products.apply(lambda row: returnID(row["produto"], nodes), axis=1)
    user_problems["id_problema"] = user_problems.apply(lambda row: returnID(row["problema"], nodes), axis=1)
    product_problems["id_produto"] = product_problems.apply(lambda row: returnID(row["produto"], nodes), axis=1)
    product_problems["id_problema"] = product_problems.apply(lambda row: returnID(row["problema"], nodes), axis=1)
    edges = returnEdges(user_problems, product_problems)


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
    return render_template('layouts/index.html')


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(debug=True, threaded=True, port=5000)
