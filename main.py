import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div, Select, AutocompleteInput, LabelSet, Label, RangeSlider, TextInput
from bokeh.plotting import figure
from os.path import dirname, join
import numpy as np

csv = 'data/data.csv'
players = pd.read_csv(csv)
colours = {'All':'','Goalkeeper': ' hotpink', 'Defender': 'salmon', 'Midfielder': 'teal', 'Forward': 'turquoise'}
positions = list(colours.keys())
players['color'] = players['Position'].map(colours)
max_mins = round(players['minutes'].max(), -1)

axis_map = {
    'Minutes': 'minutes',
    'Total Mistakes': 'sumerrors',
    'Red Cards': 'redcards',
    'Penalties Conceded': 'pensconceded',
    'Errors leading to a goal': 'errors'
}

full_names = players['PlayerName'].values.tolist()
last_names = list()
for i in range(len(full_names)):
    last_names.append(full_names[i].rsplit(' ', 1)[-1])
names = list(set(last_names + full_names))

desc = Div(text=open(join(dirname(__file__), 'my-application/description.html')).read(), sizing_mode="stretch_width")
minutes = RangeSlider(title='Number of minutes', value=(0, max_mins), start=0, end=max_mins, step=10)
position = Select(title='Position', value="All", options=positions)
highlight_name = AutocompleteInput(title='Highlight player', value='Xhaka', completions=names,
                                   restrict=False, case_sensitive=False)
x_axis = Select(title='X Axis', options=sorted(axis_map.keys()), value='Minutes')
y_axis = Select(title='Y Axis', options=sorted(axis_map.keys()), value='Total Mistakes')

# Create Column Data Source that will be used by the plot
source = ColumnDataSource(data=dict(x=[], y=[], position=[], color=[])) #, redcards=[], pensconceded=[], errors=[], alpha=[]))
highlight = ColumnDataSource(data=dict(x=[], y=[]))

TOOLTIPS=[
    ('Name', '@name'),
    ('Red Cards', '@redcards'),
    ('Penalties Conceded', '@pensconceded'),
    ('Errors leading to a goal', '@errors')
]

p = figure(height=600, width=700, title='', toolbar_location=None, tooltips=TOOLTIPS, sizing_mode='scale_both')
r = p.circle(x='x', y='y', source=source, size=6, color='color', line_color=None, legend_field='position')
p.circle(x='x', y='y', source=highlight, size=11, line_color='black', fill_alpha=0, line_width=1)
p.legend.location = "top_left"
p.hover.renderers = [r]

def select_players():
    selected = players[
        (players.minutes >= minutes.value[0]) &
        (players.minutes <= minutes.value[1])
        ]
    if position.value != 'All':
        selected = selected[selected['Position'] == position.value]
    return selected

def highlight_players(selected):
    if (highlight_name.value != ""):
        selected = selected[selected['PlayerName'].str.contains(highlight_name.value.strip(), case=False)]
    else:
        selected = selected[selected['PlayerName'] == None]
    return selected

def update():
    df = select_players()
    df2 = highlight_players(df)
    x_name = axis_map[x_axis.value]
    y_name = axis_map[y_axis.value]
    p.xaxis.axis_label = x_axis.value
    p.yaxis.axis_label = y_axis.value
    p.title.text = '%d players selected' % len(df)
    source.data = dict(
        x=df[x_name],
        y=df[y_name],
        color=df['color'],
        position=df['Position'],
        name=df['PlayerName'],
        redcards=df['redcards'],
        pensconceded=df['pensconceded'],
        errors=df['errors']
    )
    highlight.data = dict(
        x=df2[x_name],
        y=df2[y_name],
    )
    # par = np.polyfit(source.data['x'], source.data['y'], 1, full=True)
    # slope = par[0][0]
    # intercept = par[0][1]
    # y_predicted = [slope * i + intercept for i in source.data['x']]
    # p.line(source.data['x'], y_predicted, color='red')

controls = [minutes, position, x_axis, y_axis, highlight_name]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())

inputs = column(*controls, width=250)

l = column(desc, row(inputs, p), sizing_mode='scale_both')

update()  # initial load of the data
curdoc().add_root(l)
curdoc().title = 'Players'