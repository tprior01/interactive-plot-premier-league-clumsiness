import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div, Select, LabelSet, Label, RangeSlider, TextInput
from bokeh.plotting import figure
from os.path import dirname, join

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

desc = Div(text=open(join(dirname(__file__), 'my-application/description.html')).read(), sizing_mode="stretch_width")
minutes = RangeSlider(title='Number of minutes', value=(0, max_mins), start=0, end=max_mins, step=10)
position = Select(title='Position', value="All", options=positions)
highlight_name = TextInput(title='Highlight player name containing', value='Xhaka')
x_axis = Select(title='X Axis', options=sorted(axis_map.keys()), value='Minutes')
y_axis = Select(title='Y Axis', options=sorted(axis_map.keys()), value='Total Mistakes')

# Create Column Data Source that will be used by the plot
position_data = {
    'Goalkeeper': ColumnDataSource(data=dict(x=[], y=[])),
    'Defender': ColumnDataSource(data=dict(x=[], y=[])),
    'Midfielder': ColumnDataSource(data=dict(x=[], y=[])),
    'Forward': ColumnDataSource(data=dict(x=[], y=[]))
}

TOOLTIPS=[
    ('Name', '@name'),
    ('Red Cards', '@redcards'),
    ('Penalties Conceded', '@pensconceded'),
    ('Errors leading to a goal', '@errors')
]

p = figure(height=600, width=700, title='', toolbar_location=None, tooltips=TOOLTIPS, sizing_mode='scale_both')
p.circle(x='x', y='y', source=position_data['Goalkeeper'], size=6, color='hotpink', line_color=None, legend_label='Goalkeeper')
p.circle(x='x', y='y', source=position_data['Defender'], size=6, color='salmon', line_color=None, legend_label='Defender')
p.circle(x='x', y='y', source=position_data['Midfielder'], size=6, color='teal', line_color=None, legend_label='Midfielder')
p.circle(x='x', y='y', source=position_data['Forward'], size=6, color='cyan', line_color=None, legend_label='Forward')
p.legend.location = "top_left"
p.legend.click_policy="hide"

def select_players():
    selected = players[
        (players.minutes >= minutes.value[0]) &
        (players.minutes <= minutes.value[1])
        ]
    if position.value != 'All':
        selected = selected[selected['Position'] == position.value]
    return selected

def update():
    df = select_players()
    x_name = axis_map[x_axis.value]
    y_name = axis_map[y_axis.value]
    p.xaxis.axis_label = x_axis.value
    p.yaxis.axis_label = y_axis.value
    p.title.text = '%d players selected' % len(df)
    for position, data in position_data:
        data.data = dict(
        x=df[df['Position'] == position][x_name],
        y=df[df['Position'] == position][y_name],
        color=df[df['Position'] == position]['color'],
        position=df[df['Position'] == position]['Position'],
        name=df[df['Position'] == position]['PlayerName'],
        redcards=df[df['Position'] == position]['redcards'],
        pensconceded=df[df['Position'] == position]['pensconceded'],
        errors=df[df['Position'] == position]['errors']
    )

controls = [minutes, position, x_axis, y_axis, highlight_name]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())

inputs = column(*controls, width=250)

l = column(desc, row(inputs, p), sizing_mode='scale_both')

update()  # initial load of the data
curdoc().add_root(l)
curdoc().title = 'Players'
