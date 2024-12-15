import streamlit as st
import pandas as pd

from scripts.openai import generate_response
from scripts.sapi import write_table

def sentiment_color(val):
    color_map = {
        'Positive': 'color: #34A853',
        'Mixed': 'color: #FBBC05',
        'Negative': 'color: #EA4335',
        'Unknown': 'color: #B3B3B3'
    }
    return color_map.get(val, '')


def support(data, reviews_data):
    st.markdown("<br>", unsafe_allow_html=True)
    
    if data.empty:
        st.info('No reviews with feedback text available for the selected filters.', icon=':material/info:')
        st.stop()
    data['SELECT'] = [True] + [False] * (len(data) - 1)
    #filtered_review_data_detailed['RATING'] = filtered_review_data_detailed['RATING'].astype(int)
    data['CUSTOMER_SUCCESS_NOTES'] = data['CUSTOMER_SUCCESS_NOTES'].fillna('')
    df_to_edit = st.data_editor(
        data[['SELECT', 'REVIEW_ID','REVIEWER_NAME', 'SENTIMENT', 'REVIEW_TEXT', 'RATING', 'ADDRESS',
                                    'REVIEW_DATE', 'CUSTOMER_SUCCESS_NOTES', 'REVIEW_URL', 'STATUS', 'RESPONSE']].style.map(sentiment_color, subset=["SENTIMENT"]),
        column_order=('SELECT', 'REVIEW_DATE', 'REVIEWER_NAME', 'RATING', 'REVIEW_TEXT', 'SENTIMENT', 'STATUS', 'ADDRESS', 'REVIEW_URL', 'RESPONSE', 'CUSTOMER_SUCCESS_NOTES'), 
        column_config={
            'SELECT': 'Select',
            'REVIEW_DATE': 'Date',
            'REVIEWER_NAME': st.column_config.Column(
                        "Author",
                        width="small"),
                    'RATING': st.column_config.Column(
                        "Rating",
                        width="small"),
                    'REVIEW_TEXT': st.column_config.Column(
                        'Review',
                        width="large"),
                    'SENTIMENT': 'Sentiment',
                    'STATUS': st.column_config.SelectboxColumn(
                        'Status',
                        help="The status of the review",
                        width="small",
                        options=[
                            '🌱 New',
                            '✔️ Resolved',
                            '🚫 Spam',
                        ]),
                    'ADDRESS': st.column_config.Column(
                        "Location",
                        width="medium"),
                    'REVIEW_URL': st.column_config.LinkColumn(
                         '🔗',
                         width='small',
                         help='Link to the review',
                         display_text='URL'),
                    'RESPONSE': 'Response',
                    'CUSTOMER_SUCCESS_NOTES': 'Customer Success Notes'
                    },
        disabled=['SENTIMENT', 'REVIEW_TEXT', 'RATING', 'REVIEW_DATE', 'REVIEWER_NAME', 'ADDRESS', 'REVIEW_URL', 'RESPONSE'],
        use_container_width=True, 
        hide_index=True
    )
    
    selected_sum = df_to_edit['SELECT'].sum()

    if selected_sum == 1:
        selected_review = df_to_edit.loc[df_to_edit['SELECT'] == True].iloc[0]
        review_text = selected_review['REVIEW_TEXT']
        author_name = selected_review['REVIEWER_NAME']
        prompt = f"""
Jsi manažer sociálních sítí ČSOB. Vytvoř stručnou (3-5 vět), profesionální odpověď na recenzi níže. Kde je to vhodné, uznej konkrétní detaily z recenze, aby odpověď byla personalizovaná. Začni pozdravem, zaměř se na řešení zpětné vazby a nabídni následné kroky. Nezahrnuj žádný jiný text nebo komentáře. Vrať pouze odpověď.

Recenze:
{review_text}

Autor: {author_name}
"""
        col8, col9 = st.columns(2, gap='medium', vertical_alignment='top')
        with col8:
            st.write(f'**Selected Review**')
            with st.container(border=True, height=170):
                col1, col2 = st.columns([0.05, 0.95], gap='medium')
                col1.write('🧑🏻')
                col2.write(f'{review_text}')
            col1, col2 = st.columns(2)
            placeholder = col2.empty()

        if placeholder.button('💬 Generate Response', use_container_width=True):
            if review_text in st.session_state['generated_responses']:
                response = st.session_state['generated_responses'][review_text]
            else:
                with st.spinner(':robot_face: Generating response, please wait...'):
                    response = generate_response(prompt)
                if response:
                    st.session_state['generated_responses'][review_text] = response
                else:
                    response = ''

        if review_text in st.session_state['generated_responses']:
            with col9:
                st.write(f'**Response Draft**')
                edited_response = st.text_area("Response Draft", st.session_state['generated_responses'][review_text], label_visibility='collapsed', height=170)
                col1, col2, col3 = st.columns(3)
                
                if col3.button('🔄 Regenerate', use_container_width=True):
                    st.session_state.regenerate_clicked = True

                if st.session_state.regenerate_clicked:
                    instruction = st.text_input("Additional instructions:", 
                                              key="regen_instruction",
                                              value=st.session_state.instruction)
                    
                    if instruction:
                        st.session_state.instruction = instruction
                        with st.spinner(':robot_face: Regenerating response, please wait...'):
                            new_prompt = f"""
Původní úkol:
{prompt}

Předchozí odpověď: {st.session_state['generated_responses'][review_text]}

Další instrukce: {instruction}

Prosím, aktualizuj odpověď.
"""
                            response = generate_response(new_prompt)
                            if response:
                                st.session_state['generated_responses'][review_text] = response
                                st.session_state.regenerate_clicked = False
                                st.session_state.instruction = ''
                                st.rerun()
        
                if col3.button('💾 Save response', use_container_width=True):
                    review_id = selected_review['REVIEW_ID']
                    data['RESPONSE'] = data['RESPONSE'].astype('object')
                    data.loc[data['REVIEW_ID'] == review_id, 'RESPONSE'] = edited_response
                    
                    try:
                        update_df = pd.DataFrame({
                            'REVIEW_ID': [review_id],
                            'RESPONSE': [edited_response],
                            'STATUS': ['✔️ Resolved'] if selected_review['STATUS'] == '🌱 New' else [selected_review['STATUS']],
                            'CUSTOMER_SUCCESS_NOTES': [selected_review['CUSTOMER_SUCCESS_NOTES']]
                        })
                        update_df['RESPONSE'] = update_df['RESPONSE'].astype(str)
                        update_df['STATUS'] = update_df['STATUS'].astype(str)
                        update_df['CUSTOMER_SUCCESS_NOTES'] = update_df['CUSTOMER_SUCCESS_NOTES'].astype(str)
                        
                        reviews_data.loc[reviews_data['REVIEW_ID'] == review_id, ['RESPONSE', 'STATUS', 'CUSTOMER_SUCCESS_NOTES']] = [
                            update_df['RESPONSE'].iloc[0],
                            update_df['STATUS'].iloc[0], 
                            update_df['CUSTOMER_SUCCESS_NOTES'].iloc[0]
                        ]
                        
                        update_df = reviews_data[reviews_data['REVIEW_ID'] == review_id].copy()
                        write_table(st.secrets['reviews_path'], update_df, is_incremental=True)
                        st.success('Response saved successfully!')
                    except Exception as e:
                        st.error(f'Failed to save response: {str(e)}')
                        
    elif selected_sum > 1:
        st.info('Select only one review to generate a response.')
    else:
        st.info('Select the review you want to respond to in the table above.')