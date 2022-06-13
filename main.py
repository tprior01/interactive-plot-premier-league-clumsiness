import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div, Select, Slider, LegendItem, Legend
from bokeh.plotting import figure
from os.path import dirname, join

csv = 'data/data.csv'
players = pd.read_csv(csv)
colours = {'All':'','Goalkeeper': ' hotpink', 'Defender': 'salmon', 'Midfielder': 'teal', 'Forward': 'turquoise'}
positions = list(colours.keys())
players['color'] = players['Position'].map(colours)

axis_map = {
    'Minutes': 'minutes',
    'Total Mistakes': 'sumerrors',
    'Red Cards': 'redcards',
    'Penalties Conceded': 'pensconceded',
    'Errors leading to a goal': 'errors'
}

desc = Div(text=open(join(dirname(__file__), 'my-application/description.html')).read(), sizing_mode="stretch_width")
minutes = Slider(title='Minimum number of minutes', value=0, start=0, end=round(players['minutes'].max(),-1), step=10)
position = Select(title='Position', value="All", options=positions)
x_axis = Select(title='X Axis', options=sorted(axis_map.keys()), value='Minutes')
y_axis = Select(title='Y Axis', options=sorted(axis_map.keys()), value='Total Mistakes')

# Create Column Data Source that will be used by the plot
source = ColumnDataSource(data=dict(x=[], y=[], position=[], color=[], redcards=[], pensconceded=[], errors=[], alpha=[]))

TOOLTIPS=[
    ('Name', '@name'),
    ('Red Cards', '@redcards'),
    ('Penalties Conceded', '@pensconceded'),
    ('Errors leading to a goal', '@errors')
]

p = figure(height=600, width=700, title='', toolbar_location=None, tooltips=TOOLTIPS, sizing_mode='scale_both')
p.circle(x='x', y='y', source=source, size=6, color='color', line_color=None, legend_field='position')
p.legend.location = "top_left"

# # legend
# legend_items = []
# for position, colour in colours:
#     l = LegendItem(label = position, color=colour)
# legend = Legend(items=legend_items, location='top_left')
# p.add_layout(legend)

def select_players():
    selected = players[(players.minutes >= minutes.value)]
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

controls = [minutes, position, x_axis, y_axis]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())

inputs = column(*controls, width=250)

l = column(desc, row(inputs, p), sizing_mode='scale_both')

update()  # initial load of the data
curdoc().add_root(l)
curdoc().title = 'Players'