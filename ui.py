from PyQt6 import QtCore, QtWidgets, QtGui, QtMultimedia
from PyQt6.QtWidgets import QMainWindow, QWidget, QPushButton, QLabel, QColorDialog, QFontDialog, QVBoxLayout, QHBoxLayout, QComboBox, QStackedLayout 
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor 
from PyQt6.QtCore import QUrl 
from PyQt6.QtMultimedia import QSoundEffect     
from dataclasses import dataclass  
from fpl import FPL 
import requests 
import mysql.connector 
import json  
import sys    
import os 
import utils  
import base   

class WindowParent(QMainWindow): 
    def __init__(self, previous_window, fpl):   
        super().__init__() 
        self.previous_window = previous_window  
        self.fpl = fpl 
        self.settings = Settings()   
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose) 
        self.setStyleSheet(f'background-color: {self.settings.colour_scheme.primary_colour}')  
        self.window_switcher = { 
            0: LoginWindow, 
            1: MainWindow, 
            2: LineupWindow, 
            3: LeagueWindow,  
            4: DatabaseWindow, 
            5: SettingsWindow, 
            6: ExitWindow
        }  
        self.colour_switcher = { 
            0: f'background-color: {self.settings.colour_scheme.primary_colour}'f'color: {self.settings.colour_scheme.secondary_colour}', 
            1: f'background-color: {self.settings.colour_scheme.secondary_colour}'f'color: {self.settings.colour_scheme.primary_colour}' 
        } 
    
    def refresh(self): 
        self.close() 
        self.new_window = self.window_switcher[self.window_id](fpl=self.fpl, previous_window=self.previous_window)    

    def open_window(self, window): 
        if window != 6: 
            self.close() 
        self.new_window = self.window_switcher[window](fpl=self.fpl, previous_window=self.window_id)     
        self.new_window.show() 
    
    def back_window(self): 
        if self.previous_window: 
            self.open_window(self.previous_window)   

    def apply_colour(self, widget):  
        if widget.children(): 
            for child in widget.children():  
                if not isinstance(child, QtCore.QObject):   
                    self.apply_colour(child)  
        try: 
            widget.setStyleSheet(self.colour_switcher[widget.colour]) 
        except: 
            widget.setStyleSheet(self.colour_switcher[widget.parent().colour]) 

    def apply_colours(self, parent): 
        for widget in parent.findChildren(QWidget): 
            if hasattr(widget, 'colour'): 
                parent.apply_colour(widget)    
    
    def relayout(self, widget): 
        QWidget().setLayout(widget.layout()) 
        

class CustomButton(QPushButton): 
    def __init__(self, parent=None): 
        super().__init__(parent) 
        self.parent = parent 
        self.clicked.connect(self.handle_clicked) 
        if self.parent: 
            self.sound_effect = QSoundEffect() 
            self.sound_effect.setSource(QUrl.fromLocalFile(self.parent.settings.button_sound))   
    
    def play_sound(self, volume): 
        self.sound_effect.setVolume(volume) 
        self.sound_effect.play() 

    def handle_clicked(self): 
        if self.parent: 
            self.play_sound(self.parent.settings.button_volume)  

class Settings: 
    def __init__(self): 
        self.settings_path = os.path.join(os.getcwd(), 'json_data', 'settings.json')  
        try: 
            settings = utils.read_json(self.settings_path)  
        except json.JSONDecodeError: 
            settings = { 
                'primary_colour': None, 
                'secondary_colour': None, 
                'font': 'Arial', 
                'button_sound': None, 
                'button_volume': None 
            }  
            utils.write_json(settings, self.settings_path)  
        self.colour_scheme = ColourScheme(settings['primary_colour'], settings['secondary_colour']) 
        self.font = settings['font'] 
        self.button_sound = settings['button_sound'] 
        self.button_volume = settings['button_volume']  
        self.settings_switcher = { 
            0: self.colour_scheme.primary_colour, 
            1: self.colour_scheme.secondary_colour, 
            2: self.font, 
            3: self.button_sound, 
            4: self.button_volume 
        }
    
    def change_settings(self, settings_dict): 
        settings = utils.read_json(self.settings_path)
        for k in settings_dict: 
            settings[k] = settings_dict[k] 
            self.settings_switcher[k] = settings_dict[k] 
        utils.write_json(settings, self.settings_path)   

@dataclass 
class ColourScheme: 
    primary_colour: str = None 
    secondary_colour: str = None 
    error_colour = 'rgb(255, 0, 0);'   

class LoginWindow(WindowParent): 
    def __init__(self, previous_window=None, fpl=None): 
        super().__init__(previous_window, fpl)    
        self.session = requests.Session() 
        self.window_id = 0    
        self.setup_ui() 
        self.apply_colours(self) 
    
    def setup_ui(self): 
            self.setFixedSize(750, 750) 
            self.title_label = QtWidgets.QLabel(self) 
            self.title_label.setGeometry(QtCore.QRect(0, 15, 750, 75)) 
            self.title_label.colour = 1 
            self.title_label.setFont(QFont(self.settings.font, 30))  
            self.title_label.setText('FPL Helper') 

            self.email_edit = QtWidgets.QLineEdit(self) 
            self.email_edit.setGeometry(QtCore.QRect(75, 135, 300, 30)) 
            self.email_edit.colour = 1 
            self.email_edit.setPlaceholderText('Enter Email') 
            self.email_edit.setFont(QFont(self.settings.font, 12)) 
            self.email_edit.setText('harryespley@outlook.com') 

            self.password_edit = QtWidgets.QLineEdit(self) 
            self.password_edit.setGeometry(QtCore.QRect(75, 210, 300, 30)) 
            self.password_edit.colour = 1 
            self.password_edit.setPlaceholderText('Enter Password') 
            self.password_edit.setFont(QFont(self.settings.font, 12)) 
            self.password_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)  
            self.password_edit.setText('James141005!') 

            self.email_label = QtWidgets.QLabel(self) 
            self.email_label.setGeometry(QtCore.QRect(75, 105, 300, 30)) 
            self.email_label.colour = 0  
            self.email_label.setText('Email:') 
            self.email_label.setFont(QFont(self.settings.font, 12))   

            self.password_label = QtWidgets.QLabel(self) 
            self.password_label.setGeometry(QtCore.QRect(75, 180, 300, 30)) 
            self.password_label.colour = 0 
            self.password_label.setText('Password:') 
            self.password_label.setFont(QFont(self.settings.font, 12))   

            self.error_label = QtWidgets.QLabel(self) 
            self.error_label.setGeometry(QtCore.QRect(150, 105, 300, 30)) 
            self.error_label.setStyleSheet(f'color: {self.settings.colour_scheme.error_colour}')
            self.error_label.setFont(QFont(self.settings.font, 12))  

            self.login_button = CustomButton(self) 
            self.login_button.setGeometry(QtCore.QRect(75, 255, 300, 30)) 
            self.login_button.colour = 1 
            self.login_button.setText('Login') 
            self.login_button.setFont(QFont(self.settings.font, 12)) 
            self.login_button.clicked.connect(self.check_login) 

            self.exit_button = CustomButton(self) 
            self.exit_button.setGeometry(QtCore.QRect(75, 300, 300, 30)) 
            self.exit_button.colour = 1 
            self.exit_button.setText('Exit') 
            self.exit_button.setFont(QFont(self.settings.font, 12)) 
            self.exit_button.clicked.connect(lambda: self.open_window(5))    

    def check_login(self): 
        cookies = utils.get_account_cookies(self.session, self.email_edit.text(), self.password_edit.text())  
        if cookies:  
            user = utils.create_user_object(self.session, cookies)   
            fpl_cookies = self.session.cookies 
            self.fpl = FPL(self.session, user)   
            self.fpl.session.cookies = fpl_cookies  
            self.open_window(1) 
        else:     
            raise Exception('Login failed!') 

class MainWindow(WindowParent): 
    def __init__(self, previous_window, fpl): 
        super().__init__(previous_window, fpl)  
        self.window_id = 1   
        self.setup_ui()   
        self.apply_colours(self) 
    
    def setup_ui(self): 
        self.setFixedSize(1000, 1000)  
        self.title_label = QtWidgets.QLabel(self) 
        self.title_label.setGeometry(QtCore.QRect(0, 10, 1000, 100))  
        self.title_label.colour = 1 
        self.title_label.setFont(QFont(self.settings.font, 20)) 
        self.title_label.setText('FPL Companion')  

        self.rank_label = QtWidgets.QLabel(self) 
        self.rank_label.setGeometry(QtCore.QRect(350, 150, 250, 50)) 
        self.rank_label.colour = 0 
        self.rank_label.setFont(QFont(self.settings.font, 16)) 
        self.rank_label.setText(f'Current Rank: {self.fpl.get_current_user_rank()}')  

        self.update_players_button = CustomButton(self) 
        self.update_players_button.setGeometry(QtCore.QRect(25, 150, 250, 50)) 
        self.update_players_button.colour = 1 
        self.update_players_button.setFont(QFont(self.settings.font, 8)) 
        self.update_players_button.setText('Update Player Data') 
        self.update_players_button.clicked.connect(lambda: utils.update_player_table(self.fpl.db_connection, self.fpl.session)) 
        self.update_players_button.clicked.connect(lambda: utils.update_composite_scores(self.fpl.db_connection)) 

        self.lineup_button = CustomButton(self) 
        self.lineup_button.setGeometry(QtCore.QRect(300, 250, 400, 80)) 
        self.lineup_button.colour = 1 
        self.lineup_button.setFont(QFont(self.settings.font, 14)) 
        self.lineup_button.setText('View my lineup')    
        self.lineup_button.clicked.connect(lambda: self.open_window(2)) 

        self.league_button = CustomButton(self) 
        self.league_button.setGeometry(QtCore.QRect(300, 330, 400, 80)) 
        self.league_button.colour = 1 
        self.league_button.setFont(QFont(self.settings.font, 14)) 
        self.league_button.setText('Leagues Viewer')  
        self.league_button.clicked.connect(lambda: self.open_window(3)) 

        self.database_button = CustomButton(self) 
        self.database_button.setGeometry(QtCore.QRect(300, 410, 400, 80))  
        self.database_button.colour = 1 
        self.database_button.setFont(QFont(self.settings.font, 14)) 
        self.database_button.setText('Player Database')   
        self.database_button.clicked.connect(lambda: self.open_window(4)) 

        self.settings_button = CustomButton(self) 
        self.settings_button.setGeometry(QtCore.QRect(300, 490, 400, 80)) 
        self.settings_button.colour = 1 
        self.settings_button.setFont(QFont(self.settings.font, 14)) 
        self.settings_button.setText('Settings')   
        self.settings_button.clicked.connect(lambda: self.open_window(5)) 

        self.exit_button = CustomButton(self) 
        self.exit_button.setGeometry(QtCore.QRect(300, 570, 400, 80)) 
        self.exit_button.colour = 1 
        self.exit_button.setFont(QFont(self.settings.font, 14)) 
        self.exit_button.setText('Exit') 

class LineupWindow(WindowParent): 
    def __init__(self, previous_window, fpl): 
        super().__init__(previous_window, fpl) 
        self.window_id = 2   
        self.column_headers = ['Name', 'Team', 'Position', 'Price', 'Total Points', 'PPG']  
        picks_json = self.fpl.get_current_user_picks() 
        picks = [utils.create_player_object(fpl.db_connection, x['element']) for x in picks_json]   
        for index, x in enumerate(picks): 
            x.sell_cost = picks_json[index]['selling_price']/10 
        self.starting_eleven = picks[:11] 
        self.bench = picks[11:]  
        self.user_balance = self.fpl.get_current_user_balance() 
        self.setup_ui()  
        self.apply_colours(self)      
        players = self.fpl.get_all_players()     
        self.free_hit = self.generate_free_hit(players)  
        self.free_hit_starters, self.free_hit_bench = self.seperate_lineup(self.free_hit) 
    
    def generate_free_hit(self, players):  
        budget = sum([player.sell_cost for player in self.starting_eleven]) + sum([player.sell_cost for player in self.bench]) + self.user_balance   
        bench_importance = 0.1
        chip_type = 'free_hit'  
        return base.ChipOptimiser.generate_team(players, budget, bench_importance, chip_type) 
    
    def generate_wildcard(self, players): 
        budget = sum([player.sell_cost for player in self.starting_eleven]) + sum([player.sell_cost for player in self.bench]) + self.user_balance   
        bench_importance = 0.3
        chip_type = 'wildcard' 
        return base.ChipOptimiser.generate_team(players, budget, bench_importance, chip_type)   
    
    def seperate_lineup(self, arr): 
        return arr[:11], arr[11:]     

    def setup_ui(self): 
        self.setFixedSize(1000, 1000)  

        self.formation_button = CustomButton(self) 
        self.formation_button.setGeometry(QtCore.QRect(290, 10, 100, 40)) 
        self.formation_button.colour = 1 
        self.formation_button.setFont(QFont(self.settings.font, 8)) 
        self.formation_button.setText('Formation View')  
        self.formation_button.clicked.connect(self.toggle)  

        self.list_button = CustomButton(self) 
        self.list_button.setGeometry(QtCore.QRect(400, 10, 100, 40)) 
        self.list_button.colour = 1 
        self.list_button.setFont(QFont(self.settings.font, 8)) 
        self.list_button.setText('List View')  
        self.list_button.clicked.connect(self.toggle)    

        self.back_button = CustomButton(self) 
        self.back_button.setGeometry(QtCore.QRect(10, 10, 100, 40)) 
        self.back_button.colour = 1 
        self.back_button.setFont(QFont(self.settings.font, 8)) 
        self.back_button.setText('Back') 
        self.back_button.clicked.connect(self.back_window)   

        self.my_team_button = CustomButton(self) 
        self.my_team_button.setGeometry(QtCore.QRect(10, 800, 100, 40)) 
        self.my_team_button.colour = 1 
        self.my_team_button.setFont(QFont(self.settings.font, 8)) 
        self.my_team_button.setText('My Team') 
        self.my_team_button.clicked.connect(lambda: self.change_starting_eleven_list(self.starting_eleven)) 
        self.my_team_button.clicked.connect(lambda: self.change_bench_list(self.bench)) 

        self.free_hit_button = CustomButton(self) 
        self.free_hit_button.setGeometry(QtCore.QRect(150, 800, 100, 40)) 
        self.free_hit_button.colour = 1 
        self.free_hit_button.setFont(QFont(self.settings.font, 8)) 
        self.free_hit_button.setText('Free Hit')  
        self.free_hit_button.clicked.connect(lambda: self.change_starting_eleven_list(self.free_hit_starters)) 
        self.free_hit_button.clicked.connect(lambda: self.change_bench_list(self.free_hit_bench)) 

        self.wildcard_button = CustomButton(self) 
        self.wildcard_button.setGeometry(QtCore.QRect(290, 800, 100, 40)) 
        self.wildcard_button.colour = 1 
        self.wildcard_button.setFont(QFont(self.settings.font, 8)) 
        self.wildcard_button.setText('Wildcard')  

        self.transfer_button = CustomButton(self)  
        self.transfer_button.setGeometry(QtCore.QRect(430, 800, 100, 40)) 
        self.transfer_button.colour = 1 
        self.transfer_button.setFont(QFont(self.settings.font, 8)) 
        self.transfer_button.setText('Recommend Transfers') 

        self.main_widget = QtWidgets.QWidget(self) 
        self.main_widget.setGeometry(QtCore.QRect(0, 50, 1000, 750)) 

        self.formation_widget = QtWidgets.QWidget(self) 
        self.formation_widget.setLayout(self.setup_formation_view()) 

        self.list_widget = QtWidgets.QWidget(self) 
        self.list_widget.setLayout(self.setup_list_view())  


        self.stacked_layout = QStackedLayout(self)  
        self.stacked_layout.addWidget(self.formation_widget) 
        self.stacked_layout.addWidget(self.list_widget)  

        self.main_widget.setLayout(self.stacked_layout) 
    
    def toggle(self): 
        if self.sender() == self.formation_button or self.sender() == None:  
            self.formation_button.setStyleSheet('background-color: rgb(0, 255, 0);')  
            self.apply_colour(self.list_button) 
            self.stacked_layout.setCurrentWidget(self.formation_widget) 
        else: 
            self.list_button.setStyleSheet('background-color: rgb(0, 255, 0);')  
            self.apply_colour(self.formation_button) 
            self.stacked_layout.setCurrentWidget(self.list_widget) 

    def setup_list_view(self):  
        layout = QVBoxLayout() 
        self.starting_eleven_table = QtWidgets.QTableWidget(self) 
        self.starting_eleven_table.colour = 1 
        self.starting_eleven_table.setFont(QFont(self.settings.font, 8)) 
        self.starting_eleven_table.setColumnCount(6) 
        self.starting_eleven_table.setRowCount(11) 
        self.starting_eleven_table.setHorizontalHeaderLabels(self.column_headers)   

        self.bench_table = QtWidgets.QTableWidget(self)  
        self.bench_table.colour = 1 
        self.bench_table.setFont(QFont(self.settings.font, 8)) 
        self.bench_table.setColumnCount(6)  
        self.bench_table.setRowCount(4) 
        self.bench_table.setHorizontalHeaderLabels(self.column_headers)   

        layout.addWidget(self.starting_eleven_table)
        layout.addWidget(self.bench_table)  
        return layout  

    def change_starting_eleven_list(self, players): 
        self.starting_eleven_table.clearContents() 
        for index, player in enumerate(players): 
            self.starting_eleven_table.setItem(index, 0, QtWidgets.QTableWidgetItem(player.name)) 
            self.starting_eleven_table.setItem(index, 1, QtWidgets.QTableWidgetItem(str(utils.convert_team(player.team)))) 
            self.starting_eleven_table.setItem(index, 2, QtWidgets.QTableWidgetItem(str(utils.convert_position(player.position)))) 
            self.starting_eleven_table.setItem(index, 3, QtWidgets.QTableWidgetItem(str(player.cost))) 
            self.starting_eleven_table.setItem(index, 4, QtWidgets.QTableWidgetItem(str(player.total_points))) 
            self.starting_eleven_table.setItem(index, 5, QtWidgets.QTableWidgetItem(str(player.ppg)))  
    
    def change_bench_list(self, players): 
        self.bench_table.clearContents() 
        for index, player in enumerate(players): 
            self.bench_table.setItem(index, 0, QtWidgets.QTableWidgetItem(player.name)) 
            self.bench_table.setItem(index, 1, QtWidgets.QTableWidgetItem(str(utils.convert_team(player.team)))) 
            self.bench_table.setItem(index, 2, QtWidgets.QTableWidgetItem(str(utils.convert_position(player.position)))) 
            self.bench_table.setItem(index, 3, QtWidgets.QTableWidgetItem(str(player.cost))) 
            self.bench_table.setItem(index, 4, QtWidgets.QTableWidgetItem(str(player.total_points))) 
            self.bench_table.setItem(index, 5, QtWidgets.QTableWidgetItem(str(player.ppg))) 

    def setup_formation_view(self):   
        layout = QVBoxLayout() 
        return layout 

class LeagueWindow(WindowParent): 
    def __init__(self, previous_window, fpl): 
        super().__init__(previous_window, fpl) 
        self.window_id = 3  
        self.leagues = self.fpl.get_current_user_leagues() 
        self.setup_ui() 
        self.apply_colours(self) 
    
    def setup_ui(self): 
        self.setFixedSize(1000, 1000) 

        self.league_chooser = QComboBox(self)  
        self.league_chooser.setGeometry(QtCore.QRect(800, 0, 200, 50))  
        self.league_chooser.colour = 1 
        for x in self.fpl.get_current_user_leagues():  
            self.league_chooser.addItem(x['name'])  

        self.view_league_button = CustomButton(self)   
        self.view_league_button.setGeometry(QtCore.QRect(800, 50, 200, 50))   
        self.view_league_button.colour = 1  
        self.view_league_button.setFont(QFont(self.settings.font, 8))
        self.view_league_button.setText('View League')  
        self.view_league_button.clicked.connect(self.view_league)  

        self.back_button = CustomButton(self) 
        self.back_button.setGeometry(QtCore.QRect(0, 0, 100, 50)) 
        self.back_button.colour = 1 
        self.back_button.setFont(QFont(self.settings.font, 8)) 
        self.back_button.setText('Back') 
        self.back_button.clicked.connect(self.back_window) 

        self.league_table = QtWidgets.QTableWidget(self) 
        self.league_table.setGeometry(QtCore.QRect(0, 100, 1000, 900))  
        self.league_table.colour = 1 
        self.league_table.setFont(QFont(self.settings.font, 8)) 
        self.league_table.setColumnCount(5) 
        self.league_table.setHorizontalHeaderLabels(['Rank', 'Name', 'Team Name', 'Gameweek Points', 'Total Points'])  
    
    def view_league(self):  
        self.league_table.clearContents() 
        league = self.league_chooser.currentText() 
        league_id = [x for x in self.leagues if x['name'] == league][0]['id'] 
        standings = self.fpl.get_league_standings(league_id)   
        self.league_table.setRowCount(len(standings))   
        for x in standings:   
            self.league_table.setItem(x['rank']-1, 0, QtWidgets.QTableWidgetItem(str(x['rank']))) 
            self.league_table.setItem(x['rank']-1, 1, QtWidgets.QTableWidgetItem(x['player_name'])) 
            self.league_table.setItem(x['rank']-1, 2, QtWidgets.QTableWidgetItem(x['entry_name'])) 
            self.league_table.setItem(x['rank']-1, 3, QtWidgets.QTableWidgetItem(str(x['event_total']))) 
            self.league_table.setItem(x['rank']-1, 4, QtWidgets.QTableWidgetItem(str(x['total']))) 

class DatabaseWindow(WindowParent): 
    def __init__(self, previous_window, fpl): 
        super().__init__(previous_window, fpl) 
        self.window_id = 4  
        self.sort_switcher = { 
            0: lambda x: x.player_id, 
            1: lambda x: x.name, 
            2: lambda x: -x.cost, 
            3: lambda x: -x.total_points, 
            4: lambda x: x.position, 
            5: lambda x: x.team, 
            6: lambda x: -x.ppg, 
            7: lambda x: -x.owned_by, 
            8: lambda x: -x.composite_score 
        } 
        self.raw_players = self.fpl.get_all_players()  
        self.setup_ui() 
        self.apply_colours(self)        
    
    def sort_by(self, players, value): 
        players = utils.merge_sort(players, key=self.sort_switcher[value]) 
        return players  

    def add_players_to_table(self, value=0): 
        self.player_table.clearContents() 
        players = self.sort_by(self.raw_players, value) 
        self.player_table.setRowCount(len(players))   
        for index, x in enumerate(players):   
            self.player_table.setItem(index, 0, QtWidgets.QTableWidgetItem(str(x.player_id))) 
            self.player_table.setItem(index, 1, QtWidgets.QTableWidgetItem(x.name)) 
            self.player_table.setItem(index, 2, QtWidgets.QTableWidgetItem(str(x.cost))) 
            self.player_table.setItem(index, 3, QtWidgets.QTableWidgetItem(str(x.total_points))) 
            self.player_table.setItem(index, 4, QtWidgets.QTableWidgetItem(str(utils.convert_position(x.position)))) 
            self.player_table.setItem(index, 5, QtWidgets.QTableWidgetItem(str(utils.convert_team(x.team)))) 
            self.player_table.setItem(index, 6, QtWidgets.QTableWidgetItem(str(x.ppg))) 
            self.player_table.setItem(index, 7, QtWidgets.QTableWidgetItem(str(x.owned_by))) 
            self.player_table.setItem(index, 8, QtWidgets.QTableWidgetItem(str(round(x.composite_score)))) 
    
    def setup_ui(self):
        self.setFixedSize(1000, 1000) 
        
        self.title_label = QtWidgets.QLabel(self) 
        self.title_label.setGeometry(QtCore.QRect(0, 0, 1000, 100)) 
        self.title_label.colour = 1 
        self.title_label.setFont(QFont(self.settings.font, 20)) 
        self.title_label.setText('Player Database')  

        self.sort_by_box = QComboBox(self) 
        self.sort_by_box.setGeometry(QtCore.QRect(10, 150, 200, 50)) 
        self.sort_by_box.colour = 1 
        self.sort_by_box.setFont(QFont(self.settings.font, 8))  
        self.sort_by_box.addItems(['ID', 'Name', 'Cost', 'Total Points', 'Position', 'Team', 'PPG', 'Owned by', 'Composite Score'])
        self.sort_by_box.currentIndexChanged.connect(self.add_players_to_table)  

        self.back_button = CustomButton(self) 
        self.back_button.setGeometry(QtCore.QRect(230, 150, 200, 50)) 
        self.back_button.colour = 1 
        self.back_button.setFont(QFont(self.settings.font, 8)) 
        self.back_button.setText('Back') 
        self.back_button.clicked.connect(self.back_window) 

        self.player_table = QtWidgets.QTableWidget(self) 
        self.player_table.setGeometry(QtCore.QRect(0, 200, 1000, 750)) 
        self.player_table.colour = 1 
        self.player_table.setFont(QFont(self.settings.font, 8)) 
        self.player_table.setColumnCount(9)         
        self.player_table.verticalHeader().hide() 
        self.player_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.player_table.setHorizontalHeaderLabels([
            'ID', 
            'Name', 
            'Cost',   
            'Total Points', 
            'Position', 
            'Team', 
            'PPG', 
            'Owned by', 
            'Composite Score'
        ])  
        self.add_players_to_table() 


class SettingsWindow(WindowParent): 
    def __init__(self, previous_window, fpl): 
        super().__init__(previous_window, fpl) 
        self.window_id = 5 
        self.settings_dict = {} 
        self.recent_press = None  
        self.setup_ui() 
        self.section_switcher = { 
            self.colour_button: self.open_colour_settings, 
            self.font_button: self.open_font_settings, 
            self.sound_button: self.open_sound_settings
        }    
        self.apply_colours(self) 

    def settings_window_refresh(self): 
        self.close() 
        self.window = self.window_switcher[self.window_id](self.previous_window, self.fpl) 
        if self.recent_press != None: 
            self.section_switcher[self.recent_press]() 
        self.window.show()   

    def volume_value_changed(self, value): 
        self.sender().parent().volume_entry.setText(str(value)) 

    def fill_colour_widget(self): 
        self.colour_widget.info_label = QtWidgets.QLabel(self.colour_widget) 
        self.colour_widget.info_label.setGeometry(QtCore.QRect(0, 0, 200, 40))  
        self.colour_widget.info_label.setFont(QFont(self.settings.font, 8)) 
        self.colour_widget.info_label.setText('Colour Settings:') 
        
        self.colour_widget.primary_button = QPushButton(self.colour_widget) 
        self.colour_widget.primary_button.setGeometry(QtCore.QRect(0, 50, 100, 40)) 
        self.colour_widget.primary_button.colour = 1 
        self.colour_widget.primary_button.setFont(QFont(self.settings.font, 8)) 
        self.colour_widget.primary_button.setText('Primary Colour') 
        self.colour_widget.primary_button.clicked.connect(lambda: self.open_colour_window('primary_colour'))  
        
        self.colour_widget.secondary_button = QPushButton(self.colour_widget) 
        self.colour_widget.secondary_button.setGeometry(QtCore.QRect(125, 50, 100, 40)) 
        self.colour_widget.secondary_button.colour = 1 
        self.colour_widget.secondary_button.setFont(QFont(self.settings.font, 8)) 
        self.colour_widget.secondary_button.setText('Secondary Colour') 
        self.colour_widget.secondary_button.clicked.connect(lambda: self.open_colour_window('secondary_colour')) 
    
    def fill_font_widget(self): 
        self.font_widget.info_label = QtWidgets.QLabel(self.font_widget) 
        self.font_widget.info_label.setGeometry(QtCore.QRect(0, 0, 200, 40)) 
        self.font_widget.info_label.setFont(QFont(self.settings.font, 8)) 
        self.font_widget.info_label.setText('Font Settings:')  

        self.font_widget.font_button = QPushButton(self.font_widget) 
        self.font_widget.font_button.setGeometry(QtCore.QRect(0, 50, 100, 40)) 
        self.font_widget.font_button.colour = 1 
        self.font_widget.font_button.setFont(QFont(self.settings.font, 8)) 
        self.font_widget.font_button.setText('Font') 
        self.font_widget.font_button.clicked.connect(self.open_font_window)    
    
    def fill_sound_widget(self): 
        self.sound_widget.info_label = QtWidgets.QLabel(self.sound_widget) 
        self.sound_widget.info_label.setGeometry(QtCore.QRect(0, 0, 200, 40)) 
        self.sound_widget.info_label.setFont(QFont(self.settings.font, 8)) 
        self.sound_widget.info_label.setText('Sound Settings:')   

        self.sound_widget.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, self.sound_widget) 
        self.sound_widget.slider.setGeometry(QtCore.QRect(0, 50, 200, 40)) 
        self.sound_widget.slider.colour = 1   
        self.sound_widget.slider.setMinimum(0) 
        self.sound_widget.slider.setMaximum(100) 
        self.sound_widget.slider.setValue(self.settings.button_volume)  
        self.sound_widget.slider.valueChanged.connect(self.volume_value_changed) 

        self.sound_widget.volume_entry = QtWidgets.QLineEdit(self.sound_widget) 
        self.sound_widget.volume_entry.setGeometry(QtCore.QRect(250, 50, 100, 40)) 
        self.sound_widget.volume_entry.colour = 1 
        self.sound_widget.volume_entry.setFont(QFont(self.settings.font, 8))
        self.sound_widget.volume_entry.setText(str(self.settings.button_volume))  

        self.sound_widget.sound_box = QtWidgets.QComboBox(self.sound_widget) 
        self.sound_widget.sound_box.setGeometry(QtCore.QRect(0, 100, 200, 40)) 
        self.sound_widget.sound_box.colour = 1 
        self.sound_widget.sound_box.setFont(QFont(self.settings.font, 8)) 
        self.sound_widget.sound_box.addItems([x for x in os.listdir(os.path.join(os.getcwd(), 'sounds')) if x.endswith('.wav')]) 

    def open_colour_settings(self):  
        self.recent_press = self.sender() 
        self.stacked_layout.setCurrentWidget(self.colour_widget) 

    def open_font_settings(self): 
        self.stacked_layout.setCurrentWidget(self.font_widget)  

    def open_sound_settings(self): 
        self.stacked_layout.setCurrentWidget(self.sound_widget) 

    def open_colour_window(self, section): 
        col = {'primary_colour': 0, 'secondary_colour': 1} 
        colour = QColorDialog.getColor() 
        rgb_list = [colour.red(), colour.green(), colour.blue()] 
        if colour.isValid():  
            if float(utils.colour_distance(rgb_list, utils.string_to_rgb(self.settings.settings_switcher[col[section]]))) > 20: 
                rgb_string = utils.rgb_to_string(rgb_list) 
                self.add_to_settings(section, rgb_string) 
            else: 
                self.error_label.setText('Colour too similiar to other colour!') 

    def open_font_window(self): 
        font, ok = QFontDialog.getFont() 
        if ok: 
            self.settings_dict['font'] = font.family()  

    def add_to_settings(self, key, value): 
        self.settings_dict[key] = value 

    def apply_settings(self): 
        if self.recent_press == 'button_sound': 
            self.settings_dict['button_sound'] = self.sound_box.currentText() 
            self.settings_dict['button_volume'] = int(self.volume_entry.text()) 
        self.settings.change_settings(self.settings_dict) 
        self.settings_window_refresh()  
    
    def log_out(self): 
        pass 
    
    def setup_ui(self):  
        self.setFixedSize(600, 600) 
        self.title_label = QtWidgets.QLabel(self)  
        self.title_label.setGeometry(QtCore.QRect(0, 10, 600, 100))  
        self.title_label.colour = 1 
        self.title_label.setFont(QFont(self.settings.font, 20)) 
        self.title_label.setText('Settings')  

        self.back_button = CustomButton(self) 
        self.back_button.setGeometry(QtCore.QRect(0, 520, 100, 50)) 
        self.back_button.colour = 1 
        self.back_button.setFont(QFont(self.settings.font, 8)) 
        self.back_button.setText('Back')  
        self.back_button.clicked.connect(self.back_window)  

        self.apply_button = CustomButton(self) 
        self.apply_button.setGeometry(460, 520, 100, 40) 
        self.apply_button.colour = 1 
        self.apply_button.setFont(QFont(self.settings.font, 8)) 
        self.apply_button.setText('Apply') 
        self.apply_button.clicked.connect(self.apply_settings) 

        self.colour_button = CustomButton(self) 
        self.colour_button.setGeometry(QtCore.QRect(0, 150, 150, 40)) 
        self.colour_button.colour = 1 
        self.colour_button.setFont(QFont(self.settings.font, 8)) 
        self.colour_button.setText('Colour')   
        self.colour_button.clicked.connect(self.open_colour_settings) 

        self.font_button = CustomButton(self) 
        self.font_button.setGeometry(QtCore.QRect(0, 190, 150, 40)) 
        self.font_button.colour = 1 
        self.font_button.setFont(QFont(self.settings.font, 8))  
        self.font_button.setText('Font')  
        self.font_button.clicked.connect(self.open_font_settings)    

        self.sound_button = CustomButton(self) 
        self.sound_button.setGeometry(QtCore.QRect(0, 230, 150, 40)) 
        self.sound_button.colour = 1 
        self.sound_button.setFont(QFont(self.settings.font, 8)) 
        self.sound_button.setText('Button Sound')  
        self.sound_button.clicked.connect(self.open_sound_settings)   

        self.logout_button = CustomButton(self) 
        self.logout_button.setGeometry(QtCore.QRect(0, 270, 150, 40)) 
        self.logout_button.colour = 1 
        self.logout_button.setFont(QFont(self.settings.font, 8)) 
        self.logout_button.setText('Log Out')   

        self.error_label = QtWidgets.QLabel(self) 
        self.error_label.setGeometry(QtCore.QRect(0, 500, 150, 40)) 
        self.error_label.setStyleSheet(f'color: {self.settings.colour_scheme.error_colour}') 
        self.error_label.setFont(QFont(self.settings.font, 8)) 

        self.main_widget = QWidget(self) 
        self.main_widget.setGeometry(QtCore.QRect(200, 150, 350, 350))    

        self.colour_widget = QWidget(self.main_widget) 
        self.colour_widget.setFixedSize(350, 350) 
        self.fill_colour_widget() 

        self.font_widget = QWidget(self.main_widget) 
        self.font_widget.setFixedSize(350, 350)  
        self.fill_font_widget() 

        self.sound_widget = QWidget(self.main_widget) 
        self.sound_widget.setFixedSize(350, 350)  
        self.fill_sound_widget() 

        self.stacked_layout = QStackedLayout(self)   
        self.stacked_layout.addWidget(QWidget())  
        self.stacked_layout.addWidget(self.colour_widget)  
        self.stacked_layout.addWidget(self.font_widget)
        self.stacked_layout.addWidget(self.sound_widget)

        self.main_widget.setLayout(self.stacked_layout)   


class ExitWindow(WindowParent): 
    pass 

if __name__ == '__main__': 
    app = QtWidgets.QApplication(sys.argv)  
    window = LoginWindow() 
    window.show()  
    sys.exit(app.exec()) 
