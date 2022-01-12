#############
# LIBRARIES #
#############

from get_data import fetch_data # Module to fetch and process data
import pandas as pd
import numpy as np

import folium
from folium.features import CustomIcon
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import plotly
import datetime

from PIL import Image

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

@st.cache(show_spinner=False)
def fetch_and_clean_data():
    with st.spinner('Data Refreshing... May take up to 5 minutes.'):
        collisions_df = fetch_data()
        return collisions_df

data = fetch_and_clean_data()


#################################
# TRANSFORMING DATA FOR METRICS #
##################################

data_start_date = '2018-12-31' # Limiting data to from 2020 to present day


collisions = data.copy()

collisions = collisions[collisions['crash_date'] > data_start_date]

last_updated = collisions['crash_date'].max()
first_date = collisions['crash_date'].min()

grouped_by_day = collisions.groupby(['crash_year', 'crash_date']).agg({
    'collision_id': 'count',
    'number_of_persons_injured': 'sum',
    'number_of_persons_killed': 'sum',
    'number_of_pedestrians_injured': 'sum',
    'number_of_pedestrians_killed': 'sum',
    'number_of_cyclist_injured': 'sum',
    'number_of_cyclist_killed': 'sum',
    'number_of_motorist_injured': 'sum',
    'number_of_motorist_killed': 'sum'
})
grouped_by_day.reset_index(inplace=True)

# Grouping by Year to obtain the cummulative sum
grouped_by_day['collisions_cumsum'] = grouped_by_day.groupby(['crash_year'])['collision_id'].cumsum()

grouped_by_day['person_injured_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_persons_injured'].cumsum()
grouped_by_day['person_killed_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_persons_killed'].cumsum()

grouped_by_day['peds_injured_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_pedestrians_injured'].cumsum()
grouped_by_day['peds_killed_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_pedestrians_killed'].cumsum()

grouped_by_day['cyclist_injured_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_cyclist_injured'].cumsum()
grouped_by_day['cyclist_killed_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_cyclist_killed'].cumsum()
grouped_by_day.reset_index(inplace=True)

# Year to Date metrics
max_date = collisions['crash_date'].max()

collisions_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['collisions_cumsum']

# persons_injured_YTD = grouped_by_month.loc[grouped_by_month['crash_month_year'] == max_date]['person_injured_cumsum']
# persons_killed_YTD = grouped_by_month.loc[grouped_by_month['crash_month_year'] == max_date]['person_killed_cumsum']

peds_injured_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['peds_injured_cumsum']
peds_killed_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['peds_killed_cumsum']

cyclists_injured_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['cyclist_injured_cumsum']
cyclists_killed_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['cyclist_killed_cumsum']

# Previous YTD
last_year = max_date - pd.DateOffset(years=1)
last_YTD = last_year

collisions_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['collisions_cumsum']

# persons_injured_YTD_previous = grouped_by_month.loc[grouped_by_month['crash_month_year'] == last_YTD]['person_injured_cumsum']
# persons_killed_YTD_previous = grouped_by_month.loc[grouped_by_month['crash_month_year'] == last_YTD]['person_killed_cumsum']

peds_injured_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['peds_injured_cumsum']
peds_killed_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['peds_killed_cumsum']

cyclists_injured_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['cyclist_injured_cumsum']
cyclists_killed_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['cyclist_killed_cumsum']

# Percent Change YTD
collisions_perc_change = (collisions_YTD.values - collisions_YTD_previous.values)/collisions_YTD_previous.values*100

peds_injured_perc_change = (peds_injured_YTD.values - peds_injured_YTD_previous.values)/peds_injured_YTD_previous.values*100
peds_killed_perc_change = (peds_killed_YTD.values - peds_killed_YTD_previous.values)/peds_killed_YTD_previous.values*100

cyclists_injured_perc_change = (cyclists_injured_YTD.values - cyclists_injured_YTD_previous.values)/cyclists_injured_YTD_previous.values*100
cyclists_killed_perc_change = (cyclists_killed_YTD.values - cyclists_killed_YTD_previous.values)/cyclists_killed_YTD_previous.values*100

####################
# DATA FOR MAPPING #
####################

##########################
# COLLISIONS IN PAST DAY #
##########################

# latest_collision_date = data.crash_date.max()



def map_collisions(latest_collision_date):
    latest_collision_date_df = data[data['crash_date'] == latest_collision_date].dropna()
    locations = zip(latest_collision_date_df.latitude, latest_collision_date_df.longitude)
    # Initializing a new map centered around NYC
    collision_map = folium.Map(location=[40.7128, -74.0060], zoom_start=10, dragging=True, scrollWheelZoom=True, tiles='cartodbpositron')

    # Adding maps layers
    tooltip = "Click for more info!"
    for (_, row) in latest_collision_date_df.iterrows(): # Iterrating through all teams
        
        icon = './Assets/traffic-accident.png'
        icon_image = Image.open(icon)
        
        icon = CustomIcon(
        np.array(icon_image),
        icon_size=(20, 20),
        popup_anchor=(0, -30),
        )
        html = '<i>Cause of Collision: </i>' + '<b>' + row.loc['contributing_factor_vehicle_1'] + '</b>' + '<br>' + '</b>' '<i>Number of Persons Injured: </i>' + '<b>' + str(row.loc['number_of_persons_injured']) + '</b>' + '<br>' + '</b>' '<i>Number of Persons Killed: </i>' + '<b>' + str(row.loc['number_of_persons_killed']) + '</b>'
        iframe = folium.IFrame(html=html, width=330, height=100)
        popup = folium.Popup(iframe, max_width=330, min_height=100)
        
        folium.Marker(location=[row.loc['latitude'], row.loc['longitude']], icon=icon, popup=popup, tooltip=tooltip).add_to(collision_map)
        
    HeatMap(locations).add_to(collision_map)
    locations = zip(latest_collision_date_df.latitude, latest_collision_date_df.longitude)

    folium_static(collision_map, width=1000)




#############
# FRONT END #
#############

st.title('How Safe are NYC Streets?')
st.image('./Assets/OPS-0333-Crossride-Illustration_FINAL.jpeg', caption=None, width='auto', use_column_width=True)
st.caption(f'Data between {first_date.strftime("%m/%d/%Y")} and {last_updated.strftime("%m/%d/%Y")}')

### TOP ROW
st.markdown(f'### NYC Vehicle Collision Statistics Year-to-Date (YTD) through {last_updated.strftime("%Y-%m-%d")}')
col1, col2, col3, col4, col5 = st.columns(5)

# col1.metric('Vehicle Collisions (YTD)', collisions_YTD, f'{collisions_perc_change}%')
# col2.metric("Pedestrians Injured (YTD)", peds_injured_YTD, f'{peds_injured_perc_change}%')
# col3.metric("Pedestrians Killed (YTD)", peds_killed_YTD, f'{peds_killed_perc_change}%')
# col4.metric("Cyclists Injured (YTD)", cyclists_injured_YTD, f'{cyclists_injured_perc_change}%')
# col5.metric("Cyclists Killed (YTD)", cyclists_killed_YTD, f'{cyclists_killed_perc_change}%')

col1.metric('Vehicle Collisions (YTD)', collisions_YTD, f'{round(collisions_perc_change[0], 0)}% (2021 YTD)')
col2.metric("Pedestrians Injured (YTD)", peds_injured_YTD, f'{round(peds_injured_perc_change[0], 0)}% (2021 YTD)')
col3.metric("Pedestrians Killed (YTD)", peds_killed_YTD, f'{round(peds_killed_perc_change[0], 0)}% (2021 YTD)')
col4.metric("Cyclists Injured (YTD)", cyclists_injured_YTD, f'{round(cyclists_injured_perc_change[0], 0)}% (2021 YTD)')
col5.metric("Cyclists Killed (YTD)", cyclists_killed_YTD, f'{round(cyclists_killed_perc_change[0], 0)}% (2021 YTD)')

st.subheader('')

#########################
# SLIDER TO SELECT DATE #
#########################

all_dates = []



for d in grouped_by_day.crash_date:
    all_dates.append(d.strftime('%Y-%m-%d'))

col6, col7 = st.columns(2)

with col6:
    st.markdown('### Daily Vehicle Collisions')
    st.markdown(f'*Use slider to visualize collisions dating back to {all_dates[0]}*')
with col7:
    latest_collision_date = st.select_slider('',options=all_dates, value=all_dates[-1])
    total_collisions = data[data['crash_date'] == latest_collision_date]['collision_id'].count()

with st.container():
    # st.subheader(f'Daily Vehicle Collisions')
    # latest_collision_date = st.select_slider('',options=all_dates, value=all_dates[-1])
    # st.info(f'**Use slider to visualize collisions dating back to {all_dates[0]}')
    st.markdown(f'##### {total_collisions} Collisions on {latest_collision_date}**')
    map_collisions(latest_collision_date)
    


st.sidebar.subheader("About")
st.sidebar.write()
st.sidebar.text('Dashboard created by Roger Lefort')

