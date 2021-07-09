  function createGraphVis(nodes, edges) {

      /*
      Função utilizada para selecionar uma dimensão de um determinado array
       */
      const arrayColumn = (arr, n) => arr.map(x => x[n]);

      /*
      Atribui os valores dos arrays às variáveis [keys, values]      
      */
      const [keys, values] = [Object.values(arrayColumn(nodes, 0)), Object.values(arrayColumn(nodes, 1))]
      const [from, to] = [Object.values(arrayColumn(edges, 0)), Object.values(arrayColumn(edges, 1))]

      /*
      Criará uma estrutura de dados para os nós similar a:
      var nodes = new vis.DataSet([
        {id: 1, label: 'Node 1', group: 1},
        {id: 2, label: 'Node 2', group: 2}
      ]);      
      */
      var keys_vis = keys.map(e => ({ id: e }));
      var values_vis = values.map(e => ({ values: e }));
      var nodes_vis = keys_vis.map((o, i) => ({ id: o.id, label: values_vis[i].values.label, group: values_vis[i].values.group }));

      /*
      Criará uma estrutura de dados para as arestas similar a:
      var edges = new vis.DataSet([
        {from: 1, to: 3},
        {from: 1, to: 2},
        {from: 2, to: 4},
        {from: 2, to: 5}
      ]);
      */
      var from_vis = from.map(e => ({ from: e }));
      var to_vis = to.map(e => ({ to: e }));
      var edge_vis = from_vis.map((o, i) => ({ from: o.from, to: to_vis[i].to }));


      // Criar um array com os nós
      var nodes = new vis.DataSet(nodes_vis);

      // Criar um array com as arestas
      var edges = new vis.DataSet(edge_vis);

      // Criar o grafo
      var container = document.getElementById('mynetwork');

      // Mapear os dados: nós e arestas
      var data = {
          nodes: nodes,
          edges: edges
      };

      // Definir as características do grafo
      var options = {
          groups: {
              1: { color: { background: 'red' }, borderWidth: 3 },
              2: { color: { background: 'yellow' }, borderWidth: 3 },
              3: { color: { background: 'blue' }, borderWidth: 3 },
          },
          nodes: {
              shape: "dot",
              size: 16,
          },
          physics: {
              forceAtlas2Based: {
                  gravitationalConstant: -26,
                  centralGravity: 0.005,
                  springLength: 230,
                  springConstant: 0.18,
              },
              maxVelocity: 73,
              solver: "forceAtlas2Based",
              timestep: 0.35,
              stabilization: {
                  iterations: 150
              },
          },
          interaction: { hover: true },
          manipulation: {
              enabled: false,
          },
      };

      // Iniciar o grafo
      var network;
      network = new vis.Network(container, data, options);

      // Configurar a ação duplo clique no nó
      network.on("doubleClick", function(params) {
          params.event = "[original event]";
          filter(params.nodes[0]);
      });

      // Criar a barra de progresso
      network.on("stabilizationProgress", function(params) {
          var maxWidth = 496;
          var minWidth = 20;
          var widthFactor = params.iterations / params.total;
          var width = Math.max(minWidth, maxWidth * widthFactor);

          document.getElementById("bar").style.width = width + "px";
          document.getElementById("text").innerText =
              Math.round(widthFactor * 100) + "%";
      });
      network.once("stabilizationIterationsDone", function() {
          document.getElementById("text").innerText = "100%";
          document.getElementById("bar").style.width = "496px";
          document.getElementById("loadingBar").style.opacity = 0;
          // really clean the dom element
          setTimeout(function() {
              document.getElementById("loadingBar").style.display = "none";
          }, 500);
      });



  }