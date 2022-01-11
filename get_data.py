import os
import requests
import numpy as np
import pyarrow.parquet as pq
from pyarrow import csv, parquet
import datetime
import pandas as pd


def fetch_data():
    data_path = r'./Data/'
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    # Fetching new data
    URL = 'https://data.cityofnewyork.us/api/views/h9gi-nx95/rows.csv?accessType=DOWNLOAD' # URL to fetch data in csv format
    r = requests.get(URL, allow_redirects=True)
    open(os.path.join(data_path, 'collisions.csv'), 'wb').write(r.content) # Downloading csv

    collisions_csv = csv.read_csv(os.path.join(data_path, 'collisions.csv')) # Opening downloaded csv with pyarrow
    parquet.write_table(collisions_csv, os.path.join(data_path, 'collisions.parquet')) # Saving csv as parquet file
    collisions_pq = pq.read_table(os.path.join(data_path, 'collisions.parquet'))
    if (os.path.join(data_path, 'collisions.parquet')):
        print('Data successfully downloaded and processed!')
    else:
        print('Error in processing data!')
    os.remove(os.path.join(data_path, 'collisions.csv'))
    collisions_df = collisions_pq.to_pandas()
    
    # Cleaning dataset: replacing values identified as erroneous; update as more errors are identified
    collisions_df.replace({
                            'unknown': np.nan,
                            'Unknown': np.nan,
                            '': np.nan, 
                            'Unspecified' : np.nan, 
                            'unspecified' : np.nan, 
                            '80': np.nan, 
                            '1': np.nan, 
                            'Illnes': 'Illness',
                            'Drugs (illegal)': 'Drugs (Illegal)'
                            }, inplace=True)
    collisions_df.drop(['LOCATION', 'ON STREET NAME', 'CROSS STREET NAME', 'OFF STREET NAME', 'VEHICLE TYPE CODE 1', 'VEHICLE TYPE CODE 2', 'VEHICLE TYPE CODE 3', 'VEHICLE TYPE CODE 4', 'VEHICLE TYPE CODE 5', 'CONTRIBUTING FACTOR VEHICLE 2', 'CONTRIBUTING FACTOR VEHICLE 3', 'CONTRIBUTING FACTOR VEHICLE 4', 'CONTRIBUTING FACTOR VEHICLE 5'], axis=1, inplace=True)
    # collisions_df.dropna(inplace=True) # Dropping all rows with missing values; may revist this later to augment data

    # Creating new columns for analysis
    collisions_df['CRASH DATE'] = pd.to_datetime(collisions_df['CRASH DATE'])
    collisions_df['CRASH YEAR'] = pd.DatetimeIndex(collisions_df['CRASH DATE']).year
    collisions_df['CRASH MONTH-YEAR'] = pd.to_datetime(collisions_df['CRASH DATE']).dt.to_period('M')
    collisions_df['CRASH TIME'] = pd.to_datetime(collisions_df['CRASH TIME'])
    collisions_df['CRASH HOUR'] = pd.DatetimeIndex(collisions_df['CRASH TIME']).hour


    return collisions_df    

def main():
    fetch_data()

if __name__ == "__main__":
    main()


