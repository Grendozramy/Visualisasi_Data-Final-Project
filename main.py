# utilities
import pandas as pd
import numpy as np
from os.path import dirname, join

# bokeh
from bokeh.io import curdoc
from bokeh.models.tools import HoverTool
from bokeh.models import DateRangeSlider,  ColumnDataSource, PreText, Select, RadioButtonGroup
from bokeh.plotting import figure
from bokeh.layouts import column, row


# import data
df_confirmed = pd.read_csv(
    join(dirname(__file__), 'data', 'confirmed.csv'), parse_dates=['date'])
df_death = pd.read_csv(join(dirname(__file__), 'data',
                            'death.csv'), parse_dates=['date'])
df_recovered = pd.read_csv(
    join(dirname(__file__), 'data', 'recovered.csv'), parse_dates=['date'])

# drop data
df_confirmed.drop("Unnamed: 0", axis=1, inplace=True)
df_death.drop("Unnamed: 0", axis=1, inplace=True)
df_recovered.drop("Unnamed: 0", axis=1, inplace=True)

# indexing
regions_death = df_death.columns[0:-1]
regions_confirmed = df_confirmed.columns[0:-1]
regions_recovered = df_recovered.columns[0:-1]

# # select rows and columns
# total_death_case = dict(df_death.iloc[-1, ])
# total_recovered_case = dict(df_recovered.iloc[-1, ])
# total_confirmed_case = dict(df_confirmed.iloc[-1, ])

# function region, case and date
def create_source(region, case, date_range=None):
    if case == 'confirmed':
        plot = df_confirmed[region]
    elif case == 'death':
        plot = df_death[region]
    elif case == 'recovered':
        plot = df_recovered[region]
    if case == "all":
        df = pd.DataFrame(data={
            'date': df_death['date'],
            'death': df_death[region],
            'recovered': df_recovered[region],
            'plot': df_confirmed[region]
        })
    else:
        df = pd.DataFrame(data={
            'date': df_death['date'],
            'plot': plot
        })
    if date_range is not None:
        mask = (df['date'] > np.datetime64(date_range[0])) & (
            df['date'] <= np.datetime64(date_range[1]))
        df = df.loc[mask]
    return ColumnDataSource(df)

# function create plot (Line Plot)
def make_plot(source, title, case='confirmed', sizing_mode=None):
    if sizing_mode is None:
        plt = figure(x_axis_type='datetime', name='plt')
    else:
        plt = figure(x_axis_type='datetime',
                     sizing_mode=sizing_mode, name='plt', height=800)
    plt.title.text = title
    plt.line('date', 'plot', source=source, color='dodgerblue', line_width=2,
             name='case', legend_label=case)
    plt.circle('date', 'plot', size=5, color="dodgerblue", source=source)

    hover = HoverTool(tooltips=[('Date', '@date{%F}'), ('Total case', '@plot')],
                      formatters={'@date': 'datetime'})
    plt.add_tools(hover)
    plt.legend.location = "top_left"
    
    plt.xaxis.axis_label = "Date"
    plt.yaxis.axis_label = "Total cases"
    plt.axis.axis_label_text_font_style = "bold"
    plt.grid.grid_line_alpha = 0.3
    return plt

# function update for region, case dan result plot
def update(date_range=None, force=False):
    global region, case, plt
    plt.title.text = case.capitalize() + " Case in Region " + region
    newdata = create_source(region, case, date_range).data
    source.data.update(newdata)

# function update/change for region
def handle_region_change(attrname, old, new):
    global region
    region = region_select.value
    update()

# function update/change for case
def handle_case_change(attrname, old, new):
    global case
    cases = ["confirmed", "recovered", "death", 'all']
    case = cases[new]
    update()

    if case == 'confirmed' or case == "all":
        color = 'dodgerblue'
    elif case == 'death':
        color = 'red'
    elif case == 'recovered':
        color = "green"

    if case != "all" or case == 'global':
        plt.legend.items = [
            (case, [plt.renderers[0]])
        ]
        plt.renderers[0].glyph.line_color = color
        plt.renderers[1].glyph.line_color = color
        try:
            plt.renderers[2].visible = False
            plt.renderers[3].visible = False
        except IndexError:
            print(False)
    else:
        try:
            plt.renderers[0].glyph.line_color = 'dodgerblue'
            plt.renderers[1].glyph.line_color = 'dodgerblue'
            plt.renderers[2].visible = True
            plt.renderers[3].visible = True
            plt.legend.items = [
                ("confirmed", [plt.renderers[0]]),
                ("recovered", [plt.renderers[2]]),
                ("death", [plt.renderers[3]])
            ]
        except IndexError:
            plt.vbar('date', top='recovered', width=1, line_width=5, source=source, color='green',
                     name='recovered', legend_label="recovered")
            plt.step(x='date', y='death', source=source, color='red', line_width=2,
                     name='death', legend_label="death")

# function update/change untuk date
def handle_range_change(attrname, old, new):
    global slider_value
    slider_value = range_slider.value_as_datetime
    update(date_range=slider_value)

# default value
stats = PreText(text='', width=500)
case = "confirmed"
region = 'Indonesia'
source = create_source(region, case)
total_data = len(source.data['date'])-1
case_date = pd.to_datetime(source.data['date'])
slider_value = case_date[0], case_date[-1]

# widgets cnhage for case and date
case_select = RadioButtonGroup(
    labels=["Confirmed", "Recovered", "Death", "Show All"], active=0, name="case_select")
region_select = Select(value=region, title='Country/Region',
                       options=list(regions_confirmed), name="region_select")
range_slider = DateRangeSlider( start=slider_value[0], end=slider_value[1], 
                               value=(0, slider_value[1]), title='Date', name="range_slider")

# onchange
region_select.on_change('value', handle_region_change)
case_select.on_change('active', handle_case_change)
range_slider.on_change('value', handle_range_change)
plt = make_plot(source, case.capitalize() + " Case in Region " +
                region, case, sizing_mode="stretch_both")

# control
controls = column(region_select,  case_select, range_slider)

# layout
main_layout = column(
    row(controls, plt, sizing_mode="stretch_height"), sizing_mode="stretch_both")
curdoc().add_root(main_layout)
curdoc().title = "Final Project - Kasus Covid-19"