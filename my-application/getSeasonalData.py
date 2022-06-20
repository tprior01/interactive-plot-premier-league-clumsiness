import pandas as pd

csv = '/Users/tom/Documents/Personal/Errors/data/data_ss2.csv'
path = '/Users/tom/Documents/Personal/Errors/'
players = pd.read_csv(csv)
directories = ['redcards', 'errors', 'pensconceded', 'owngoals']


ids = players['PlayerID'].values.tolist()

def getBarData(playerid):
    data = {
        'seasons': [],
        'redcards': [],
        'pensconceded': [],
        'errors': [],
        'owngoals': []
    }
    for i in range(8, 23):
        df = pd.read_csv(path + f"minutes/{i}.csv")
        if df[df['PlayerID'] == playerid]['PlayerID'].count() == 1:
            data['seasons'].append(f'{str(i - 1).zfill(2)}/{str(i).zfill(2)}')
            for directory in directories:
                dfx = pd.read_csv(path + f"{directory}/{i}.csv")
                if dfx[dfx['PlayerID'] == playerid][directory].count() == 1:
                    data[directory].append(dfx[dfx['PlayerID'] == playerid][directory].iloc[0])
                else:
                    data[directory].append(0)
    return data

for playerid in ids:
    df = pd.DataFrame.from_dict(getBarData(playerid))
    df.to_csv(path + f'seasonaldata/{playerid}.csv', index=False)
