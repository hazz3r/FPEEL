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
        # Initiates a settings object 
        self.settings = Settings()   
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose) 
        # Sets the background colour of the window to the primary colour from the colour scheme in the settings 
        self.setStyleSheet(f'background-color: {self.settings.colour_scheme.primary_colour}')   
        # Different windows mapped to different integer values makes the process of opening a new window much more streamlined 
        # Any of these integers can simply be passed as an argument into the `open_window` method 
        self.window_switcher = { 
            0: LoginWindow, 
            1: MainWindow, 
            2: LineupWindow, 
            3: LeagueWindow,  
            4: DatabaseWindow, 
            5: SettingsWindow, 
            6: ExitWindow, 
        }  
        # This dictionary allows for the dynamic acccess and modification of styles and colour schemes 
        self.colour_switcher = { 
            0: f'background-color: {self.settings.colour_scheme.primary_colour}'f'color: {self.settings.colour_scheme.secondary_colour}', 
            1: f'background-color: {self.settings.colour_scheme.secondary_colour}'f'color: {self.settings.colour_scheme.primary_colour}' 
        } 
    
    def refresh(self):  
        # Closes the current instance of the window 
        self.close()  
        # Creates a new instance of the same time of window (as it would have the same window_id) 
        self.new_window = self.window_switcher[self.window_id](fpl=self.fpl, previous_window=self.previous_window)    

    def open_window(self, window):  
        # If the window entered is not ExitWindow then close the current window 
        if window != 6: 
            self.close()  
        # Creates a new window 
        # Which window is created by which value the input window corresponds to in self.window_switcher 
        self.new_window = self.window_switcher[window](fpl=self.fpl, previous_window=self.window_id)     
        self.new_window.show() 
    
    def back_window(self):  
        # If there has been a previous window (the starting value is None) 
        if self.previous_window:  
            # Open a the window with id=self.previous_window 
            self.open_window(self.previous_window)   

    def apply_colour(self, widget):  
        # If the widget has child widgets 
        # e.g. A DialogButtonBox has two QPushButtons within it 
        if widget.children(): 
            # Iterates through the children of 'widget' 
            for child in widget.children():   
                # Don't colour QObjects 
                if not isinstance(child, QtCore.QObject):   
                    # Recursive 
                    # As seen below it tries with the parent colour if the selected widget does not have an attribute colour 
                    self.apply_colour(child)  
        try: 
            # Sets the stylesheet of the widget to what their colour attribute corresponds to in colour_switcher 
            widget.setStyleSheet(self.colour_switcher[widget.colour]) 
        except:  
            # If the above did not work 
            # Sets the stylesheet of teh widget to what their parent's colour attribute correspodns to in colour_switcher 
            widget.setStyleSheet(self.colour_switcher[widget.parent().colour]) 

    def apply_colours(self, parent):  
        # Iterates through all the widgets in a window 
        for widget in parent.findChildren(QWidget):  
            # If a given widget has the attribute 'colour' 
            if hasattr(widget, 'colour'):  
                # Applies colour to the widget 
                parent.apply_colour(widget)     

    def relayout(self, widget): 
        QWidget().setLayout(widget.layout()) 

class CustomButton(QPushButton): 
    def __init__(self, parent=None): 
        super().__init__(parent) 
        self.parent = parent 
        # Connects self.handle_clicked to when the button is clicked 
        self.clicked.connect(self.handle_clicked) 
        # If the button has a parent (i.e. if the button is in a window) 
        if self.parent:  
            # Creates a sound effect 
            self.sound_effect = QSoundEffect() 
            # Populates the sound effect with the source file (must be .wav) 
            self.sound_effect.setSource(QUrl.fromLocalFile(self.parent.settings.button_sound))   
    
    def play_sound(self, volume): 
        # Sets the volume to be played at 
        self.sound_effect.setVolume(volume)  
        # Plays the sound effect 
        self.sound_effect.play() 

    def handle_clicked(self): 
        # If the button is in a window 
        if self.parent:  
            # Plays the QSoundEffect 
            self.play_sound(self.parent.settings.button_volume)  

class Settings: 
    def __init__(self): 
        # Sets self.settings_path to the Working Directory + \json_data\settings.json\  
        self.settings_path = os.path.join(os.getcwd(), 'json_data', 'settings.json')  
        try:  
            # Tries to read the contents of settings.json into a JSON string 
            settings = utils.read_json(self.settings_path)  
        except json.JSONDecodeError:  
            # If the above fails then creates a new JSON string with default values 
            settings = { 
                'primary_colour': None, 
                'secondary_colour': None, 
                'font': 'Arial', 
                'button_sound': None, 
                'button_volume': None 
            }   
            # Writes the new JSON string into settings.json 
            utils.write_json(settings, self.settings_path)   
        # Sets the colour scheme atttribute to a ColourScheme object based on the contents of settings.json 
        self.colour_scheme = ColourScheme(settings['primary_colour'], settings['secondary_colour'])  
        # Sets the font attributes of the settings object to the font in settings.json 
        self.font = settings['font']  
        # Sets the button_sound attribute of the settings object to the button_sound path in settings.json 
        self.button_sound = settings['button_sound']  
        # Sets the button_volume attribute of the settings object to the integer value of button_volume in settings.json 
        self.button_volume = settings['button_volume']   
        # Settings switcher that allows for the dynamic modification of settings in the application 
        # Does so through mapping the settings to integer values 
        self.settings_switcher = { 
            0: self.colour_scheme.primary_colour, 
            1: self.colour_scheme.secondary_colour, 
            2: self.font, 
            3: self.button_sound, 
            4: self.button_volume 
        }
    
    def change_settings(self, settings_dict): 
        # Reads settings.json as a JSON string 
        settings = utils.read_json(self.settings_path) 
        # Iterates by key (k) through the JSON string 
        for k in settings_dict:  
            # Changes the JSON string to the same value in the new, modified settings (settings_dict) 
            settings[k] = settings_dict[k] 
            # Changes the value in the runtime settings 
            self.settings_switcher[k] = settings_dict[k] 
        # Writes the changes in settings.json 
        utils.write_json(settings, self.settings_path)   

# Dataclass used for dynamic access and modification of the colour scheme used to colour widgets in the application
@dataclass 
class ColourScheme: 
    primary_colour: str = None 
    secondary_colour: str = None 
    error_colour = 'rgb(255, 0, 0);'   

class LoginWindow(WindowParent): 
    def __init__(self, previous_window=None, fpl=None): 
        super().__init__(previous_window, fpl)  
        # Session used to interact with fantasy.premierleague.com to login  
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
            # Sets default text 
            self.email_edit.setPlaceholderText('Enter Email') 
            self.email_edit.setFont(QFont(self.settings.font, 12)) 
            self.email_edit.setText('GrgeHkt@outlook.com') 

            self.password_edit = QtWidgets.QLineEdit(self) 
            self.password_edit.setGeometry(QtCore.QRect(75, 210, 300, 30)) 
            self.password_edit.colour = 1  
            # Sets default text 
            self.password_edit.setPlaceholderText('Enter Password') 
            self.password_edit.setFont(QFont(self.settings.font, 12)) 
            # Makes the password asterixs instead of regular characters 
            self.password_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)  
            self.password_edit.setText('Fortnote2*') 

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
            # Makes check_login run when the login_button is clicked 
            self.login_button.clicked.connect(self.check_login) 

            self.exit_button = CustomButton(self) 
            self.exit_button.setGeometry(QtCore.QRect(75, 300, 300, 30)) 
            self.exit_button.colour = 1 
            self.exit_button.setText('Exit') 
            self.exit_button.setFont(QFont(self.settings.font, 12))  
            # Opens the exit window 
            # Lambda function used so that parameters can be passed 
            self.exit_button.clicked.connect(lambda: self.open_window(6))    

    def check_login(self):  
        # Retrieves the account cookies of the user by authenticating on the FPL website 
        # Takes the relevant cookies from the cookies of the authenticated session 
        cookies = utils.get_account_cookies(self.session, self.email_edit.text(), self.password_edit.text())   
        # If the authentication worked (email and password were correct) 
        if cookies:   
            # Creates a user object based on the cookies provided 
            user = utils.create_user_object(self.session, cookies) 
            # Temporary storage for the cookies    
            fpl_cookies = self.session.cookies 
            # Creates an fpl object using the session and user objects 
            self.fpl = FPL(self.session, user)    
            # Makes the cookies of the fpl object the cookies obtained from authentication 
            self.fpl.session.cookies = fpl_cookies   
            # Opens an instance of MainWindow (closing this instance of LoginWindow) 
            self.open_window(1) 
        else:     
            self.error_label.setText('Login failed please try again') 

class MainWindow(WindowParent): 
    def __init__(self, previous_window, fpl): 
        super().__init__(previous_window, fpl)  
        self.window_id = 1   
        self.setup_ui()   
        # Applies colours to all widgets in MainWindow 
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
        # Displays the current rank of the user in the 'overall' league
        self.rank_label.setText(f'Current Rank: {self.fpl.get_current_user_rank()}')  

        self.update_players_button = CustomButton(self) 
        self.update_players_button.setGeometry(QtCore.QRect(25, 150, 250, 50)) 
        self.update_players_button.colour = 1 
        self.update_players_button.setFont(QFont(self.settings.font, 8)) 
        self.update_players_button.setText('Update Player Data') 
        # Updates both the generic data and composite scores of the players in the database 
        # Lambda functions used so parameters can be passed 
        self.update_players_button.clicked.connect(lambda: utils.update_player_table(self.fpl.db_connection, self.fpl.session)) 
        self.update_players_button.clicked.connect(lambda: utils.update_composite_scores(self.fpl.db_connection)) 

        ### All of the following buttons use lambda functions to open the window their name corresponds with 
        # MainWindow needs no functions of its own as the functionality occurs in the windows it allows you to open
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
        self.exit_button.clicked.connect(lambda: self.open_window(6)) 
        self.exit_button.setText('Exit')  

class LineupWindow(WindowParent): 
    def __init__(self, previous_window, fpl): 
        super().__init__(previous_window, fpl) 
        self.window_id = 2   
        # Sets the column headers for the list view of the lineup 
        self.column_headers = ['Name', 'Team', 'Position', 'Price', 'Total Points', 'PPG'] 
        # Gets the current user picks in JSON format   
        picks_json = self.fpl.get_current_user_picks() 
        # Turns the picks in JSON format into an array of player objects  
        picks = [utils.create_player_object(fpl.db_connection, x['element']) for x in picks_json] 
        # Finds the sell cost of each player in the lineup (this is the price that will be shown)    
        for index, x in enumerate(picks): 
            x.sell_cost = picks_json[index]['selling_price']/10  
        # The starting eleven is the first 11 players in the array 
        self.starting_eleven = picks[:11] 
        # The bench is the last 4 players in the array (array is 15 long) 
        self.bench = picks[11:]   
        # Finds the current balance of the user 
        self.user_balance = self.fpl.get_current_user_balance() 
        self.setup_ui()  
        self.apply_colours(self)      
        # Creates a list of all of the players in the FPL database 
        players = self.fpl.get_all_players()      
        # Creates the optimium team for the next gameweek 
        self.free_hit = self.generate_free_hit(players)  
        # Seperates the starting 11 and the bench of the above optimal team 
        self.free_hit_starters, self.free_hit_bench = self.seperate_lineup(self.free_hit) 
        # Makes it so the list view is what appears when the window is loaded   
        self.stacked_layout.setCurrentWidget(self.list_widget) 
    
    def generate_free_hit(self, players):  
        # The budget for the free hit is the sell cost of all the players in the user's team + their remaining bank balance 
        budget = sum([player.sell_cost for player in self.starting_eleven]) + sum([player.sell_cost for player in self.bench]) + self.user_balance   
        # Is a parameter of generate_team, determines how strong the bench should be 
        bench_importance = 0.1  
        # So it should judge by composite score instead of composite_score3 
        chip_type = 'free_hit'  
        # Because `base.ChipOptimiser.generate_team()` returns the players sorted by which team they are in and THEN position...
        # ... There is no need to format this data further 
        return base.ChipOptimiser.generate_team(players, budget, bench_importance, chip_type) 
    
    ### Unused ###
    # For later development 
    def generate_wildcard(self, players): 
        budget = sum([player.sell_cost for player in self.starting_eleven]) + sum([player.sell_cost for player in self.bench]) + self.user_balance   
        bench_importance = 0.3
        chip_type = 'wildcard' 
        return base.ChipOptimiser.generate_team(players, budget, bench_importance, chip_type)   
    
    def seperate_lineup(self, arr): 
        # Seperates the lineup into the starting 11 and the bench players 
        return arr[:11], arr[11:]     

    def setup_ui(self): 
        # Sets the size of the window to 1000x1000 (cannot be changed) 
        self.setFixedSize(1000, 1000)  

        ### Unused ### 
        self.formation_button = CustomButton(self) 
        self.formation_button.setGeometry(QtCore.QRect(290, 10, 100, 40)) 
        self.formation_button.colour = 1 
        self.formation_button.setFont(QFont(self.settings.font, 8)) 
        self.formation_button.setText('Formation View')   
        # Switches between list view and formation view  
        self.formation_button.clicked.connect(self.toggle)  

        self.list_button = CustomButton(self) 
        self.list_button.setGeometry(QtCore.QRect(400, 10, 100, 40)) 
        self.list_button.colour = 1 
        self.list_button.setFont(QFont(self.settings.font, 8)) 
        self.list_button.setText('List View')   
        # Switches from formation view to list view 
        self.list_button.clicked.connect(self.toggle)    

        self.back_button = CustomButton(self) 
        self.back_button.setGeometry(QtCore.QRect(10, 10, 100, 40)) 
        self.back_button.colour = 1 
        self.back_button.setFont(QFont(self.settings.font, 8)) 
        self.back_button.setText('Back')  
        # Opens the previous window 
        self.back_button.clicked.connect(self.back_window)   

        self.my_team_button = CustomButton(self) 
        self.my_team_button.setGeometry(QtCore.QRect(10, 800, 100, 40)) 
        self.my_team_button.colour = 1 
        self.my_team_button.setFont(QFont(self.settings.font, 8)) 
        self.my_team_button.setText('My Team')  
        # Changes the current team displayed in the window to the user's team
        # Lambda functions used so that parameters can be used 
        self.my_team_button.clicked.connect(lambda: self.change_starting_eleven_list(self.starting_eleven)) 
        self.my_team_button.clicked.connect(lambda: self.change_bench_list(self.bench)) 

        self.free_hit_button = CustomButton(self) 
        self.free_hit_button.setGeometry(QtCore.QRect(150, 800, 100, 40)) 
        self.free_hit_button.colour = 1 
        self.free_hit_button.setFont(QFont(self.settings.font, 8)) 
        self.free_hit_button.setText('Free Hit')  
        # Changes the current team displayed to the optimal team for the next gameweek  
        # Lambda functions used so taht parameters can be used 
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
        # Opens the transfer window 
        self.transfer_button.clicked.connect(self.open_transfer_window) 

        self.main_widget = QtWidgets.QWidget(self) 
        self.main_widget.setGeometry(QtCore.QRect(0, 50, 630, 750)) 

        self.formation_widget = QtWidgets.QWidget(self) 
        ### Unused ### 
        self.formation_widget.setLayout(self.setup_formation_view()) 

        self.list_widget = QtWidgets.QWidget(self)  
        # Sets up the list view of the main widget  
        self.list_widget.setLayout(self.setup_list_view())  

        self.stacked_layout = QStackedLayout(self)  
        self.stacked_layout.addWidget(self.formation_widget) 
        self.stacked_layout.addWidget(self.list_widget)  

        self.main_widget.setLayout(self.stacked_layout)  
    
    def open_transfer_window(self): 
        self.new_window = TransferWindow(self.window_id, self.fpl, self.starting_eleven+self.bench, self.fpl.get_all_players(), self.user_balance) 
        self.new_window.show() 
    
    def toggle(self):  
        # If the button clicked was self.formation button or there was no sender () 
        # There would be no sender if it was called in the __init__() function 
        if self.sender() == self.formation_button or self.sender() == None:  
            self.formation_button.setStyleSheet('background-color: rgb(0, 255, 0);')  
            self.apply_colour(self.list_button)  
            # Changes the display to the formation display 
            self.stacked_layout.setCurrentWidget(self.formation_widget) 
        else: 
            self.list_button.setStyleSheet('background-color: rgb(0, 255, 0);')  
            self.apply_colour(self.formation_button)  
            # Changes the display to the list display 
            self.stacked_layout.setCurrentWidget(self.list_widget) 

    def setup_list_view(self):  
        layout = QVBoxLayout() 
        self.starting_eleven_table = QtWidgets.QTableWidget(self) 
        self.starting_eleven_table.colour = 1 
        self.starting_eleven_table.setFont(QFont(self.settings.font, 8))  
        # Sets the column count to how many metrics are shown 
        self.starting_eleven_table.setColumnCount(6) 
        # Sets the row count to the number of players in the starting 11 
        self.starting_eleven_table.setRowCount(11)  
        # The column headers correspond to the data that is presented about players 
        self.starting_eleven_table.setHorizontalHeaderLabels(self.column_headers)   

        self.bench_table = QtWidgets.QTableWidget(self)  
        self.bench_table.colour = 1 
        self.bench_table.setFont(QFont(self.settings.font, 8)) 
        # Sets the column count to how many metrics are shown 
        self.bench_table.setColumnCount(6)  
        # Sets the row count to the number of players on the bench 
        self.bench_table.setRowCount(4)  
        # The column headers correspond to the data that is presented about players 
        self.bench_table.setHorizontalHeaderLabels(self.column_headers)   

        layout.addWidget(self.starting_eleven_table)
        layout.addWidget(self.bench_table)  
        # Returns the layout so that it can be used by `list_widget` 
        return layout  

    def change_starting_eleven_list(self, players): 
        # Clears the contents of the player table to remove the previous team shown 
        self.starting_eleven_table.clearContents()  
        # Iterates through the players in the starting 11 
        for index, player in enumerate(players): 
            # Assigns every cell in the row to the information on the player corresponding to the header of the column 
            self.starting_eleven_table.setItem(index, 0, QtWidgets.QTableWidgetItem(player.name)) 
            self.starting_eleven_table.setItem(index, 1, QtWidgets.QTableWidgetItem(str(utils.convert_team(player.team)))) 
            self.starting_eleven_table.setItem(index, 2, QtWidgets.QTableWidgetItem(str(utils.convert_position(player.position)))) 
            self.starting_eleven_table.setItem(index, 3, QtWidgets.QTableWidgetItem(str(player.cost))) 
            self.starting_eleven_table.setItem(index, 4, QtWidgets.QTableWidgetItem(str(player.total_points))) 
            self.starting_eleven_table.setItem(index, 5, QtWidgets.QTableWidgetItem(str(player.ppg)))  
    
    def change_bench_list(self, players): 
        # Clears the contents of the player table to remove the previous team shown 
        self.bench_table.clearContents()  
        # Iterates through the players in the bench 
        for index, player in enumerate(players):  
            # Assigns every cell in the row to the information on the player corresponding to the header of the column 
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
        # Retrieves all the FPl leagues the user currently participates in
        self.leagues = self.fpl.get_current_user_leagues() 
        self.setup_ui() 
        self.apply_colours(self) 
    
    def setup_ui(self): 
        self.setFixedSize(1000, 1000) 

        self.league_chooser = QComboBox(self)  
        self.league_chooser.setGeometry(QtCore.QRect(800, 0, 200, 50))  
        self.league_chooser.colour = 1  
        # Iterates through the leagues that the user is in 
        for x in self.fpl.get_current_user_leagues():   
            # Add the name of the league to the combo box 
            self.league_chooser.addItem(x['name'])  

        self.view_league_button = CustomButton(self)   
        self.view_league_button.setGeometry(QtCore.QRect(800, 50, 200, 50))   
        self.view_league_button.colour = 1  
        self.view_league_button.setFont(QFont(self.settings.font, 8))
        self.view_league_button.setText('View League')   
        # Makes the standings of the league that is on top of the combo box visible 
        self.view_league_button.clicked.connect(self.view_league)  

        self.back_button = CustomButton(self) 
        self.back_button.setGeometry(QtCore.QRect(0, 0, 100, 50)) 
        self.back_button.colour = 1 
        self.back_button.setFont(QFont(self.settings.font, 8)) 
        self.back_button.setText('Back')  
        # Opens the previous window 
        self.back_button.clicked.connect(self.back_window) 

        self.league_table = QtWidgets.QTableWidget(self) 
        self.league_table.setGeometry(QtCore.QRect(0, 100, 1000, 900))  
        self.league_table.colour = 1 
        self.league_table.setFont(QFont(self.settings.font, 8)) 
        self.league_table.setColumnCount(5)  
        # Sets the name of the columns 
        self.league_table.setHorizontalHeaderLabels(['Rank', 'Name', 'Team Name', 'Gameweek Points', 'Total Points'])  
    
    def view_league(self):   
        # Clears the contents of the league table 
        # Incase there was a league being viewed before this one 
        self.league_table.clearContents()  
        # The league being displayed is the league on top of the combo box 
        league = self.league_chooser.currentText()  
        # Iterates through the users leagues 
        # Retrieves the id of the league with the same name as the one on top of the combo box 
        league_id = [x for x in self.leagues if x['name'] == league][0]['id']  
        # Retrieves the standings of the league with the league id found above 
        standings = self.fpl.get_league_standings(league_id)    
        # Sets the row count to the number of players on the first page of the league 
        self.league_table.setRowCount(len(standings))    
        # Iterates through the users in the standings of the league 
        # Sets the cells in the table equal to the information on each user (row by row) 
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
        # Allows for the sorting of objects by different attributes 
        # '-' indicates makes it so that it is being sorted in reverse order 
        # e.g. higher composite score is better so the highest composite score should be first in the array  
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
        # Generates an array of player objects representing all players in FPL 
        self.raw_players = self.fpl.get_all_players()  
        self.setup_ui() 
        self.apply_colours(self)        
    
    def sort_by(self, players, value):  
        # utilises the sort_switcher to sort players by certain metrics  
        players = utils.merge_sort(players, key=self.sort_switcher[value]) 
        return players  

    def add_players_to_table(self, value=0):  
        # Clears the contents of the player table 
        self.player_table.clearContents()  
        # Sorts the players by the metric 'value' with the default being player.id
        players = self.sort_by(self.raw_players, value)  
        # Sets the number of rows as the number of players 
        self.player_table.setRowCount(len(players))    
        # Iterates through the list of players 
        # Enumerate so index can be used to set the row 
        # Sets the items in the row to the attributes of the player object 
        # Converts integer values like team and position to their string counterparts 
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
        # Combo box contains all the attributes that users can sort the players by 
        self.sort_by_box.addItems(['ID', 'Name', 'Cost', 'Total Points', 'Position', 'Team', 'PPG', 'Owned by', 'Composite Score']) 
        # Adds the players to the players table when the combo box is changed
        # Sorted by whatever is currently in the combo box  
        self.sort_by_box.currentIndexChanged.connect(self.add_players_to_table)  

        self.back_button = CustomButton(self) 
        self.back_button.setGeometry(QtCore.QRect(230, 150, 200, 50)) 
        self.back_button.colour = 1 
        self.back_button.setFont(QFont(self.settings.font, 8)) 
        self.back_button.setText('Back')  
        # Opens the previous window 
        self.back_button.clicked.connect(self.back_window) 

        self.player_table = QtWidgets.QTableWidget(self) 
        self.player_table.setGeometry(QtCore.QRect(0, 200, 1000, 750)) 
        self.player_table.colour = 1 
        self.player_table.setFont(QFont(self.settings.font, 8))  
        # Sets the number of columns (corresponds to number of pieces of data on the player) 
        self.player_table.setColumnCount(9)         
        # Hides the vertical header (aesthetic choice)  
        self.player_table.verticalHeader().hide()  
        # Makes it so that the values inside the player table cannot be edited 
        self.player_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers) 
        # Sets the labels for the columns as the corresponding metrics 
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
        # Populates the player table 
        # On startup of the window the players will always be sorted by id 
        # Because id is what the combo box starts on and there is no parameter passed here (default for `value` is 0) 
        # (Check `sort_switcher` to understand above line) 
        self.add_players_to_table() 


class SettingsWindow(WindowParent): 
    def __init__(self, previous_window, fpl): 
        super().__init__(previous_window, fpl) 
        self.window_id = 5 
        # Changed settings will be stored in here 
        # When the settings are applied this will be used to change settings.json and the `Settings` object 
        self.settings_dict = {}   
        self.setup_ui() 
        self.apply_colours(self)  
    
    def settings_window_refresh(self):  
        # Checks if `main_widget` exists 
        # If `main_widget` exists then this is not the first instance of `SettingsWindow` 
        # Meaning `main_widget` has to be deleted to refresh the window (otherwise there will be a crash) 
        if self.main_widget is not None: 
            # Deletes `main_widget` 
            self.main_widget.deleteLater() 
        # Refreshes the window as normal  
        self.close() 
        self.open_window(5) 

    def volume_value_changed(self, value): 
        # Changes the volume in response to the volume slider/volume entry 
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
        # Opens a colour dialog box which lets the user change colour 
        # Has the input 'primary_colour' as this is the colour that will change from this button
        self.colour_widget.primary_button.clicked.connect(lambda: self.open_colour_window('primary_colour'))  
        
        self.colour_widget.secondary_button = QPushButton(self.colour_widget) 
        self.colour_widget.secondary_button.setGeometry(QtCore.QRect(125, 50, 100, 40)) 
        self.colour_widget.secondary_button.colour = 1 
        self.colour_widget.secondary_button.setFont(QFont(self.settings.font, 8)) 
        self.colour_widget.secondary_button.setText('Secondary Colour')  
        # Opens a colour dialog box which lets users select a colour 
        # Has the input 'secondary_colour' as this is the colour that will change from this button 
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
        # Opens a font dialog box which lets users select a font 
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
        # The value of the slider when the widget is shown is set to the current button volume 
        self.sound_widget.slider.setValue(self.settings.button_volume)  
        # When the slider value is changed it changes the value of the entry also 
        self.sound_widget.slider.valueChanged.connect(self.volume_value_changed) 

        self.sound_widget.volume_entry = QtWidgets.QLineEdit(self.sound_widget) 
        self.sound_widget.volume_entry.setGeometry(QtCore.QRect(250, 50, 100, 40)) 
        self.sound_widget.volume_entry.colour = 1 
        self.sound_widget.volume_entry.setFont(QFont(self.settings.font, 8)) 
        # Sets the value of the entry to the current button volume 
        self.sound_widget.volume_entry.setText(str(self.settings.button_volume))  

        self.sound_widget.sound_box = QtWidgets.QComboBox(self.sound_widget) 
        self.sound_widget.sound_box.setGeometry(QtCore.QRect(0, 100, 200, 40)) 
        self.sound_widget.sound_box.colour = 1 
        self.sound_widget.sound_box.setFont(QFont(self.settings.font, 8))  
        # Adds the names of the .wav files in the 'sounds' local folder to the combo box 
        self.sound_widget.sound_box.addItems([x for x in os.listdir(os.path.join(os.getcwd(), 'sounds')) if x.endswith('.wav')]) 

    def open_colour_settings(self):  
        self.stacked_layout.setCurrentWidget(self.colour_widget) 

    def open_font_settings(self):  
        self.stacked_layout.setCurrentWidget(self.font_widget)  

    def open_sound_settings(self):  
        self.stacked_layout.setCurrentWidget(self.sound_widget) 

    def open_colour_window(self, section): 
        # Opens colour dialog box 
        colour = QColorDialog.getColor() 
        # Converts the rgb values of the colour provided by user interaction with the dialog... 
        # ... box into an array formatted as [R, G, B] 
        rgb_list = [colour.red(), colour.green(), colour.blue()] 
        # Checks that the colour is valid (each value in the range 0-255) 
        if colour.isValid():  
            # Converts the RGB list into a string so it can be interpreted by Qt 
            rgb_string = utils.rgb_to_string(rgb_list)  
            # Adds the section (primary or secondary) and rgb in string form to settings 
            # The inputs provided will correspond exactly to the name of the setting in settings.json 
            self.add_to_settings(section, rgb_string) 

    def open_font_window(self): 
        # The first value font is the font provided by user interaction with the dialog box 
        # The second value verifies that the font is valid 
        font, ok = QFontDialog.getFont() 
        # If the font provided is valid 
        if ok:  
            # Adds the font to settings 
            self.settings_dict['font'] = font.family()  

    def add_to_settings(self, key, value): 
        self.settings_dict[key] = value 

    def apply_settings(self): 
        self.settings.change_settings(self.settings_dict) 
        self.settings_window_refresh() 
    
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
        # Opens the previous window (MainWindow) 
        self.back_button.clicked.connect(self.back_window)  

        self.apply_button = CustomButton(self) 
        self.apply_button.setGeometry(460, 520, 100, 40) 
        self.apply_button.colour = 1 
        self.apply_button.setFont(QFont(self.settings.font, 8)) 
        self.apply_button.setText('Apply') 
        # Applies the settings currently in `settings_dict` 
        self.apply_button.clicked.connect(self.apply_settings) 

        self.colour_button = CustomButton(self) 
        self.colour_button.setGeometry(QtCore.QRect(0, 150, 150, 40)) 
        self.colour_button.colour = 1 
        self.colour_button.setFont(QFont(self.settings.font, 8)) 
        self.colour_button.setText('Colour')   
        # Sets the current widget as `colour_widget`
        self.colour_button.clicked.connect(self.open_colour_settings) 

        self.font_button = CustomButton(self) 
        self.font_button.setGeometry(QtCore.QRect(0, 190, 150, 40)) 
        self.font_button.colour = 1 
        self.font_button.setFont(QFont(self.settings.font, 8))  
        self.font_button.setText('Font')   
        # Sets the current widget as `font_widget` 
        self.font_button.clicked.connect(self.open_font_settings)    

        self.sound_button = CustomButton(self) 
        self.sound_button.setGeometry(QtCore.QRect(0, 230, 150, 40)) 
        self.sound_button.colour = 1 
        self.sound_button.setFont(QFont(self.settings.font, 8)) 
        self.sound_button.setText('Button Sound')  
        # Sets the current widget as `sound_widget` 
        self.sound_button.clicked.connect(self.open_sound_settings)  

        self.main_widget = QWidget(self) 
        self.main_widget.setGeometry(QtCore.QRect(200, 150, 350, 350))    

        # Creates the colour widget and populates it 
        self.colour_widget = QWidget(self.main_widget) 
        self.colour_widget.setFixedSize(350, 350) 
        self.fill_colour_widget() 

        # Creates the font widget and populates it 
        self.font_widget = QWidget(self.main_widget) 
        self.font_widget.setFixedSize(350, 350)  
        self.fill_font_widget() 

        # Creates the sound widget and populates it 
        self.sound_widget = QWidget(self.main_widget) 
        self.sound_widget.setFixedSize(350, 350)  
        self.fill_sound_widget() 

        # Adds the relevant settigns widgets to the stacked layout 
        self.stacked_layout = QStackedLayout(self)   
        self.stacked_layout.addWidget(QWidget())  
        self.stacked_layout.addWidget(self.colour_widget)  
        self.stacked_layout.addWidget(self.font_widget)
        self.stacked_layout.addWidget(self.sound_widget)  
        # Sets the stacked layout as the layout of `main_widget` 
        # The starting widget is `QWidget()` which is an empty widget... 
        # ...as nothing has been pressed yet on window startup 
        self.main_widget.setLayout(self.stacked_layout)     


class TransferWindow(WindowParent): 
    def __init__(self, previous_window, fpl, user_team, players, budget): 
        super().__init__(previous_window, fpl) 
        self.window_id = 7 
        # Uses an instance of the class as `base.TransferOptimiser` has no class methods 
        optimiser = base.TransferOptimiser()  
        # Generates transfers based on the users team, available players and the users spare budget 
        self.transfers = optimiser.generate_transfers(user_team, players, budget) 
        self.setup_ui() 
        self.apply_colours(self) 
    
    def setup_ui(self): 
        self.setFixedSize(500, 500) 
        self.transfer_label = QtWidgets.QLabel(self) 
        self.transfer_label.setGeometry(QtCore.QRect(0, 0, 500, 50)) 
        self.transfer_label.setText("Transfer Recommendations:") 
        self.transfer_label.colour = 0 
        self.transfer_label.setFont(QFont(self.settings.font, 20)) 

        self.main_widget = QtWidgets.QWidget(self) 
        self.main_widget.setGeometry(QtCore.QRect(0, 50, 500, 500)) 
        self.main_widget.setLayout(self.setup_list_view()) 

    def setup_list_view(self):  
        layout = QVBoxLayout() 
        self.transfer_table = QtWidgets.QTableWidget(self)
        self.transfer_table.colour = 1 
        self.transfer_table.setFont(QFont(self.settings.font, 8))    
        # Sets the amount of columns 
        # Two columns because an indiviudal transfer only involves two players 
        self.transfer_table.setColumnCount(2) 
        # Sets the row count 
        # Ten rows as this is the number of transfers to be recommended (top 10 most recommended)   
        self.transfer_table.setRowCount(10) 
        # Sets the column headers 
        # Players on the left is to be transferred out 
        # Player on the right is to be transferred in 
        self.transfer_table.setHorizontalHeaderLabels(['Transfer Out', 'Transfer In'])   
        # Iterates through the 2-D array of transfers 
        # Remembering that the transfers are represented as [x, y] 
        # x is the player transferred out and y is the player transferred in  
        for index, x in enumerate(self.transfers):  
            self.transfer_table.setItem(index, 0, QtWidgets.QTableWidgetItem(x[0].name)) 
            self.transfer_table.setItem(index, 1, QtWidgets.QTableWidgetItem(x[1].name)) 

        # Adds the transfer table to the layout 
        layout.addWidget(self.transfer_table) 
        # Returns the layout which will populate `main_widget`  
        return layout 

class ExitWindow(WindowParent): 
    def __init__(self, previous_window, fpl): 
        super().__init__(previous_window, fpl) 
        self.window_id = 6  
        self.setup_ui() 
        self.apply_colours(self) 
    
    def setup_ui(self):  
        self.setFixedSize(100, 150) 
        self.exit_button = CustomButton(self)  
        self.exit_button.setGeometry(0, 50, 50, 50) 
        self.exit_button.colour = 1 
        self.exit_button.setText('Exit') 
        self.exit_button.setFont(QFont(self.settings.font, 8))   
        # Makes the exit button kill the program when pressed 
        self.exit_button.clicked.connect(sys.exit) 

        self.cancel_button = CustomButton(self) 
        self.cancel_button.setGeometry(50, 50, 50, 50) 
        self.cancel_button.colour = 1 
        self.cancel_button.setText('Cancel') 
        self.cancel_button.setFont(QFont(self.settings.font, 8)) 
        # Makes the cancel button close the window when pressed 
        # This just makes it return to the previous window (which was never closed) 
        # The window was never closed due to the seleciton statement present in `WindowParent.open_window'... 
        # ...(If the window_id is 6 (ExitWindow, then do not close then the current window is not closed) 
        self.cancel_button.clicked.connect(self.close) 


if __name__ == '__main__': 
    app = QtWidgets.QApplication(sys.argv)  
    window = LoginWindow() 
    window.show()  
    sys.exit(app.exec()) 
