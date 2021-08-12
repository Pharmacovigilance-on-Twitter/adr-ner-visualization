"""TransformerIOBSchema.ipynb

Original file is located at https://colab.research.google.com/OurDrive
"""

#Importação da biblioteca do Doccano Transformer para modificar JSON (TextLabel) para **CoNLL 2003** ou **spaCy**


!pip install doccano-transformer
from doccano_transformer.datasets import NERDataset
from doccano_transformer.utils import read_jsonl
from collections import defaultdict
import pandas as pd
from pymongo import MongoClient
import dns

#Variaveis para contar e armazenar as sentenças
sentence_number = 0
dictTokenALL = []

#Adicionando o caminho a variavel d (o caminho do jsonl)
d = NERDataset.from_jsonl(filepath='/.../ADR-TextLabel.jsonl')

#verifica cada linha se está em conll2003 e dá um Split 
for x in d.to_conll2003(str.split):

  #ver só o NoData(NoUser não entra) a cada \n pular de linha e divide uma string em substrings
  for y in x['data'].split('\n'):

    #coloca aspas em cada substring
    fields = y.split(' ')

    #conta os itens da variavel fields se for igual a 4 (não entra a quebra de linha entre tweets)
    if(len(fields) == 4):

      #retira o inicio, pois comeca sempre em DOCSTART
      if (fields[0] == '-DOCSTART-'):
        sentence_number += 1
      else:
        dictToken = {}
        dictToken['sentence'] = sentence_number
        dictToken['word'] = fields[0]
        dictToken['tag'] = fields[3]
        dictTokenALL.append(dictToken)
        print(dictToken)


import pymongo
myclient = pymongo.MongoClient("Link da conexão com o MongoDB")

#database 
mydb = myclient["bio_tokens"]
#collection do db
mycol = mydb["bio_tokens"]
#variavel para adicionar em Massa na Collection BioTokens
x = mycol.insert_many(dictTokenALL)

#print list of the _id values of the inserted documents:
print(x.inserted_ids)

