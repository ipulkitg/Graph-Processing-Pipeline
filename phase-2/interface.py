from neo4j import GraphDatabase
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

class Interface:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self._driver.verify_connectivity()

    def close(self):
        self._driver.close()

    def check_and_drop_graph(self, graph_name):
        with self._driver.session() as session:
            check_query = """
                CALL gds.graph.exists($graph_name) YIELD exists
                RETURN exists
            """
            exists = session.run(check_query, graph_name=graph_name).single()["exists"]

            if exists:
                drop_query = "CALL gds.graph.drop($graph_name) YIELD graphName"
                session.run(drop_query, graph_name=graph_name)
            else:
                print(f"Graph '{graph_name}' does not exist, proceeding with graph creation.")

    def create_graph_projection(self, graph_name):

        query = (
            "CALL gds.graph.project($graph_name, "
            "{ Location: { properties: ['name'] } }, "
            "{ TRIP: { type: 'TRIP', orientation: 'NATURAL', "
            "properties: { distance: { property: 'distance', defaultValue: 1.0 } } } }) "
            "YIELD graphName, nodeCount, relationshipCount"
        )

        parameters = {"graph_name": graph_name}

        with self._driver.session() as session:
            result = session.run(query, parameters).single()

        if result:
            return {
                "graph": result["graphName"],
                "nodes": result["nodeCount"],
                "relationships": result["relationshipCount"],
            }

        raise RuntimeError("Failed to create graph projection.")
    

    def initialize_graph(self, graph_name):
        """
        Ensure the graph is set up by dropping and recreating it.
        """
        self.check_and_drop_graph(graph_name)
        self.create_graph_projection(graph_name)

    def get_node_id(self, node_name):
        """
        Retrieve the node ID for a node with the given name.
        """
        with self._driver.session() as session:
            node_id_query = """
                MATCH (n:Location)
                WHERE n.name = $node_name
                RETURN id(n) AS node_id
            """
            result = session.run(node_id_query, node_name=node_name).single()
            return result["node_id"] if result else None

    
    def pagerank(self, iterations=20, weight_attr="distance"):

        graph_id = "bfs_graph"
        self.initialize_graph(graph_id)
        
        query_template = (
            "CALL gds.pageRank.stream($graph, { "
            "maxIterations: $iterations, "
            "dampingFactor: 0.85, "
            "relationshipWeightProperty: $weight "
            "}) "
            "YIELD nodeId, score "
            "RETURN gds.util.nodeProperty($graph, nodeId, 'name', 'Location') AS name, score "
            "ORDER BY score DESC"
        )
        
        params = {"graph": graph_id, "iterations": iterations, "weight": weight_attr}
        
        with self._driver.session() as session:
            records = session.run(query_template, params).data()
        
        if not records:
            print("No PageRank results available.")
            return []
        
        return [records[0], records[-1]]


    def bfs(self, origin, destinations):
        """
        Execute Breadth-First Search (BFS) using the GDS library.
        """
        graph_label = "bfs_graph"
        self.initialize_graph(graph_label)

        if isinstance(destinations, int):
            destinations = [destinations]

        origin_id = self.get_node_id(origin)
        destination_ids = [self.get_node_id(node) for node in destinations if self.get_node_id(node)]

        if origin_id is None:
            print(f"Origin node '{origin}' not found.")
            return []

        query_statement = f"""
            UNWIND $destination_ids AS target
            CALL gds.shortestPath.dijkstra.stream('{graph_label}', {{
                sourceNode: $origin_id,
                targetNode: target,
                relationshipWeightProperty: 'distance'
            }})
            YIELD nodeIds, totalCost
            RETURN [nodeId IN nodeIds | {{
                        name: gds.util.asNode(nodeId).name,
                        id: nodeId
                    }}] AS path_nodes,
                totalCost AS total_distance
        """

        params = {"origin_id": origin_id, "destination_ids": destination_ids}

        with self._driver.session() as session:
            records = session.run(query_statement, params).data()

        paths = [{"path": record["path_nodes"], "total_distance": record["total_distance"]} for record in records]

        return paths