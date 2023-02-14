'''Assetto Corsa log converter'''

import sys
import os
import json
import configparser
import getopt
from xml.dom import minidom
from datetime import datetime

QUICK_RACE = 'Race'
PRACTICE = 'Practice1'
QUALIFYING = 'Qualify'

def create_element(root, parent, name, attributes=None):
    '''Creates a XML element'''
    element = root.createElement(name)
    if attributes is not None:
        for attribute in attributes:
            element.setAttribute(attribute[0], attribute[1])
    parent.appendChild(element)
    return element

def create_text_element(root, parent, name, text, attributes=None):
    '''Creates a XML Text element'''
    element = create_element(root, parent, name, attributes)
    text_element = root.createTextNode(text)
    element.appendChild(text_element)
    return element

def load_config():
    '''Loads config file'''
    config_parser = configparser.ConfigParser()
    config = config_parser.read('config.ini')

    if len(config) == 0:
        raise Exception('Could not load config.ini file or the file is invalid')

    return config_parser

def load_input_path(config_parser):
    '''Loads path where CM log files are saved'''
    paths_config = config_parser['PATHS']
    input_path = paths_config['INPUT_PATH']

    if input_path == 'REPLACE_ME':
        raise Exception('Please replace the paths in the config.ini file')

    return input_path

def load_target_path(config_parser):
    '''Loads path where the converted files will be saved'''
    paths_config = config_parser['PATHS']
    target_path = paths_config['TARGET_PATH']

    if target_path == 'REPLACE_ME':
        raise Exception('Please replace the paths in the config.ini file')

    return target_path

def get_log_file_name(path):
    '''Gets file file'''
    pathname, _ = os.path.splitext(path)
    pathname = pathname.replace('/', '\\')
    return pathname.split('\\')[-1]

def get_latest_log_file(input_path):
    '''Gets most recent log file from logs directory'''
    return f'{input_path}\\{os.listdir(input_path)[-1]}'

def read_args(argv, input_path):
    '''Reads command-line args'''
    opts, _ = getopt.getopt(argv,'', ['file=', 'latest'])

    for opt, arg in opts:
        if opt == '--file':
            return arg
        elif opt == '--latest':
            return get_latest_log_file(input_path)

        print ('converter.py -f <inputfile>')
        sys.exit()

def load_cm_log_file(input_file):
    '''Loads Assetto Corsa Content Manager log file'''
    file = open(input_file, encoding='utf-8')
    return json.load(file)

def load_race_ini(data):
    '''Loads race ini config file'''
    race_ini = data['__raceIni']
    config_parser = configparser.ConfigParser()
    config_parser.read_string(race_ini)
    return config_parser

def get_player_starting_position(race_ini_parser):
    '''Gets player starting position from race ini'''
    session_config = race_ini_parser['SESSION_0']
    return int(session_config['STARTING_POSITION'])

def get_track_info(race_ini_parser):
    '''Gets track info from race ini'''
    race_config = race_ini_parser['RACE']
    return race_config['TRACK'], race_config['CONFIG_TRACK']

def get_session(data):
    '''Gets session from data file'''
    session = data['sessions'][0]

    if session['name'] not in ('Quick Race', 'Practice', 'Qualifying'):
        raise Exception(f'Session type \'{session["name"]}\' not supported')

    return session

def get_session_laps(session):
    '''Gets session laps'''
    return session['laps']

def get_lap_count(session):
    '''Gets lap count'''
    return str(max(session['lapstotal']))

def get_session_result(session):
    '''Gets session result'''
    return session['raceResult']

def create_session_result(players):
    '''Creates session result'''    
    session_result = []
    for i, _ in enumerate(players):
        session_result.append(i)
    return session_result

def set_players_finish_position(players, session_result):
    '''Update players with finish position attribute'''    
    for i, player in enumerate(players):
        position = session_result.index(i) + 1
        player.update({'finish_position': position})

def set_players_start_position(players, player_starting_position):
    '''Update players with start position attribute'''
    grid_order = players.copy()
    grid_order.insert(player_starting_position-1, grid_order.pop(0))
    for position, player in enumerate(grid_order, 1):
        player.update({'start_position': position})
    return grid_order

def get_race_date(date_string):
    '''Gets race date from string'''
    date_string_splitted = date_string.split('-')
    year_string = date_string_splitted[0]
    time_string = date_string_splitted[1]
    year_string = '/'.join(year_string[i:i+2] for i in range(0, len(year_string), 2))
    time_string = ':'.join(time_string[i:i+2] for i in range(0, len(time_string), 2))
    date_string = f'20{year_string} {time_string}'
    return date_string

def get_timestamp(date):
    '''Returns the timestamp for a given date'''
    datetime_object = datetime.strptime(date, '%Y/%m/%d %H:%M:%S')
    timestamp = datetime.timestamp(datetime_object)
    return str(int(timestamp))

def print_race_summary(grid_order):
    '''Logs race summary'''
    print('*'*20 + ' Race Summary ' + '*'*20)
    print('Start\tFinish\tDiff\tName')
    for player in grid_order:
        diff = int(player['start_position']) - int(player['finish_position'])
        print(f'{player["start_position"]}\t{player["finish_position"]}\t{diff}\t{player["name"]}')

def get_car_number(player):
    '''Tries to get car number from skin'''
    try:
        return str(int(player['skin'].split('-')[0]))
    except ValueError:
        return '-'

def get_session_type(session):
    '''Gets session string'''
    if session['name'] == 'Quick Race':
        return QUICK_RACE
    elif session['name'] == 'Practice':
        return PRACTICE
    elif session['name'] == 'Qualifying':
        return QUALIFYING

def create_global_elements(root, race_results, lap_count, race_date, track, track_layout):
    '''Creates global XML elements'''
    create_text_element(root, race_results, 'Setting', 'Race Weekend')
    create_text_element(root, race_results, 'PlayerFile', 'player')
    create_text_element(root, race_results, 'DateTime', get_timestamp(race_date))
    create_text_element(root, race_results, 'TimeString', race_date)
    create_text_element(root, race_results, 'Mod', 'All Tracks &amp; Cars')
    create_text_element(root, race_results, 'Season', '')
    create_text_element(root, race_results, 'TrackVenue', track)
    create_text_element(root, race_results, 'TrackCourse', f'{track}-{track_layout}')
    create_text_element(root, race_results, 'TrackEvent', track)
    create_text_element(root, race_results, 'TrackData', '')
    create_text_element(root, race_results, 'TrackLength', '1000')
    create_text_element(root, race_results, 'GameVersion', '1.1131')
    create_text_element(root, race_results, 'Dedicated', '0')
    create_text_element(root, race_results, 'ConnectionType', 'ADSL2+ 16M',
                        [('upload','1000'), ('download','8000')])
    create_text_element(root, race_results, 'RaceLaps', lap_count)
    create_text_element(root, race_results, 'RaceTime', '0')
    create_text_element(root, race_results, 'MechFailRate', '1')
    create_text_element(root, race_results, 'DamageMult', '50')
    create_text_element(root, race_results, 'FuelMult', '1')
    create_text_element(root, race_results, 'TireMult', '1')
    create_text_element(root, race_results, 'VehiclesAllowed', '')
    create_text_element(root, race_results, 'ParcFerme', '3')
    create_text_element(root, race_results, 'FixedSetups', '0')
    create_text_element(root, race_results, 'FreeSettings', '11')
    create_text_element(root, race_results, 'FixedUpgrades', '0')

def create_race_elements(root, session_type, race_results, lap_count, race_date):
    '''Creates race XML elements'''
    race_element = create_element(root, race_results, session_type)
    create_text_element(root, race_element, 'DateTime', get_timestamp(race_date))
    create_text_element(root, race_element, 'TimeString', race_date)
    create_text_element(root, race_element, 'Laps', lap_count)
    create_text_element(root, race_element, 'Minutes', '0')
    _ = create_element(root, race_element, 'Stream') #TODO: is this needed?
    create_text_element(root, race_element, 'FormationAndStart', '0')
    create_text_element(root, race_element, 'MostLapsCompleted', lap_count)
    return race_element

def create_players_elements(root, players, laps, race_element):
    '''Creates players XML elements'''

    for i, player in enumerate(players):
        driver_element = create_element(root, race_element, 'Driver')
        create_text_element(root, driver_element, 'Name', player['name'].split('(')[0]) # removing AI level
        create_text_element(root, driver_element, 'Connected', '1')
        create_text_element(root, driver_element, 'VehFile', '')
        create_text_element(root, driver_element, 'UpgradeCode', '00000000 00000000 00000000 00000000')
        create_text_element(root, driver_element, 'VehName', player['car'])
        create_text_element(root, driver_element, 'Category', 'Assetto Corsa')
        create_text_element(root, driver_element, 'CarType', player['skin'])
        create_text_element(root, driver_element, 'CarClass', '')
        create_text_element(root, driver_element, 'CarNumber', get_car_number(player))
        create_text_element(root, driver_element, 'TeamName', '')
        create_text_element(root, driver_element, 'isPlayer', '1' if i == 0 else '0')
        create_text_element(root, driver_element, 'ServerScored', '1')
        create_text_element(root, driver_element, 'GridPos', str(player['start_position']))
        create_text_element(root, driver_element, 'Position', str(player['finish_position']))
        create_text_element(root, driver_element, 'ClassGridPos', str(player['start_position']))
        create_text_element(root, driver_element, 'ClassPosition', str(player['finish_position']))
        create_text_element(root, driver_element, 'Points', '0')
        create_text_element(root, driver_element, 'ClassPoints', '0')
        create_text_element(root, driver_element, 'LapRankIncludingDiscos', '') #TODO: is this needed?

        best_lap = 10000000
        finish_time = 0
        total_laps = 0

        prev_lap = -1

        for lap in laps:
            if lap['time'] < 0:
                continue

            if prev_lap != lap['lap']:
                position = 1
                prev_lap = lap['lap']

            if lap['car'] == i:
                total_laps += 1
                lap_time = lap['time']/1000
                sector_1 = str(lap['sectors'][0]/1000)
                sector_2 = str(lap['sectors'][1]/1000)
                sector_3 = str(lap['sectors'][2]/1000)

                best_lap = min(lap_time, best_lap)
                finish_time += lap_time

                create_text_element(root, driver_element, 'Lap', str(lap_time), [
                                    ('p',str(position)),
                                    ('et','0'), #TODO: gap to leader?
                                    ('s1',sector_1), ('s2',sector_2), ('s3',sector_3),
                                    ('fuel','1'),
                                    ('twfl','1'), ('twfr','1'), ('twrl','1'), ('twrr','1'),
                                    ('fcompound','0,Slicks'), ('rcompound','0,Slicks')
                ])
            else:
                position += 1

        create_text_element(root, driver_element, 'BestLapTime', str(best_lap))
        create_text_element(root, driver_element, 'FinishTime', str(finish_time))
        create_text_element(root, driver_element, 'Laps', str(total_laps))
        create_text_element(root, driver_element, 'Pitstops', '0') #TODO: include pitstops?
        create_text_element(root, driver_element, 'FinishStatus', 'Finished Normally') #TODO: handle DNFs
        #create_text_element(root, driver_element, 'DNFReason', 'DNF')

def create_xml_document(session_type, players, laps, lap_count, race_date, track, track_layout):
    '''Generates the XML log file using the rFactor2 format'''
    root = minidom.Document()
    root.encoding = 'utf-8'
    xml_document = create_element(root, root, 'rFactorXML', [('version','1.0')])
    race_results = create_element(root, xml_document, 'RaceResults')

    create_global_elements(root, race_results, lap_count, race_date, track, track_layout)
    race_element = create_race_elements(root, session_type, race_results, lap_count, race_date)
    create_players_elements(root, players, laps, race_element)

    return root.toprettyxml(indent ="\t")

def save_xml_document(xml_document, path, file_name):
    '''Saves the XML document'''
    full_name = f'{path}\\{file_name}'
    with open(full_name, 'w', encoding='utf-8') as file:
        file.write(xml_document)
    print(f'Saved XML document to {full_name}')

def sort_laps(laps):
    '''Sorts laps by time'''
    sorted_laps = laps.copy()
    sorted_laps.sort(key=lambda lap: (int(lap['lap']), int(lap['time'])))
    return sorted_laps

def main(argv):
    '''Entry point'''
    config_parser = load_config()
    input_path = load_input_path(config_parser)
    target_path = load_target_path(config_parser)
    input_file = read_args(argv, input_path)
    log_file_name = get_log_file_name(input_file)

    data = load_cm_log_file(input_file)
    race_ini_parser = load_race_ini(data)

    session = get_session(data)
    session_type = get_session_type(session)
    laps = get_session_laps(session)
    laps = sort_laps(laps)
    lap_count = get_lap_count(session)

    players = data['players'].copy()

    if session_type == QUICK_RACE:
        session_result = get_session_result(session)
        player_starting_position = get_player_starting_position(race_ini_parser)
    elif session_type in (PRACTICE, QUALIFYING):
        session_result = create_session_result(players)
        player_starting_position = 1
        
    track, track_layout = get_track_info(race_ini_parser)
    set_players_finish_position(players, session_result)
    _ = set_players_start_position(players, player_starting_position)
    #print_race_summary(grid_order)

    race_date = get_race_date(log_file_name)

    xml_document = create_xml_document(session_type, players, laps, lap_count, race_date, track, track_layout)
    save_xml_document(xml_document, target_path, f'{log_file_name}.xml')

if __name__ == "__main__":
    main(sys.argv[1:])
