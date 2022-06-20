import pandas as pd
from bokeh.io import curdoc, show
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div, Select, AutocompleteInput, RangeSlider, DataRange1d, \
    SingleIntervalTicker, Circle, Tap, NumericInput, Dropdown
from bokeh.plotting import figure
from os.path import dirname, join
from bokeh import events

# data
csv = 'data/data.csv'
players = pd.read_csv(csv)

maxMins = round(players['minutes'].max(), -1)
ids = players['PlayerID'].values.tolist()
names = players['PlayerName'].values.tolist()
positions = players['Position'].values.tolist()
nameMap = dict()
positionMap = dict()
for i in range(len(ids)):
    shortName = names[i].rsplit(' ', 1)[-1]
    nameMap[str(ids[i])] = shortName
    positionMap[str(ids[i])] = positions[i]
    names[i] = shortName
# idMap= {v: k for k, v in nameMap.items()}
idMap = dict()
for i in range(len(names)):
    if names[i] not in idMap:
        idMap[names[i]] = [str(ids[i])]
    else:
        idMap[names[i]].append(str(ids[i]))
names = list(set(names))
ids.sort()
names.sort()


positions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
directories = ['redcards', 'errors', 'pensconceded', 'owngoals']
positionColours = ['hotpink', 'salmon', 'teal', 'turquoise']
barColours = ['hotpink', 'teal', 'salmon', 'turquoise']
categories = ['Red Cards', 'Errors Leading to a Goal', 'Penalties Conceded', 'Own Goals']

axisMap = {
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
minutes = RangeSlider(title='Number of minutes', value=(0, maxMins), start=0, end=maxMins, step=10)
x_axis = Select(title='X Axis', options=sorted(axisMap.keys()), value='Minutes')
y_axis = Select(title='Y Axis', options=sorted(axisMap.keys()), value='Total Mistakes')

playerName = AutocompleteInput(title='Highlight player', value='Xhaka', completions=names, restrict=True, case_sensitive=False)
playerID = Select(value='12136', options=idMap[playerName.value])
# playerPosition = Select(value='Midfielder', options=positions)

# column data sources
highlight = ColumnDataSource(data=dict(x=[], y=[]))
seasonal = ColumnDataSource(data=dict(seasons=[], redcards=[], pensconceded=[], errors=[]))
positionData = dict(Goalkeeper=ColumnDataSource(data=dict(x=[], y=[])),
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
for position, data, colour in zip(positionData.keys(), positionData.values(), positionColours):
    temp = p.circle(x='x', y='y', source=positionData[position], size=8, color=colour, line_color=None, legend_label=position)
    renderers.append(temp)
    legend_items[position] = temp
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
q.vbar_stack(directories, x='seasons', width=0.2, color=barColours, source=seasonal, legend_label=categories)
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


def getBarData(playerID):
    data = {
        'seasons': [],
        'redcards': [],
        'pensconceded': [],
        'errors': [],
        'owngoals': []
    }
    for i in range(8, 23):
        df = pd.read_csv(f"minutes/{i}.csv")
        if df[df['PlayerID'] == playerID]['PlayerID'].count() == 1:
            data['seasons'].append(f'{str(i - 1).zfill(2)}/{str(i).zfill(2)}')
            for directory in directories:
                dfx = pd.read_csv(f"{directory}/{i}.csv")
                if dfx[dfx['PlayerID'] == playerID][directory].count() == 1:
                    data[directory].append(dfx[dfx['PlayerID'] == playerID][directory].iloc[0])
                else:
                    data[directory].append(0)
    return data


def updatebar():
    # playerID = index[2]
    seasonal.data = getBarData(int(playerID.value))
    q.x_range.factors = seasonal.data['seasons']
    q.title.text = '%s mistakes by season' % nameMap[playerID.value]


def updatescatter():
    df = select_players()
    x_name = axisMap[x_axis.value]
    y_name = axisMap[y_axis.value]
    p.xaxis.axis_label = x_axis.value
    p.yaxis.axis_label = y_axis.value
    for position, data in positionData.items():
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
    # positionData[index[0]].selected.indices = [index[1]]
    id = playerID.value
    position = positionMap[id]
    indice = positionData[position].data['playerid'].values.tolist().index(int(id))
    positionData[position].selected.indices = [indice]
    updatebar()



def goalkeeper(attr, old, new):
    try:
        # global index
        # id = positionData['Goalkeeper'].data['playerid'].iloc[new[0]]
        # index = ['Goalkeeper', new[0], id]
        # playerName.value = nameMap[id]
        playerID.value = str(positionData['Goalkeeper'].data['playerid'].iloc[new[0]])
        playerName.value = nameMap[playerID.value]
    except IndexError:
        pass

def defender(attr, old, new):
    try:
        # global index
        # id = positionData['Defender'].data['playerid'].iloc[new[0]]
        # index = ['Defender', new[0], id]
        # playerName.value = nameMap[id]
        playerID.value = str(positionData['Defender'].data['playerid'].iloc[new[0]])
        playerName.value = nameMap[playerID.value]
    except IndexError:
        pass


def midfielder(attr, old, new):
    try:
        # global index
        # id = positionData['Midfielder'].data['playerid'].iloc[new[0]]
        # index = ['Midfielder', new[0], id]
        # playerName.value = nameMap[id]
        playerID.value = str(positionData['Midfielder'].data['playerid'].iloc[new[0]])
        playerName.value = nameMap[playerID.value]
    except IndexError:
        pass


def forward(attr, old, new):
    try:
        # global index
        # id = positionData['Forward'].data['playerid'].iloc[new[0]]
        # index = ['Forward', new[0], id]
        # playerName.value = nameMap[id]
        playerID.value = str(positionData['Forward'].data['playerid'].iloc[new[0]])
        playerName.value = nameMap[playerID.value]
    except IndexError:
        pass


def highlightbar():
    try:
        global index
        if playerName.value == nameMap[index[2]]:
            positionData[index[0]].selected.indices = [index[1]]
        else:
            id = idMap[playerName.value]
            position = positionMap[id]
            indice = positionData[position].data['playerid'].values.tolist().index(id)
            index = [position, indice, id]
            print(index)
            updatebar()
            updatehighlighted()
    except IndexError:
        pass
    except TypeError:
        pass
    except KeyError:
        pass

def updateIdList():
    playerID.options = idMap[playerName.value]
    playerID.value = playerID.options[0]

renderers[0].data_source.selected.on_change('indices', goalkeeper)
renderers[1].data_source.selected.on_change('indices', defender)
renderers[2].data_source.selected.on_change('indices', midfielder)
renderers[3].data_source.selected.on_change('indices', forward)

controls = [minutes, x_axis, y_axis, playerName, playerID]
for control in controls:
    control.on_change('value', lambda attr, old, new: updatescatter())
playerName.on_change('value', lambda attr, old, new: updateIdList())
playerID.on_change('value', lambda attr, old, new: updatehighlighted())

# playerName.on_change('value', lambda attr, old, new: highlightbar())
minutes.on_change('value', lambda attr, old, new: updatesize())

for position in positions:
    legend_items[position].on_change('visible', lambda attr, old, new: updatesize())

p.on_event(events.Tap, updatehighlighted)

inputs = column(*controls, width=250)

l = column(desc, row(inputs, p), q, sizing_mode='scale_both', max_width=1000)

q.add_layout(q.legend[0], 'right')
updatescatter()  # initial load of the scatter data
updatebar()  # initial load of the bar data
updatesize()
curdoc().add_root(l)
curdoc().title = 'Players'

positionData['Midfielder'].selected.indices = [0]

show(l)