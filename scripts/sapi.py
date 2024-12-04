import streamlit as st
import pandas as pd
import os

from kbcstorage.client import Client, Files
from keboola_streamlit import KeboolaStreamlit

kbc_client = Client(st.secrets['kbc_url'], st.secrets['KEBOOLA_TOKEN'])

@st.cache_data(show_spinner='Loading data... 📊')
def read_data(table_name):
    keboola = KeboolaStreamlit(st.secrets['kbc_url'], st.secrets['KEBOOLA_TOKEN'])
    df = keboola.read_table(table_name)
    return df

def write_table(table_id: str, df: pd.DataFrame, is_incremental: bool = False):    
    csv_path = f'{table_id}.csv'
    try:
        df.to_csv(csv_path, index=False)
        
        files = Files(st.secrets['kbc_url'], st.secrets['KEBOOLA_TOKEN'])
        file_id = files.upload_file(file_path=csv_path, tags=['file-import'],
                                    do_notify=False, is_public=False)
        job = kbc_client.tables.load_raw(table_id=table_id, data_file_id=file_id, is_incremental=is_incremental)
        
    except Exception as e:
        st.error(f'Data upload failed with: {str(e)}')
    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)
    return job