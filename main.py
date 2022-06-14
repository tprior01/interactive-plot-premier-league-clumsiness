import pandas as pd
from bokeh.io import curdoc, show
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div, Select, AutocompleteInput, RangeSlider, Range1d, FactorRange
from bokeh.plotting import figure
from os.path import dirname, join

csv = 'data/data.csv'
players = pd.read_csv(csv)


coulour_map = {'All': '', 'Goalkeeper': ' hotpink', 'Defender': 'salmon', 'Midfielder': 'teal', 'Forward': 'turquoise'}
positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
directories = ['redcards', 'errors', 'pensconceded']

players['color'] = players['Position'].map(coulour_map)
max_mins = round(players['minutes'].max(), -1)
names = players[players['minutes'] > 1000]['PlayerName'].values.tolist()

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

# Create Column Data Source that will be used by the plot
source = ColumnDataSource(data=dict(x=[], y=[], position=[], color=[]))
highlight = ColumnDataSource(data=dict(x=[], y=[]))
seasonal = ColumnDataSource(data=dict(seasons=[], redcards=[], mpensconceded=[], errors=[]))
bar_colours = ["hotpink", "teal", "salmon"]
categories = ['Red Cards', 'Errors Leading to a Goal', 'Penalties Conceded']

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

# bar chart
q = figure(x_range=seasonal.data['seasons'], title="Mistakes by year", height=250, toolbar_location=None, tools="")
q.vbar_stack(directories, x='seasons', width=0.2, color=bar_colours, source=seasonal, legend_label=categories)
q.y_range.start = 0
q.xgrid.grid_line_color = None
q.axis.minor_tick_line_color = None
q.outline_line_color = None

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


def updatebarchart(selected):
    if (highlight_name.value != ""):
        playerid = selected['PlayerID'].iat[0]
        print(playerid)
        data = {
            'seasons': [],
            'redcards': [],
            'pensconceded': [],
            'errors': []
        }
        for i in range(8, 23):
            df = pd.read_csv(f"minutes/{i}.csv")
            if (df[df['PlayerID'] == playerid]['PlayerID'].count() == 1):
                data['seasons'].append(f'{str(i - 1).zfill(2)}/{str(i).zfill(2)}')
                for directory in directories:
                    dfx = pd.read_csv(f"{directory}/{i}.csv")
                    if (dfx[dfx['PlayerID'] == playerid][directory].count() == 1):
                        data[directory].append(dfx[dfx['PlayerID'] == playerid][directory].iloc[0])
                    else:
                        data[directory].append(0)
        return data

def update():
    df = select_players()
    df2 = highlight_players(df)
    # bar_dict = updatebarchart(df2)
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
    seasonal.data = bar_dict
    q.x_range.factors = seasonal.data['seasons']

controls = [minutes, position, x_axis, y_axis, highlight_name]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())

inputs = column(*controls, width=250)

l = column(desc, row(inputs, p), q, sizing_mode='scale_both')

q.add_layout(q.legend[0],'right')
update()  # initial load of the data
curdoc().add_root(l)
curdoc().title = 'Players'