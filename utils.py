import base 
import time  
import json    
import mysql.connector 
import os 
import requests 

base_url = 'https://fantasy.premierleague.com/api/' 
api_urls = { 
    'login': 'https://users.premierleague.com/accounts/login/',
    'fantasy_login': 'https://fantasy.premierleague.com/login/',
    'static': '{}bootstrap-static/'.format(base_url), 
    'user': '{}entry/{{}}/'.format(base_url), 
    'league': '{}leagues-classic/{{}}/'.format(base_url),  
    'me': '{}me/'.format(base_url), 
    'current-team': '{}my-team/{{}}/'.format(base_url), 
    'given-team': '{}entry/{{}}/event/{{}}/'.format(base_url) 
}  

# takes a JSON string and the file's path that it is to be written to as parameters 
def write_json(data: json, path: str):  
    # opens the file in write mode d
    with open(path, 'w') as f:  
        # writes 'data' to the file 
        # uses an indent of 4 so it is more readable 
        json.dump(data, f, indent=4)   

# takes the path of the file as a parameter 
def read_json(path):  
    # opens the file in read mode
    with open(path, 'r') as f:  
        # returns the contents of the file (will be formatted as a JSON string) 
        return json.load(f)     

def fetch(session, url, cookies=None, retries=2, cooldown=1): 
    # Retries count starts at 0 
    retries_count = 0 
    while True: 
        try:  
            # Attempts to retrieve JSON data from URL
            with session.get(url, cookies=cookies) as response:  
                # Returns the JSON data from the URL 
                return response.json() 
        except:  
            # Increments the retries count 
            retries_count += 1  
            # If the retries count reaches retries then raise an exception 
            if retries_count == retries: 
                raise Exception("Too many retries") 
            time.sleep(cooldown)  

def get_account_cookies(session, email, password, retries=1, cooldown=1):  
    # Retries count starts at 0 
    retries_count = 0  
    # POST must contain working email and password 
    # POST must also contain certain values for the cookies returned to be accurate 
    data = {
        'login': email, 
        'password': password, 
        'app': 'plfpl-web', 
        'redirect_uri': api_urls['fantasy_login']
    }  
    # POST must have certain headers for the cookies returned to be accurate 
    headers = { 
        'User-Agent': 'Dalvik', 
        'Accept-Language': 'en-US,enq=0.5'
    }
    while True: 
        try:  
            # POSTs the login request to the login URL specified in api_urls 
            with session.post(api_urls['login'], data=data, headers=headers):  
                # Returns two of the cookies generated in the response 
                # These cookies allow authenticated API calls 
                return { 
                    'pl_profile': session.cookies['pl_profile'], 
                    'datadome': session.cookies['datadome'] 
                } 
        except: 
            # Increments retries count 
            retries_count += 1 
            # If retries count is equal to retires then return False (means the login has failed)  
            if retries_count == retries: 
                return False 
            time.sleep(cooldown)   

def connect_to_db(): 
    return mysql.connector.connect(
        host='5.133.180.245', 
        user='espleyh', 
        password='HE141005wgsb', 
        database='espleyh_fpl' 
    ) 

def get_current_gameweek(session): 
    data = fetch(session, api_urls['static']) 
    for x in data['events']: 
        if x['is_current']: 
            return x['id']

def convert_team(team_id): 
    team_switcher = { 
        1: "Arsenal", 
        2: "Aston Villa", 
        3: "Bournemouth", 
        4: "Brentford", 
        5: "Brighton", 
        6: "Burnley", 
        7: "Chelsea", 
        8: "Crystal Palace", 
        9: "Everton", 
        10: "Fulham", 
        11: "Liverpool", 
        12: "Luton", 
        13: "Manchester City", 
        14: "Manchester United", 
        15: "Newcastle United", 
        16: "Nottingham Forest", 
        17: "Sheffield United", 
        18: "Tottenham Hotspur", 
        19: "West Ham United", 
        20: "Wolves"
    } 
    return team_switcher[team_id] 

def convert_position(position_id): 
    return {
        1: 'Goalkeeper', 
        2: 'Defender', 
        3: 'Midfielder', 
        4: 'Forward' 
    }[position_id]         

def update_static_data(connection): 
    pass  

def update_player_table(connection, session): 
    for x in fetch(session, api_urls['static'])['elements']:  
        print(x['web_name'])
        cursor = connection.cursor()  
        sql = f""" INSERT INTO players 
        VALUES ({x['id']}, "{x['web_name']}", {x['now_cost']/10}, {x['total_points']}, {x['element_type']}, {x['team']}, {x['points_per_game']}, {x['selected_by_percent']}, {x['ep_next']}) 
        ON DUPLICATE KEY UPDATE cost={x['now_cost']/10}, total_points={x['total_points']}, position={x['element_type']}, team_id={x['team']}, ppg={x['points_per_game']}, owned_by={x['selected_by_percent']}"""     
        cursor.execute(sql) 
        connection.commit() 
        cursor.close() 

def update_composite_scores(connection): 
    cursor = connection.cursor() 
    cursor.execute('SELECT * FROM players') 
    data = cursor.fetchall() 
    for x in data:  
        print(x) 
        cursor.execute(f'UPDATE players SET composite_score={base.RatingSystem.get_player_rating(x[6], x[3], x[7])} WHERE id={x[0]}') 
        connection.commit() 
    cursor.close()

def create_player_object(connection, player_id): 
    cursor = connection.cursor() 
    cursor.execute('SELECT * FROM players WHERE id = {}'.format(player_id)) 
    data = cursor.fetchall()  
    print(*data[0]) 
    cursor.close()  
    return base.Player(*data[0])  

def create_user_object(session, cookies): 
    data = fetch(session, api_urls['me'], cookies=cookies)['player']
    return base.User( 
        data['entry'], 
        data['first_name'], 
        data['email'], 
        cookies 
    )  

def rgb_to_string(rgb: list) -> str: 
    return f'rgb({rgb[0]}, {rgb[1]}, {rgb[2]});'

def string_to_rgb(string: str) -> list: 
    string = string.strip('rgb();') 
    arr = string.split(',') 
    return [int(x) for x in arr] 

def merge_sort(arr, key=lambda x: x): 
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left_half = merge_sort(arr[:mid], key)
    right_half = merge_sort(arr[mid:], key)

    return merge(left_half, right_half, key)

def merge(left, right, key):
    merged = []
    left_index, right_index = 0, 0

    while left_index < len(left) and right_index < len(right):
        if key(left[left_index]) <= key(right[right_index]):
            merged.append(left[left_index])
            left_index += 1
        else:
            merged.append(right[right_index])
            right_index += 1

    merged.extend(left[left_index:])

    merged.extend(right[right_index:])

    return merged 



