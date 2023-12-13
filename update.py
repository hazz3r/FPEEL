def graph_unweighted(): 
    edges = [ 
        [0, 21, 0, 3, 0, 0], 
        [21, 0, 9, 0, 5, 12], 
        [0, 9, 0, 0, 0, 10], 
        [0, 5, 0, 16, 0, 0], 
        [0, 5, 9, 16, 0, 0],  
        [0, 12, 10, 0, 0, 0] 
    ] 

    nodes = ["A", "B", "C", "D", "E", "F"]  

    for i in nodes: 
        for j in nodes: 
            print(i,j, edges[nodes.index(i)][nodes.index(j)])  

graph_unweighted() 