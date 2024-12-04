import streamlit as st
import pandas as pd
import pydeck as pdk

def get_color(rating):
    if rating <= 1:
        return [234, 67, 53, 255]
    elif rating <= 2:
        return [233, 143, 65, 255]
    elif rating <= 3:
        return [251, 189, 5, 255]
    elif rating <= 4:
        return [165, 197, 83, 255]
    else:
        return [52, 168, 83, 255]

def locations(data):
    map_data = data.groupby(['ADDRESS', 'LATITUDE', 'LONGITUDE', 'COUNTRY_CODE', 'PLACE_TOTAL_SCORE']).agg({
        'REVIEW_ID': 'count',
        'RATING': 'mean'
    }).reset_index().rename(columns={'REVIEW_ID': 'COUNT'})
    if map_data.empty:
        st.info("No map data available.", icon=':material/info:')
        st.stop()
    
    map_data['RATING'] = map_data['RATING'].round(2)
    state_reviews = map_data.groupby('COUNTRY_CODE')['COUNT'].sum().reset_index()
    state_reviews = state_reviews.sort_values('COUNT', ascending=False)
    state_with_most_reviews = state_reviews.iloc[0]['COUNTRY_CODE']
    state_coords = map_data[map_data['COUNTRY_CODE'] == state_with_most_reviews].agg({
        'LATITUDE': 'mean',
        'LONGITUDE': 'mean'
    })

    center_lat = state_coords['LATITUDE']
    center_long = state_coords['LONGITUDE']

    map_data['color'] = map_data['RATING'].apply(get_color)
    
    column_layer = pdk.Layer(
        "ColumnLayer",
        data=map_data,
        disk_resolution=12,
        radius=800,
        elevation_scale = 500,
        get_position=["LONGITUDE", "LATITUDE"],
        get_color="color",
        get_elevation="COUNT",
        pickable=True
    )

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_long,
        zoom=8,
        pitch=50
    )

    deck = pdk.Deck(
        initial_view_state=view_state,
        map_style=None,
        layers=[column_layer],
        tooltip={
            "text": "Location: {ADDRESS}\nLocation Rating: {PLACE_TOTAL_SCORE}\nCollected Reviews: {COUNT}\nAvg Review Rating: {RATING}",
            "style": {
                "backgroundColor": "white",
                "color": "black",
                "fontSize": "16px"
            }
        }
    )
    st.pydeck_chart(deck, use_container_width=True, height=700)
    st.caption("_The height of the column represents the number of collected reviews, the color represents the average rating._")
