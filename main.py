import pandas as pd
from bokeh.io import curdoc, show
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div, Select, AutocompleteInput, RangeSlider, DataRange1d, \
    SingleIntervalTicker, Circle, Tap
from bokeh.plotting import figure
from os.path import dirname, join
from bokeh import events

# data
csv = 'data/data.csv'
players = pd.read_csv(csv)

positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
directories = ['redcards', 'errors', 'pensconceded', 'owngoals']
position_colours = ['hotpink', 'salmon', 'teal', 'turquoise']
bar_colours = ['hotpink', 'teal', 'salmon', 'turquoise']
categories = ['Red Cards', 'Errors Leading to a Goal', 'Penalties Conceded', 'Own Goals']

max_mins = round(players['minutes'].max(), -1)

ids = players['PlayerID'].values.tolist()
names = players['PlayerName'].values.tolist()
nameMap = dict()
for i in range(len(ids)):
    shortName = names[i].rsplit(' ', 1)[-1]
    nameMap[ids[i]] = shortName
    names[i] = shortName
names.sort()

axis_map = {
    'Minutes': 'minutes',
    'Total Mistakes': 'sumerrors',
    'Red Cards': 'redcards',
    'Penalties Conceded': 'pensconceded',
    'Errors leading to a goal': 'errors',
    'Own goals': 'owngoals'
}

# text to display at the top of page
desc = Div(text=open(join(dirname(__file__), 'my-application/description.html')).read(), sizing_mode="stretch_width")

# widgets
minutes = RangeSlider(title='Number of minutes', value=(0, max_mins), start=0, end=max_mins, step=10)
highlight_name = AutocompleteInput(title='Highlight player', value='Xhaka', completions=names, restrict=True, case_sensitive=False)
x_axis = Select(title='X Axis', options=sorted(axis_map.keys()), value='Minutes')
y_axis = Select(title='Y Axis', options=sorted(axis_map.keys()), value='Total Mistakes')

# column data sources
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
    ('Errors leading to a goal', '@errors'),
    ('Own goals', '@owngoals')
]

# scatter plot
p = figure(tools='tap',height=600, width=700, title='', toolbar_location=None, tooltips=TOOLTIPS, sizing_mode='scale_both')
renderers = []
legend_items = dict()
for position, data, colour in zip(position_data.keys(), position_data.values(), position_colours):
    temp = p.circle(x='x', y='y', source=position_data[position], size=6, color=colour, line_color=None, legend_label=position)
    renderers.append(temp)
    legend_items[position] = temp
p.circle(x='x', y='y', source=highlight, size=11, line_color='black', fill_alpha=0, line_width=1)
p.legend.location = "top_left"
p.legend.click_policy = "hide"
p.x_range = DataRange1d(only_visible=True, renderers=renderers)
p.y_range = DataRange1d(only_visible=True, renderers=renderers)
p.hover.renderers = renderers
for renderer in renderers:
    renderer.nonselection_glyph = None
    renderer.selection_glyph = Circle(fill_alpha=1, fill_color="yellow", line_color='black', line_width=2)

# bar chart
q = figure(x_range=seasonal.data['seasons'], height=150, toolbar_location=None, tools="")
q.vbar_stack(directories, x='seasons', width=0.2, color=bar_colours, source=seasonal, legend_label=categories)
q.y_range.start = 0
q.xgrid.grid_line_color = None
q.axis.minor_tick_line_color = None
q.outline_line_color = None
q.yaxis.ticker = SingleIntervalTicker(interval=1)


def select_players():
    selected = players[
        (players.minutes >= minutes.value[0]) &
        (players.minutes <= minutes.value[1])
        ]
    return selected


def updatebar():
    playerid = index[2]
    data = {
        'seasons': [],
        'redcards': [],
        'pensconceded': [],
        'errors': [],
        'owngoals': []
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
    q.title.text = '%s mistakes by season' % nameMap[playerid]

def updatescatter():
    df = select_players()
    x_name = axis_map[x_axis.value]
    y_name = axis_map[y_axis.value]
    p.xaxis.axis_label = x_axis.value
    p.yaxis.axis_label = y_axis.value
    for position, data in position_data.items():
        dft = df[df['Position'] == position]
        data.data = dict(
            x=dft[x_name],
            y=dft[y_name],
            position=dft['Position'],
            name=dft['PlayerName'],
            redcards=dft['redcards'],
            pensconceded=dft['pensconceded'],
            errors=dft['errors'],
            owngoals=dft['owngoals'],
            playerid=dft['PlayerID']
        )

index = ['Midfielder', 0, 12136]

def updatesize():
    size = 0
    df = select_players()
    for position in positions:
        if legend_items[position].visible:
            size += len(df[df['Position'] == position])
    p.title.text = '%d players selected' % size

def updatehighlighted():
    position_data[index[0]].selected.indices = [index[1]]

def goalkeeper(attr, old, new):
    try:
        global index
        id = position_data['Goalkeeper'].data['playerid'].iloc[new[0]]
        index = ['Goalkeeper', new[0], id]
        highlight_name.value = nameMap[id]
    except IndexError:
        pass

def defender(attr, old, new):
    try:
        global index
        id = position_data['Defender'].data['playerid'].iloc[new[0]]
        index = ['Defender', new[0], id]
        highlight_name.value = nameMap[id]
    except IndexError:
        pass

def midfielder(attr, old, new):
    try:
        global index
        id = position_data['Midfielder'].data['playerid'].iloc[new[0]]
        index = ['Midfielder', new[0], id]
        highlight_name.value = nameMap[id]
    except IndexError:
        pass

def forward(attr, old, new):
    try:
        global index
        id = position_data['Forward'].data['playerid'].iloc[new[0]]
        index = ['Forward', new[0], id]
        highlight_name.value = nameMap[id]
    except IndexError:
        pass

renderers[0].data_source.selected.on_change('indices', goalkeeper)
renderers[1].data_source.selected.on_change('indices', defender)
renderers[2].data_source.selected.on_change('indices', midfielder)
renderers[3].data_source.selected.on_change('indices', forward)

controls = [minutes, x_axis, y_axis, highlight_name]
for control in controls:
    control.on_change('value', lambda attr, old, new: updatescatter())
highlight_name.on_change('value', lambda attr, old, new: updatebar())
highlight_name.on_change('value', lambda attr, old, new: updatehighlighted())
minutes.on_change('value', lambda attr, old, new: updatesize())

for position in positions:
    legend_items[position].on_change('visible', lambda attr, old, new: updatesize())

p.on_event(events.Tap, updatehighlighted)

inputs = column(*controls, width=250)

l = column(desc, row(inputs, p), q, sizing_mode='scale_both')

q.add_layout(q.legend[0], 'right')
updatescatter()  # initial load of the scatter data
updatebar()  # initial load of the bar data
updatesize()
curdoc().add_root(l)
curdoc().title = 'Players'

position_data['Midfielder'].selected.indices = [0]

show(l)