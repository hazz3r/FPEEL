from dataclasses import dataclass 
import pulp  
import random 

@dataclass 
class Player: 
    player_id: int 
    name: str 
    cost: float  
    total_points: int 
    position: int 
    team: int 
    ppg: float 
    owned_by: float 
    composite_score: float                                                  
    sell_cost: float = None  


@dataclass 
class User: 
    id: int 
    name: str   
    email: str  
    cookies: dict 

@dataclass 
class League: 
    id: int 
    name: str 
    standings: list 

class Optimiser:  
    lineup_size = 11  
    bench_size = 4  
    # Maximum number of players from each team
    team_max = 3  

    # Minimum number and maximum number of players in each position -> position: (minimum, maximum) 
    formation_constraints = { 
        1: (1, 1), 
        2: (3, 5), 
        3: (2, 5), 
        4: (1, 3) 
    } 
    # The number of players required per position -> position: amount 
    position_constraints = { 
        1: 2, 
        2: 5, 
        3: 5,
        4: 3
    } 

class TransferOptimiser(Optimiser):   
    def generate_transfers(self, user_team, players, budget): 
        # Recommended transfers starts out as an empty list 
        transfers = []  
        # Find the pool of available players by removing the players in the user's team from all the players 
        available_players = self.get_unused_players(user_team, players)  
        # Finds the top 20 players by composite score in the goalkeeper position 
        goalkeepers = self.get_top_20(1, available_players)  
        # Finds the top 20 players by composite score in the defender position
        defenders = self.get_top_20(2, available_players)  
        # Finds the top 20 players by composite score in the midfielder position 
        midfielders = self.get_top_20(3, available_players) 
        # Finds the top 20 players by composite score in the forward position
        forwards = self.get_top_20(4, available_players)    
        # Iterates through the user's team
        for x in user_team:   
            # If the position of the current player is goalkeeper 
            if x.position == 1:  
                # Iterates through the list of top 20 goalkeepers 
                for y in goalkeepers:  
                    # If trading player x with player y is a valid transfer then append [x,y] to transfers 
                    if self.is_valid_transfer(y, x, user_team, budget): 
                        transfers.append([x, y])   
            # The above process is the same for every position 
            elif x.position == 2: 
                for y in defenders: 
                    if self.is_valid_transfer(y, x, user_team, budget): 
                        transfers.append([x, y]) 
            elif x.position == 3: 
                for y in midfielders: 
                    if self.is_valid_transfer(y, x, user_team, budget): 
                        transfers.append([x, y]) 
            elif x.position == 4: 
                for y in forwards: 
                    if self.is_valid_transfer(y, x, user_team, budget): 
                        transfers.append([x, y])   

        # Returns the list of transfers in a format such that: 
        # The transfer which nets the highest gain in composite score is at index 0 
        # The transfer which nets the lowest gain in composite score is at -1 
        return sorted(transfers, key=lambda x: x[1].composite_score-x[0].composite_score, reverse=True) 

    def get_unused_players(self, user_team, players):  
        # Finds the unique identifiers of all the players in the team
        team_ids = [x.player_id for x in user_team]  
        # Returns all the players in `players` that are not in `team_ids` (the players who are not in `user_team`) 
        return [x for x in players if x.player_id not in team_ids] 
    
    def get_top_20(self, position, players):   
        # Finds all the players with the same position as `position` 
        valid_players = [player for player in players if player.position == position]    
        # Sorts the players with the same position by composite score 
        # The player with the highest composite score is at index [0] 
        valid_players = sorted(valid_players, key=lambda x: x.composite_score, reverse=True)  
        # Takes the top 20 by composite score 
        valid_players = valid_players[:20]  
        # Returns the top 20 
        return valid_players          
    
    def is_valid_transfer(self, player_in, player_out, user_team, budget):   
        # If the player being transferred in does not have the same position as the player transferred out then return False (invalid transfer) 
        if player_in.position != player_out.position: 
            return False  
        # If the player being transferred in causes the amount of players from 1 team to be above 3 then return False (invalid transfer) 
        if sum([1 for x in user_team if x.team == player_in.team]) - sum([1 if player_out.team == player_in.team else 0]) >= 3:
            return False   
        # If the player being transferred in is more than the sell cost of the player being transferred + the remaining budget then return False (invalid transfer) 
        if player_in.cost > player_out.cost+budget: 
            return False   
        return True 

class ChipOptimiser(Optimiser):  
    chip_switcher = { 
        'free_hit': lambda player: player.composite_score, 
        'wildcard': lambda player: player.composite_score3 
    } 
    @classmethod 
    def captain_chooser(cls, team: list) -> dict:  
        # Returns the highest composite score player as the captain 
        # Returns the second highest composite score player as vice-captain
        return { 
            'captain': max(team, key=lambda player: player.composite_score), 
            'vice_captain': sorted(team, key=lambda player: player.composite_score, reverse=True)[1]  
        } 
    
    @classmethod 
    def bench_boost_predict(cls, team: list) -> float:  
        # Returns the sum composite score of the last 4 players in the user's team (bench players) 
        return sum([player.composite_score for player in team[11:]])      
    
    def interpolate_budget(cls, bench_importance: float, budget: float) -> float:  
        # If bench_importance is not between 0 and 1 then raised
        if bench_importance < 0 or bench_importance > 1: 
            raise ValueError('Bench importance value must be between 0 and 1') 
        min_multi = 0.83 
        max_multi = (220/3)/100     
        return budget*(min_multi + (max_multi - min_multi)*bench_importance) 

    def get_position_requirements(cls, team: list): 
        return {
            1: cls.position_constraints[1] - sum(1 for player in team if player.position == 1), 
            2: cls.position_constraints[2] - sum(1 for player in team if player.position == 2), 
            3: cls.position_constraints[3] - sum(1 for player in team if player.position == 3), 
            4: cls.position_constraints[4] - sum(1 for player in team if player.position == 4) 
        } 
    
    def generate_starters(cls, players: list, budget: float, chip_type: str):  
        key_function = cls.chip_switcher[chip_type] 
        problem = pulp.LpProblem('Starting_11_Optimiser', pulp.LpMaximize) 
        selected = pulp.LpVariable.dicts('Starters', [player.player_id for player in players], cat=pulp.LpBinary) 

        problem += pulp.lpSum(key_function(player)*selected[player.player_id] for player in players)   
        problem += pulp.lpSum(selected[player.player_id] for player in players) == cls.lineup_size 
        problem += pulp.lpSum(player.cost*selected[player.player_id] for player in players) <= budget 
        for position, (min, max) in cls.formation_constraints.items(): 
            problem += pulp.lpSum(selected[player.player_id] for player in players if player.position == position) >= min 
            problem += pulp.lpSum(selected[player.player_id] for player in players if player.position == position) <= max 
        for team in range(1, 21): 
            problem += pulp.lpSum(selected[player.player_id] for player in players if player.team == team) <= cls.team_max 
        
        problem.solve() 
        selected_team = [player for player in players if pulp.value(selected[player.player_id])==1]  
        budget_used = sum([player.cost for player in selected_team]) 
        return sorted(selected_team, key=lambda x: x.position), budget_used  

    def generate_bench(cls, players: list, budget: float, positions_left: dict, selected_11: list, chip_type: str) -> list:  
        key_function = cls.chip_switcher[chip_type]  
        problem = pulp.LpProblem('FPL_Optimiser', pulp.LpMaximize) 
        selected = pulp.LpVariable.dicts('Bench', [player.player_id for player in players], cat=pulp.LpBinary) 

        problem += pulp.lpSum(key_function(player)*selected[player.player_id] for player in players) 
        problem += pulp.lpSum(selected[player.player_id] for player in players) == cls.bench_size 
        problem += pulp.lpSum(player.cost*selected[player.player_id] for player in players) <= budget 
        for position, value in positions_left.items(): 
            problem += pulp.lpSum(selected[player.player_id] for player in players if player.position == position) == value     
        problem.solve() 
        selected_bench = [player for player in players if pulp.value(selected[player.player_id])==1]  
        return sorted(selected_bench, key=lambda x: x.position) 
    
    @classmethod 
    def generate_team(self, players: list, budget: float, bench_importance: float, chip_type: str) -> list: 
        starter_budget = self.interpolate_budget(self, bench_importance, budget) 
        result_11, budget_used = self.generate_starters(self, players, starter_budget, chip_type)  
        bench_budget = budget-budget_used  
        result_11_ids = [x.player_id for x in result_11] 
        bench_players = [x for x in players if x.player_id not in result_11_ids] 
        positions_left = self.get_position_requirements(self, result_11)  
        result_bench = self.generate_bench(self, bench_players, bench_budget, positions_left, result_11, chip_type)
        return result_11+result_bench

class RatingSystem: 
    players_weights = {
        'ppg': 0.5, 
        'total_points': 0.4, 
        'ownership_percentage': 0.1
    } 

    @classmethod 
    def get_player_rating(cls, ppg, total_points, ownership_percentage): 
        return ppg*cls.players_weights['ppg'] + total_points*cls.players_weights['total_points'] + ownership_percentage*cls.players_weights['ownership_percentage'] 
    

