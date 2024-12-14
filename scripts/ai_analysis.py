import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import plotly.express as px

from wordcloud import WordCloud
from scripts.viz import sentiment_color

def create_network_graph(attributes, slider_entities):
    # Get top entities by total attribute counts
    pivot_attrs = attributes.pivot(index='ENTITY', columns='ATTRIBUTE', values='COUNT').fillna(0)
    pivot_attrs['Total'] = pivot_attrs.sum(axis=1)
    top_entities = pivot_attrs.nlargest(slider_entities, 'Total').index.tolist()
    
    # Initialize graph and figure
    G = nx.Graph()
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Calculate entity positions in a circle
    entity_positions = calculate_entity_positions(top_entities)
    
    # Add nodes and edges to graph
    add_nodes_and_edges(G, top_entities, attributes)
    
    # Position attribute nodes
    pos = position_attribute_nodes(G, entity_positions)
    
    # Draw the network
    draw_network(G, pos, top_entities)
    
    # Configure plot
    ax.axis('off')
    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    
    return fig

def calculate_entity_positions(entities, radius=1.5):
    return {entity: (radius * np.cos(2 * np.pi * i / len(entities)), radius * np.sin(2 * np.pi * i / len(entities))) 
            for i, entity in enumerate(entities)}

def add_nodes_and_edges(G, top_entities, attributes):
    for entity in top_entities:
        G.add_node(entity, node_type='entity')
        entity_attrs = attributes[attributes['ENTITY'] == entity]
        
        for _, row in entity_attrs.iterrows():
            attr, count = row['ATTRIBUTE'], row['COUNT']
            G.add_node(attr, node_type='attribute') if attr not in G else None
            G.add_edge(entity, attr, weight=count)

def position_attribute_nodes(G, entity_positions, scale_factor=0.8):
    pos = entity_positions.copy()
    attr_nodes = [n for n in G.nodes() if n not in entity_positions]
    attr_connections = {attr: len([n for n in G.neighbors(attr) if n in entity_positions]) for attr in attr_nodes}
    attr_nodes.sort(key=lambda x: attr_connections[x], reverse=True)
    
    occupied_positions = []
    min_distance = 0.2

    for attr in attr_nodes:
        connected_entities = [n for n in G.neighbors(attr) if n in entity_positions]
        if connected_entities:
            attempts = 0
            while attempts < 50:
                if attr_connections[attr] > 1:
                    x, y = np.mean([entity_positions[e] for e in connected_entities], axis=0) * scale_factor
                    offset = 0.15 + (0.1 * attempts / 50)
                    angle = np.random.uniform(0, 2 * np.pi)
                    x += offset * np.cos(angle)
                    y += offset * np.sin(angle)
                else:
                    entity = connected_entities[0]
                    angle = 2 * np.pi * attempts / 50
                    radius = 0.25 + (0.1 * attempts / 50)
                    x = entity_positions[entity][0] + radius * np.cos(angle)
                    y = entity_positions[entity][1] + radius * np.sin(angle)

                position = (x, y)
                if all(np.sqrt((x - ox)**2 + (y - oy)**2) > min_distance for ox, oy in occupied_positions):
                    occupied_positions.append(position)
                    pos[attr] = position
                    break
                
                attempts += 1
            
            if attr not in pos:
                pos[attr] = position
                occupied_positions.append(position)

    return pos

def draw_network(G, pos, top_entities):
    attr_nodes = [n for n in G.nodes() if n not in top_entities]
    nx.draw_networkx_nodes(G, pos, nodelist=top_entities, node_color='#e6f2ff', node_size=2500)
    nx.draw_networkx_nodes(G, pos, nodelist=attr_nodes, node_color='#F2F2F2', node_size=1000, alpha=0.7)
    
    colors = plt.cm.rainbow(np.linspace(0, 1, len(top_entities)))
    for i, entity in enumerate(top_entities):
        entity_edges = [(u, v) for (u, v) in G.edges() if u == entity or v == entity]
        if entity_edges:
            edge_weights = [G[u][v]['weight'] for u, v in entity_edges]
            nx.draw_networkx_edges(G, pos, edgelist=entity_edges, 
                                     width=[w / max(edge_weights) * 2 for w in edge_weights],
                                     edge_color=[colors[i]], alpha=0.7)
    
    nx.draw_networkx_labels(G, pos, labels={node: node for node in top_entities}, font_size=10, font_color='#238dff', font_weight='600')
    nx.draw_networkx_labels(G, pos, labels={node: node for node in attr_nodes}, font_size=8)

@st.fragment
def display_network_graph(attributes):
    st.markdown("##### Entity-Attribute Relations")
    st.caption("_See up to top 10 mentioned entities and their attributes._")
    col1, col2 = st.columns([0.9, 0.1], vertical_alignment='center')
    num_entities = col2.number_input("Select the number of entities", min_value=1, max_value=10, value=5)
    fig = create_network_graph(attributes, num_entities)
    col1.pyplot(fig, use_container_width=True)


def ai_analysis(data, attributes):
    ## SENTIMENT COUNT BY DATE
    data['REVIEW_DATE'] = pd.to_datetime(data['REVIEW_DATE']).dt.date
    data = data[data['REVIEW_TEXT'].notna() & (data['REVIEW_TEXT'] != '')]
    avg_rating_per_day = data.groupby('REVIEW_DATE')['RATING'].mean().reset_index()
    color_scale = avg_rating_per_day['RATING'].apply(lambda x: '#EA4335' if x < 1.5 else '#e98f41' if x < 2.5 else '#FBBC05' if x < 3.6 else '#a5c553' if x < 4.5 else '#34A853').tolist()

    fig_avg_rating_per_day = px.line(
        avg_rating_per_day,
        x='REVIEW_DATE',
        y='RATING',
        labels={'RATING': 'Average Rating', 'REVIEW_DATE': 'Date'},
        title='Average Rating per Date',
        height=300
    )
    fig_avg_rating_per_day.update_traces(mode='lines+markers', hovertemplate='Avg Rating: %{y:.2f}<extra></extra>', line=dict(color='#E6E6E6'), marker=dict(color=color_scale))  
    fig_avg_rating_per_day.update_layout(xaxis_title=None, yaxis_title=None, hovermode='x')
    st.plotly_chart(fig_avg_rating_per_day, use_container_width=True)

    ## ENTITY-ATTRIBUTE RELATIONS
    st.divider()
    display_network_graph(attributes)


    ## REVIEW DETAILS
    st.markdown("##### Review Details")

    if data.empty:
        st.info("No reviews available for the selected filters.", icon=':material/info:')
        st.stop()

    columns = ['REVIEW_DATE', 'REVIEW_TEXT', 'RATING', 'SENTIMENT',  'CATEGORY', 'ADDRESS', 'REVIEWER_NAME', 'REVIEW_URL']
    st.dataframe(data[columns],
                #.style.map(sentiment_color, subset=["SENTIMENT"]),
                column_config={
                    'REVIEW_DATE': 'Date',
                    'RATING': 'Rating',
                    'REVIEW_TEXT': st.column_config.Column(
                        'Review',
                        width="large"),
                    'SENTIMENT': 'Sentiment',
                    'ADDRESS': st.column_config.Column(
                        'Location',
                        width="small"),
                    'CATEGORY': st.column_config.Column(
                        'Category',
                        width="medium"),
                    'REVIEWER_NAME': 'Author',
                    'REVIEW_URL': st.column_config.LinkColumn(
                        '🔗',
                        width='small',
                        help='Link to the review',
                        display_text='URL')
                },
                column_order=columns,
                hide_index=True, 
                use_container_width=True)
    
    st.markdown("##### Keywords")
    # Import the WordCloud class
    keywords_text = " ".join(data['KEYWORDS'].dropna().astype(str).values).replace("'", "")
    if keywords_text:  # Skip if there are no words in keywords_text
        wordcloud = WordCloud(width=2500, height=500, background_color='white', colormap='CMRmap_r').generate(keywords_text)
        # Create new figure and axis
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        
        st.pyplot(fig)
