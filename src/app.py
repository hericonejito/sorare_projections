import requests
import json
import pandas as pd
import numpy as np
from time import sleep
import os
from pulp import *
from dash.dash_table.Format import Scheme, Format
from dash import Dash, dcc, html, Input, Output,callback, dash_table
from dash.dependencies import Input, Output, State
import dash_table
import numpy as np
import dash_core_components as dcc
import plotly.graph_objects as go
import dash_html_components as html
from plotly.subplots import make_subplots
from pulp import *
import pandas as pd
import numpy as np
own_limited =['Luka Doncic', 'Kawhi Leonard', 'Jalen Brunson', 'James Harden', 'Jrue Holiday', 'Jaren Jackson Jr.', 'Keldon Johnson', 'Nikola Vucevic', 'C.J. McCollum',"Tyrese Maxey", 'O.G. Anunoby', 'Brook Lopez', 'Scottie Barnes', 'Tyler Herro', 'Julius Randle', 'Derrick White', 'Al Horford', 'Jakob Poeltl', 'Bruce Brown', 'Josh Hart', 'Tyus Jones', 'Jalen Johnson', 'Isaiah Hartenstein', 'P.J. Tucker', 'Cam Payne', 'Cody Martin', 'Paul Reed', 'Jevon Carter', 'Shake Milton', 'Joe Harris', 'Ziaire Williams', 'Haywood Highsmith', 'Ryan Arcidiacono', 'Jeff Green', 'Omer Yurtseven', 'Max Christie']
own_rare = ["LaMelo Ball",'Fred VanVleet', 'Desmond Bane', 'Chris Paul', 'Evan Mobley', 'O.G. Anunoby', 'Scottie Barnes', 'Deandre Ayton', 'Ivica Zubac', 'Xavier Tillman', 'Jakob Poeltl', 'John Collins', 'Isaiah Jackson', 'Josh Hart', 'Onyeka Okongwu', 'Jalen Suggs', "De'Anthony Melton", 'Precious Achiuwa', 'Dominick Barlow', 'Eric Gordon', 'Trey Lyles', 'Brandon Boston Jr.', 'Thaddeus Young', 'Cole Swider', 'Jake LaRavia',"Patrick Williams","Damian Jones",'Drew Eubanks','Keon Johnson']
def optimize_lineup(df, competition,projection_type):
    temp_df = df.copy()
    projection_to_use = 'proj_score'
    if projection_type=='Ceiling':
        projection_to_use = 'proj_ceiling'
        temp_df = temp_df.sort_values(by='proj_ceiling',ascending=False)
    comp_cap = 120
    comp_players = 4
    if competition=='Contender':
        comp_cap=110
        comp_players = 5
    elif competition=='Underdog':
        comp_cap=60
        comp_players=5
    elif competition=='Champion':

        champion_name = temp_df.iloc[0]['displayName']
        champion_score = temp_df.iloc[0][projection_to_use]
        temp_df = temp_df.iloc[1:]
    inv_item = list(temp_df['displayName'])
    x = dict(zip(inv_item, temp_df['tenGameAverage']))
    y = dict(zip(inv_item, temp_df[projection_to_use]))
    # z = dict(zip(inv_item, df['Lim.']))
    prob = LpProblem('Sorare', LpMaximize)
    inv_vars = LpVariable.dicts('Varirable', inv_item, lowBound=0, cat='Integer')
    prob += lpSum([inv_vars[i] * y[i] for i in inv_item])
    prob += lpSum([inv_vars[i] * x[i] for i in inv_item]) <= comp_cap, competition
    # prob += lpSum([inv_vars[i] * z[i] for i in inv_item]) <= 800, 'Price Cap'
    prob += lpSum([inv_vars[i] for i in inv_item]) == comp_players, 'Number of Players'
    for name in inv_vars:
        prob += inv_vars[name] <= 1

    prob.solve()
    print('The optimal answer\n' + '-' * 70)
    total_score = 0
    variables = []
    for v in prob.variables():
        if v.varValue > 0:
            print(v.name, '=', v.dj)
            total_score +=v.dj
            variables.append(f'{v.name.split("_")[1]} {v.name.split("_")[2]}')
    if competition=='Champion':
        print(f"{champion_name} : {champion_score}")
        total_score+=champion_score
        variables.append(champion_name)
    print(f"Expected Score : {total_score}")
    return variables

projections_files =['Export_2023_11_06','Export_2023_11_08','Export_2023_11_09']
total_df = pd.DataFrame()
for file in projections_files:
    df = pd.read_csv(f'data/{file}.csv',index_col=False)
    total_df = pd.concat([total_df,df])
players_dict = pd.read_pickle('data/players_dict.pkl')
total_df = total_df.groupby('id').agg(
        {'value': 'max', 'id': 'count', 'first_name': 'first', 'last_name': 'first'}).sort_values(by='value',
                                                                                                  ascending=False)
total_df['displayName']=total_df['first_name'].astype(str) + " " + total_df['last_name'].astype(str)

caps = pd.read_csv('data/sorare_caps.csv')
caps = caps.sort_values(by='tenGameAverage',ascending=False)
game_logs = pd.read_csv('data/game_logs_sorare.csv')
game_logs = game_logs[game_logs['gw']!=35]
game_logs = game_logs[game_logs['gw']<48]
game_logs.columns = ['Unnamed: 0', 'slug', 'playedInGame', 'player_age', 'team_name',
       'against', 'date', 'gw', 'points', 'rebounds', 'assists', 'blocks',
       'steals', 'turnovers', 'fieldGoalAttempts', 'freeThrowAttempts',
       'made3PointFGs', 'doubleDoubles', 'tripleDoubles', 'score']
game_logs_combined = game_logs.groupby('slug').agg(mean_score=('score',"mean"),std = ('score',"std"),games=("score",'count'),ceiling=("score","max"))
caps= caps.join(game_logs_combined,on='slug')
players_in_cap = list(caps['displayName'].unique())
# players_in_projections = list(total_df['displayName'].unique())
# players_dict= {}
for player_in_cap,player_corr in players_dict.items():


    if len(caps.loc[caps['displayName']==player_in_cap,'displayName'])>0:
         caps.loc[caps['displayName']==player_in_cap,'displayName']=player_corr
         slug = caps[caps['displayName']==player_corr]['slug'].values[0]
         ten_game_average= caps[caps['displayName']==player_corr]['tenGameAverage'].values[0]
         game_logs[np.logical_and(game_logs['slug']==slug,game_logs['score']>ten_game_average)]

total_df = total_df.set_index(total_df['displayName'])
caps = caps.set_index(caps['displayName'])
projections=  pd.concat([total_df,caps],axis=1)
projections = projections[projections['value'].notna()].fillna(0)
projections['proj_score'] = (abs(1-projections['id'])*0.4*projections['std'])+projections['value']
projections['proj_ceiling'] = 0.2*projections['ceiling']+0.8*projections['proj_score']
projections = projections.sort_values(by='proj_score',ascending=False)
projections =projections.iloc[:,[1,4,7,8,15,16]]
projections.columns = [ 'games', 'displayName',
       'tenGameAverage',"slug",'proj_score','proj_ceiling']
# df = pd.read_csv('d:/test/projections_with_caps.csv')
# df = df.set_index(df['displayName'])
# df['tenGameAverage'].fillna(0,inplace=True)
projections['tenGameAverage'] = projections['tenGameAverage'].astype(int)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__,external_stylesheets=external_stylesheets)
# Declare server for Heroku deployment. Needed for Procfile.
server = app.server
app.layout = html.Div(children=[
    html.H1(
        children='Projections',
        style={
            'textAlign': 'center',

        }
    ),#end of H1
    html.Div([html.Div([
        dcc.RadioItems(['Champion', 'Contender','Underdog'], 'Champion',id='contest',inline=True),
              dcc.RadioItems(['ProjectedScore', 'Ceiling'], 'ProjectedScore',id='projection',inline=True),
                       html.Button('Optimize', id='optimize', n_clicks=0)
    ]
                       ),
        html.Div(id='optimizer_results'),
dash_table.DataTable(
                id='table_z',
                columns=[{"name": i, "id": i, 'format': Format(
                            precision=3,
                            scheme=Scheme.fixed,

                        ),}  for i in projections.columns],
                style_cell={'textAlign': 'left'},
                editable=True,
                #filter_action="native",
                sort_action="native",
                sort_mode="single",
                column_selectable="single",
            #     fixed_columns={'headers':True,'data':2},
            #     style_table ={'max-width':'100% !important'},
                row_selectable="multi",
                #row_deletable=True,
                #column_deletable = True,
                selected_columns=[],
                selected_rows=[],
                page_action="native",
                page_current= 0,
                page_size= 100,
                data=projections.round(3).to_dict('records'),
                ),# end of datatable


             ]),

        ])

@callback(
    Output('optimizer_results', 'children'),
    Input('optimize', 'n_clicks'),
    State('contest', 'value'),
State('projection', 'value'),
    prevent_initial_call=True
)
def update_output(n_clicks, contest_type,projection_type):
    names_used =  optimize_lineup(projections,contest_type,projection_type)
    return [f"{name} - " for name in names_used]


if __name__ == "__main__":
    app.run_server(debug=True)