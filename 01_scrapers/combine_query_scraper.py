import requests
import time
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np


for yr in range(2000, 2019):

  annual_players = []

  # main query
  url = 'https://www.pro-football-reference.com/play-index/nfl-combine-results.cgi?request=1&year_min=' + str(yr) + '&year_max=' + str(yr) + '&pos%5B%5D=SS&pos%5B%5D=FS&pos%5B%5D=S&pos%5B%5D=CB&show=all&order_by=year_id'

  r = requests.get(url)

  soup = BeautifulSoup(r.content, 'html.parser')

  table = soup.find('table', id='results')

  if table == None:
    print(r.status_code)
  #  print(r.text)
  else:
    print('Found a table!')

  body = table.find('tbody')
  rows = body.find_all('tr')

  # COMBINE
  for row in rows:
    
    # iterate through rows and collect p
    cells = row.find_all('td')
    if len(cells) < 5:
      continue
    else:
      p = {
        'nfl_url': '',
        'ncaa_url': ''
      }

      p['combine_year'] = cells[0].text.strip()

      # NFL URL
      b = cells[1].find_all('a', href=True)
      if len(b) > 0:
        p['nfl_url'] = 'https://www.pro-football-reference.com' + b[0]['href']

      p['name'] = cells[1].text.strip()
      p['college'] = cells[4].text.strip()

      # NCAA URL
      a = cells[5].find_all('a', href=True)
      if len(a) > 0:
        p['ncaa_url'] = a[0]['href']
      
      # Combine p
      p['height'] = cells[6].text.strip()
      p['weight'] = cells[7].text.strip()
      p['forty_yd'] = cells[8].text.strip()
      p['vertical'] = cells[9].text.strip()
      p['bench_reps'] = cells[10].text.strip()
      p['broad_jump'] = cells[11].text.strip()
      p['cone'] = cells[12].text.strip()
      p['shuttle'] = cells[13].text.strip()
      p['draft_info'] = cells[14].text.strip()
      
      # College Stats
      p['ncaa_yr_ct'] = 0
      p['games'] = 0
      p['tackles_solo'] = 0
      p['tackles_asst'] = 0
      p['tfl_yards'] = 0
      p['sacks'] = 0
      p['intercepts'] = 0
      p['int_ret_yards'] = 0
      p['int_td'] = 0
      p['passes_defended'] = 0
      p['fum_recovered'] = 0
      p['fum_yards'] = 0
      p['fum_td'] = 0
      p['ffum'] = 0
      p['kick_ret'] = 0
      p['kick_ret_yards'] = 0
      p['kick_ret_td'] = 0
      p['punt_ret'] = 0
      p['punt_ret_yards'] = 0
      p['punt_ret_td'] = 0

      if p['ncaa_url']:
        ncaa_r = requests.get(p['ncaa_url'])
        soup = BeautifulSoup(ncaa_r.content, 'html.parser')
        
        defense = ''
        defense = soup.find('div', id = 'all_defense')
        
        returns = ''
        returns = soup.find('div', id = 'all_kick_ret')

        if defense is not None:
          d_table = defense.find('table')
          if d_table:
            print('Defense: {}'.format(d_table.attrs))
            body = d_table.find('tbody')
            rows = body.find_all('tr')
            
            # collect NCAA defensive stats
            for row in rows:
              cells = row.find_all('td')
              if len(cells) < 5:
                break
              p['ncaa_yr_ct'] += 1
              if len(cells[4].text.strip()) != 0:
                p['games'] += int(cells[4].text.strip())
              if len(cells[5].text.strip()) != 0:
                p['tackles_solo'] += int(cells[5].text.strip())
              if len(cells[6].text.strip()) != 0:
                p['tackles_asst'] += int(cells[6].text.strip())
              if len(cells[8].text.strip()) != 0:
                p['tfl_yards'] += float(cells[8].text.strip())
              if len(cells[9].text.strip()) != 0:
                p['sacks'] += float(cells[9].text.strip())
              if len(cells[10].text.strip()) != 0:
                p['intercepts'] += int(cells[10].text.strip())
              if len(cells[11].text.strip()) != 0:
                p['int_ret_yards'] += int(cells[11].text.strip())
              if len(cells[13].text.strip()) != 0:
                p['int_td'] += int(cells[13].text.strip())
              if len(cells[14].text.strip()) != 0:
                p['passes_defended'] += int(cells[14].text.strip())
              if len(cells[15].text.strip()) != 0:
                p['fum_recovered'] += int(cells[15].text.strip())
              if len(cells[16].text.strip()) != 0:
                p['fum_yards'] += float(cells[16].text.strip())
              if len(cells[17].text.strip()) != 0:
                p['fum_td'] += int(cells[17].text.strip())
              if len(cells[18].text.strip()) != 0:
                p['ffum'] += int(cells[18].text.strip())

        if returns is not None:
          rt_table = returns.find('table')
          if rt_table:
            print('Returns: {}'.format(rt_table.attrs))
            body = rt_table.find('tbody')
            rows = body.find_all('tr')

            # collect NCAA returns stats
            for row in rows:
              cells = row.find_all('td')
              if len(cells[5].text.strip()) != 0:
                p['kick_ret'] += int(cells[5].text.strip())
              if len(cells[6].text.strip()) != 0:
                p['kick_ret_yards'] += int(cells[6].text.strip())
              if len(cells[8].text.strip()) != 0:
                p['kick_ret_td'] += int(cells[8].text.strip())
              if len(cells[9].text.strip()) != 0:
                p['kick_ret'] += int(cells[9].text.strip())
              if len(cells[10].text.strip()) != 0:
                p['kick_ret_yards'] += int(cells[10].text.strip())
              if len(cells[12].text.strip()) != 0:
                p['kick_ret_td'] += int(cells[12].text.strip())
      
      p['nfl_yr_ct'] = 0
      # NFL Years
      if p['nfl_url']:
        nfl_r = requests.get(p['nfl_url'])
        soup = BeautifulSoup(nfl_r.content, 'html.parser')
        
        defense = soup.find('div', id = 'all_defense')
        returns = soup.find('div', id = 'all_returns')

        if defense is not None:
          d_table = defense.find('table')
          if d_table:
            print('Defense: {}'.format(d_table.attrs))
            body = d_table.find('tbody')
            rows = body.find_all('tr')
            d_table_row_count = len(rows)
            if p['nfl_yr_ct'] < d_table_row_count:
              p['nfl_yr_ct'] = d_table_row_count

        if returns is not None:
          rt_table = returns.find('table')
          if rt_table:
            print('Returns: {}'.format(rt_table.attrs))
            body = rt_table.find('tbody')
            rows = body.find_all('tr')
            rt_table_row_count = len(rows)
            if p['nfl_yr_ct'] < rt_table_row_count:
              p['nfl_yr_ct'] = rt_table_row_count

      annual_players.append(p)
      print('Just appended players for {}'.format(yr))

  # create a DF to store the players
  if yr == 2000:
    df = pd.DataFrame()

  # create a DF for each year
  annual_df = pd.DataFrame(annual_players)

  # concatenate the current year's players with previous years
  df = pd.concat([df, annual_df])

# break out draft info
df['draft_team'], df['draft_round'], df['draft_pick'], df['draft_year'] = df.draft_info.str.split('\/', 4).str
df.drop(['draft_info'], axis=1)

# extract int for draft_round
df.draft_round = df.draft_round.str.extract('(\d+)')

# extract int for draft_pick
df.draft_pick = df.draft_pick.str.extract('(\d+)')

# fix height
df.height = df.height.str[:1].astype(int) * 12 + df.height.str[2:].astype(int)

df = df.reset_index(drop = True)
print(df)

df.to_csv('combine.csv')