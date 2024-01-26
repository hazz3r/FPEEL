import base 
import utils   
import os  
import requests 

class FPL: 
    def __init__(self, session, user=None):  
        # Allows HTTP requests to be made 
        self.session = session 
        # Provides access to authentication cookies 
        self.user = user  
        # Provides access to database 
        self.db_connection = utils.connect_to_db()     

    def get_all_players(self): 
        cursor = self.db_connection.cursor()  
        # Gets all players data
        cursor.execute('SELECT * FROM players') 
        # Stores all players data in 'data' 
        data = cursor.fetchall() 
        cursor.close()  
        # Turns the data into a series of player objects 
        return [base.Player(*x) for x in data]  
    
    def get_current_user_picks(self):  
        # If there is a user logged in 
        if self.user:  
            # Retrieve the JSON data at the current team api url using authenticated cookies 
            data = utils.fetch(self.session, utils.api_urls['current-team'].format(self.user.id), cookies=self.session.cookies)
            # Retrieves the ids of every player in the team      
            ids_list = [x for x in data['picks']]  
            # Returns the ids of every player in the team
            return ids_list
        # If there is not a user logged in then we cannot retrieve a team so return False 
        return False   
    
    def get_current_user_rank(self):  
        # Retrieves the JSON data at the user api url and returns the data in the key 'summary_overall_rank' 
        return utils.fetch(self.session, utils.api_urls['user'].format(self.user.id))['summary_overall_rank']

    def get_current_user_leagues(self):  
        data = utils.fetch(self.session, utils.api_urls['user'].format(self.user.id))['leagues']['classic']  
        return [x for x in data]  

    def get_current_user_balance(self):  
        # Retrieves the JSON dat at the user api url and returns the data in the key 'last_deadline_bank' and divides it by 10
        return utils.fetch(self.session, utils.api_urls['user'].format(self.user.id))['last_deadline_bank']/10 

    # returns the standings in json format of a league when inputted with the league id 
    def get_league_standings(self, league_id):   
        return utils.fetch(self.session, utils.api_urls['league'].format(league_id)+'standings/')['standings']['results'] 

    def get_player_from_id(self, player_id): 
        data = utils.read_json(os.path.join(os.getcwd(), 'json_data', 'static.json')) 
        for x in data['elements']: 
            if x['id'] == player_id: 
                return x['web_name'] 

    def update_fpl_data(self, type: str): 
        data = utils.fetch(self.session, utils.api_urls[type]) 
        utils.write_json(data, os.path.join(os.getcwd(), 'json_data', type+'.json'))   


    







    
