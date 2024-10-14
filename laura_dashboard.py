import panel as pn
from laura_etf_api import etf_API
# import sankey as sk
import datetime as dt

# import panel as pn
import pandas as pd
import altair as alt
import plotly.graph_objects as go
from matplotlib.figure import Figure
# import hvplot.pandas
import time_series as ts

# Loads javascript dependencies and configures Panel (required)
pn.extension()


# INITIALIZE API
api = etf_API()
api.load_df('data/ETFprices.csv')


# WIDGET DECLARATIONS
# Search Widgets
fund_name = pn.widgets.MultiSelect(name="Select All ETFs of Interest", options=api.get_funds(), value=['SPY', 'QQQ', 'GLD'], 
    height=250)
# fund_name = pn.widgets.Select(name="Fund", options=api.get_funds(), value='AAA')
timeseries_filter = pn.widgets.Select(name="Market Price Data", options = api.get_options(), value='close')
date_range_slider = pn.widgets.DateRangeSlider(
    name='Select a Date Range',
    start=dt.datetime(1993, 1, 28), end=dt.datetime(2021, 11, 29),
    value=(dt.datetime(1993, 1, 28), dt.datetime(2021, 11, 29)),
    step=2,
    width=300
)
ts_width = pn.widgets.IntSlider(name="Width", start=250, end=800, step=50, value=600)
ts_height = pn.widgets.IntSlider(name="Height", start=200, end=800, step=50, value=400)
trend_width = pn.widgets.IntSlider(name="Width", start=50, end=600, step=50, value=300)
trend_height = pn.widgets.IntSlider(name="Height", start=50, end=600, step=50, value=100)
# vol_width = pn.widgets.IntSlider(name="Width", start=200, end=400, step=50, value=300)
# vol_height = pn.widgets.IntSlider(name="Height", start=200, end=400, step=50, value=300)

# this decorator tells the function when to rerun 
@pn.depends(fund_name.param.value, watch=True)
def update_date_range(fund_name):
    '''updates the time range slider depending on the 
    minimum date and maximum date funds for each given 
    fund seleciton'''
    # selected_funds = event.new
    min_date = api.fund_df[api.fund_df['fund_symbol'].isin(fund_name)]['price_date'].min()
    max_date = api.fund_df[api.fund_df['fund_symbol'].isin(fund_name)]['price_date'].max()
    date_range_slider.start = min_date
    date_range_slider.end = max_date
    date_range_slider.value = (min_date, max_date)

# def update_date_range(event):
#     selected_funds = event.new
#     if selected_funds:
#         min_date = api.fund_df[api.fund_df['fund_name'].isin(selected_funds)]['price_date'].min()
#         max_date = api.fund_df[api.fund_df['fund_name'].isin(selected_funds)]['price_date'].max()
#         date_range_slider.start = min_date
#         date_range_slider.end = max_date
#         date_range_slider.value = (min_date, max_date)
# fund_name.param.watch(update_date_range, 'value')



# CALLBACK FUNCTIONS

# time slider 
def get_plotly(fund_name, timeseries_filter, date_range_slider, width, height):
    '''given fundname, value of itnerest (e.g. open,close prices), 
    returns a time series plot for one or more etf funds '''
    # global filtered_local 
    filtered_local = api.get_filtered_data(fund_name, timeseries_filter, date_range_slider)
    # plotting time series 
    fig = ts.make_time_series(fund_name, filtered_local, timeseries_filter, width, height)

    # fig = go.Figure()

    # for etf in fund_name:
    #     etf_data = filtered_local[filtered_local['fund_symbol'] == etf]  # filter data for each ETF
    #     fig.add_trace(go.Scatter(x=etf_data['price_date'], y=etf_data[timeseries_filter],
    #         mode='lines', name=etf, hoverinfo='x+y'))

    # # Customize the layout with titles and axis labels
    # fig.update_layout(
    #     title="ETF Price Tracker",
    #     xaxis_title="Date",
    #     yaxis_title=timeseries_filter,
    #     legend_title="ETF",
    #     hovermode="x unified"  # Shows the hover info for all traces at the same x-position
    # )

    return fig


def get_trend_indicator(fund_name, timeseries_filter, date_range_slider, width=250, height=200):
    '''get trends for each fund automatically calculated (y value (chosen value of interest) 
    most recent value percentage change is computed by first value (from chosen start date) 
    and last value (from chosen end date)) measures done by indicators widget 
    and then each fund with its metrics gets returns as column'''
    # collecting all Trend indicators
    trends = []  
    
    # Iterate over each fund symbol in the list
    for symbol in fund_name:
        # Use the API function to fetch and filter the data
        df = api.get_filtered_data([symbol], timeseries_filter, date_range_slider)
        # print(df)

        # prepping data for the trend indicator in dct format
        data = {'x': df['price_date'].values, 'y': df[timeseries_filter].values}
        
        # Create the Trend indicator for the ETF
        trend = pn.indicators.Trend(
            name=f'{symbol} Price Trend',
            data=data,
            plot_x='x',
            plot_y='y',
            plot_color='#428bca',
            plot_type='line',
            pos_color='#5cb85c',
            neg_color='#d9534f',
            width=width,
            height=height
        )
        
        # append each trend to the list
        trends.append(trend)
    
    # returning a column containing all trend indicators
    return pn.Column(*trends)



def get_total_volume_plot(fund_name, date_range_slider, width=600, height=400):
    '''make bar plots for total volume for each given fund'''
    df = api.get_filtered_data(fund_name, 'volume', date_range_slider)

    # Calculate total volume per ETF
    total_volumes = df.groupby('fund_symbol')['volume'].sum().reset_index()
    # Plot total volume
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=total_volumes['fund_symbol'], 
        y=total_volumes['volume'],
        name="Total Volume",
        opacity=1
    ))
    
    fig.update_layout(
        title="Total Volume Traded Over Selected Date Range",
        xaxis_title="ETF",
        yaxis_title="Total Volume",
        barmode='group',
        width = width,
        height=height
    )
    
    return fig

def get_total_volume_indicator(fund_name, date_range_slider, width=200, height=50):
    '''Create a summary indicator for total volume over the selected time range for each ETF with numeric values and suffixes in the name.'''
    df = api.get_filtered_data(fund_name, 'volume', date_range_slider)

    # Calculate total volume per ETF
    total_volumes = df.groupby('fund_symbol')['volume'].sum()
    
    # List to hold each volume indicator
    indicators = []
    
    for symbol, volume in total_volumes.items():
        # Determine suffix based on the value's magnitude
        if volume >= 1_000_000_000:
            display_value = volume / 1_000_000_000
            suffix = 'Billions'
        elif volume >= 1_000_000:
            display_value = volume / 1_000_000
            suffix = 'Millions'
        elif volume >= 1_000:
            display_value = volume / 1_000
            suffix = 'Thousands'
        else:
            display_value = volume
            suffix = ''

        # Create a Number indicator, using numeric value and adding the suffix in the name
        indicator = pn.indicators.Number(
            name=f'Total Volume for {symbol} ({suffix})',
            value=display_value,  # This remains a numeric value
            format='{value:.1f}',  # Use formatting for one decimal place
            sizing_mode='fixed',
            width=width,
            height=height
        )
        indicators.append(indicator)
            # Arrange indicators in a Row and make it horizontally scrollable
    scrollable_row = pn.Column(
        pn.Row(*indicators, sizing_mode='stretch_width'),
        scroll=True,
        width=1000 # Fixed width; adjust based on how much space you want to display
        # height=height + 20  # Add some padding to height if needed
    )

    return scrollable_row

    # return pn.Row(*indicators)






# CALLBACK BINDINGS (Connecting widgets to callback functions)


# time_slider = pn.bind(update_date_range, fund_name)
plot = pn.bind(get_plotly, fund_name, timeseries_filter, date_range_slider, ts_width, ts_height)
trend_indicators = pn.bind(get_trend_indicator, fund_name, timeseries_filter, date_range_slider.param.value, trend_width, trend_height)
# total_volume_plot = pn.bind(get_total_volume_plot, fund_name, date_range_slider.param.value, vol_width, vol_height)


total_volume_plot = pn.bind(get_total_volume_indicator, fund_name, date_range_slider.param.value, width=300, height=300)
# total_volume_plot = pn.bind(get_total_volume_indicator, fund_name, date_range_slider.param.value)

# maybe add average volume traded on the side of the volume plot (similar look to the trend indicators next to the time series plot)
# also make the width and height of the cards adjustable
# and have consistent color coding across all plots 
# strech the bars horizontally below the time series plot 




# DASHBOARD WIDGET CONTAINERS ("CARDS")
trend_indicators_scrollable = pn.Column(trend_indicators, scroll=True, height=400)  # Set height limit

volume_plotting = pn.Column(total_volume_plot, height=400)

volume_plot = pn.Row(total_volume_plot, scroll=True)
# Combine into a single layout line
plot_and_trend = pn.Column(pn.Row(plot, trend_indicators_scrollable ), volume_plot)



card_width = 320

search_card = pn.Card(
    pn.Column(fund_name, timeseries_filter, date_range_slider),
    title="Search",
    width=card_width,
    sizing_mode='stretch_width',  
    collapsed=False
)

plot_card = pn.Card(
    pn.Column(ts_width, ts_height),
    title="Time Series Dimensions",
    width=card_width,
    sizing_mode='stretch_width',  
    collapsed=True
)

trend_card = pn.Card(
    pn.Column(trend_width, trend_height),
    title="Price Trend Dimensions",
    width=card_width,
    sizing_mode='stretch_width',  
    collapsed=True
)

# volume_card = pn.Card(
#     pn.Column(vol_width, vol_height),
#     title="Total Volume Dimensions",
#     width=card_width,
#     sizing_mode='stretch_width',  
#     collapsed=True
# )

stacked_cards = pn.Column(
    search_card,
    plot_card,
    trend_card,
    # volume_card,
    sizing_mode='stretch_width'
    )

# LAYOUT

layout = pn.template.FastListTemplate(
    title="ETF Explorer",
    sidebar=[
        stacked_cards
    ],
    theme= 'dark',
    theme_toggle=False,
    main=[
        plot_and_trend
        # pn.Tabs(
            # ("ETF Time Series", plot_and_trend),
            # ("Volume Traded", volume_plotting),  # Replace None with callback binding
            # active=0  # Which tab is active by default
        # )

    ],
    header_background='#a93226'

).servable()

layout.show()
