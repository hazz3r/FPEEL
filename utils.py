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

def write_json(data: json, path: str): 
    with open(path, 'w') as f: 
        json.dump(data, f, indent=4)   

def read_json(path): 
    with open(path, 'r') as f: 
        return json.load(f)     

def fetch(session, url, cookies=None, retries=2, cooldown=1):
    retries_count = 0 
    while True: 
        try: 
            with session.get(url, cookies=cookies) as response: 
                return response.json() 
        except: 
            retries_count += 1 
            if retries_count == retries: 
                raise Exception("Too many retries") 
            time.sleep(cooldown)  

def get_account_cookies(session, email, password, retries=1, cooldown=1): 
    retries_count = 0 
    data = {
        'login': email, 
        'password': password, 
        'app': 'plfpl-web', 
        'redirect_uri': api_urls['fantasy_login']
    } 
    headers = { 
        'User-Agent': 'Dalvik', 
        'Accept-Language': 'en-US,enq=0.5'
    }
    while True: 
        try: 
            with session.post(api_urls['login'], data=data, headers=headers): 
                return { 
                    'pl_profile': session.cookies['pl_profile'], 
                    'datadome': session.cookies['datadome'] 
                } 
        except: 
            retries_count += 1  
            print(retries_count) 
            if retries_count > retries: 
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
    pass 

def convert_team_short(team_idea): 
    pass 

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





