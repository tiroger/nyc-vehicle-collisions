import os
# import requests
import numpy as np
# import pyarrow.parquet as pq
# from pyarrow import csv, parquet
from pyarrow.csv import read_csv, ParseOptions, ConvertOptions, ReadOptions
import datetime
import pandas as pd
from sodapy import Socrata

import streamlit as st
# import config
APP_TOKEN = st.secrets['SOCRATA_APP_TOKEN']
# APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN")


# def fetch_data():
#     data_path = r'./Data/'
#     if not os.path.exists(data_path):
#         os.makedirs(data_path)

#     # # Fetching new data
#     # URL = f'https://data.cityofnewyork.us/resource/h9gi-nx95.csv?$$app_token={APP_TOKEN}&$limit=100000'
#     URL = 'https://data.cityofnewyork.us/api/views/h9gi-nx95/rows.csv?accessType=DOWNLOAD' # URL to fetch data in csv format
#     r = requests.get(URL, allow_redirects=True)
#     open(os.path.join(data_path, 'collisions.csv'), 'wb').write(r.content) # Downloading csv

#     parse_options = ParseOptions(ignore_empty_lines=True)
#     collisions_csv = csv.read_csv(os.path.join(data_path, 'collisions.csv'), parse_options=parse_options) # Opening downloaded csv with pyarrow
#     parquet.write_table(collisions_csv, os.path.join(data_path, 'collisions.parquet')) # Saving csv as parquet file
#     collisions_pq = pq.read_table(os.path.join(data_path, 'collisions.parquet'))
#     if (os.path.join(data_path, 'collisions.parquet')):
#         print('Data successfully downloaded and processed!')
#     else:
#         print('Error in processing data!')
#     os.remove(os.path.join(data_path, 'collisions.csv'))
#     collisions_df = collisions_pq.to_pandas()
    
#     # Cleaning dataset: replacing values identified as erroneous; update as more errors are identified
#     collisions_df.columns = collisions_df.columns.str.replace(' ','_').str.lower()
#     collisions_df.drop(['location', 'on_street_name', 'cross_street_name', 'off_street_name', 'vehicle_type_code_1', 'vehicle_type_code_2', 'vehicle_type_code_3', 'vehicle_type_code_4', 'vehicle_type_code_5', 'contributing_factor_vehicle_2', 'contributing_factor_vehicle_3', 'contributing_factor_vehicle_4', 'contributing_factor_vehicle_5'], axis=1, inplace=True)
#     # collisions_df.dropna(inplace=True) # Dropping all rows with missing values; may revist this later to augment data

#     # Creating new columns for analysis
#     collisions_df['crash_date'] = pd.to_datetime(collisions_df['crash_date'])
#     collisions_df['crash_year'] = pd.DatetimeIndex(collisions_df['crash_date']).year
#     collisions_df['crash_month_year'] = pd.to_datetime(collisions_df['crash_date']).dt.to_period('M')
#     collisions_df['crash_time'] = pd.to_datetime(collisions_df['crash_time'])
#     collisions_df['crash_hour'] = pd.DatetimeIndex(collisions_df['crash_time']).hour

#     collisions_df.number_of_persons_injured.fillna(0, inplace=True)
#     collisions_df.number_of_persons_killed.fillna(0, inplace=True)
#     collisions_df.number_of_pedestrians_injured.fillna(0, inplace=True)
#     collisions_df.number_of_pedestrians_killed.fillna(0, inplace=True)
#     collisions_df.number_of_cyclist_injured.fillna(0, inplace=True)
#     collisions_df.number_of_cyclist_killed.fillna(0, inplace=True)
#     collisions_df.number_of_motorist_injured.fillna(0, inplace=True)
#     collisions_df.number_of_motorist_killed.fillna(0, inplace=True)

#     # Converting objects to int
#     cols_to_convert = ['number_of_persons_injured', 'number_of_persons_killed',
#         'number_of_pedestrians_injured', 'number_of_pedestrians_killed',
#         'number_of_cyclist_injured', 'number_of_cyclist_killed',
#         'number_of_motorist_injured', 'number_of_motorist_killed']
#     collisions_df[cols_to_convert] = collisions_df[cols_to_convert].astype(int)


# USING SODAPY

def fetch_data():
    ################################
    # FETCHING AND PROCESSING DATA #
    ################################

    client = Socrata("data.cityofnewyork.us", APP_TOKEN)

    # Example authenticated client (needed for non-public datasets):
    # client = Socrata(data.cityofnewyork.us,
    #                  MyAppToken,
    #                  userame="user@example.com",
    #                  password="AFakePassword")

    # First 100 for testing results, returned as JSON from API / converted to Python list of
    # Change to get_all to fetch entire dataset
    # dictionaries by sodapy.
    # results = client.get_all("h9gi-nx95")
    results = client.get("h9gi-nx95", offset=1400000,limit=2000000, order="crash_date")
    # Convert to pandas DataFrame
    results_df = pd.DataFrame.from_records(results)


    # Cleaning dataset: replacing values identified as erroneous; update as more errors are identified
    results_df.replace({
                            'unknown': np.nan,
                            'Unknown': np.nan,
                            '': np.nan, 
                            'Unspecified' : np.nan, 
                            'unspecified' : np.nan, 
                            'Illnes': 'Illness',
                            'Drugs (illegal)': 'Drugs (Illegal)'
                            }, inplace=True)
    results_df.drop(['location', 'on_street_name', 'cross_street_name', 'off_street_name', 'vehicle_type_code1', 'vehicle_type_code2', 'vehicle_type_code_3', 'vehicle_type_code_4', 'vehicle_type_code_5', 'contributing_factor_vehicle_2', 'contributing_factor_vehicle_3', 'contributing_factor_vehicle_4', 'contributing_factor_vehicle_5'], axis=1, inplace=True)
    # collisions_df.dropna(inplace=True) # Dropping all rows with missing values; may revist this later to augment data

    # Creating new columns for analysis
    results_df['crash_date'] = pd.to_datetime(results_df['crash_date'])
    results_df['crash_year'] = pd.DatetimeIndex(results_df['crash_date']).year
    results_df['crash_month'] = pd.DatetimeIndex(results_df['crash_date']).month
    results_df['crash_month_year'] = pd.to_datetime(results_df['crash_date']).dt.to_period('M')
    results_df['crash_time'] = pd.to_datetime(results_df['crash_time'])
    results_df['crash_hour'] = pd.DatetimeIndex(results_df['crash_time']).hour

    results_df.number_of_persons_injured.fillna(0, inplace=True)
    results_df.number_of_persons_killed.fillna(0, inplace=True)
    results_df.number_of_pedestrians_injured.fillna(0, inplace=True)
    results_df.number_of_pedestrians_killed.fillna(0, inplace=True)
    results_df.number_of_cyclist_injured.fillna(0, inplace=True)
    results_df.number_of_cyclist_killed.fillna(0, inplace=True)
    results_df.number_of_motorist_injured.fillna(0, inplace=True)
    results_df.number_of_motorist_killed.fillna(0, inplace=True)

    # Converting objects to int
    cols_to_convert = ['number_of_persons_injured', 'number_of_persons_killed',
        'number_of_pedestrians_injured', 'number_of_pedestrians_killed',
        'number_of_cyclist_injured', 'number_of_cyclist_killed',
        'number_of_motorist_injured', 'number_of_motorist_killed']
    results_df[cols_to_convert] = results_df[cols_to_convert].astype(int)
    client.close()


    return results_df    

def main():
    fetch_data()

if __name__ == "__main__":
    main()


