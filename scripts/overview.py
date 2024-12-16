import streamlit as st
import pandas as pd
import plotly.express as px

rating_colors_index = {'0': '#B3B3B3', '1': '#EA4335', '2': '#e98f41', '3': '#FBBC05', '4': '#a5c553', '5': '#34A853'}
rating_colors = {0: '#B3B3B3', 1: '#EA4335', 2: '#e98f41', 3: '#FBBC05', 4: '#a5c553', 5: '#34A853'}

def overview(data):
    data_rating_sorted = (
        data
        .sort_values(by='REVIEW_DATE') 
        .groupby(['PLACE_ID', 'ADDRESS', 'PLACE_TOTAL_SCORE', 'PLACE_URL']) 
        .agg({'RATING': [lambda x: x.tolist(), 'count']})   
        .reset_index()  
        .sort_values(by=['PLACE_TOTAL_SCORE', ('RATING', 'count')], ascending=[False, False])  
    )
    data_rating_sorted.columns = ['PLACE_ID', 'ADDRESS', 'PLACE_TOTAL_SCORE', 'PLACE_URL', 'RATING', 'COUNT']

    ## RATING DISTRIBUTION FOR TOP/BOTTOM X    
    col1, col2 = st.columns([0.8, 0.2], vertical_alignment='center', gap='small')
    with col2:
        st.caption("Select the number of locations")
        top_x = st.slider("Locations", min_value=1, max_value=20, value=5, label_visibility='collapsed')
        min_count = data_rating_sorted['COUNT'].min()
        max_count = data_rating_sorted['COUNT'].max()
        st.caption("Select the minimum number of reviews")   
        num_reviews = st.number_input("Reviews", min_value=min_count, max_value=max_count, value=min_count, label_visibility='collapsed')
    
    with col1:
        top_locations = data_rating_sorted[data_rating_sorted['COUNT'] >= num_reviews].head(top_x)
        top_rating_distribution = top_locations['RATING'].apply(lambda ratings: pd.Series(ratings).value_counts(normalize=True).reindex([1, 2, 3, 4, 5], fill_value=0)).fillna(0)
        top_rating_distribution.index = top_locations['ADDRESS']
        top_rating_distribution = top_rating_distribution.sort_index(axis=1, ascending=False).iloc[::-1]

        fig_top = px.bar(
            top_rating_distribution,
            x=top_rating_distribution.columns,
            y=top_rating_distribution.index,
            orientation='h',
            labels={'value': 'Percentage', 'index': 'Location', 'rating': 'Rating', 'variable': 'Rating'},
            title=f'Rating Distribution',
            color_discrete_map=rating_colors_index
        )
        fig_top.update_traces(hovertemplate='%{x:.2%}<extra></extra>')
        fig_top.update_layout(
            showlegend=False, 
            xaxis_title=None, 
            yaxis_title=None, 
            xaxis_tickformat='.0%',
            xaxis={'showticklabels': False},
            yaxis={'tickvals': top_rating_distribution.index, 'ticktext': top_rating_distribution.index}
        )
        st.plotly_chart(fig_top, use_container_width=True)

    st.dataframe(
        data_rating_sorted[data_rating_sorted['COUNT'] >= num_reviews],
        column_order=('PLACE_TOTAL_SCORE', 'ADDRESS', 'RATING', 'COUNT', 'PLACE_URL'),
        column_config={
            "PLACE_TOTAL_SCORE": st.column_config.ProgressColumn(
                "Location Rating",
                width="small",
                help="The total rating of the location",
                format="⭐️ %.1f",
                max_value=5
            ),
            "ADDRESS": st.column_config.Column(
                "Location",
                width="medium",
            ),
            "RATING": st.column_config.LineChartColumn(
                "Rating over Time",
                width="large",
                help="The rating of collected reviews for the location over time",
                y_min=1,
                y_max=5,
            ),
            "COUNT": st.column_config.Column("# of Reviews",
                width="small",
                help="The number of collected reviews for the location"
            ),
            "PLACE_URL": st.column_config.LinkColumn(
                '🔗',
                width='small',
                help='Link to the location',
                display_text='URL')
        },
        hide_index=True, 
        use_container_width=True)
    
    col1, col2 = st.columns([0.2, 0.8], gap='medium', vertical_alignment='top')
    ## COUNT OF RATINGS
    with col1: 
        rating_counts = data['RATING'].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)

        fig_ratings = (
            px.bar(x=rating_counts.values,
                   y=rating_counts.index,
                   orientation='h',
                   labels={'x': 'Count', 'y': 'Rating'},
                   title='Count of Ratings',
                   text=rating_counts.values,
                   color=rating_counts.index.map(rating_colors),
                   color_discrete_map='identity')
            .update_traces(textposition='inside', textfont_color='white', texttemplate='%{text:,}')
            .update_layout(xaxis_title=None, hovermode=False)
            .update_yaxes(title_text=None)
        )
        st.plotly_chart(fig_ratings, use_container_width=True)
    
    ## COUNT OF RATINGS PER DAY
    with col2:
        data['REVIEW_DATE'] = pd.to_datetime(data['REVIEW_DATE']).dt.date
        count_ratings_per_day = data.groupby(['REVIEW_DATE', 'RATING']).size().reset_index(name='COUNT')
        count_ratings_per_day['RATING'] = count_ratings_per_day['RATING'].astype(str)
        count_ratings_per_day = count_ratings_per_day.sort_values(by='RATING')

        fig_count_ratings = px.bar(
            count_ratings_per_day,
            x='REVIEW_DATE',
            y='COUNT',
            color='RATING',
            labels={'COUNT': 'Count', 'RATING': 'Rating', 'REVIEW_DATE': 'Date'},
            title='Count of Ratings Per Day Across All Selected Locations',
            color_discrete_map=rating_colors_index,
            opacity=0.8
        )

        fig_count_ratings.update_traces(hovertemplate='Count: %{y}<extra></extra>')
        fig_count_ratings.update_layout(xaxis_title=None, showlegend=False, hovermode='x')
        st.plotly_chart(fig_count_ratings, use_container_width=True)