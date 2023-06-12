import requests
import time
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import pickle
import sys
from collections import OrderedDict

# TO DO:
# loop through years 2006 - 2015 and add all players to a single team DF
# create a tuple for each player's name, class, school, year, assign id as key in dict
# if data looks suspect, compare values for dups, then look at keys/ids
# look to see that all teams have similar numbers of DBs
# DB -> Defensive Back in 2013-14
# source for home state, HS, birth date?  Search CSVs?  Kaggle?

def save(obj, name ):
    with open('player_ids/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load(name ):
    with open('player_ids/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

team = sys.argv[1]
team_name = team.replace(' ', '_').lower().strip()
print(team_name)


team_name = team_name
orgId = int(sys.argv[2])



df = None
player_ids = set()

team_url = 'https://web1.ncaa.org/stats/StatsSrv/careerteam'

for y in range(2005, 2017):

  # Division 1 is listed as 11 after 2014
  if y < 2014:
    div = 1
  else:
    div = 11

  team_formdata = {
    'sortOn': 0,
    'doWhat': 'display',
    'playerId': -100,
    'coachId': -100,
    'orgId': orgId,
    'academicYear': y,
    'division': div,
    'sportCode': 'MFB',
    'idx': ''
  }

  r = requests.post(team_url, data=team_formdata)
  print('PARSING: {}'.format(y))
  soup = BeautifulSoup(r.text, 'lxml')

  statstables = soup.find_all('table', attrs={ "class" : "statstable"})

  team_stats_table = statstables[0]
  ind_stats_table = statstables[1]

  rows = ind_stats_table.find_all('tr')
  rows = rows[3:]

  players = []
  
  for row in rows:
      p = {}
      cells = row.find_all('td')
      if len(cells) > 0:
        p['name'] = cells[0].text.strip()
        ahref = cells[0].find('a')
        _, id_string = ahref.get('href').split('(', 1)
        p['player_id'], _ = id_string.split(')')
        p['class'] = cells[1].text.strip()
        p['year'] = cells[2].text.strip()
        p['position'] = cells[3].text.strip()
        if p['position'] in ['CB', 'DB', 'FS', 'SS', 'S', 'Defensive Back']:
          players.append(p)
          player_ids.add(p['player_id'])
  year_df = pd.DataFrame(players)
  if df is not None:
    df = pd.concat([df, year_df], axis=0, ignore_index=True, sort=False)
  else:
    df = pd.DataFrame(year_df)

# clean class strings
df['class'] = df['class'].str.upper()
df['class'] = df['class'].str.strip('.')

# create player name in format to match Combine and NFL
df['last_name'], df['first_name'] = df.name.str.split(',', 1).str
df['player'] = df.loc[:, ['first_name', 'last_name']].apply(lambda x: ' '.join(x), axis=1)

# clean year
df.year, _ = df.year.str.split('-').str

# unify 'position'
df.position = df.position.str.replace('Defensive Back', 'DB')

# clean column names
df.drop(['name'], inplace=True, axis=1)
cols = df.columns.tolist()
cols = ['player_id', 'player', 'class', 'year', 'position', 'last_name', 'first_name']
df = df[cols]

# save to disk so it can be used later to help identify problems 
df.to_csv('team_rosters/' + team_name + '.csv')

# create (id, year) tuples to use when scraping career stats
# since all of a player's years exist in this DF, need to extract one id and one year for each player, store in a tuple
# many mistakes here, but look-up relies on id, which seems to be consistently attached to that year's stats
# EX. Devin Smith at Wisconsin has 2 ids, one for his first 3 seasons and another for his SR year:
#   stats for the FR-JR years are attached to one id and SR year stats are attached to the other
#   for this reason, we need to create an (id, year) tuple for both ids, using the most recent year in each case
#   and perform a career stats search for boths ids.  I'll join the two after that stats have been retrieved.

deduped = df.drop_duplicates(['player_id'], keep='last')
print(len(deduped))
print(deduped)


id_year = list(zip(deduped.player_id, deduped.year))


save(id_year, team_name)


###

def standardizeClasses(class_list):
  all_classes = ['rf', 'fr', 'so', 'jr', 'sr']
  ac_to_junior = ['rf', 'fr', 'so', 'jr']
  ac_to_sophomore = ['rf', 'fr', 'so']
  ac_to_freshman = ['rf', 'fr']
  ct = len(class_list)
  class_set = set(class_list)

  # if there are 5 years of stats, return complete list of all classes
  if ct == 5:
    return all_classes

  # if there are fewer than 5 classes but no dups, return classes provided in DB
  if len(class_set) == ct:
    return [c.lower().strip('.') for c in class_list]

  # if last class listed is 'sr', dedup and shift left
  if class_list[-1] == 'sr':
    return all_classes[-ct:]
  elif class_list[-1] == 'jr':
    return ac_to_junior[-ct:]
  elif class_list[-1] == 'so':
    return ac_to_sophomore[-ct:]
  elif class_list[-1] == 'fr':
    return ac_to_freshman[-ct:]
  else:
    return all_classes[:ct]

def clean_player_stats(dirty_stats):
  """[summary]
  
  Arguments:
    dirty_stats {[type]} -- [description]
  """
  
  dirty_classes = []
  for d in dirty_stats:
    dirty_classes.append(d['class'])

  clean_classes = standardizeClasses(dirty_classes)
  clean_stats = []

  for idx in range(len(clean_classes)):
    p = clean_classes[idx] + '_'
    st = OrderedDict()
    st[p + 'year'] = dirty_stats[idx]['year']
    st[p + 'position'] = dirty_stats[idx]['position']
    
    # games
    st[p + 'games'] = int(dirty_stats[idx]['games'])


    # tackles
    st[p + 'tackles_solo'] = int(dirty_stats[idx]['tackles_solo'])
    st[p + 'tackles_asst'] = int(dirty_stats[idx]['tackles_asst'])
    st[p + 'tfl_solo'] = int(dirty_stats[idx]['tfl_solo'])
    st[p + 'tfl_asst'] = int(dirty_stats[idx]['tfl_asst'])
    st[p + 'tfl_yards'] = int(dirty_stats[idx]['tfl_yards'])
    st[p + 'sacks_solo'] = int(dirty_stats[idx]['sacks_solo'])
    st[p + 'sacks_asst'] = int(dirty_stats[idx]['sacks_asst'])
    st[p + 'sacks_yards'] = int(dirty_stats[idx]['sacks_yards'])
    
    # interceptions
    st[p + 'int'] = int(dirty_stats[idx]['int'])
    st[p + 'int_yards'] = int(dirty_stats[idx]['int_yards'])
    st[p + 'int_td'] = int(dirty_stats[idx]['int_td'])
    
    # fumbles
    st[p + 'fum'] = int(dirty_stats[idx]['fum'])
    st[p + 'fum_yards'] = int(dirty_stats[idx]['fum_yards'])
    st[p + 'fum_td'] = int(dirty_stats[idx]['fum_td'])
    st[p + 'ffum'] = int(dirty_stats[idx]['ffum'])
    
    # safety
    st[p + 'safety'] = int(dirty_stats[idx]['safety'])
    st[p + 'punt_ret'] = int(dirty_stats[idx]['punt_ret'])
    st[p + 'punt_ret_yards'] = int(dirty_stats[idx]['punt_ret_yards'])
    st[p + 'punt_ret_td'] = int(dirty_stats[idx]['punt_ret_td'])
    
    # kick returns
    st[p + 'kick_ret'] = int(dirty_stats[idx]['kick_ret'])
    st[p + 'kick_ret_yards'] = int(dirty_stats[idx]['kick_ret_yards'])
    st[p + 'kick_ret_td'] = int(dirty_stats[idx]['kick_ret_td'])
    
    # total points
    st[p + 'total_points'] = int(dirty_stats[idx]['total_points'])
    
    clean_stats.append(st)

  return (clean_classes, clean_stats)
    


url = 'https://web1.ncaa.org/stats/StatsSrv/careerplayer'

players = []

# pids = load(team_name)
pids = id_year
print('Scraping {} players'.format(len(pids)))


for item in pids:
  pid, yr = item
  pid = int(pid)
  yr = int(yr) + 1
  print('scraping: {} - {}'.format(pid, yr))
  if yr < 2014:
    div = 1
  else:
    div = 11

  formdata = {
    'sortOn': 0,
    'doWhat': 'display',
    'playerId': pid,
    'coachId': pid,
    'orgId': orgId,
    'academicYear': yr,
    'division': div,
    'sportCode': 'MFB',
    'idx' : ''
  }

  r = requests.post(url, data=formdata)

  soup = BeautifulSoup(r.text, 'lxml')

  table = soup.find('table', attrs={ "class" : "statstable"})
  if table == None:
    print(r.status_code)
    print(r.text)
    continue


  # Create dict for each year of stats, add to list of all years of one player's stats
  # deal with class prefixes and assign prefixes to keys in each dict
  # merge each class dict into a single player dict
  # append play dict to team's df
  
  # get all rows of the stats table
  rows = table.find_all('tr')

  # remove top 3 header rows
  rows = rows[3:]
  
  # create the orderedDict that will hold one player's info
  # in Python 3.7, all dicts will respect the order in which keys are added
  # this is pre-3.7, so, I'll use an OrderedDict so as not to have to mess with rearranging cols in DF
  player_stats = OrderedDict()
  player_stats['player_id'] = pid
  player_stats['player'] = ''
  player_stats['names'] = ''
  player_stats['team'] = team
  player_stats['ncaa_yr_ct'] = 0
  # player_stats['classes'] = ''
  # player_stats['multi_names'] = ''
  
  # value of years key will hold list containing yearly stats dicts
  # player_stats['years'] = []

  # player's name sometimes changes from year-to-year
  # adding names to a set ensures that only one version of each unique name will be 
  #   given to the player
  names = set()

  # classes are added to a list and dealt with after all years' stats have been parsed
  classes = []

  # list of all possible strings that might be in the 'Class' column
  inc_classes = ['FR', 'SO', 'JR', 'SR', 'Fr.', 'So.', 'Jr.', 'Sr.']

  # this is the list of yearly stats dicts to be added as value for player_stats['years':[]]
  years = []
  for row in rows:
    # create a new dict to hold yearly stats
    y = {}
    cells = row.find_all('td')
    cl = cells[1].text.strip()

    # remove rows that have anything other than an accepted class string (primarily, '-')
    if cl not in inc_classes:
      rows.remove(row)
      continue
    else:
      y['class'] = cl.lower().strip('.')
      classes.append(cl)

    nm = cells[0].text.strip()
    names.add(nm)
    print(nm)
    
    # year for year
    year = cells[2].text.strip()
    y['year'], _ = year.split('-')
    
    # position for year
    po = cells[3].text.strip()
    if po == 'Defensive Back':
      po = 'DB'
    elif po == 'Linebacker':
      po = 'LB'
    elif po == 'Wide Receiver':
      po = 'WR'
    elif po == 'Running Back':
      po = 'RB'
    elif po == 'Quarterback':
      po = 'QB'
    y['position'] = po
        
    y['games'] = cells[5].text.strip()
    y['int'] = cells[20].text.strip()
    y['int_yards'] = cells[21].text.strip()
    y['int_td'] = cells[22].text.strip()
    y['fum'] = cells[23].text.strip()
    y['fum_yards'] = cells[24].text.strip()
    y['fum_td'] = cells[25].text.strip()
    y['punt_ret'] = cells[28].text.strip()
    y['punt_ret_yards'] = cells[29].text.strip()
    y['punt_ret_td'] = cells[30].text.strip()
    y['kick_ret'] = cells[31].text.strip()
    y['kick_ret_yards'] = cells[32].text.strip()
    y['kick_ret_td'] = cells[33].text.strip()
    y['safety'] = cells[45].text.strip()
    y['total_points'] = cells[46].text.strip()
    y['ffum'] = cells[47].text.strip()
    y['tackles_solo'] = cells[48].text.strip()
    y['tackles_asst'] = cells[49].text.strip()
    y['tfl_solo'] = cells[51].text.strip()
    y['tfl_asst'] = cells[52].text.strip()
    y['tfl_yards'] = cells[54].text.strip()
    y['sacks_solo'] = cells[55].text.strip()
    y['sacks_asst'] = cells[56].text.strip()
    y['sacks_yards'] = cells[58].text.strip()
    
    for k, v in y.items():
      if v == '-':
        y[k] = 0
      
    
    # add yearly stats to years list
    years.append(y)

  
    
  names_list = []
  for n in names:
    if ',' not in n:
      print('problem parsing this name {}'.format(n))
      continue
    if '@' in n:
      n, at = n.split('@')
      n.strip()
      print('Stripped {} from {} {}'.format(n, n, at))
    last, first = n.split(',', 1)
    new_name = first.strip() + ' ' + last.strip()
    names_list.append(new_name)

  player_stats['names'] = ', '.join(names_list)
  try:
    player_stats['player'] = names_list[0]
  except IndexError:
    print('could not deal with this name list: {}'.format(names_list))
  player_stats['ncaa_yr_ct'] = len(years)
  # player_stats['classes'], clean_stats = clean_player_stats(years)
  _, clean_stats = clean_player_stats(years)

  for y in clean_stats:
    for k, v in y.items():
      player_stats[k] = v

  players.append(player_stats)


# build & save DataFrame
df = pd.DataFrame(players)
# df.to_csv('player_stats/' + team_name + '.csv')
df.to_csv('player_stats/s_gregory.csv')
print(df)

# Check that player_id -> names are equal, if not, write team name to file to look at later.
a = len(df.player_id.unique())
b = len(df.names.unique())

print ('Unique ids: \t{}\nUnique names: {}'.format(a, b))

if a != b:
  ps = load('problems')
  ps.add(team_name)
  save(ps, 'problems')
