import pandas as pd

seasons = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
directories = ['minutes', 'redcards', 'errors', 'pensconceded']

# main dataframe
df = pd.read_csv('/names/names.csv')
for directory in directories:
    # temporary dataframe for each directory
    dfx = pd.DataFrame({'PlayerID' : []})
    for season in seasons:
        # build up temporary dataframe by adding season data
        season_string = f'{directory}/{season}.csv'
        dfy = pd.read_csv(season_string)
        dfx = pd.concat([dfx, dfy], ignore_index=True)
    # group by id then sum season data and add to main dataframe
    dfx = dfx.groupby(['PlayerID']).sum()
    df = df.join(dfx, on='PlayerID', how='left').fillna(0)

# add new column summing other columns
df['sumerrors'] = df['redcards'] + df['pensconceded'] + df['errors']
df = df.sort_values(by=['sumerrors'], ascending=False)

df.to_csv('data.csv')
