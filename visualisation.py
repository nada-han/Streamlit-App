import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# Configurer le titre de l'application Streamlit
st.title("Analyse de Graphes depuis Neo4j : ")
st.write("Explorez différents algorithmes appliqués sur les graphes.")

# Configuration de la connexion à Neo4j
NEO4J_URI = "bolt://neo4j:7687"
NEO4J_USER = "neo4j"  # Remplacez par votre nom d'utilisateur
NEO4J_PASSWORD = "password"  # Remplacez par votre mot de passe
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Fonction pour exécuter une requête dans Neo4j
def query_neo4j(query):
    with driver.session() as session:
        result = session.run(query)
        return [dict(record) for record in result]

# Fonction pour visualiser le graphe
def visualize_graph(df, algorithm_name=None):
    if 'source' not in df.columns:
        st.error("Le graphe ne contient pas de données valides pour la visualisation.")
        return

    G = nx.DiGraph()
    for _, row in df.iterrows():
        node_attrs = {}
        if 'pagerank' in row:
            node_attrs['pagerank'] = row['pagerank']
        if 'component' in row:
            node_attrs['component'] = row['component']
        if 'triangle_count' in row:
            node_attrs['triangle_count'] = row['triangle_count']

        G.add_node(row['source'], **node_attrs)
        if pd.notna(row.get('target', None)):
            G.add_edge(row['source'], row['target'])

    pos = nx.spring_layout(G)
    labels = {
        node: f"{node}\nPR: {data.get('pagerank', 'N/A'):.2f}" if data.get('pagerank') is not None else f"{node}\nPR: N/A"
        for node, data in G.nodes(data=True)
    }

    plt.figure(figsize=(12, 8))
    nx.draw(
        G, pos, with_labels=True, node_size=700, node_color='lightblue',
        labels=labels, font_size=10, font_color='black'
    )
    title = f"Visualisation du graphe - {algorithm_name}" if algorithm_name else "Visualisation du graphe"
    plt.title(title)
    st.pyplot(plt)

# Fonction pour récupérer et nettoyer les données selon l'algorithme sélectionné
def query_graph_data(graph_name, algorithm):
    query = f"""
    MATCH (n:Vertex {{graph_name: '{graph_name}'}})
    OPTIONAL MATCH (n)-[r]->(m:Vertex)
    RETURN 
        n.id AS source, 
        n.pagerank AS pagerank, 
        n.component AS component,
        n.triangle_count AS triangle_count, 
        m.id AS target
    """
    result_df = pd.DataFrame(query_neo4j(query))

    # Filtrer les données en fonction de l'algorithme sélectionné
    if algorithm == "PageRank":
        result_df = result_df[['source', 'pagerank']].dropna(subset=['pagerank'])
    elif algorithm == "Connected Components":
        result_df = result_df[['source', 'component']].dropna(subset=['component'])
    elif algorithm == "Triangle Count":
        result_df = result_df[['source', 'triangle_count']].dropna(subset=['triangle_count'])

    # Supprimer les lignes où 'target' est None (pour visualisation)
    if 'target' in result_df.columns:
        result_df = result_df.dropna(subset=['target'])

    return result_df

# Interface Streamlit pour sélectionner un algorithme
st.subheader("Sélectionner un algorithme")
algorithm = st.selectbox(
    "Choisissez un algorithme à appliquer",
    ("PageRank", "Connected Components", "Triangle Count")
)

# Récupérer les noms des graphes disponibles
graph_names = query_neo4j("MATCH (n:Vertex) RETURN DISTINCT n.graph_name AS name")
if graph_names:
    # Afficher les graphes disponibles
    selected_graph = st.selectbox("Choisissez un graphe à analyser", [g['name'] for g in graph_names])

    if selected_graph:
        st.write(f"Analyse du graphe : {selected_graph}")
        df = query_graph_data(selected_graph, algorithm)

        # Exécuter l'algorithme sélectionné
        if algorithm == "PageRank":
            st.subheader("Résultats de PageRank")
            st.write(df[["source", "pagerank"]])
            visualize_graph(df, algorithm_name="PageRank")

        elif algorithm == "Connected Components":
            st.subheader("Composantes connexes")
            st.write(df[["source", "component"]])
            visualize_graph(df, algorithm_name="Connected Components")

        elif algorithm == "Triangle Count":
            st.subheader("Nombre de triangles")
            st.write(df[["source", "triangle_count"]])
            visualize_graph(df, algorithm_name="Triangle Count")
else:
    st.warning("Aucun graphe disponible dans la base de données Neo4j.")

# Fermer le driver Neo4j
driver.close()
