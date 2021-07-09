# Grafo para visualização de dados do Twitter
## As postagens foram marcadas por meio de um modelo de reconhecimento de entidades


### Esta aplicação utilizou os seguintes componentes:
* Banco de dados: **MongoDB** (https://www.mongodb.com/)
* Framework para desenvolvimento web: **Flask** (https://flask.palletsprojects.com/en/2.0.x/)
* Hospedagem: **Heroku** (http://heroku.com)
* Biblioteca para visualização de dados no cliente: **vis.js** (https://visjs.org/)
* Manipulação de redes complexas: **networkx** (https://networkx.org/)


### Alterar parâmetros de conexão com o banco no arquivo `app.py`
```
uri = "**Inserir a sua URI de conexão**"
db = returnDatabase(uri = uri, database = '**twitter**' )
collection = returnCollection(db, collection = '**allbancos_crf**')
```

### As postagens do Twitter devem possuir a estrutura marcada na figura
<image width='500px' src='./postagens.png'>


### Iniciar a aplicação localmente: 
`python3 app.py`

### Instruções para publicar na plataforma Heroku
https://devcenter.heroku.com/articles/getting-started-with-python


### Home page
#### Site demonstração: https://flask-graph-vis-js.herokuapp.com/
<image width='500px' src='./home.png'>