import pandas as pd
from bokeh.io import curdoc, show
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div, Select, AutocompleteInput, RangeSlider, DataRange1d, \
    SingleIntervalTicker, TapTool
from bokeh.events import Tap
from bokeh.plotting import figure
from os.path import dirname, join

csv = 'data/data.csv'
players = pd.read_csv(csv)

positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
directories = ['redcards', 'errors', 'pensconceded']
position_colours = ['hotpink', 'salmon', 'teal', 'turquoise']
bar_colours = ['hotpink', 'teal', 'salmon']
categories = ['Red Cards', 'Errors Leading to a Goal', 'Penalties Conceded']

max_mins = round(players['minutes'].max(), -1)
ids = players['PlayerID'].values.tolist()
names = players['PlayerName'].values.tolist()
player_map = dict()
for i in range(len(ids)):
    player_map[names[i]] = ids[i]

axis_map = {
    'Minutes': 'minutes',
    'Total Mistakes': 'sumerrors',
    'Red Cards': 'redcards',
    'Penalties Conceded': 'pensconceded',
    'Errors leading to a goal': 'errors'
}

desc = Div(text=open(join(dirname(__file__), 'my-application/description.html')).read(), sizing_mode="stretch_width")
minutes = RangeSlider(title='Number of minutes', value=(0, max_mins), start=0, end=max_mins, step=10)
position = Select(title='Position', value="All", options=positions)
highlight_name = AutocompleteInput(title='Highlight player', value='Granit Xhaka', completions=names,
                                   restrict=True, case_sensitive=False)
x_axis = Select(title='X Axis', options=sorted(axis_map.keys()), value='Minutes')
y_axis = Select(title='Y Axis', options=sorted(axis_map.keys()), value='Total Mistakes')

# create Column Data Sources that will be used by the plots
source = ColumnDataSource(data=dict(x=[], y=[], position=[], color=[]))
highlight = ColumnDataSource(data=dict(x=[], y=[]))
seasonal = ColumnDataSource(data=dict(seasons=[], redcards=[], pensconceded=[], errors=[]))

position_data = dict(Goalkeeper=ColumnDataSource(data=dict(x=[], y=[])),
                     Defender=ColumnDataSource(data=dict(x=[], y=[])),
                     Midfielder=ColumnDataSource(data=dict(x=[], y=[])),
                     Forward=ColumnDataSource(data=dict(x=[], y=[])))

TOOLTIPS = [
    ('Name', '@name'),
    ('Red Cards', '@redcards'),
    ('Penalties Conceded', '@pensconceded'),
    ('Errors leading to a goal', '@errors')
]

# scatter plot
p = figure(height=600, width=700, title='', toolbar_location=None, tooltips=TOOLTIPS, sizing_mode='scale_both')
renderers = []
legend_items = dict()
for position, data, colour in zip(position_data.keys(), position_data.values(), position_colours):
    temp = p.circle(x='x', y='y', source=position_data[position], size=6, color=colour, line_color=None,
                              legend_label=position)
    renderers.append(temp)
    legend_items[position] = temp
p.circle(x='x', y='y', source=highlight, size=11, line_color='black', fill_alpha=0, line_width=1)
p.legend.location = "top_left"
p.legend.click_policy = "hide"
p.x_range = DataRange1d(only_visible=True, renderers=renderers)
p.y_range = DataRange1d(only_visible=True, renderers=renderers)
p.hover.renderers = renderers
legend_items["Goalkeeper"].visible = False



# bar chart
q = figure(x_range=seasonal.data['seasons'], height=150, toolbar_location=None, tools="")
q.vbar_stack(directories, x='seasons', width=0.2, color=bar_colours, source=seasonal, legend_label=categories)
q.y_range.start = 0
q.xgrid.grid_line_color = None
q.axis.minor_tick_line_color = None
q.outline_line_color = None
q.yaxis.ticker = SingleIntervalTicker(interval=1)


p.add_tools(TapTool())
def callback(event):
    print(source.selected.indices[0])

p.on_event(Tap, callback)

def select_players():
    selected = players[
        (players.minutes >= minutes.value[0]) &
        (players.minutes <= minutes.value[1])
        ]
    return selected


def highlight_players(selected):
    if highlight_name.value != "":
        selected = selected[selected['PlayerName'] == highlight_name.value]
    else:
        selected = selected[selected['PlayerName'] == None]
    return selected


def updatebar():
    if highlight_name.value in names:
        playerid = player_map[highlight_name.value]
        data = {
            'seasons': [],
            'redcards': [],
            'pensconceded': [],
            'errors': []
        }
        for i in range(8, 23):
            df = pd.read_csv(f"minutes/{i}.csv")
            if df[df['PlayerID'] == playerid]['PlayerID'].count() == 1:
                data['seasons'].append(f'{str(i - 1).zfill(2)}/{str(i).zfill(2)}')
                for directory in directories:
                    dfx = pd.read_csv(f"{directory}/{i}.csv")
                    if dfx[dfx['PlayerID'] == playerid][directory].count() == 1:
                        data[directory].append(dfx[dfx['PlayerID'] == playerid][directory].iloc[0])
                    else:
                        data[directory].append(0)
        seasonal.data = data
        q.x_range.factors = seasonal.data['seasons']
        q.title.text = '%s mistakes by season' % highlight_name.value


def updatescatter():
    df = select_players()
    df_highlighted = highlight_players(df)
    x_name = axis_map[x_axis.value]
    y_name = axis_map[y_axis.value]
    p.xaxis.axis_label = x_axis.value
    p.yaxis.axis_label = y_axis.value
    size = 0
    for position, data in position_data.items():
        data.data = dict(
            x=df[df['Position'] == position][x_name],
            y=df[df['Position'] == position][y_name],
            position=df[df['Position'] == position]['Position'],
            name=df[df['Position'] == position]['PlayerName'],
            redcards=df[df['Position'] == position]['redcards'],
            pensconceded=df[df['Position'] == position]['pensconceded'],
            errors=df[df['Position'] == position]['errors']
        )
        if legend_items[position].visible:
            size += len(df[df['Position'] == position])
    p.title.text = '%d players selected' % size

    highlight.data = dict(
        x=df_highlighted[x_name],
        y=df_highlighted[y_name],
    )

controls = [minutes, x_axis, y_axis, highlight_name]

for control in controls:
    control.on_change('value', lambda attr, old, new: updatescatter())
highlight_name.on_change('value', lambda attr, old, new: updatebar())

def updatesize():
    size = 0
    df = select_players()
    for position in positions:
        if legend_items[position].visible:
            size += len(df[df['Position'] == position])
    p.title.text = '%d players selected' % size


for position in positions:
    legend_items[position].on_change('visible', lambda attr, old, new: updatesize())

inputs = column(*controls, width=250)

l = column(desc, row(inputs, p), q, sizing_mode='scale_both')

# def changehighlighted(name):
#     highlight_name.value = name
#
# taptool = p.select(type=TapTool)
# taptool.callback = changehighlighted('@name')
# taptool.renderers = renderers

q.add_layout(q.legend[0], 'right')
updatescatter()  # initial load of the scatter data
updatebar()  # initial load of the bar data
curdoc().add_root(l)
curdoc().title = 'Players'
show(l)