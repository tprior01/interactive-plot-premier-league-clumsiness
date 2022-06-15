import pandas as pd
from bokeh.io import curdoc, show
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div, Select, AutocompleteInput, RangeSlider, Range1d, FactorRange, CustomJS, \
    DataRange1d
from bokeh.plotting import figure
from os.path import dirname, join

csv = 'data/data.csv'
players = pd.read_csv(csv)


coulour_map = {'All': '', 'Goalkeeper': ' hotpink', 'Defender': 'salmon', 'Midfielder': 'teal', 'Forward': 'turquoise'}
positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
directories = ['redcards', 'errors', 'pensconceded']
colours = ['hotpink', 'salmon', 'teal', 'turquoise']


players['color'] = players['Position'].map(coulour_map)
max_mins = round(players['minutes'].max(), -1)
ids = players['PlayerID'].values.tolist()
names = players['PlayerName'].values.tolist()
id_dic = dict()
for i in range(len(ids)):
    id_dic[names[i]] = ids[i]
print(id_dic)

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

position_data = {
    'Goalkeeper': ColumnDataSource(data=dict(x=[], y=[])),
    'Defender': ColumnDataSource(data=dict(x=[], y=[])),
    'Midfielder': ColumnDataSource(data=dict(x=[], y=[])),
    'Forward': ColumnDataSource(data=dict(x=[], y=[]))
}


p = figure(height=600, width=700, title='', toolbar_location=None, tooltips=TOOLTIPS, sizing_mode='scale_both')

for position, data, colour in zip(position_data.keys(), position_data.values(), colours):
    p.circle(x='x', y='y', source=position_data[position], size=6, color=colour, line_color=None, legend_label=position)

# r = p.circle(x='x', y='y', source=source, size=6, color='color', line_color=None, legend_field='position')
# p.circle(x='x', y='y', source=highlight, size=11, line_color='black', fill_alpha=0, line_width=1)
legend = p.legend
legend.location = "top_left"
legend.click_policy="hide"
p.x_range = DataRange1d(range_padding=0.0, only_visible=True)
p.y_range = DataRange1d(range_padding=0.0, only_visible=True)


# p.hover.renderers = [r]

# bar chart
q = figure(x_range=seasonal.data['seasons'], title='%s mistakes by season' % highlight_name.value, height=150, toolbar_location=None, tools="")
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
    return selected

def highlight_players(selected):
    if (highlight_name.value != ""):
        selected = selected[selected['PlayerName'].str.contains(highlight_name.value.strip(), case=False)]
    else:
        selected = selected[selected['PlayerName'] == None]
    return selected


def updatebar():
    if (highlight_name.value in names):
        playerid = id_dic[highlight_name.value]
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
        seasonal.data = data
        q.x_range.factors = seasonal.data['seasons']

def updatescatter():
    df = select_players()
    df2 = highlight_players(df)
    x_name = axis_map[x_axis.value]
    y_name = axis_map[y_axis.value]
    p.xaxis.axis_label = x_axis.value
    p.yaxis.axis_label = y_axis.value
    p.title.text = '%d players selected' % len(df)
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
    highlight.data = dict(
        x=df2[x_name],
        y=df2[y_name],
    )

controls = [minutes, x_axis, y_axis, highlight_name]
for control in controls:
    control.on_change('value', lambda attr, old, new: updatescatter())
highlight_name.on_change('value', lambda attr, old, new: updatebar())

inputs = column(*controls, width=250)

l = column(desc, row(inputs, p), q, sizing_mode='scale_both')

q.add_layout(q.legend[0],'right')
updatescatter()  # initial load of the data
updatebar()
curdoc().add_root(l)
curdoc().title = 'Players'

show(l)