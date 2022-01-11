#############
# LIBRARIES #
#############

from get_data import fetch_data # Module to fetch and process data
import pandas as pd
import numpy as np

import folium
import plotly

import streamlit as st

#############
# STREAMLIT #
#############

st.set_page_config(
    page_title = 'How Safe are NYC Streets',
    page_icon = './Assets/1024px-Circle-icons-bike.svg.png',
    layout = 'wide',
    initial_sidebar_state="expanded",
    menu_items={
         'Get Help': 'https://www.extremelycoolapp.com/help',
         'Report a bug': "https://www.extremelycoolapp.com/bug",
         'About': "This is a breakdown of every collision in NYC by location and injury. The data is collected as a result of the NYC Council passing Local Law #11 in 2011. Each record represents a collision in NYC by city, borough, precinct and cross street. This data can be used by the public to see how dangerous/safe intersections are in NYC. The information is presented in csv format to allow the user to do in-depth analyses."
     }
)


#################
# FETCHING DATA #
# ###############
@st.cache
def fetch_and_clean_data():
    collisions_df = fetch_data()
    return collisions_df

data = fetch_and_clean_data()


#################################
# TRANSFORMING DATA FOR METRICS #
##################################

collisions = data.copy()
last_updated = collisions['CRASH DATE'].max()

grouped_by_month = collisions.groupby(['CRASH YEAR', 'CRASH MONTH-YEAR']).agg({
    'COLLISION_ID': 'count',
    'NUMBER OF PERSONS INJURED': 'sum',
    'NUMBER OF PERSONS KILLED': 'sum',
    'NUMBER OF PEDESTRIANS INJURED': 'sum',
    'NUMBER OF PEDESTRIANS KILLED': 'sum',
    'NUMBER OF CYCLIST INJURED': 'sum',
    'NUMBER OF CYCLIST KILLED': 'sum',
    'NUMBER OF MOTORIST INJURED': 'sum',
    'NUMBER OF MOTORIST KILLED': 'sum'
})
grouped_by_month.reset_index(inplace=True)

# Grouping by Year to obtain the cummulative sum
grouped_by_month['collisions_cumsum'] = grouped_by_month.groupby(['CRASH YEAR'])['COLLISION_ID'].cumsum()

grouped_by_month['person_injured_cumsum'] = grouped_by_month.groupby(['CRASH YEAR'])['NUMBER OF PERSONS INJURED'].cumsum()
grouped_by_month['person_killed_cumsum'] = grouped_by_month.groupby(['CRASH YEAR'])['NUMBER OF PERSONS KILLED'].cumsum()

grouped_by_month['peds_injured_cumsum'] = grouped_by_month.groupby(['CRASH YEAR'])['NUMBER OF PEDESTRIANS INJURED'].cumsum()
grouped_by_month['peds_killed_cumsum'] = grouped_by_month.groupby(['CRASH YEAR'])['NUMBER OF PEDESTRIANS KILLED'].cumsum()

grouped_by_month['cyclist_injured_cumsum'] = grouped_by_month.groupby(['CRASH YEAR'])['NUMBER OF CYCLIST INJURED'].cumsum()
grouped_by_month['cyclist_killed_cumsum'] = grouped_by_month.groupby(['CRASH YEAR'])['NUMBER OF CYCLIST KILLED'].cumsum()
grouped_by_month.reset_index(inplace=True)

# Year to Date metrics
max_date = collisions['CRASH MONTH-YEAR'].max()

collisions_YTD = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == max_date]['collisions_cumsum']

# persons_injured_YTD = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == max_date]['person_injured_cumsum']
# persons_killed_YTD = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == max_date]['person_killed_cumsum']

peds_injured_YTD = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == max_date]['peds_injured_cumsum']
peds_killed_YTD = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == max_date]['peds_killed_cumsum']

cyclists_injured_YTD = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == max_date]['cyclist_injured_cumsum']
cyclists_killed_YTD = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == max_date]['cyclist_killed_cumsum']

# Previous YTD
last_year = max_date.to_timestamp() - pd.DateOffset(years=1)
last_YTD= last_year.to_period('M')

collisions_YTD_previous = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == last_YTD]['collisions_cumsum']

# persons_injured_YTD_previous = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == last_YTD]['person_injured_cumsum']
# persons_killed_YTD_previous = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == last_YTD]['person_killed_cumsum']

peds_injured_YTD_previous = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == last_YTD]['peds_injured_cumsum']
peds_killed_YTD_previous = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == last_YTD]['peds_killed_cumsum']

cyclists_injured_YTD_previous = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == last_YTD]['cyclist_injured_cumsum']
cyclists_killed_YTD_previous = grouped_by_month.loc[grouped_by_month['CRASH MONTH-YEAR'] == last_YTD]['cyclist_killed_cumsum']

# Percent Change YTD
collisions_perc_change = (collisions_YTD.values - collisions_YTD_previous.values)/collisions_YTD_previous.values*100

peds_injured_perc_change = (peds_injured_YTD.values - peds_injured_YTD_previous.values)/peds_injured_YTD_previous.values*100
peds_killed_perc_change = (peds_killed_YTD.values - peds_killed_YTD_previous.values)/peds_killed_YTD_previous.values*100

cyclists_injured_perc_change = (cyclists_injured_YTD.values - cyclists_injured_YTD_previous.values)/cyclists_injured_YTD_previous.values*100
cyclists_killed_perc_change = (cyclists_killed_YTD.values - cyclists_killed_YTD_previous.values)/cyclists_killed_YTD_previous.values*100


#############
# FRONT END #
#############

st.title('How Safe are NYC Streets?')
st.image('./Assets/Bike_Path-scaled.jpeg', caption=None, width='auto', use_column_width=True)
st.caption(f'Data through {last_updated.strftime("%m/%d/%Y")}')

### TOP ROW
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric('Vehicle Collisions (YTD)', collisions_YTD, f'{round(collisions_perc_change[0], 0)}%')
col2.metric("Pedestrians Injured (YTD)", peds_injured_YTD, f'{round(peds_injured_perc_change[0], 0)}%')
col3.metric("Pedestrians Killed (YTD)", peds_killed_YTD, f'{round(peds_killed_perc_change[0], 0)}%')
col4.metric("Cyclists Injured (YTD)", cyclists_injured_YTD, f'{round(cyclists_injured_perc_change[0], 0)}%')
col5.metric("Cyclists Killed (YTD)", cyclists_killed_YTD, f'{round(cyclists_killed_perc_change[0], 0)}%')

# st.dataframe(data)

st.sidebar.subheader("About")
st.sidebar.write()
st.sidebar.text('Dashboard created by Roger Lefort')

