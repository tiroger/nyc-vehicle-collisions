#############
# LIBRARIES #
#############

# from operator import index
# from os import rename
# from streamlit.state.session_state import Value
# import secrets
from distutils.command import config
from get_data import fetch_data # Module to fetch and process data
import pandas as pd
import numpy as np

import folium
from folium.features import CustomIcon
from folium.plugins import HeatMap
from streamlit_folium import folium_static
# import plotly
# import datetime
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
config = {'displayModeBar': False}

# import pyarrow.parquet as pq
# import awswrangler as wr
# import calendar

# data_URI = 's3://nypdcollisions/collisions.parquet'

from PIL import Image

import streamlit as st
# APP_TOKEN = st.secrets['SOCRATA_APP_TOKEN']
# MAPBOX_TOKEN = st.secrets[MAPBOX_TOKEN]

# import sys


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

# Front end elements
html_title = """ 
    <div padding:5px"> 
    <h1 style ="color:black; text-align:center">How Safe are NYC Streets?</h1>
    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/I_Love_New_York.svg/1101px-I_Love_New_York.svg.png" alt="City" style="width:100%;height:auto;"> 
    </div>
    """
st.sidebar.markdown(html_title, unsafe_allow_html=True)
# st.sidebar.caption('Image from www.mississaugabikes.ca/crossrides-and-bike-signals/')

#################
# FETCHING DATA #
# ###############

@st.cache(show_spinner=False, max_entries=5, ttl=86400)
def fetch_and_clean_data():
    with st.spinner('Data Refreshing... May take up to 5 minutes.'):
        collisions_df = fetch_data()
        return collisions_df

collisions = fetch_and_clean_data()

collisions.rename(columns={
    'number_of_cyclist_injured': 'number_of_cyclists_injured',
    'number_of_cyclist_killed': 'number_of_cyclists_killed',
    'number_of_motorist_injured': 'number_of_motorists_injured',
    'number_of_motorist_killed': 'number_of_motorists_killed'
}, inplace=True)


#################################
# TRANSFORMING DATA FOR METRICS #
#################################

data_start_date = '2019-01-01' # Limiting data to from 2019 to present day
collisions = collisions[collisions['crash_date'] >= data_start_date]

last_updated = collisions['crash_date'].max()
first_date = collisions['crash_date'].min()

all_boros = collisions.borough.unique()

# chk1, chk2, chk3 = st.columns(3)
# chk4, chk5, chk6 = st.columns(3)

chk1, chk2, chk3, chk4, chk5, chk6 = st.columns(6)
###
boro_selection = []
with chk1:
    man = st.checkbox('Manhattan', value=True, key='man')
    if man:
        boro_selection.append('MANHATTAN')

with chk2:
    bk = st.checkbox('Brooklyn', value=True, key='bk')
    if bk:
        boro_selection.append('BROOKLYN')

with chk3:
    si = st.checkbox('Bronx', value=True, key='si')
    if si:
        boro_selection.append('BRONX')

with chk4:
    qns = st.checkbox('Queens', value=True, key='qns')
    if qns:
        boro_selection.append('QUEENS')

with chk5:
    bx = st.checkbox('Staten Island', value=True, key='bx')
    if bx:
        boro_selection.append('STATEN ISLAND')

with chk6:
    unk = st.checkbox('Unspecified', value=True, key='unk')
    if unk:
        boro_selection.append(np.nan)
###
# 'st.checkbox(label, value=False, key=None, help=None, on_change=None, args=None, kwargs=None, *, disabled=False)'
# 'array([nan, 'QUEENS', 'BROOKLYN', 'STATEN ISLAND', 'MANHATTAN', 'BRONX'],'

# if len(boro_selection) == 0:
#     sys.tracebacklimit = 0
#     sys.exit('Please select at least 1 borough to proceed')

# while len(boro_selection) == 0:
#     sys.exit('Please select a borough!')

collisions = collisions[collisions.borough.isin(boro_selection)]
grouped_by_day = collisions.groupby(['crash_year', 'crash_date']).agg({
    'collision_id': 'count',
    'number_of_persons_injured': 'sum',
    'number_of_persons_killed': 'sum',
    'number_of_pedestrians_injured': 'sum',
    'number_of_pedestrians_killed': 'sum',
    'number_of_cyclists_injured': 'sum',
    'number_of_cyclists_killed': 'sum',
    'number_of_motorists_injured': 'sum',
    'number_of_motorists_killed': 'sum'
}).reset_index()


# Grouping by Year to obtain the cummulative daily count
grouped_by_day['collisions_cumsum'] = grouped_by_day.groupby(['crash_year'])['collision_id'].cumsum()

grouped_by_day['person_injured_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_persons_injured'].cumsum()
grouped_by_day['person_killed_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_persons_killed'].cumsum()

grouped_by_day['peds_injured_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_pedestrians_injured'].cumsum()
grouped_by_day['peds_killed_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_pedestrians_killed'].cumsum()

grouped_by_day['cyclist_injured_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_cyclists_injured'].cumsum()
grouped_by_day['cyclist_killed_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_cyclists_killed'].cumsum()

grouped_by_day['motorists_injured_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_motorists_injured'].cumsum()
grouped_by_day['motorists_killed_cumsum'] = grouped_by_day.groupby(['crash_year'])['number_of_motorists_killed'].cumsum()

grouped_by_day.reset_index(inplace=True)

# Year to Date metrics
max_date = collisions['crash_date'].max()

collisions_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['collisions_cumsum']

persons_injured_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['person_injured_cumsum']
persons_killed_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['person_killed_cumsum']

peds_injured_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['peds_injured_cumsum']
peds_killed_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['peds_killed_cumsum']

cyclists_injured_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['cyclist_injured_cumsum']
cyclists_killed_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['cyclist_killed_cumsum']

motorists_injured_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['motorists_injured_cumsum']
motorists_killed_YTD = grouped_by_day.loc[grouped_by_day['crash_date'] == max_date]['motorists_killed_cumsum']



# Previous YTD
last_year = max_date - pd.DateOffset(years=1)
last_YTD = last_year

collisions_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['collisions_cumsum']

persons_injured_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['person_injured_cumsum']
persons_killed_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['person_killed_cumsum']

peds_injured_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['peds_injured_cumsum']
peds_killed_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['peds_killed_cumsum']

cyclists_injured_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['cyclist_injured_cumsum']
cyclists_killed_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['cyclist_killed_cumsum']

motorists_injured_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['motorists_injured_cumsum']
motorists_killed_YTD_previous = grouped_by_day.loc[grouped_by_day['crash_date'] == last_YTD]['motorists_killed_cumsum']

# Percent Change YTD
collisions_perc_change = (collisions_YTD.values - collisions_YTD_previous.values)/collisions_YTD_previous.values*100

persons_injured_perc_change = (persons_injured_YTD.values - persons_injured_YTD_previous.values)/persons_injured_YTD_previous.values*100
persons_killed_perc_change = (persons_killed_YTD.values - persons_killed_YTD_previous.values)/persons_killed_YTD_previous.values*100

peds_injured_perc_change = (peds_injured_YTD.values - peds_injured_YTD_previous.values)/peds_injured_YTD_previous.values*100
peds_killed_perc_change = (peds_killed_YTD.values - peds_killed_YTD_previous.values)/peds_killed_YTD_previous.values*100

cyclists_injured_perc_change = (cyclists_injured_YTD.values - cyclists_injured_YTD_previous.values)/cyclists_injured_YTD_previous.values*100
cyclists_killed_perc_change = (cyclists_killed_YTD.values - cyclists_killed_YTD_previous.values)/cyclists_killed_YTD_previous.values*100

motorists_injured_perc_change = (motorists_injured_YTD.values - motorists_injured_YTD_previous.values)/motorists_injured_YTD_previous.values*100
motorists_killed_perc_change = (motorists_killed_YTD.values - motorists_killed_YTD_previous.values)/motorists_killed_YTD_previous.values*100

############################
# FETCHING HISTORICAL DATA #
############################

# # Retrieving the data directly from Amazon S3
# all_collisions_df = pq.read_pandas('./Data/collisions.parquet').to_pandas()
# # Modifying column names
# all_collisions_df.columns = all_collisions_df.columns.str.lower()
# all_collisions_df.columns = all_collisions_df.columns.str.replace(' ', '_')

# all_collisions_df['crash_date'] = pd.to_datetime(all_collisions_df['crash_date'])
# all_collisions_df['crash_year'] = pd.DatetimeIndex(all_collisions_df['crash_date']).year
# all_collisions_df['crash_month'] = pd.DatetimeIndex(all_collisions_df['crash_date']).month
# # all_collisions_df['crash_month'] = all_collisions_df['crash_date'].dt.month_name()
# all_collisions_df['crash_month_year'] = pd.to_datetime(all_collisions_df['crash_date']).dt.to_period('M')
# historical_df = all_collisions_df[all_collisions_df.crash_date < '2022-01-01'] # Removing 2022 data
# historical_df = all_collisions_df[all_collisions_df.crash_year > 2012]

# collisions = collisions[collisions.borough.isin(boro_selection)]
by_year_and_boro = collisions.groupby(['crash_year', 'crash_month']).agg({
    'collision_id': 'count',
    'number_of_persons_injured': 'sum',
    'number_of_persons_killed': 'sum',
    'number_of_pedestrians_injured': 'sum',
    'number_of_pedestrians_killed': 'sum',
    'number_of_cyclists_injured': 'sum',
    'number_of_cyclists_killed': 'sum',
    'number_of_motorists_injured': 'sum',
    'number_of_motorists_killed': 'sum'
}).rename(columns={'collision_id': 'total_collisions'}).reset_index()

# Most dangerous streets
dangerous_streets = collisions.groupby(['borough', 'on_street_name']).agg({'collision_id': 'count'}).reset_index()
dangerous_streets.sort_values(by='collision_id', ascending=False, inplace=True)
dangerous_streets = dangerous_streets.replace('', np.nan)
dangerous_streets.dropna(inplace=True)
dangerous_streets.rename(columns={'collision_id': 'Total Collisions'}, inplace=True)
top_10_dangerous_st = dangerous_streets.head(1000)

##########################
# COLLISIONS IN PAST DAY #
##########################

# latest_collision_date = data.crash_date.max()
def map_collisions(latest_collision_date):
    latest_collision_date_df = collisions[collisions['crash_date'] == latest_collision_date].dropna()
    latest_collision_date_df['latitude'] = pd.to_numeric(latest_collision_date_df['latitude'])
    latest_collision_date_df['longitude'] = pd.to_numeric(latest_collision_date_df['longitude'])
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
        html = '<i style="font-family:arial"> Cause of Collision: </i>' + '<b style="font-family:arial">' + row.loc['contributing_factor_vehicle_1'] + '</b>' + '<br style="font-family:arial">' + '</b>' '<i style="font-family:arial">Number of Persons Injured: </i>' + '<b style="font-family:arial">' + str(row.loc['number_of_persons_injured']) + '</b>' + '<br style="font-family:arial">' + '</b>' '<i style="font-family:arial">Number of Persons Killed: </i>' + '<b style="font-family:arial">' + str(row.loc['number_of_persons_killed']) + '</b>'
        iframe = folium.IFrame(html=html, width=330, height=100)
        popup = folium.Popup(iframe, max_width='100%', min_height='100%')
        
        folium.Marker(location=[row.loc['latitude'], row.loc['longitude']], icon=icon, popup=popup, tooltip=tooltip).add_to(collision_map)
        
    HeatMap(locations).add_to(collision_map)
    locations = zip(latest_collision_date_df.latitude, latest_collision_date_df.longitude)

    folium_static(collision_map, width=1020)


#############
# FRONT END #
#############

# # Front end elements
# html_title = """ 
#     <div style ="background-color:white; padding:5px"> 
#     <h1 style ="color:black; text-align:center">How Safe are NYC Streets?</h1>
#     <img src="https://www.mississaugabikes.ca/wp-content/uploads/2018/11/OPS-0333-Crossride-Illustration_FINAL.jpg" alt="City" style="width:100%;height:auto;"> 
#     </div>
#     """
# st.sidebar.markdown(html_title, unsafe_allow_html=True)
# st.sidebar.caption('Image from www.mississaugabikes.ca/crossrides-and-bike-signals/')

# st.title('How Safe are NYC Streets?')
# st.image('./Assets/OPS-0333-Crossride-Illustration_FINAL.jpeg', caption=None, width='auto', use_column_width=True)

if len(boro_selection) > 5:
    add_text = 'all Boroughs'
else:
    add_text = 'your Selections'

### TOP ROW
st.markdown(f'### NYC Vehicle Collision Statistics Year-to-Date (YTD) for {add_text} through {last_updated.strftime("%m-%d-%Y")}') 
col1, col9, col10 = st.columns(3)
col2, col3, col4 = st.columns(3)
col5, col6, col7 = st.columns(3)


# col1.metric('Vehicle Collisions (YTD)', collisions_YTD, f'{collisions_perc_change}%')
# col2.metric("Pedestrians Injured (YTD)", peds_injured_YTD, f'{peds_injured_perc_change}%')
# col3.metric("Pedestrians Killed (YTD)", peds_killed_YTD, f'{peds_killed_perc_change}%')
# col4.metric("Cyclists Injured (YTD)", cyclists_injured_YTD, f'{cyclists_injured_perc_change}%')
# col5.metric("Cyclists Killed (YTD)", cyclists_killed_YTD, f'{cyclists_killed_perc_change}%')

# with col1:
#     st.markdown('**Vehicle Collisions (YTD)**', unsafe_allow_html=True)
#     number1 = st.metric('', collisions_YTD, f'{round(collisions_perc_change[0], 0)}% (2021 YTD)')

# with col2:
#     st.markdown('**Pedestrians Injured (YTD)**')
#     number2 = st.metric('', peds_injured_YTD, f'{round(peds_injured_perc_change[0], 0)}% (2021 YTD)')

# with col3:
#     st.markdown('**Pedestrians Killed (YTD)**')
#     number3 = st.metric('', peds_killed_YTD, f'{round(peds_killed_perc_change[0], 0)}% (2021 YTD)')

# with col4:
#     st.markdown('**Cyclists Injured (YTD)**')
#     number4 = st.metric('', cyclists_injured_YTD, f'{round(cyclists_injured_perc_change[0], 0)}% (2021 YTD)')

# with col5:
#     st.markdown('**Cyclists Killed (YTD)**')
#     st.metric("", cyclists_injured_YTD, f'{round(cyclists_killed_perc_change[0], 0)}% (2021 YTD)')

col1.metric('Vehicle Collisions (YTD)', collisions_YTD, f'{round(collisions_perc_change[0], 0)}% (2021 YTD)')
# col9.metric('Persons Injured (YTD)', persons_injured_YTD, f'{round(persons_injured_perc_change[0], 0)}% (2021 YTD)')
# col10.metric('Persons Killed (YTD)', persons_killed_YTD, f'{round(persons_killed_perc_change[0], 0)}% (2021 YTD)')
col2.metric('Pedestrians Injured (YTD)', peds_injured_YTD, f'{round(peds_injured_perc_change[0], 0)}% (2021 YTD)')
col5.metric('Pedestrians Killed (YTD)', peds_killed_YTD, f'{round(peds_killed_perc_change[0], 0)}% (2021 YTD)')
col3.metric('Cyclists Injured (YTD)', cyclists_injured_YTD, f'{round(cyclists_injured_perc_change[0], 0)}% (2021 YTD)')
col6.metric('Cyclists Killed (YTD)', cyclists_killed_YTD, f'{round(cyclists_killed_perc_change[0], 0)}% (2021 YTD)')
col4.metric('Motorists Injured (YTD)', motorists_injured_YTD, f'{round(motorists_injured_perc_change[0], 0)}% (2021 YTD)')
col7.metric('Motorists Killed (YTD)', motorists_killed_YTD, f'{round(motorists_killed_perc_change[0], 0)}% (2021 YTD)')

st.markdown('<hr/>', unsafe_allow_html=True)

#########################
# SLIDER TO SELECT DATE #
#########################

all_dates = []



for d in grouped_by_day.crash_date:
    all_dates.append(d.strftime('%Y-%m-%d'))

col6, col7 = st.columns(2)

with col6:
    st.markdown(f'### Daily Vehicle Collisions for {add_text}')
    st.markdown(f'*Use slider to visualize collisions dating back to {all_dates[0]}*')
with col7:
    latest_collision_date = st.select_slider('',options=all_dates, value=all_dates[-1])
    collisions = collisions[collisions.borough.isin(boro_selection)]
    total_collisions = collisions[collisions['crash_date'] == latest_collision_date]['collision_id'].count()

#### HEXBIN ######
# px.set_mapbox_access_token('[KEY]')

# st.markdown(f'<h5>There were <em style="font-size:30px" "color:red">{total_collisions}</em> collisions on {latest_collision_date}</h5>', unsafe_allow_html=True)

# # latest_collision_date_df = collisions[collisions['crash_date'] == latest_collision_date].dropna()
# collisions['latitude'] = pd.to_numeric(collisions['latitude'])
# collisions['longitude'] = pd.to_numeric(collisions['longitude'])
# latest_collision_date_df = collisions[collisions.longitude != 0.0]

# fig = ff.create_hexbin_mapbox(
#     data_frame=latest_collision_date_df, lat="latitude", lon="longitude", nx_hexagon=10, opacity=0.5, labels={"color": "Number of Collisions", "frame": "crash_month"},
#     min_count=1, show_original_data=False, center={'lat': 40.7128, 'lon': -74.0060},
#     original_data_marker=dict(size=6, opacity=0.6, color="deeppink"), color_continuous_scale="Icefire",
# )
# fig.data[0].hovertemplate = 'Number of Collisions: %{z:,.0f}'
# fig.update_layout(margin=dict(b=0, t=0, l=0, r=0), showlegend=False)
# st.plotly_chart(fig, use_container_width = True)
#### HEXBIN ######

### FOLIUM ###
with st.container():
    # st.subheader(f'Daily Vehicle Collisions')
    # latest_collision_date = st.select_slider('',options=all_dates, value=all_dates[-1])
    # st.info(f'**Use slider to visualize collisions dating back to {all_dates[0]}')
    st.markdown(f'<h5>There were <em style="font-size:30px" "color:red">{total_collisions}</em> collisions on {last_updated.strftime("%m-%d-%Y")}</h5>', unsafe_allow_html=True)
    map_collisions(latest_collision_date)
### FOLIUM ###

st.markdown('<hr/>', unsafe_allow_html=True)

###################
# HISTORICAL DATA #
###################

st.markdown(f'### Historical Data from 2019 to 2022*')
col8, col9 = st.columns(2)

metrics = ['total_collisions', 'number_of_persons_injured', 'number_of_persons_killed', 'number_of_pedestrians_injured', 'number_of_pedestrians_killed', 'number_of_cyclists_injured', 'number_of_cyclists_killed', 'number_of_motorists_injured', 'number_of_motorists_killed']
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def change_case(string):
    no_under = string.replace('_', ' ')
    final = no_under.title()
    return final

with col8:

    annotation = {
    'xref': 'paper',
    'yref': 'paper',
    'x': 0.24,  # If we consider the x-axis as 100%, we will place it on the x-axis with how many %
    'y': 0.53,
    'ax':50,
    'text': 'Start of COVID-19 lockdown',
    'showarrow': True,
    'arrowhead': 3,
    'font': {'size': 10, 'color': 'black'},
    'hovertext': 'On March 7, Cuomo declared a state of emergency in New York State after 162 cases had been confirmed in the state.'
    }
    metric = st.selectbox('', options=metrics, format_func=lambda x: change_case(x))
    proper_metric = metric.replace('_', ' ')
    proper_metric = proper_metric.title()

    fig = px.line(by_year_and_boro, x="crash_month", y=metric, color='crash_year', markers=True, title=f'Monthly {proper_metric} between 2019 and 2022 <br><sup>*2022 data still maturing.</sup>' , labels={
                        'crash_year': 'Year',
                        "crash_month": 'Month',
                        metric: proper_metric,
                    })

    # fig.for_each_trace(lambda trace: fig.add_annotation(
    #     x=trace.x[-1], y=trace.y[-1], text='  '+trace.name, 
    #     font_color=trace.line.color,
    #     ax=10, ay=10, xanchor="left", showarrow=False))
    fig.update_traces(mode="markers+lines", hovertemplate=None)
    fig.update_xaxes(ticktext=month_names, tickvals=[1,2,3,4,5,6,7,8,9,10,11,12])
    fig.update_layout({'annotations': [annotation]})    
    fig.update_layout(
            xaxis=dict(
                showline=True,
                showgrid=False,
                showticklabels=True,
                linecolor='rgb(204, 204, 204)',
                linewidth=2,
                ticks='outside',
                title='',
                tickfont=dict(
                    family='Arial',
                    size=12,
                    color='rgb(82, 82, 82)',
                ),
            ),
            yaxis=dict(
                # showgrid=True,
                zeroline=False,
                showline=True,
                gridcolor = 'rgb(235, 236, 240)',
                showticklabels=True,
                title='',
                autorange=True
            ),
            autosize=True,
            hovermode="x unified",
            margin=dict(
                autoexpand=True,
                l=100,
                r=20,
                t=110,
            ),
            showlegend=True,
    #         legend=dict(
    #         # orientation="h",
    #         yanchor="bottom",
    #         y=0.9,
    #         xanchor="left",
    #         x=0.7
    # ),
            plot_bgcolor='rgba(0,0,0,0)'
        )
    # fig.show()

    st.plotly_chart(fig, use_container_width = True)



with col9:
    borough_of_st = st.selectbox('', options=['Manhattan', 'Brooklyn', 'Bronx', 'Queens', 'Staten Island'])
    cap_borough_of_st = borough_of_st.upper()

    top_10_dangerous_st = top_10_dangerous_st[top_10_dangerous_st.borough.isin([cap_borough_of_st])].head(10).sort_values(by='Total Collisions', ascending=True)
    fig = px.bar(top_10_dangerous_st, y='on_street_name', x='Total Collisions', title=f'Most Dangerous Cross Streets in {borough_of_st} <br><sup>*Total Number of Collisions Since 2019</sup>', hover_data=['Total Collisions'], orientation='h')
    # fig.update_xaxes(tickangle=45)
    
    fig.update_traces(hovertemplate=None, marker_color='rgb(253,184,19)')
    fig.update_layout(
            xaxis=dict(
                showline=True,
                showgrid=False,
                showticklabels=True,
                linecolor='rgb(204, 204, 204)',
                linewidth=2,
                ticks='outside',
                title='',
                tickfont=dict(
                    family='Arial',
                    size=12,
                    color='rgb(82, 82, 82)',
                ),
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showline=False,
                gridcolor = 'rgb(235, 236, 240)',
                showticklabels=True,
                title='',
                autorange=True
            ),
            autosize=True,
            hovermode="x unified",
            margin=dict(
                autoexpand=True,
                l=100,
                r=20,
                t=110,
            ),
            showlegend=True,
    #         legend=dict(
    #         # orientation="h",
    #         yanchor="bottom",
    #         y=0.9,
    #         xanchor="left",
    #         x=0.7
    # ),
            plot_bgcolor='rgba(0,0,0,0)'
        )

    st.plotly_chart(fig, use_container_width = True)



col15, col16 = st.columns(2)
with col15:
    # n_reasons = st.slider('Slide to see more', min_value=5, max_value=20, value=5)
    crash_causes = collisions['contributing_factor_vehicle_1'].value_counts().rename_axis('unique_values').reset_index(name='counts')
    top_10_crashes_causes = crash_causes[crash_causes.unique_values != 'Unspecified'].head(10)

    labels = top_10_crashes_causes.unique_values
    values = top_10_crashes_causes.counts

# pull is given as a fraction of the pie radius
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, pull=[0.2,0,0,0,0,0,0,0,0,0,0])])
    fig.update_layout(
    title_text=f'Top 10 Vehicle Collision Causes <br><sup>~30% of causes listed as "Unspecified" .</sup>')

    st.plotly_chart(fig, use_container_width = True)

with col16:
    # n_reasons = st.slider('Slide to see more', min_value=5, max_value=20, value=5)
    crash_causes = collisions['vehicle_type_code1'].value_counts().rename_axis('unique_values').reset_index(name='counts')
    top_10_crashes_causes = crash_causes[crash_causes.unique_values != 'Unspecified'].head(10)

    labels = top_10_crashes_causes.unique_values
    values = top_10_crashes_causes.counts

# pull is given as a fraction of the pie radius
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, pull=[0.2,0,0,0,0,0,0,0,0,0,0])])
    fig.update_layout(
    title_text=f'Top 10 Vehicle Types Involved in Collisions <br><sup></sup>')

    st.plotly_chart(fig, use_container_width = True)


############
# SIDE BAR #
############

st.sidebar.subheader("About")
st.sidebar.markdown('*In 2011 the New York City Council passed Local Law #12 requiring the NYPD to collect and make available to the public records of all accidents involving motor vehicles. A police report (MV104-AN) is required to be filled out for collisions where someone is injured or killed, or where there is at least $1000 worth of damage. Each report represents a unique collision and includes date and time, location(city, borough, address, zip code, latitude and longitude), number of injuries and/or deaths, contributing factors, and information about the vehicles involved. The information is available in a variety of formats, including downloadable json and csv files, and through the Socrata Open Data API.*')
st.sidebar.caption('*For perfomance, we are only including data going back to 2019.*')


st.sidebar.caption(f'Data current as of {last_updated.strftime("%m/%d/%Y")}')
st.sidebar.markdown('<hr/>', unsafe_allow_html=True)
st.sidebar.text('Dashboard created by Roger Lefort')


