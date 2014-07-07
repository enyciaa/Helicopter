'''
ADDED
-Added scores
-Made back background scroll
-Obstacle sizing changed to percentages
-Made tunnel percentages
-Added delta time
-Made velocitys related to screen size/resoloution

TODO
-Refactor
-A 'You crashed pop up' to prevent quick restarting
-Work out how best to do delta time
-Work out best way to make movement based on screen size
-Add texture to walls
-Alter how tunnel collisions/new obstacle position is calculated

'''

import kivy
kivy.require('1.8.0')

#if this line is removed theres a'Fatal Python error: (pygame parachute) Segmentation Fault'
#Yet window isn't used in the main file?
from kivy.core.window import Window

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.properties import ListProperty, NumericProperty, \
	ObjectProperty, BooleanProperty, ReferenceListProperty
from kivy.vector import Vector
from kivy.uix.popup import Popup
from kivy.modules import inspector
from random import randrange
import random

class StartPopUp(Popup):
    app = ObjectProperty(None)
    
    'Popup size'
    popup_size = ListProperty([.2, .2])
           
    def start_click(self):
        self.app.game.start_game() 
        
class Score(Widget):
    game = ObjectProperty(None)
    
    'adjust to increase or decrease score'
    score_add = NumericProperty(0.25)
    
    score = NumericProperty(0)
    score_display = NumericProperty(0)
    high_score = NumericProperty(0)
    
    def start(self):
        self.score = 0
        
    def update(self):
        if self.game.game_state:
            score_adj = self.score_add * self.game.app.fps_adj_factor
            self.score += score_adj
            self.score_display = int(round(self.score, 0))
    
    def new_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score_display
        
class Background(Widget):
    game = ObjectProperty(None)
    
    'Speed of scrolling'
    back_scroll_factor = NumericProperty(0.0000008)
    mid_scroll_factor = NumericProperty(0.0000016)
    'Background Image'
    texture_back = CoreImage('Images/Sky_back_layer.png').texture
    texture_back.wrap = 'repeat'
    'Middleground Image'
    texture_mid = CoreImage('Images/background.png').texture
    texture_mid.wrap = 'repeat'
    
    back_scroll_speed = NumericProperty(0)
    mid_scroll_speed = NumericProperty(0)
    back_position = NumericProperty(0)
    mid_position = NumericProperty(0)
    texture_coords_back = ListProperty([-0.0, 0.0, -1.0, 0.0, -1.0, -1.0, -0.0, -1.0])   #initial co-ordinates of background
    texture_coords_mid = ListProperty([-0.0, 0.0, -1.0, 0.0, -1.0, -1.0, -0.0, -1.0])    #-1 as its repeating
    
    def start(self):
        self.back_scroll_speed = self.game.width * self.back_scroll_factor
        self.mid_scroll_speed = self.game.width * self.mid_scroll_factor
        self.back_position = 0
        self.mid_position = 0
    
    def scroll_back(self):
        back_scroll_speed = self.back_scroll_speed * self.game.app.fps_adj_factor
        self.back_position += back_scroll_speed
        a = -(self.back_position)
        b = 0
        c = -(self.back_position + 1)
        d = 0
        e = -(self.back_position + 1)
        f = -1
        g = -(self.back_position)
        h = -1
        self.texture_coords_back = (a, b, c, d, e, f, g, h)  
        
    def scroll_mid(self):    
        mid_scroll_speed = self.mid_scroll_speed * self.game.app.fps_adj_factor
        self.mid_position += mid_scroll_speed
        a = -(self.mid_position)
        b = 0
        c = -(self.mid_position + 1)
        d = 0
        e = -(self.mid_position + 1)
        f = -1
        g = -(self.mid_position)
        h = -1
        self.texture_coords_mid = (a, b, c, d, e, f, g, h) 
            
    def scroll_background(self):
        self.scroll_back()  
        self.scroll_mid()   

class Tunnel(Widget):
    game = ObjectProperty(None)
    
    'gap between top and bottom terrain'
    gap_factor = NumericProperty(0.7)
    'tunnel speed needs to be the same as obstacle speed'
    velocity_factor = NumericProperty(0.005)
    'the speed at which the gap gets smaller'
    gap_change = NumericProperty(0.05)
    'the gradient between vertices'
    gradient_factor = NumericProperty(0.03)
    'number of vertices'
    num_vertices = NumericProperty(20)
    
    #Lists for mesh points
    vertices_top = ListProperty([])
    indices_top = ListProperty([])
    vertices_bot = ListProperty([])
    indices_bot = ListProperty([])
    
    velocity = NumericProperty(0)
    start_thickness = NumericProperty(0)
    gradient = NumericProperty(0)
    min_gap = NumericProperty(0)
    vertice_left_x = NumericProperty(0)
    vertice_right_x = NumericProperty(0)
    gap = NumericProperty(0)
    new_bot_y = NumericProperty(0)
    indice = 0
    
    def start(self, *args):
        #Platform scaling calculations
        self.velocity = self.game.width * self.velocity_factor
        self.gap = self.game.height * self.gap_factor
        self.min_gap = self.game.helicopter.height*2 + self.game.app.obstacle_height
        self.vertice_left_x = int(0 - (self.game.width * 0.1))
        self.vertice_right_x = int(self.game.width + (self.game.width * 0.1))  
        self.vertice_gap = int((self.vertice_right_x - self.vertice_left_x) / self.num_vertices)  
        self.start_thickness = (self.game.height - self.gap) / 2 
        self.gradient = self.game.height * self.gradient_factor 
         
        #Initialise
        self.vertices_bot = [] 
        self.vertices_top = []
        self.indices_bot = [] 
        self.indices_top= []
        self.generate_tunnel()
    
    def generate_tunnel(self):
        #First point
        self.vertices_bot = self.vertice_left_x, 0, 0, 0
        self.indices_bot.append(0)
        self.vertices_top = self.vertice_left_x, self.game.height, 0, 0
        self.indices_top.append(0)
        
        #Middle points
        for x in range(self.vertice_left_x, self.vertice_right_x, self.vertice_gap):
            self.indice = self.indice+1
            y_bot = self.start_thickness
            y_top = self.gap + self.start_thickness
            self.vertices_bot.extend([x, y_bot, 0, 0])
            self.indices_bot.append(self.indice)
            self.vertices_top.extend([x, y_top, 0, 0])
            self.indices_top.append(self.indice)
        
        #Last point    
        self.vertices_bot.extend([self.vertice_right_x, 0, 0, 0])
        self.indices_bot.extend([self.indice+1])   
        self.vertices_top.extend([self.vertice_right_x, self.game.height, 0, 0])
        self.indices_top.extend([self.indice+1]) 
        
        self.indice = 0
    
    def remove(self):  
        if self.vertices_bot[4] < self.vertice_left_x:      #4 is the x co-ordinate of the 2nd vertice
            #add new point
            self.add()    
            #remove points    
            for _ in range(4):            #  _ is used to indicate a variable that doesn't actually get stored (less memory)
                del self.vertices_bot[4]
                del self.vertices_top[4] 
    
    def add(self):  
        new_point = len(self.vertices_bot) - 4    #where new vertice is placed in the list
        
        #bounds of new point
        lower_bound = int(self.vertices_bot[new_point-3] - self.gradient)
        if lower_bound < self.start_thickness:
            lower_bound = int(self.start_thickness)    
        upper_bound = int(self.vertices_bot[new_point-3] + self.gradient)
        top_limit = upper_bound + self.gap
        if top_limit > self.game.height:
            upper_bound = int(self.game.height - self.gap)  
        
        #new vertice and texture points                
        vx = self.vertice_right_x
        self.new_bot_y = randrange(lower_bound, upper_bound, 1)
        vy_top = self.new_bot_y + self.gap
        tx = 0
        ty = 0
        
        #insert new points
        self.vertices_bot.insert(new_point, ty)
        self.vertices_bot.insert(new_point, tx)
        self.vertices_bot.insert(new_point, self.new_bot_y)
        self.vertices_bot.insert(new_point, vx)  
        self.vertices_top.insert(new_point, ty)
        self.vertices_top.insert(new_point, tx)
        self.vertices_top.insert(new_point, vy_top)
        self.vertices_top.insert(new_point, vx)        
        
    def move_tunnel(self):
        list_length = len(self.vertices_bot)
        scroll_speed = self.velocity * self.game.app.fps_adj_factor
        for x in range(4, list_length-4, 4):
            self.vertices_bot[x] = self.vertices_bot[x] - scroll_speed
            self.vertices_top[x] = self.vertices_top[x] - scroll_speed      
                
    def update(self):
        if self.gap > self.min_gap:
            self.gap = self.gap - self.gap_change 
        self.remove()    
        self.move_tunnel()
        
class Obstacle(Widget):
    game = ObjectProperty(None)
    
    'size of obstacle'
    ob_height_factor = NumericProperty(0.15)
    ob_width_factor = NumericProperty(0.09)
    'obstacle speed, needs to be the same as tunnel speed'
    velocity_x_factor = NumericProperty(0.005)
    'distance between obstacles'
    dist_factor = NumericProperty(0.7)
    
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)
    
    distance = NumericProperty(0)
    obstacle_height = NumericProperty(0)
    obstacle_width = NumericProperty(0)
    next_added = BooleanProperty(False)  #Has the next obstacle been addeed?
    
    def __init__(self, **kw):
        super(Obstacle, self).__init__(**kw)
        self.velocity_x = self.game.width * self.velocity_x_factor
        self.distance = self.game.width * self.dist_factor
        self.start_size()
        self.start_position() 
    
    def start_size(self):
        self.obstacle_height = self.game.height * self.ob_height_factor
        self.game.app.obstacle_height = self.obstacle_height
        self.obstacle_width = self.game.width * self.ob_width_factor
        self.size = self.obstacle_width , self.obstacle_height      #Otherwise size is 100,100 (although visibly doesn't look this size
    
    #Runs when an instance of the widget is created
    def start_position(self):
        pos_x = self.game.width  #x-co-ordinate of new obstacle
        #Hacky way to link obstacles to wall
        #better way?
        self.tunnel_top = int(self.game.tunnel.vertices_top[73] - self.obstacle_height/2)  #obstacle can be half way into wall
        self.tunnel_bot = int(self.game.tunnel.vertices_bot[73] - self.obstacle_height/2)
        pos_y = randrange(self.tunnel_bot, self.tunnel_top, 1)  #y-co-ordinate of new obstacle 
        self.pos = pos_x , pos_y

    #Check if obstacle should be added
    def add_check(self):
        screen_right = self.game.width
        current_distance = screen_right - self.pos[0]   #Distance between right hand side of screen and current x co-ordinate of obstacle
        cond1 = current_distance > self.distance
        cond2 = self.next_added == False
        if cond1 and cond2:
            self.game.add_obstacle()
            self.next_added = True
            
    #Check if obstacle should be removed
    def remove_check(self):
        screen_left = 0 - self.obstacle_width  #x-coordinate of left side of screen minus obstacle width
        if self.pos[0] < screen_left:   #0 indicates first position in position list (which is the x_co-ordinate)
            self.game.remove_obstacle()

    def update(self):
        self.add_check()
        self.remove_check() 
        self.pos = Vector(*self.pos) - (Vector(*self.velocity) * self.game.app.fps_adj_factor)    #current position plus velocity
        
class Helicopter(Widget):
    game = ObjectProperty(None)
    
    'Helicopter physics'
    velocity_factor = NumericProperty(0.0008)
    acceleration_factor = NumericProperty(0.0006)
    
    'helicopter size'
    sizing = ListProperty([0.09, 0.12])
    
    start_position = ([])
    
    general_velocity = NumericProperty(1.2)
    general_acceleration = NumericProperty(0.4)
    
    start_x = NumericProperty(0)
    start_y = NumericProperty(0)
    start_position = ReferenceListProperty(start_x, start_y)
    
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    acceleration_x = NumericProperty(0)
    acceleration_y = NumericProperty(0)
    acceleration = ReferenceListProperty(acceleration_x, acceleration_y)

    touched_down = BooleanProperty(False)
    got_start_pos = BooleanProperty(False)
        
    #ensures helicopter isn't moving when game is restarted
    #positions helicopter in start position
    def start(self):
        self.general_velocity = self.game.height * self.velocity_factor
        self.general_acceleration = self.game.height * self.acceleration_factor
        self.velocity_x = 0
        self.velocity_y = 0
        self.acceleration_x = 0
        self.acceleration_y = 0
        #bit of a hacky way to get start position of helicopter for game restart
        #better way?
        if self.got_start_pos == False:
            self.start_position = self.pos
            self.got_start_pos = True
        self.pos = self.start_position              
        
    def on_touch_down(self, touch):
        self.touched_down = True

    def on_touch_up(self, touch):
        self.touched_down = False     
        
    def move(self):
        if self.touched_down:
            self.acceleration = Vector(0,self.acceleration_y + self.general_acceleration)
            self.velocity = Vector(0,self.general_velocity) + Vector(*self.acceleration)
            self.pos = (Vector(*self.velocity) * self.game.app.fps_adj_factor) + self.pos

        else:
            self.acceleration = Vector(0,self.acceleration_y - self.general_acceleration)
            self.velocity = Vector(0,-self.general_velocity) + Vector(*self.acceleration)
            self.pos = (Vector(*self.velocity) * self.game.app.fps_adj_factor) + self.pos
            
    def obstacle_collision(self):
        for obstacle in self.game.obstacles:
            if self.collide_widget(obstacle):
                self.game.end_game()
    
    'very hacky, need to fix'
    def tunnel_collision(self):
        cond1 = (self.height+self.y) > self.game.tunnel.vertices_top[21]
        cond2 = self.y < self.game.tunnel.vertices_bot[21]
        if cond1 or cond2:
            self.game.end_game()
                    
    def alive_check(self):
        self.obstacle_collision()
        self.tunnel_collision()
        
class HelicopterGame(Widget):
    app = ObjectProperty(None)
    helicopter = ObjectProperty(None)
    background = ObjectProperty(None)
    tunnel = ObjectProperty(None)
    score = ObjectProperty(None)
    obstacles = ListProperty([])
    
    'time until first obstacle'
    time_first_ob = NumericProperty(1)   
    game_state = BooleanProperty(False)
    
    #Runs when popup is clicked        
    def start_game(self):
        self.tunnel.start()
        self.score.start()
        self.background.start()
        for obstacle in self.obstacles:
            self.remove_widget(obstacle)
            self.obstacles = self.obstacles[1:] 
        self.helicopter.start()
        self.game_state = True  
        Clock.schedule_once(self.add_obstacle, self.time_first_ob)   #adds obstacle after certain time
    
    #Runs on game start and when conditions are met in Obstacle() thereafter    
    def add_obstacle(self, *args):
        new_obstacle = Obstacle() 
        self.add_widget(new_obstacle)
        self.obstacles = self.obstacles + [new_obstacle]   
    
    #Runs when conditions are met in Obstacle()        
    def remove_obstacle(self):
        self.remove_widget(self.obstacles[0])
        self.obstacles = self.obstacles[1:]    #not sure what this line does, moves next obstacle to start of array?
    
    #Runs when alive_check detects a collision    
    def end_game(self):
        self.game_state = False
        Clock.unschedule(self.add_obstacle)     #unscheduled incase game ends before event fires
        self.helicopter.touched_down = False    #Need this line as the on_touch_up event isn't fired when the helicopter crashes
        self.score.new_high_score()
        self.app.start_popup()     
    
    def update(self, dt):
        if self.game_state:
            self.app.delta_time()
            self.helicopter.alive_check()     
            self.background.scroll_background()
            self.helicopter.move()
            self.tunnel.update() 
            self.score.update() 
            for obstacle in self.obstacles:
                obstacle.update()   

class HelicopterApp(App):
    game = ObjectProperty()
    startpopup = ObjectProperty()

    fps = NumericProperty(60)
    current_fps = NumericProperty(60)
    fps_adj_factor = NumericProperty(1)
    obstacle_height = NumericProperty(0)   #So tunnel minimum gap can be calculated (as obstacle reference is only added after game start)

    def build(self):
        self.game = HelicopterGame()
        self.startpopup = StartPopUp()

        Clock.schedule_once(self.start_popup, 1)
        Clock.schedule_once(self.game.tunnel.start, 1)        
        Clock.schedule_interval(self.game.update, 1/self.fps)
               
        #inspector.create_inspector(Window, self.game)

        return self.game        
    
    def delta_time(self):
        self.current_fps = Clock.get_rfps()
        if self.current_fps == 0:   #to prevent division by zero error
            self.current_fps = 60
        self.fps_adj_factor = self.fps / float(self.current_fps)
    
    def start_popup(self, *args):    
        self.startpopup.open() 

if __name__ == '__main__':
    HelicopterApp().run()

if __name__ == '__main__':
    pass