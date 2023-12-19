from neo4j import GraphDatabase

class GraphAlgorithms:
    def __init__(self):
        self._uri = "bolt://localhost:7687"
        self._user = "neo4j"
        self._password = "password"
        self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))

    def close(self):
        self._driver.close()

    def execute_query(self, query):
        with self._driver.session() as session:
            session.run(query)

    def get_all_nodes(self):
        query = "MATCH (n) RETURN n"
        with self._driver.session() as session:
            result = session.run(query)
            nodes = [record['n'] for record in result]
            return nodes

    # Define other methods to perform specific operations on the database


#grap instance creation pulling all the nodes
graph_algo = GraphAlgorithms()
nodes = graph_algo.get_all_nodes()
print(nodes)
graph_algo.close()