$(document).ready(function() {

    /*
    Enviará solicitação ao servidor para resgatar dados do MongoDB
    O retorno dos dados do MongoDB será enviado para o cliente javascript criar o grafo.
    */
    function getData() {
        $.post("/postmethod", {},
            function(err, req, resp) {
                var nodes = resp["responseJSON"]['nodes'];
                const objNodes = eval(nodes)
                var edges = resp["responseJSON"]['edges'];
                const objEdges = eval(edges)
                createGraphVis(objNodes, objEdges);
            });
    };

    /*
    Será acionado quando o usuário clicar 2 vezes sobre os nós.
    Enviará solicitação ao servidor para reconstruir o grafo a partir do nó (filtro) selecionado.
    O retorno dos dados será enviado para o cliente javascript criar o grafo.
    */
    window.filter = function(node_id) {
        $.post("/postfilter", { node_param: node_id },
            function(err, req, resp) {
                var nodes = resp["responseJSON"]['nodes'];
                const objNodes = eval(nodes)
                var edges = resp["responseJSON"]['edges'];
                const objEdges = eval(edges)
                createGraphVis(objNodes, objEdges);
            });
    };

    /*
    Função será acionada por meio do botão presente formulário index.html
    */
    $("#sendButton").click(function() {
        getData();
    });


})