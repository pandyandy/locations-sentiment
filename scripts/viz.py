import streamlit as st
import plotly.express as px


def sentiment_color(val):
    color_map = {
        'Positive': 'color: #34A853',
        'Mixed': 'color: #FBBC05',
        'Negative': 'color: #EA4335',
        'Unknown': 'color: #B3B3B3'
    }
    return color_map.get(val, '')


def generate_html(label, main_value, sub_label, sub_value, always_show_subtext=False):
    if main_value != sub_value:
        subtext = f"{sub_label}: {sub_value}"
    elif always_show_subtext:
        subtext = f"{sub_label}: {sub_value}"
    else:
        subtext = sub_label 

    html_code = f"""
    <div style='text-align: center; color: #3A3A3A;'>
        <h1 style='font-size: 16px;'>{label}</h1>
        <span style='font-size: 38px;'>{main_value}</span>
        <p style='margin:0; color: #7D7D7D; font-size: 0.8em;'>{subtext}</p>
        <br>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

def metrics(location_count_total, review_count_total, avg_rating_total, filtered_data, show_pie=False):    
    # Metrics for all
    all_review_count = review_count_total
    all_avg_rating = avg_rating_total
    all_unique_locations = location_count_total
    
    # Metrics for filtered
    filtered_review_count = len(filtered_data)
    filtered_avg_rating = filtered_data['RATING'].mean() if filtered_review_count > 0 else 0
    filtered_unique_locations = filtered_data['PLACE_ID'].nunique()

    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            generate_html("📍 Locations", f"{filtered_unique_locations:,}", "out of", f"{all_unique_locations:,}", always_show_subtext=True)
        with col2:
            generate_html("📝 Reviews", f"{filtered_review_count:,}", "out of", f"{all_review_count:,}", always_show_subtext=True)
        with col3: 
            if show_pie:
                html_code = """
                    <div style='text-align: center; color: black;'>
                        <h1 style='font-size: 16px;'>😎 Sentiment Distribution</h1>
                    </div>
                    """
                st.markdown(html_code, unsafe_allow_html=True)

                word_rating_colors = {'Negative': '#EA4335', 'Mixed': '#FBBC05', 'Unknown': '#B3B3B3', 'Positive': '#34A853'}
                sentiment_counts = filtered_data['SENTIMENT'].value_counts()
                fig_sentiment_donut = px.pie(
                    sentiment_counts,
                    values=sentiment_counts.values,
                    names=[f"{count:,} ({percentage:.1f}%)" for count, percentage in zip(sentiment_counts.values, (sentiment_counts / sentiment_counts.sum() * 100).round(2))],
                    hole=0.3,
                    color=sentiment_counts.index,
                    color_discrete_map=word_rating_colors
                )

                fig_sentiment_donut.update_traces(textinfo='none', hoverinfo='skip')
                
                fig_sentiment_donut.update_layout(
                    height=120,
                    margin=dict(l=20, r=20, t=0, b=50),  
                    paper_bgcolor='rgba(0,0,0,0)',         
                    showlegend=True,                       
                    legend=dict(
                        orientation="h",                   
                        x=0.5,                             
                        xanchor="center",
                        y=-0.2,
                        yanchor="top"
                    ),
                    hovermode=False
                )
                st.plotly_chart(fig_sentiment_donut, use_container_width=True)
            else:
                generate_html("⭐️ Average Rating", f"{filtered_avg_rating:.2f}", "avg for all", f"{all_avg_rating:.2f}")
