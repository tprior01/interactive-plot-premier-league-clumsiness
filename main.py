import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Div, Select, AutocompleteInput, RangeSlider, DataRange1d, \
    SingleIntervalTicker, Circle
from bokeh.plotting import figure
from bokeh import events

# data
csv = 'data.csv'
totals = pd.read_csv(csv, index_col='PlayerID')

# create maps
playerIDs = totals.index.values.tolist()
playerShortNames = totals['PlayerShortName'].values.tolist()
playerPositions = totals['Position'].values.tolist()
idMap = dict()
nameMap = dict()
positionMap = dict()
for i in range(len(playerIDs)):
    if playerShortNames[i] not in idMap:
        idMap[playerShortNames[i]] = [str(playerIDs[i])]
    else:
        idMap[playerShortNames[i]].append(str(playerIDs[i]))
    positionMap[str(playerIDs[i])] = playerPositions[i]
    nameMap[str(playerIDs[i])] = playerShortNames[i]
playerShortNames = list(set(playerShortNames))
playerShortNames.sort()

# more data
playerPositions = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
directories = ['redcards', 'errors', 'pensconceded', 'owngoals']
positionColours = ['hotpink', 'salmon', 'teal', 'turquoise']
barColours = ['hotpink', 'teal', 'salmon', 'turquoise']
categories = ['Red Cards', 'Errors Leading to a Goal', 'Penalties Conceded', 'Own Goals']
maxMins = round(totals['minutes'].max(), -1)
axisMap = {
    'Minutes': 'minutes',
    'Total Mistakes': 'sumerrors',
    'Red Cards': 'redcards',
    'Penalties Conceded': 'pensconceded',
    'Errors leading to a goal': 'errors',
    'Own goals': 'owngoals'
}

# text to display at the top of page
desc = Div(text=open('description.html').read(), sizing_mode="stretch_width")

# widgets
minutes = RangeSlider(title='Number of minutes', value=(0, maxMins), start=0, end=maxMins, step=10)
x_axis = Select(title='X Axis', options=sorted(axisMap.keys()), value='Minutes')
y_axis = Select(title='Y Axis', options=sorted(axisMap.keys()), value='Total Mistakes')
playerName = AutocompleteInput(title='Highlighted player name:', value='Xhaka', completions=playerShortNames,
                               restrict=True, case_sensitive=False)
playerID = Select(title='Highlighted player ID:', value='12136', options=idMap[playerName.value])

# column data sources
seasonal = ColumnDataSource(data=dict(seasons=[], redcards=[], pensconceded=[], errors=[], owngoals=[]))
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
q.add_layout(q.legend[0], 'right')


def selectPlayers():
    selected = totals[
        (totals.minutes >= minutes.value[0]) &
        (totals.minutes <= minutes.value[1])
        ]
    return selected


def updateBar():
    try:
        data = {
            'seasons': [],
            'redcards': [],
            'pensconceded': [],
            'errors': [],
            'owngoals': []
        }
        ID = int(playerID.value)
        for i in range(8, 23):
            df = pd.read_csv(f"minutes/{i}.csv", index_col='PlayerID')
            try:
                df.loc[ID].index
            except KeyError:
                continue
            data['seasons'].append(f'{str(i - 1).zfill(2)}/{str(i).zfill(2)}')
            for directory in directories:
                try:
                    x = pd.read_csv(f"{directory}/{i}.csv", index_col='PlayerID').loc[ID].values[0]
                except KeyError:
                    x = 0
                data[directory].append(x)
        seasonal.data = data
        q.x_range.factors = seasonal.data['seasons']
        temp = totals[totals.index == playerID.value][['PlayerName', 'Position']]
        q.title.text = f"{temp['PlayerName'].values[0]} ({temp['Position'].values[0]}) mistakes by season"
    except IndexError:
        pass


def updateScatter():
    df = selectPlayers()
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
            playerid=dft.index
        )


def updateSize():
    size = 0
    df = selectPlayers()
    for position in playerPositions:
        if legend_items[position].visible:
            size += len(df[df['Position'] == position])
    p.title.text = '%d players selected' % size


def updateHighlighted():
    id = playerID.value
    position = positionMap[id]
    indice = positionData[position].data['playerid'].values.tolist().index(int(id))
    for pos in playerPositions:
        positionData[pos].selected.indices = []
    positionData[position].selected.indices = [indice]
    updateBar()


def goalkeeper(attr, old, new):
    try:
        playerID.value = str(positionData['Goalkeeper'].data['playerid'][new[0]])
        playerName.value = nameMap[playerID.value]
    except IndexError:
        pass


def defender(attr, old, new):
    try:
        playerID.value = str(positionData['Defender'].data['playerid'][new[0]])
        playerName.value = nameMap[playerID.value]
    except IndexError:
        pass


def midfielder(attr, old, new):
    try:
        playerID.value = str(positionData['Midfielder'].data['playerid'][new[0]])
        playerName.value = nameMap[playerID.value]
    except IndexError:
        pass


def forward(attr, old, new):
    try:
        playerID.value = str(positionData['Forward'].data['playerid'][new[0]])
        playerName.value = nameMap[playerID.value]
    except IndexError:
        pass


def updateIdList():
    playerID.options = idMap[playerName.value]
    playerID.value = playerID.options[0]


# on_change and on_event actions
x_axis.on_change('value', lambda attr, old, new: updateScatter())
y_axis.on_change('value', lambda attr, old, new: updateScatter())
playerName.on_change('value', lambda attr, old, new: updateIdList())
playerID.on_change('value', lambda attr, old, new: updateScatter())
playerID.on_change('value', lambda attr, old, new: updateHighlighted())
minutes.on_change('value', lambda attr, old, new: updateScatter())
minutes.on_change('value', lambda attr, old, new: updateSize())
minutes.on_change('value', lambda attr, old, new: updateHighlighted())

renderers[0].data_source.selected.on_change('indices', goalkeeper)
renderers[1].data_source.selected.on_change('indices', defender)
renderers[2].data_source.selected.on_change('indices', midfielder)
renderers[3].data_source.selected.on_change('indices', forward)

for position in playerPositions:
    legend_items[position].on_change('visible', lambda attr, old, new: updateSize())

p.on_event(events.Tap, updateHighlighted)

controls = [minutes, x_axis, y_axis, playerName, playerID]
inputs = column(*controls, width=250)
layout = column(desc, row(inputs, p), q, sizing_mode='scale_both', max_width=1000)

updateScatter()
updateBar()
updateSize()
updateHighlighted()

curdoc().add_root(layout)
curdoc().title = 'Players'