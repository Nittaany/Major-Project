# # Imports

# import cv2
# import mediapipe as mp
# import pyautogui
# import math
# from enum import IntEnum
# from ctypes import cast, POINTER
# from comtypes import CLSCTX_ALL
# from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
# from google.protobuf.json_format import MessageToDict
# import screen_brightness_control as sbcontrol

# pyautogui.FAILSAFE = False
# mp_drawing = mp.solutions.drawing_utils
# mp_hands = mp.solutions.hands

# # Gesture Encodings 
# class Gest(IntEnum):
#     # Binary Encoded
#     """
#     Enum for mapping all hand gesture to binary number.
#     """

#     FIST = 0
#     PINKY = 1
#     RING = 2
#     MID = 4
#     LAST3 = 7
#     INDEX = 8
#     FIRST2 = 12
#     LAST4 = 15
#     THUMB = 16    
#     PALM = 31
    
#     # Extra Mappings
#     V_GEST = 33
#     TWO_FINGER_CLOSED = 34
#     PINCH_MAJOR = 35
#     PINCH_MINOR = 36

# # Multi-handedness Labels
# class HLabel(IntEnum):
#     MINOR = 0
#     MAJOR = 1

# # Convert Mediapipe Landmarks to recognizable Gestures
# class HandRecog:
#     """
#     Convert Mediapipe Landmarks to recognizable Gestures.
#     """
    
#     def __init__(self, hand_label):
#         """
#         Constructs all the necessary attributes for the HandRecog object.

        # Parameters
        # ----------
        #     finger : int
        #         Represent gesture corresponding to Enum 'Gest',
        #         stores computed gesture for current frame.
        #     ori_gesture : int
        #         Represent gesture corresponding to Enum 'Gest',
        #         stores gesture being used.
#             prev_gesture : int
#                 Represent gesture corresponding to Enum 'Gest',
#                 stores gesture computed for previous frame.
#             frame_count : int
#                 total no. of frames since 'ori_gesture' is updated.
#             hand_result : Object
#                 Landmarks obtained from mediapipe.
#             hand_label : int
#                 Represents multi-handedness corresponding to Enum 'HLabel'.
#         """

#         self.finger = 0
#         self.ori_gesture = Gest.PALM
#         self.prev_gesture = Gest.PALM
#         self.frame_count = 0
#         self.hand_result = None
#         self.hand_label = hand_label
    
#     def update_hand_result(self, hand_result):
#         self.hand_result = hand_result

#     def get_signed_dist(self, point):
#         """
#         returns signed euclidean distance between 'point'.

#         Parameters
#         ----------
#         point : list contaning two elements of type list/tuple which represents 
#             landmark point.
        
#         Returns
#         -------
#         float
#         """
#         sign = -1
#         if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
#             sign = 1
#         dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
#         dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
#         dist = math.sqrt(dist)
#         return dist*sign
    
#     def get_dist(self, point):
#         """
#         returns euclidean distance between 'point'.

#         Parameters
#         ----------
#         point : list contaning two elements of type list/tuple which represents 
#             landmark point.
        
#         Returns
#         -------
#         float
#         """
#         dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
#         dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
#         dist = math.sqrt(dist)
#         return dist
    
#     def get_dz(self,point):
#         """
#         returns absolute difference on z-axis between 'point'.

#         Parameters
#         ----------
#         point : list contaning two elements of type list/tuple which represents 
#             landmark point.
        
#         Returns
#         -------
#         float
#         """
#         return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)
    
#     # Function to find Gesture Encoding using current finger_state.
#     # Finger_state: 1 if finger is open, else 0
#     def set_finger_state(self):
#         """
#         set 'finger' by computing ratio of distance between finger tip 
#         , middle knuckle, base knuckle.

#         Returns
#         -------
#         None
#         """
#         if self.hand_result == None:
#             return

#         points = [[8,5,0],[12,9,0],[16,13,0],[20,17,0]]
#         self.finger = 0
#         self.finger = self.finger | 0 #thumb
#         for idx,point in enumerate(points):
            
#             dist = self.get_signed_dist(point[:2])
#             dist2 = self.get_signed_dist(point[1:])
            
#             try:
#                 ratio = round(dist/dist2,1)
#             except:
#                 ratio = round(dist1/0.01,1)

#             self.finger = self.finger << 1
#             if ratio > 0.5 :
#                 self.finger = self.finger | 1
    

#     # Handling Fluctations due to noise
#     def get_gesture(self):
#         """
#         returns int representing gesture corresponding to Enum 'Gest'.
#         sets 'frame_count', 'ori_gesture', 'prev_gesture', 
#         handles fluctations due to noise.
        
#         Returns
#         -------
#         int
#         """
#         if self.hand_result == None:
#             return Gest.PALM

#         current_gesture = Gest.PALM
#         if self.finger in [Gest.LAST3,Gest.LAST4] and self.get_dist([8,4]) < 0.05:
#             if self.hand_label == HLabel.MINOR :
#                 current_gesture = Gest.PINCH_MINOR
#             else:
#                 current_gesture = Gest.PINCH_MAJOR

#         elif Gest.FIRST2 == self.finger :
#             point = [[8,12],[5,9]]
#             dist1 = self.get_dist(point[0])
#             dist2 = self.get_dist(point[1])
#             ratio = dist1/dist2
#             if ratio > 1.7:
#                 current_gesture = Gest.V_GEST
#             else:
#                 if self.get_dz([8,12]) < 0.1:
#                     current_gesture =  Gest.TWO_FINGER_CLOSED
#                 else:
#                     current_gesture =  Gest.MID
            
#         else:
#             current_gesture =  self.finger
        
#         if current_gesture == self.prev_gesture:
#             self.frame_count += 1
#         else:
#             self.frame_count = 0

#         self.prev_gesture = current_gesture

#         if self.frame_count > 4 :
#             self.ori_gesture = current_gesture
#         return self.ori_gesture

# # Executes commands according to detected gestures
# class Controller:
#     """
#     Executes commands according to detected gestures.

#     Attributes
#     ----------
#     tx_old : int
#         previous mouse location x coordinate
#     ty_old : int
#         previous mouse location y coordinate
#     flag : bool
#         true if V gesture is detected
#     grabflag : bool
#         true if FIST gesture is detected
#     pinchmajorflag : bool
#         true if PINCH gesture is detected through MAJOR hand,
#         on x-axis 'Controller.changesystembrightness', 
#         on y-axis 'Controller.changesystemvolume'.
#     pinchminorflag : bool
#         true if PINCH gesture is detected through MINOR hand,
#         on x-axis 'Controller.scrollHorizontal', 
#         on y-axis 'Controller.scrollVertical'.
#     pinchstartxcoord : int
#         x coordinate of hand landmark when pinch gesture is started.
#     pinchstartycoord : int
#         y coordinate of hand landmark when pinch gesture is started.
#     pinchdirectionflag : bool
#         true if pinch gesture movment is along x-axis,
#         otherwise false
#     prevpinchlv : int
#         stores quantized magnitued of prev pinch gesture displacment, from 
#         starting position
#     pinchlv : int
#         stores quantized magnitued of pinch gesture displacment, from 
#         starting position
#     framecount : int
#         stores no. of frames since 'pinchlv' is updated.
#     prev_hand : tuple
#         stores (x, y) coordinates of hand in previous frame.
#     pinch_threshold : float
#         step size for quantization of 'pinchlv'.
#     """

#     tx_old = 0
#     ty_old = 0
#     trial = True
#     flag = False
#     grabflag = False
#     pinchmajorflag = False
#     pinchminorflag = False
#     pinchstartxcoord = None
#     pinchstartycoord = None
#     pinchdirectionflag = None
#     prevpinchlv = 0
#     pinchlv = 0
#     framecount = 0
#     prev_hand = None
#     pinch_threshold = 0.3
    
#     def getpinchylv(hand_result):
#         """returns distance beween starting pinch y coord and current hand position y coord."""
#         dist = round((Controller.pinchstartycoord - hand_result.landmark[8].y)*10,1)
#         return dist

#     def getpinchxlv(hand_result):
#         """returns distance beween starting pinch x coord and current hand position x coord."""
#         dist = round((hand_result.landmark[8].x - Controller.pinchstartxcoord)*10,1)
#         return dist
    
#     def changesystembrightness():
#         """sets system brightness based on 'Controller.pinchlv'."""
#         currentBrightnessLv = sbcontrol.get_brightness(display=0)/100.0
#         currentBrightnessLv += Controller.pinchlv/50.0
#         if currentBrightnessLv > 1.0:
#             currentBrightnessLv = 1.0
#         elif currentBrightnessLv < 0.0:
#             currentBrightnessLv = 0.0       
#         sbcontrol.fade_brightness(int(100*currentBrightnessLv) , start = sbcontrol.get_brightness(display=0))
    
#     def changesystemvolume():
#         """sets system volume based on 'Controller.pinchlv'."""
#         devices = AudioUtilities.GetSpeakers()
#         interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
#         volume = cast(interface, POINTER(IAudioEndpointVolume))
#         currentVolumeLv = volume.GetMasterVolumeLevelScalar()
#         currentVolumeLv += Controller.pinchlv/50.0
#         if currentVolumeLv > 1.0:
#             currentVolumeLv = 1.0
#         elif currentVolumeLv < 0.0:
#             currentVolumeLv = 0.0
#         volume.SetMasterVolumeLevelScalar(currentVolumeLv, None)
    
#     def scrollVertical():
#         """scrolls on screen vertically."""
#         pyautogui.scroll(120 if Controller.pinchlv>0.0 else -120)
        
    
#     def scrollHorizontal():
#         """scrolls on screen horizontally."""
#         pyautogui.keyDown('shift')
#         pyautogui.keyDown('ctrl')
#         pyautogui.scroll(-120 if Controller.pinchlv>0.0 else 120)
#         pyautogui.keyUp('ctrl')
#         pyautogui.keyUp('shift')

#     # Locate Hand to get Cursor Position
#     # Stabilize cursor by Dampening
#     def get_position(hand_result):
#         """
#         returns coordinates of current hand position.

#         Locates hand to get cursor position also stabilize cursor by 
#         dampening jerky motion of hand.

#         Returns
#         -------
#         tuple(float, float)
#         """
#         point = 9
#         position = [hand_result.landmark[point].x ,hand_result.landmark[point].y]
#         sx,sy = pyautogui.size()
#         x_old,y_old = pyautogui.position()
#         x = int(position[0]*sx)
#         y = int(position[1]*sy)
#         if Controller.prev_hand is None:
#             Controller.prev_hand = x,y
#         delta_x = x - Controller.prev_hand[0]
#         delta_y = y - Controller.prev_hand[1]

#         distsq = delta_x**2 + delta_y**2
#         ratio = 1
#         Controller.prev_hand = [x,y]

#         if distsq <= 25:
#             ratio = 0
#         elif distsq <= 900:
#             ratio = 0.07 * (distsq ** (1/2))
#         else:
#             ratio = 2.1
#         x , y = x_old + delta_x*ratio , y_old + delta_y*ratio
#         return (x,y)

#     def pinch_control_init(hand_result):
#         """Initializes attributes for pinch gesture."""
#         Controller.pinchstartxcoord = hand_result.landmark[8].x
#         Controller.pinchstartycoord = hand_result.landmark[8].y
#         Controller.pinchlv = 0
#         Controller.prevpinchlv = 0
#         Controller.framecount = 0

#     # Hold final position for 5 frames to change status
#     def pinch_control(hand_result, controlHorizontal, controlVertical):
#         """
#         calls 'controlHorizontal' or 'controlVertical' based on pinch flags, 
#         'framecount' and sets 'pinchlv'.

#         Parameters
#         ----------
#         hand_result : Object
#             Landmarks obtained from mediapipe.
#         controlHorizontal : callback function assosiated with horizontal
#             pinch gesture.
#         controlVertical : callback function assosiated with vertical
#             pinch gesture. 
        
#         Returns
#         -------
#         None
#         """
#         if Controller.framecount == 5:
#             Controller.framecount = 0
#             Controller.pinchlv = Controller.prevpinchlv

#             if Controller.pinchdirectionflag == True:
#                 controlHorizontal() #x

#             elif Controller.pinchdirectionflag == False:
#                 controlVertical() #y

#         lvx =  Controller.getpinchxlv(hand_result)
#         lvy =  Controller.getpinchylv(hand_result)
            
#         if abs(lvy) > abs(lvx) and abs(lvy) > Controller.pinch_threshold:
#             Controller.pinchdirectionflag = False
#             if abs(Controller.prevpinchlv - lvy) < Controller.pinch_threshold:
#                 Controller.framecount += 1
#             else:
#                 Controller.prevpinchlv = lvy
#                 Controller.framecount = 0

#         elif abs(lvx) > Controller.pinch_threshold:
#             Controller.pinchdirectionflag = True
#             if abs(Controller.prevpinchlv - lvx) < Controller.pinch_threshold:
#                 Controller.framecount += 1
#             else:
#                 Controller.prevpinchlv = lvx
#                 Controller.framecount = 0

#     def handle_controls(gesture, hand_result):  
#         """Impliments all gesture functionality."""      
#         x,y = None,None
#         if gesture != Gest.PALM :
#             x,y = Controller.get_position(hand_result)
        
#         # flag reset
#         if gesture != Gest.FIST and Controller.grabflag:
#             Controller.grabflag = False
#             pyautogui.mouseUp(button = "left")

#         if gesture != Gest.PINCH_MAJOR and Controller.pinchmajorflag:
#             Controller.pinchmajorflag = False

#         if gesture != Gest.PINCH_MINOR and Controller.pinchminorflag:
#             Controller.pinchminorflag = False

#         # implementation
#         if gesture == Gest.V_GEST:
#             Controller.flag = True
#             pyautogui.moveTo(x, y, duration = 0.1)

#         elif gesture == Gest.FIST:
#             if not Controller.grabflag : 
#                 Controller.grabflag = True
#                 pyautogui.mouseDown(button = "left")
#             pyautogui.moveTo(x, y, duration = 0.1)

#         elif gesture == Gest.MID and Controller.flag:
#             pyautogui.click()
#             Controller.flag = False

#         elif gesture == Gest.INDEX and Controller.flag:
#             pyautogui.click(button='right')
#             Controller.flag = False

#         elif gesture == Gest.TWO_FINGER_CLOSED and Controller.flag:
#             pyautogui.doubleClick()
#             Controller.flag = False

#         elif gesture == Gest.PINCH_MINOR:
#             if Controller.pinchminorflag == False:
#                 Controller.pinch_control_init(hand_result)
#                 Controller.pinchminorflag = True
#             Controller.pinch_control(hand_result,Controller.scrollHorizontal, Controller.scrollVertical)
        
#         elif gesture == Gest.PINCH_MAJOR:
#             if Controller.pinchmajorflag == False:
#                 Controller.pinch_control_init(hand_result)
#                 Controller.pinchmajorflag = True
#             Controller.pinch_control(hand_result,Controller.changesystembrightness, Controller.changesystemvolume)
        
# '''
# ----------------------------------------  Main Class  ----------------------------------------
#     Entry point of Gesture Controller
# '''


# class GestureController:
#     """
#     Handles camera, obtain landmarks from mediapipe, entry point
#     for whole program.

#     Attributes
#     ----------
#     gc_mode : int
#         indicates weather gesture controller is running or not,
#         1 if running, otherwise 0.
#     cap : Object
#         object obtained from cv2, for capturing video frame.
#     CAM_HEIGHT : int
#         highet in pixels of obtained frame from camera.
#     CAM_WIDTH : int
#         width in pixels of obtained frame from camera.
#     hr_major : Object of 'HandRecog'
#         object representing major hand.
#     hr_minor : Object of 'HandRecog'
#         object representing minor hand.
#     dom_hand : bool
#         True if right hand is domaniant hand, otherwise False.
#         default True.
#     """
#     gc_mode = 0
#     cap = None
#     CAM_HEIGHT = None
#     CAM_WIDTH = None
#     hr_major = None # Right Hand by default
#     hr_minor = None # Left hand by default
#     dom_hand = True

#     def __init__(self):
#         """Initilaizes attributes."""
#         GestureController.gc_mode = 1
#         GestureController.cap = cv2.VideoCapture(0)
#         GestureController.CAM_HEIGHT = GestureController.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
#         GestureController.CAM_WIDTH = GestureController.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    
#     def classify_hands(results):
#         """
#         sets 'hr_major', 'hr_minor' based on classification(left, right) of 
#         hand obtained from mediapipe, uses 'dom_hand' to decide major and
#         minor hand.
#         """
#         left , right = None,None
#         try:
#             handedness_dict = MessageToDict(results.multi_handedness[0])
#             if handedness_dict['classification'][0]['label'] == 'Right':
#                 right = results.multi_hand_landmarks[0]
#             else :
#                 left = results.multi_hand_landmarks[0]
#         except:
#             pass

#         try:
#             handedness_dict = MessageToDict(results.multi_handedness[1])
#             if handedness_dict['classification'][0]['label'] == 'Right':
#                 right = results.multi_hand_landmarks[1]
#             else :
#                 left = results.multi_hand_landmarks[1]
#         except:
#             pass
        
#         if GestureController.dom_hand == True:
#             GestureController.hr_major = right
#             GestureController.hr_minor = left
#         else :
#             GestureController.hr_major = left
#             GestureController.hr_minor = right

#     def start(self):
#         """
#         Entry point of whole programm, caputres video frame and passes, obtains
#         landmark from mediapipe and passes it to 'handmajor' and 'handminor' for
#         controlling.
#         """
        
#         handmajor = HandRecog(HLabel.MAJOR)
#         handminor = HandRecog(HLabel.MINOR)

#         with mp_hands.Hands(max_num_hands = 2,min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
#             while GestureController.cap.isOpened() and GestureController.gc_mode:
#                 success, image = GestureController.cap.read()

#                 if not success:
#                     print("Ignoring empty camera frame.")
#                     continue
                
#                 image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
#                 image.flags.writeable = False
#                 results = hands.process(image)
                
#                 image.flags.writeable = True
#                 image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

#                 if results.multi_hand_landmarks:                   
#                     GestureController.classify_hands(results)
#                     handmajor.update_hand_result(GestureController.hr_major)
#                     handminor.update_hand_result(GestureController.hr_minor)

#                     handmajor.set_finger_state()
#                     handminor.set_finger_state()
#                     gest_name = handminor.get_gesture()

#                     if gest_name == Gest.PINCH_MINOR:
#                         Controller.handle_controls(gest_name, handminor.hand_result)
#                     else:
#                         gest_name = handmajor.get_gesture()
#                         Controller.handle_controls(gest_name, handmajor.hand_result)
                    
#                     for hand_landmarks in results.multi_hand_landmarks:
#                         mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
#                 else:
#                     Controller.prev_hand = None
#                 cv2.imshow('Gesture Controller', image)
#                 if cv2.waitKey(5) & 0xFF == 13:
#                     break
#         GestureController.cap.release()
#         cv2.destroyAllWindows()

# # uncomment to run directly
# # gc1 = GestureController()
# # gc1.start()


'''
import cv2
import mediapipe as mp
import pyautogui
import math
import platform
import os
import subprocess
from enum import IntEnum
import screen_brightness_control as sbcontrol

# --- MACOS PATCH: Mock Windows Audio Libraries ---
IS_MACOS = platform.system() == "Darwin"

if not IS_MACOS:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
# -------------------------------------------------

pyautogui.FAILSAFE = False
# SAFETY: Use the safe import for mediapipe solutions
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

class Gest(IntEnum):
    FIST = 0
    PINKY = 1
    RING = 2
    MID = 4
    LAST3 = 7
    INDEX = 8
    FIRST2 = 12
    LAST4 = 15
    THUMB = 16    
    PALM = 31
    V_GEST = 33
    TWO_FINGER_CLOSED = 34
    PINCH_MAJOR = 35
    PINCH_MINOR = 36

class HLabel(IntEnum):
    MINOR = 0
    MAJOR = 1

class HandRecog:
    def __init__(self, hand_label):
        self.finger = 0
        self.ori_gesture = Gest.PALM
        self.prev_gesture = Gest.PALM
        self.frame_count = 0
        self.hand_result = None
        self.hand_label = hand_label
    
    def update_hand_result(self, hand_result):
        self.hand_result = hand_result

    def get_signed_dist(self, point):
        sign = -1
        if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
            sign = 1
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        dist = math.sqrt(dist)
        return dist*sign
    
    def get_dist(self, point):
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        dist = math.sqrt(dist)
        return dist
    
    def get_dz(self,point):
        return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)
    
    def set_finger_state(self):
        if self.hand_result == None:
            return
        points = [[8,5,0],[12,9,0],[16,13,0],[20,17,0]]
        self.finger = 0
        self.finger = self.finger | 0 
        for idx,point in enumerate(points):
            dist = self.get_signed_dist(point[:2])
            dist2 = self.get_signed_dist(point[1:])
            try:
                ratio = round(dist/dist2,1)
            except:
                ratio = round(dist/0.01,1)
            self.finger = self.finger << 1
            if ratio > 0.5 :
                self.finger = self.finger | 1
    
    def get_gesture(self):
        if self.hand_result == None:
            return Gest.PALM
        current_gesture = Gest.PALM
        if self.finger in [Gest.LAST3,Gest.LAST4] and self.get_dist([8,4]) < 0.05:
            if self.hand_label == HLabel.MINOR :
                current_gesture = Gest.PINCH_MINOR
            else:
                current_gesture = Gest.PINCH_MAJOR
        elif Gest.FIRST2 == self.finger :
            point = [[8,12],[5,9]]
            dist1 = self.get_dist(point[0])
            dist2 = self.get_dist(point[1])
            ratio = dist1/dist2
            if ratio > 1.7:
                current_gesture = Gest.V_GEST
            else:
                if self.get_dz([8,12]) < 0.1:
                    current_gesture =  Gest.TWO_FINGER_CLOSED
                else:
                    current_gesture =  Gest.MID
        else:
            current_gesture =  self.finger
        
        if current_gesture == self.prev_gesture:
            self.frame_count += 1
        else:
            self.frame_count = 0
        self.prev_gesture = current_gesture
        if self.frame_count > 4 :
            self.ori_gesture = current_gesture
        return self.ori_gesture

class Controller:
    tx_old = 0
    ty_old = 0
    trial = True
    flag = False
    grabflag = False
    pinchmajorflag = False
    pinchminorflag = False
    pinchstartxcoord = None
    pinchstartycoord = None
    pinchdirectionflag = None
    prevpinchlv = 0
    pinchlv = 0
    framecount = 0
    prev_hand = None
    pinch_threshold = 0.3
    
    def getpinchylv(hand_result):
        dist = round((Controller.pinchstartycoord - hand_result.landmark[8].y)*10,1)
        return dist

    def getpinchxlv(hand_result):
        dist = round((hand_result.landmark[8].x - Controller.pinchstartxcoord)*10,1)
        return dist
    
    def changesystembrightness():
        try:
            current = sbcontrol.get_brightness()
            if isinstance(current, list): current = current[0]
            current = current / 100.0
        except:
            current = 0.5 

        new_level = current + (Controller.pinchlv / 50.0)
        new_level = max(0.0, min(1.0, new_level))
        
        if IS_MACOS:
            os.system(f"brightness {new_level}")
        else:
            sbcontrol.fade_brightness(int(100*new_level))
    
    def changesystemvolume():
        vol_change = Controller.pinchlv / 50.0 
        
        if IS_MACOS:
            try:
                cmd = "osascript -e 'output volume of (get volume settings)'"
                current_vol = int(subprocess.check_output(cmd, shell=True).strip())
                new_vol = int(current_vol + (vol_change * 100))
                new_vol = max(0, min(100, new_vol))
                os.system(f"osascript -e 'set volume output volume {new_vol}'")
            except:
                pass
        else:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            currentVolumeLv = volume.GetMasterVolumeLevelScalar()
            currentVolumeLv += vol_change
            currentVolumeLv = max(0.0, min(1.0, currentVolumeLv))
            volume.SetMasterVolumeLevelScalar(currentVolumeLv, None)
    
    def scrollVertical():
        pyautogui.scroll(10 if Controller.pinchlv>0.0 else -10)
        
    def scrollHorizontal():
        pyautogui.keyDown('shift')
        pyautogui.scroll(10 if Controller.pinchlv>0.0 else -10)
        pyautogui.keyUp('shift')

    def get_position(hand_result):
        point = 9
        position = [hand_result.landmark[point].x ,hand_result.landmark[point].y]
        sx,sy = pyautogui.size()
        x_old,y_old = pyautogui.position()
        x = int(position[0]*sx)
        y = int(position[1]*sy)
        if Controller.prev_hand is None:
            Controller.prev_hand = x,y
        delta_x = x - Controller.prev_hand[0]
        delta_y = y - Controller.prev_hand[1]

        distsq = delta_x**2 + delta_y**2
        ratio = 1
        Controller.prev_hand = [x,y]

        if distsq <= 25:
            ratio = 0
        elif distsq <= 900:
            ratio = 0.07 * (distsq ** (1/2))
        else:
            ratio = 2.1
        x , y = x_old + delta_x*ratio , y_old + delta_y*ratio
        return (x,y)

    def pinch_control_init(hand_result):
        Controller.pinchstartxcoord = hand_result.landmark[8].x
        Controller.pinchstartycoord = hand_result.landmark[8].y
        Controller.pinchlv = 0
        Controller.prevpinchlv = 0
        Controller.framecount = 0

    def pinch_control(hand_result, controlHorizontal, controlVertical):
        if Controller.framecount == 5:
            Controller.framecount = 0
            Controller.pinchlv = Controller.prevpinchlv

            if Controller.pinchdirectionflag == True:
                controlHorizontal()

            elif Controller.pinchdirectionflag == False:
                controlVertical()

        lvx =  Controller.getpinchxlv(hand_result)
        lvy =  Controller.getpinchylv(hand_result)
            
        if abs(lvy) > abs(lvx) and abs(lvy) > Controller.pinch_threshold:
            Controller.pinchdirectionflag = False
            if abs(Controller.prevpinchlv - lvy) < Controller.pinch_threshold:
                Controller.framecount += 1
            else:
                Controller.prevpinchlv = lvy
                Controller.framecount = 0

        elif abs(lvx) > Controller.pinch_threshold:
            Controller.pinchdirectionflag = True
            if abs(Controller.prevpinchlv - lvx) < Controller.pinch_threshold:
                Controller.framecount += 1
            else:
                Controller.prevpinchlv = lvx
                Controller.framecount = 0

    def handle_controls(gesture, hand_result):  
        x,y = None,None
        if gesture != Gest.PALM :
            x,y = Controller.get_position(hand_result)
        
        if gesture != Gest.FIST and Controller.grabflag:
            Controller.grabflag = False
            pyautogui.mouseUp(button = "left")

        if gesture != Gest.PINCH_MAJOR and Controller.pinchmajorflag:
            Controller.pinchmajorflag = False

        if gesture != Gest.PINCH_MINOR and Controller.pinchminorflag:
            Controller.pinchminorflag = False

        if gesture == Gest.V_GEST:
            Controller.flag = True
            pyautogui.moveTo(x, y, duration = 0.1)

        elif gesture == Gest.FIST:
            if not Controller.grabflag : 
                Controller.grabflag = True
                pyautogui.mouseDown(button = "left")
            pyautogui.moveTo(x, y, duration = 0.1)

        elif gesture == Gest.MID and Controller.flag:
            pyautogui.click()
            Controller.flag = False

        elif gesture == Gest.INDEX and Controller.flag:
            pyautogui.click(button='right')
            Controller.flag = False

        elif gesture == Gest.TWO_FINGER_CLOSED and Controller.flag:
            pyautogui.doubleClick()
            Controller.flag = False

        elif gesture == Gest.PINCH_MINOR:
            if Controller.pinchminorflag == False:
                Controller.pinch_control_init(hand_result)
                Controller.pinchminorflag = True
            Controller.pinch_control(hand_result,Controller.scrollHorizontal, Controller.scrollVertical)
        
        elif gesture == Gest.PINCH_MAJOR:
            if Controller.pinchmajorflag == False:
                Controller.pinch_control_init(hand_result)
                Controller.pinchmajorflag = True
            Controller.pinch_control(hand_result,Controller.changesystembrightness, Controller.changesystemvolume)

class GestureController:
    gc_mode = 0
    cap = None
    CAM_HEIGHT = None
    CAM_WIDTH = None
    hr_major = None 
    hr_minor = None 
    dom_hand = True

    def __init__(self):
        print("[DEBUG] Initializing GestureController...")
        GestureController.gc_mode = 1
        
        # --- CAMERA INIT ATTEMPT 1 (Default) ---
        print("[DEBUG] Attempting to open Camera 0...")
        GestureController.cap = cv2.VideoCapture(0)
        
        # --- CAMERA INIT ATTEMPT 2 (Fallback for some Macs) ---
        if not GestureController.cap.isOpened():
             print("[DEBUG] Camera 0 failed. Attempting Camera 1...")
             GestureController.cap = cv2.VideoCapture(1)

        if not GestureController.cap.isOpened():
             print("[CRITICAL ERROR] Could not open ANY camera. Check Permissions!")
             GestureController.gc_mode = 0
             return

        GestureController.CAM_HEIGHT = GestureController.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        GestureController.CAM_WIDTH = GestureController.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        print(f"[DEBUG] Camera Initialized: {int(GestureController.CAM_WIDTH)}x{int(GestureController.CAM_HEIGHT)}")
    
    def classify_hands(results):
        left , right = None,None
        try:
            for idx, hand_handedness in enumerate(results.multi_handedness):
                label = hand_handedness.classification[0].label
                if label == 'Right':
                    right = results.multi_hand_landmarks[idx]
                else:
                    left = results.multi_hand_landmarks[idx]
        except:
            pass
        
        if GestureController.dom_hand == True:
            GestureController.hr_major = right
            GestureController.hr_minor = left
        else :
            GestureController.hr_major = left
            GestureController.hr_minor = right

    def start(self):
        if GestureController.gc_mode == 0:
            print("[DEBUG] GC Mode is 0. Exiting start().")
            return

        print("[DEBUG] Starting Main Loop...")
        handmajor = HandRecog(HLabel.MAJOR)
        handminor = HandRecog(HLabel.MINOR)

        with mp_hands.Hands(max_num_hands = 2,min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
            while GestureController.cap.isOpened() and GestureController.gc_mode:
                
                success, image = GestureController.cap.read()
                if not success:
                    print("[DEBUG] Ignoring empty camera frame.")
                    continue
                
                # print(".", end="", flush=True) # Dot heartbeat
                
                image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = hands.process(image)
                
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                if results.multi_hand_landmarks:                   
                    GestureController.classify_hands(results)
                    handmajor.update_hand_result(GestureController.hr_major)
                    handminor.update_hand_result(GestureController.hr_minor)

                    handmajor.set_finger_state()
                    handminor.set_finger_state()
                    gest_name = handminor.get_gesture()

                    if gest_name == Gest.PINCH_MINOR:
                        Controller.handle_controls(gest_name, handminor.hand_result)
                    else:
                        gest_name = handmajor.get_gesture()
                        Controller.handle_controls(gest_name, handmajor.hand_result)
                    
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                else:
                    Controller.prev_hand = None
                
                cv2.imshow('Gesture Controller', image)
                
                # Check for ENTER key (13) to exit
                if cv2.waitKey(5) & 0xFF == 13:
                    print("\n[DEBUG] Exit key pressed.")
                    break
        
        print("[DEBUG] Releasing camera and closing windows.")
        GestureController.cap.release()
        cv2.destroyAllWindows()

# --- ENTRY POINT (Crucial for testing) ---
if __name__ == "__main__":
    print("[DEBUG] Running Gesture_Controller as main script")
    gc = GestureController()
    gc.start()

    '''


# #!  updated features

# import cv2
# import mediapipe as mp
# import pyautogui
# import math
# import platform
# import os
# import subprocess
# from enum import IntEnum
# import screen_brightness_control as sbcontrol

# # --- MACOS PATCH: Mock Windows Audio Libraries ---
# IS_MACOS = platform.system() == "Darwin"

# if not IS_MACOS:
#     from ctypes import cast, POINTER
#     from comtypes import CLSCTX_ALL
#     from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
# # -------------------------------------------------

# pyautogui.FAILSAFE = False
# mp_drawing = mp.solutions.drawing_utils
# mp_hands = mp.solutions.hands

# class Gest(IntEnum):
#     FIST = 0
#     PINKY = 1
#     RING = 2
#     MID = 4
#     LAST3 = 7
#     INDEX = 8
#     FIRST2 = 12
#     THREE_FINGER = 14 # Index + Mid + Ring
#     LAST4 = 15
#     THUMB = 16    
#     PALM = 31
    
#     # Complex Gestures
#     V_GEST = 33
#     TWO_FINGER_CLOSED = 34
#     PINCH_MAJOR = 35
#     PINCH_MINOR = 36

# class HLabel(IntEnum):
#     MINOR = 0
#     MAJOR = 1

# class HandRecog:
#     def __init__(self, hand_label):
#         self.finger = 0
#         self.ori_gesture = Gest.PALM
#         self.prev_gesture = Gest.PALM
#         self.frame_count = 0
#         self.hand_result = None
#         self.hand_label = hand_label
    
#     def update_hand_result(self, hand_result):
#         self.hand_result = hand_result

#     def get_signed_dist(self, point):
#         sign = -1
#         if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
#             sign = 1
#         dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
#         dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
#         dist = math.sqrt(dist)
#         return dist*sign
    
#     def get_dist(self, point):
#         dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
#         dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
#         dist = math.sqrt(dist)
#         return dist
    
#     def get_dz(self,point):
#         return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)
    
#     def set_finger_state(self):
#         if self.hand_result == None:
#             return
        
#         # Points: Index, Middle, Ring, Pinky Tips vs Knuckles
#         points = [[8,5,0],[12,9,0],[16,13,0],[20,17,0]]
#         self.finger = 0
        
#         # Check Thumb separately (complex logic simplified here or assumed 0 for bitmask start)
#         # We start bitmask at 0.
        
#         for idx,point in enumerate(points):
#             dist = self.get_signed_dist(point[:2])
#             dist2 = self.get_signed_dist(point[1:])
#             try:
#                 ratio = round(dist/dist2,1)
#             except:
#                 ratio = round(dist/0.01,1)
            
#             # Shift bit left to make room for new finger
#             self.finger = self.finger << 1
#             if ratio > 0.5 :
#                 self.finger = self.finger | 1
        
#         # NOTE: This bitmask order ends up being: Index(8), Mid(4), Ring(2), Pinky(1)
#         # Thumb is not in this loop, handled via Enum if needed, but basic logic above
#         # creates the IDs we use.
    
#     def get_gesture(self):
#         if self.hand_result == None:
#             return Gest.PALM
#         current_gesture = Gest.PALM
        
#         # Check for Pinches
#         if self.finger in [Gest.LAST3,Gest.LAST4] and self.get_dist([8,4]) < 0.05:
#             if self.hand_label == HLabel.MINOR :
#                 current_gesture = Gest.PINCH_MINOR
#             else:
#                 current_gesture = Gest.PINCH_MAJOR
        
#         # Check for V Gesture
#         elif Gest.FIRST2 == self.finger :
#             point = [[8,12],[5,9]]
#             dist1 = self.get_dist(point[0])
#             dist2 = self.get_dist(point[1])
#             ratio = dist1/dist2
#             if ratio > 1.7:
#                 current_gesture = Gest.V_GEST
#             else:
#                 if self.get_dz([8,12]) < 0.1:
#                     current_gesture =  Gest.TWO_FINGER_CLOSED
#                 else:
#                     current_gesture =  Gest.MID
        
#         else:
#             current_gesture =  self.finger
        
#         if current_gesture == self.prev_gesture:
#             self.frame_count += 1
#         else:
#             self.frame_count = 0
#         self.prev_gesture = current_gesture
        
#         if self.frame_count > 4 :
#             self.ori_gesture = current_gesture
#         return self.ori_gesture

# class Controller:
#     tx_old = 0
#     ty_old = 0
#     trial = True
#     flag = False
#     grabflag = False
#     pinchmajorflag = False
#     pinchminorflag = False
#     pinchstartxcoord = None
#     pinchstartycoord = None
#     pinchdirectionflag = None
#     prevpinchlv = 0
#     pinchlv = 0
#     framecount = 0
#     prev_hand = None
#     pinch_threshold = 0.3
    
#     def getpinchylv(hand_result):
#         dist = round((Controller.pinchstartycoord - hand_result.landmark[8].y)*10,1)
#         return dist

#     def getpinchxlv(hand_result):
#         dist = round((hand_result.landmark[8].x - Controller.pinchstartxcoord)*10,1)
#         return dist
    
#     def changesystembrightness():
#         """Mac-Compatible Brightness using Native Key Codes (F1/F2)"""
#         # On Mac, KeyCode 144 is Brightness Up, 145 is Brightness Down
#         if IS_MACOS:
#             if Controller.pinchlv > 0:
#                 # Pinch moved UP -> Increase Brightness
#                 # We repeat the keypress based on magnitude to speed it up
#                 repeats = int(abs(Controller.pinchlv)) + 1
#                 for _ in range(min(repeats, 3)): # Limit speed
#                     os.system("osascript -e 'tell application \"System Events\" to key code 144'")
#             else:
#                 # Pinch moved DOWN -> Decrease Brightness
#                 repeats = int(abs(Controller.pinchlv)) + 1
#                 for _ in range(min(repeats, 3)):
#                     os.system("osascript -e 'tell application \"System Events\" to key code 145'")
#         else:
#             # Windows fallback
#             currentBrightnessLv = sbcontrol.get_brightness(display=0)/100.0
#             currentBrightnessLv += Controller.pinchlv/50.0
#             if currentBrightnessLv > 1.0: currentBrightnessLv = 1.0
#             elif currentBrightnessLv < 0.0: currentBrightnessLv = 0.0       
#             sbcontrol.fade_brightness(int(100*currentBrightnessLv) , start = sbcontrol.get_brightness(display=0))
    
#     def changesystemvolume():
#         vol_change = Controller.pinchlv / 50.0 
        
#         if IS_MACOS:
#             try:
#                 # Use simple osascript to set volume
#                 cmd = "osascript -e 'output volume of (get volume settings)'"
#                 current_vol = int(subprocess.check_output(cmd, shell=True).strip())
#                 new_vol = int(current_vol + (vol_change * 100))
#                 new_vol = max(0, min(100, new_vol))
#                 os.system(f"osascript -e 'set volume output volume {new_vol}'")
#             except:
#                 pass
#         else:
#             devices = AudioUtilities.GetSpeakers()
#             interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
#             volume = cast(interface, POINTER(IAudioEndpointVolume))
#             currentVolumeLv = volume.GetMasterVolumeLevelScalar()
#             currentVolumeLv += vol_change
#             currentVolumeLv = max(0.0, min(1.0, currentVolumeLv))
#             volume.SetMasterVolumeLevelScalar(currentVolumeLv, None)
    
#     def scrollVertical():
#         pyautogui.scroll(10 if Controller.pinchlv>0.0 else -10)
        
#     def scrollHorizontal():
#         pyautogui.keyDown('shift')
#         pyautogui.scroll(10 if Controller.pinchlv>0.0 else -10)
#         pyautogui.keyUp('shift')

#     def get_position(hand_result):
#         point = 9
#         position = [hand_result.landmark[point].x ,hand_result.landmark[point].y]
#         sx,sy = pyautogui.size()
#         x_old,y_old = pyautogui.position()
#         x = int(position[0]*sx)
#         y = int(position[1]*sy)
#         if Controller.prev_hand is None:
#             Controller.prev_hand = x,y
#         delta_x = x - Controller.prev_hand[0]
#         delta_y = y - Controller.prev_hand[1]

#         distsq = delta_x**2 + delta_y**2
#         ratio = 1
#         Controller.prev_hand = [x,y]

#         if distsq <= 25:
#             ratio = 0
#         elif distsq <= 900:
#             ratio = 0.07 * (distsq ** (1/2))
#         else:
#             ratio = 2.1
#         x , y = x_old + delta_x*ratio , y_old + delta_y*ratio
#         return (x,y)

#     def pinch_control_init(hand_result):
#         Controller.pinchstartxcoord = hand_result.landmark[8].x
#         Controller.pinchstartycoord = hand_result.landmark[8].y
#         Controller.pinchlv = 0
#         Controller.prevpinchlv = 0
#         Controller.framecount = 0

#     def pinch_control(hand_result, controlHorizontal, controlVertical):
#         if Controller.framecount == 5:
#             Controller.framecount = 0
#             Controller.pinchlv = Controller.prevpinchlv

#             if Controller.pinchdirectionflag == True:
#                 controlHorizontal()

#             elif Controller.pinchdirectionflag == False:
#                 controlVertical()

#         lvx =  Controller.getpinchxlv(hand_result)
#         lvy =  Controller.getpinchylv(hand_result)
            
#         if abs(lvy) > abs(lvx) and abs(lvy) > Controller.pinch_threshold:
#             Controller.pinchdirectionflag = False
#             if abs(Controller.prevpinchlv - lvy) < Controller.pinch_threshold:
#                 Controller.framecount += 1
#             else:
#                 Controller.prevpinchlv = lvy
#                 Controller.framecount = 0

#         elif abs(lvx) > Controller.pinch_threshold:
#             Controller.pinchdirectionflag = True
#             if abs(Controller.prevpinchlv - lvx) < Controller.pinch_threshold:
#                 Controller.framecount += 1
#             else:
#                 Controller.prevpinchlv = lvx
#                 Controller.framecount = 0

#     def handle_controls(gesture, hand_result):  
#         x,y = None,None
#         if gesture != Gest.PALM :
#             x,y = Controller.get_position(hand_result)
        
#         # flag reset
#         if gesture != Gest.FIST and Controller.grabflag:
#             Controller.grabflag = False
#             pyautogui.mouseUp(button = "left")

#         if gesture != Gest.PINCH_MAJOR and Controller.pinchmajorflag:
#             Controller.pinchmajorflag = False

#         if gesture != Gest.PINCH_MINOR and Controller.pinchminorflag:
#             Controller.pinchminorflag = False

#         # --- GESTURE MAPPING ---
        
#         # 1. MOUSE MOVE (Peace/Victory ✌️)
#         if gesture == Gest.V_GEST:
#             Controller.flag = True
#             pyautogui.moveTo(x, y, duration = 0.1)

#         # 2. LEFT CLICK (Fist or Index ☝️ logic)
#         elif gesture == Gest.FIST:
#             if not Controller.grabflag : 
#                 Controller.grabflag = True
#                 pyautogui.mouseDown(button = "left")
#             pyautogui.moveTo(x, y, duration = 0.1)

#         elif gesture == Gest.MID and Controller.flag:
#             pyautogui.click()
#             Controller.flag = False

#         elif gesture == Gest.INDEX and Controller.flag:
#             pyautogui.click(button='right')
#             Controller.flag = False

#         elif gesture == Gest.TWO_FINGER_CLOSED and Controller.flag:
#             pyautogui.doubleClick()
#             Controller.flag = False

#         # --- NEW FEATURES ---

#         # # 3. MISSION CONTROL (Open Palm ✋)
#         # # Ctrl + Up Arrow
#         # elif gesture == Gest.PALM:
#         #     if Controller.framecount == 0: 
#         #         print("[DEBUG] Mission Control Triggered")
#         #         pyautogui.hotkey('ctrl', 'up')
        
#         # 4. SCREENSHOT (Pinky Only 🤙)
#         # Cmd + Shift + 3
#         elif gesture == Gest.PINKY:
#             if Controller.framecount == 0:
#                 print("[DEBUG] Screenshot Triggered")
#                 pyautogui.hotkey('command', 'shift', '3')

#         # 5. SWITCH APP (Three Fingers Up: Index, Mid, Ring)
#         # Cmd + Tab
#         elif gesture == Gest.THREE_FINGER:
#              if Controller.framecount == 0:
#                 print("[DEBUG] Switch App Triggered")
#                 pyautogui.hotkey('command', 'tab')

#         # --------------------

#         elif gesture == Gest.PINCH_MINOR:
#             if Controller.pinchminorflag == False:
#                 Controller.pinch_control_init(hand_result)
#                 Controller.pinchminorflag = True
#             Controller.pinch_control(hand_result,Controller.scrollHorizontal, Controller.scrollVertical)
        
#         elif gesture == Gest.PINCH_MAJOR:
#             if Controller.pinchmajorflag == False:
#                 Controller.pinch_control_init(hand_result)
#                 Controller.pinchmajorflag = True
#             Controller.pinch_control(hand_result,Controller.changesystembrightness, Controller.changesystemvolume)

# class GestureController:
#     gc_mode = 0
#     cap = None
#     CAM_HEIGHT = None
#     CAM_WIDTH = None
#     hr_major = None 
#     hr_minor = None 
#     dom_hand = True

#     def __init__(self):
#         print("[DEBUG] Initializing GestureController...")
#         GestureController.gc_mode = 1
#         GestureController.cap = cv2.VideoCapture(0)
#         if not GestureController.cap.isOpened():
#              GestureController.cap = cv2.VideoCapture(1)
        
#         GestureController.CAM_HEIGHT = GestureController.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
#         GestureController.CAM_WIDTH = GestureController.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    
#     def classify_hands(results):
#         left , right = None,None
#         try:
#             for idx, hand_handedness in enumerate(results.multi_handedness):
#                 label = hand_handedness.classification[0].label
#                 if label == 'Right':
#                     right = results.multi_hand_landmarks[idx]
#                 else:
#                     left = results.multi_hand_landmarks[idx]
#         except:
#             pass
        
#         if GestureController.dom_hand == True:
#             GestureController.hr_major = right
#             GestureController.hr_minor = left
#         else :
#             GestureController.hr_major = left
#             GestureController.hr_minor = right

#     def start(self):
#         print("[DEBUG] Camera Started.")
#         handmajor = HandRecog(HLabel.MAJOR)
#         handminor = HandRecog(HLabel.MINOR)

#         with mp_hands.Hands(max_num_hands = 2,min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
#             while GestureController.cap.isOpened() and GestureController.gc_mode:
#                 success, image = GestureController.cap.read()
#                 if not success: continue
                
#                 image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
#                 image.flags.writeable = False
#                 results = hands.process(image)
#                 image.flags.writeable = True
#                 image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

#                 if results.multi_hand_landmarks:                   
#                     GestureController.classify_hands(results)
#                     handmajor.update_hand_result(GestureController.hr_major)
#                     handminor.update_hand_result(GestureController.hr_minor)

#                     handmajor.set_finger_state()
#                     handminor.set_finger_state()
#                     gest_name = handminor.get_gesture()

#                     if gest_name == Gest.PINCH_MINOR:
#                         Controller.handle_controls(gest_name, handminor.hand_result)
#                     else:
#                         gest_name = handmajor.get_gesture()
#                         Controller.handle_controls(gest_name, handmajor.hand_result)
                    
#                     for hand_landmarks in results.multi_hand_landmarks:
#                         mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
#                 else:
#                     Controller.prev_hand = None
                
#                 cv2.imshow('Gesture Controller', image)
#                 if cv2.waitKey(5) & 0xFF == 13:
#                     break
#         GestureController.cap.release()
#         cv2.destroyAllWindows()

# if __name__ == "__main__":
#     gc = GestureController()
#     gc.start()


"""


#    # #!  Phase 2.1 - Dual Mode with MediaPipe Holistic



import cv2
import mediapipe as mp
import pyautogui
import math
import platform
import os
import subprocess
import time
from enum import IntEnum
import screen_brightness_control as sbcontrol
import collections
import numpy as np

# --- USER CONFIGURATION ---
PRIMARY_HAND = "Left"  # "Left" usually detects Physical Right Hand in mirror mode
SMOOTHING_FACTOR = 0.2 # Lower = Smoother/Heavier cursor (0.1 - 0.3 recommended)
FRAME_REDUCTION = 100  # Sensitivity: Higher = Less hand movement required (100-150)
# --------------------------

IS_MACOS = platform.system() == "Darwin"
if not IS_MACOS:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

pyautogui.FAILSAFE = False
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

class Gest(IntEnum):
    FIST = 0
    PINKY = 1
    RING = 2
    MID = 4
    LAST3 = 7
    INDEX = 8
    FIRST2 = 12
    THREE_FINGER = 14
    LAST4 = 15
    THUMB = 16    
    PALM = 31
    V_GEST = 33
    TWO_FINGER_CLOSED = 34
    PINCH_MAJOR = 35
    PINCH_MINOR = 36

class HLabel(IntEnum):
    MINOR = 0
    MAJOR = 1

class HandRecog:
    def __init__(self, hand_label):
        self.finger = 0
        self.ori_gesture = Gest.PALM
        self.prev_gesture = Gest.PALM
        self.frame_count = 0
        self.hand_result = None
        self.hand_label = hand_label
    
    def update_hand_result(self, hand_result):
        self.hand_result = hand_result

    def get_signed_dist(self, point):
        sign = -1
        if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
            sign = 1
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        dist = math.sqrt(dist)
        return dist*sign
    
    def get_dist(self, point):
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        dist = math.sqrt(dist)
        return dist
    
    def get_dz(self,point):
        return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)
    
    def set_finger_state(self):
        if self.hand_result == None:
            return
        points = [[8,5,0],[12,9,0],[16,13,0],[20,17,0]]
        self.finger = 0
        for idx,point in enumerate(points):
            dist = self.get_signed_dist(point[:2])
            dist2 = self.get_signed_dist(point[1:])
            try:
                ratio = round(dist/dist2,1)
            except:
                ratio = round(dist/0.01,1)
            self.finger = self.finger << 1
            if ratio > 0.5 :
                self.finger = self.finger | 1
    
    def get_gesture(self):
        if self.hand_result == None:
            return Gest.PALM
        current_gesture = Gest.PALM
        
        if self.finger in [Gest.LAST3,Gest.LAST4] and self.get_dist([8,4]) < 0.05:
            if self.hand_label == HLabel.MINOR :
                current_gesture = Gest.PINCH_MINOR
            else:
                current_gesture = Gest.PINCH_MAJOR
        
        elif Gest.FIRST2 == self.finger :
            point = [[8,12],[5,9]]
            dist1 = self.get_dist(point[0])
            dist2 = self.get_dist(point[1])
            ratio = dist1/dist2
            if ratio > 1.7:
                current_gesture = Gest.V_GEST
            else:
                if self.get_dz([8,12]) < 0.1:
                    current_gesture =  Gest.TWO_FINGER_CLOSED
                else:
                    current_gesture =  Gest.MID
        else:
            current_gesture =  self.finger
        
        if current_gesture == self.prev_gesture:
            self.frame_count += 1
        else:
            self.frame_count = 0
        self.prev_gesture = current_gesture
        
        if self.frame_count > 4 :
            self.ori_gesture = current_gesture
        return self.ori_gesture

class Controller:
    tx_old = 0
    ty_old = 0
    flag = False # True if we are in "Move Mode"
    grabflag = False
    pinchmajorflag = False
    pinchminorflag = False
    pinchstartxcoord = None
    pinchstartycoord = None
    pinchdirectionflag = None
    prevpinchlv = 0
    pinchlv = 0
    framecount = 0
    prev_hand = None
    pinch_threshold = 0.3
    
    # Cooldowns
    last_screenshot_time = 0
    last_app_switch_time = 0
    
    def getpinchylv(hand_result):
        dist = round((Controller.pinchstartycoord - hand_result.landmark[8].y)*10,1)
        return dist

    def getpinchxlv(hand_result):
        dist = round((hand_result.landmark[8].x - Controller.pinchstartxcoord)*10,1)
        return dist
    
    def changesystembrightness():
        if IS_MACOS:
            if Controller.pinchlv > 0:
                repeats = int(abs(Controller.pinchlv)) + 1
                for _ in range(min(repeats, 3)):
                    os.system("osascript -e 'tell application \"System Events\" to key code 144'")
            else:
                repeats = int(abs(Controller.pinchlv)) + 1
                for _ in range(min(repeats, 3)):
                    os.system("osascript -e 'tell application \"System Events\" to key code 145'")
    
    def changesystemvolume():
        vol_change = Controller.pinchlv / 50.0 
        if IS_MACOS:
            try:
                cmd = "osascript -e 'output volume of (get volume settings)'"
                current_vol = int(subprocess.check_output(cmd, shell=True).strip())
                new_vol = int(current_vol + (vol_change * 100))
                new_vol = max(0, min(100, new_vol))
                os.system(f"osascript -e 'set volume output volume {new_vol}'")
            except: pass
    
    def scrollVertical():
        pyautogui.scroll(10 if Controller.pinchlv>0.0 else -10)
        
    def scrollHorizontal():
        pyautogui.keyDown('shift')
        pyautogui.scroll(10 if Controller.pinchlv>0.0 else -10)
        pyautogui.keyUp('shift')

    # --- SENSITIVITY AMPLIFICATION & SMOOTHING ---
    def get_position(hand_result):
        point = 9 
        # Raw Coordinates (0.0 to 1.0)
        raw_x = hand_result.landmark[point].x 
        raw_y = hand_result.landmark[point].y
        
        # Camera & Screen Dimensions
        wCam, hCam = int(GestureController.CAM_WIDTH), int(GestureController.CAM_HEIGHT)
        wScr, hScr = pyautogui.size()

        # Convert normalized coords to camera pixels
        x1 = raw_x * wCam
        y1 = raw_y * hCam

        # 1. Coordinate Interpolation (Amplification)
        # Map the Reduced Frame (wCam - 2*FRAME_REDUCTION) to Full Screen (wScr)
        # This means moving hand 1 inch in camera = 10 inches on screen
        x3 = np.interp(x1, (FRAME_REDUCTION, wCam - FRAME_REDUCTION), (0, wScr))
        y3 = np.interp(y1, (FRAME_REDUCTION, hCam - FRAME_REDUCTION), (0, hScr))
        
        # 2. Smooth Values
        if Controller.prev_hand is None:
            Controller.prev_hand = [x3, y3]
            return (int(x3), int(y3))

        # Exponential Smoothing
        curr_x = Controller.prev_hand[0] + (x3 - Controller.prev_hand[0]) * SMOOTHING_FACTOR
        curr_y = Controller.prev_hand[1] + (y3 - Controller.prev_hand[1]) * SMOOTHING_FACTOR
        
        Controller.prev_hand = [curr_x, curr_y]
        return (int(curr_x), int(curr_y))

    def pinch_control_init(hand_result):
        Controller.pinchstartxcoord = hand_result.landmark[8].x
        Controller.pinchstartycoord = hand_result.landmark[8].y
        Controller.pinchlv = 0
        Controller.prevpinchlv = 0
        Controller.framecount = 0

    def pinch_control(hand_result, controlHorizontal, controlVertical):
        if Controller.framecount == 5:
            Controller.framecount = 0
            Controller.pinchlv = Controller.prevpinchlv

            if Controller.pinchdirectionflag == True:
                controlHorizontal()

            elif Controller.pinchdirectionflag == False:
                controlVertical()

        lvx =  Controller.getpinchxlv(hand_result)
        lvy =  Controller.getpinchylv(hand_result)
            
        if abs(lvy) > abs(lvx) and abs(lvy) > Controller.pinch_threshold:
            Controller.pinchdirectionflag = False
            if abs(Controller.prevpinchlv - lvy) < Controller.pinch_threshold:
                Controller.framecount += 1
            else:
                Controller.prevpinchlv = lvy
                Controller.framecount = 0

        elif abs(lvx) > Controller.pinch_threshold:
            Controller.pinchdirectionflag = True
            if abs(Controller.prevpinchlv - lvx) < Controller.pinch_threshold:
                Controller.framecount += 1
            else:
                Controller.prevpinchlv = lvx
                Controller.framecount = 0

    def handle_controls(gesture, hand_result):  
        x,y = None,None
        if gesture != Gest.PALM :
            x,y = Controller.get_position(hand_result)
        
        if gesture != Gest.FIST and Controller.grabflag:
            Controller.grabflag = False
            pyautogui.mouseUp(button = "left")

        if gesture != Gest.PINCH_MAJOR and Controller.pinchmajorflag:
            Controller.pinchmajorflag = False

        if gesture != Gest.PINCH_MINOR and Controller.pinchminorflag:
            Controller.pinchminorflag = False

        # --- REFINED MAPPING ---

        # 1. MOVE: V-Gesture
        if gesture == Gest.V_GEST:
            Controller.flag = True
            pyautogui.moveTo(x, y, duration = 0)

        # 2. CLICK: Index Only
        elif gesture == Gest.INDEX and Controller.flag:
            # Only click if we were previously moving
            pyautogui.click()
            Controller.flag = False 

        # 3. RIGHT CLICK: Middle Only
        elif gesture == Gest.MID and Controller.flag:
            pyautogui.click(button='right')
            Controller.flag = False 

        # 4. DRAG: Fist
        elif gesture == Gest.FIST:
            if not Controller.grabflag : 
                Controller.grabflag = True
                pyautogui.mouseDown(button = "left")
            pyautogui.moveTo(x, y, duration = 0)

        # 5. DOUBLE CLICK: Two Fingers Closed
        elif gesture == Gest.TWO_FINGER_CLOSED and Controller.flag:
            pyautogui.doubleClick()
            Controller.flag = False

        # --- TRIGGER ACTIONS ---

        elif gesture == Gest.PINKY:
            if time.time() - Controller.last_screenshot_time > 2.0:
                pyautogui.hotkey('command', 'shift', '3')
                Controller.last_screenshot_time = time.time()

        elif gesture == Gest.THREE_FINGER:
             if time.time() - Controller.last_app_switch_time > 2.0:
                pyautogui.hotkey('command', 'tab')
                Controller.last_app_switch_time = time.time()

        # --- PINCH CONTROLS ---

        elif gesture == Gest.PINCH_MINOR:
            if Controller.pinchminorflag == False:
                Controller.pinch_control_init(hand_result)
                Controller.pinchminorflag = True
            Controller.pinch_control(hand_result,Controller.scrollHorizontal, Controller.scrollVertical)
        
        elif gesture == Gest.PINCH_MAJOR:
            if Controller.pinchmajorflag == False:
                Controller.pinch_control_init(hand_result)
                Controller.pinchmajorflag = True
            Controller.pinch_control(hand_result,Controller.changesystembrightness, Controller.changesystemvolume)


class GestureController:
    gc_mode = 0
    cap = None
    is_signing_mode = False 
    sequence_buffer = []    
    CAM_WIDTH = 0
    CAM_HEIGHT = 0
    
    def __init__(self):
        print("[DEBUG] Initializing GestureController...")
        GestureController.gc_mode = 1
        GestureController.sequence_buffer = collections.deque(maxlen=45)

        GestureController.cap = cv2.VideoCapture(0)
        if not GestureController.cap.isOpened():
             GestureController.cap = cv2.VideoCapture(1)
        
        # Set Resolution (Optional - improves FPS)
        GestureController.cap.set(3, 640)
        GestureController.cap.set(4, 480)
        
        GestureController.CAM_WIDTH = GestureController.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        GestureController.CAM_HEIGHT = GestureController.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def start(self):
        print(f"[DEBUG] Started. Target Hand: {PRIMARY_HAND}")
        handmajor = HandRecog(HLabel.MAJOR)
        handminor = HandRecog(HLabel.MINOR)

        with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
            while GestureController.cap.isOpened() and GestureController.gc_mode:
                success, image = GestureController.cap.read()
                if not success: continue
                
                # Flip for mirror effect
                image = cv2.flip(image, 1)
                
                # --- DRAW ACTIVE ZONE ---
                # This rectangle shows where your hand needs to be
                w, h = int(GestureController.CAM_WIDTH), int(GestureController.CAM_HEIGHT)
                cv2.rectangle(image, (FRAME_REDUCTION, FRAME_REDUCTION), 
                              (w - FRAME_REDUCTION, h - FRAME_REDUCTION), (255, 0, 255), 2)
                # ------------------------
                
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image_rgb.flags.writeable = False
                results = holistic.process(image_rgb)
                image_rgb.flags.writeable = True

                if not GestureController.is_signing_mode:
                    
                    mouse_hand = None
                    secondary_hand = None

                    if PRIMARY_HAND == "Left":
                         mouse_hand = results.left_hand_landmarks
                         secondary_hand = results.right_hand_landmarks
                    else:
                         mouse_hand = results.right_hand_landmarks
                         secondary_hand = results.left_hand_landmarks

                    if mouse_hand:
                        handmajor.update_hand_result(mouse_hand)
                        handmajor.set_finger_state()
                        gest_name = handmajor.get_gesture()
                        Controller.handle_controls(gest_name, handmajor.hand_result)
                        mp_drawing.draw_landmarks(image, mouse_hand, mp_holistic.HAND_CONNECTIONS)
                    
                    if secondary_hand:
                        handminor.update_hand_result(secondary_hand)
                        handminor.set_finger_state()
                        gest_name = handminor.get_gesture()
                        if gest_name == Gest.PINCH_MINOR or gest_name == Gest.PINCH_MAJOR:
                             Controller.handle_controls(gest_name, handminor.hand_result)
                        mp_drawing.draw_landmarks(image, secondary_hand, mp_holistic.HAND_CONNECTIONS)

                else:
                    if results.pose_landmarks and results.right_hand_landmarks:
                         mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)
                         cv2.putText(image, "SIGN MODE ACTIVE", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                cv2.imshow('Gesture Controller', image)
                if cv2.waitKey(5) & 0xFF == 13: break
                    
        GestureController.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    gc = GestureController()
    gc.start()


    """


#! phase 2.2 - Refined Gesture Controller with ISL language mode

import cv2
import mediapipe as mp
import pyautogui
import math
import platform
import os
import subprocess
import time
import numpy as np
import collections
from enum import IntEnum

# --- ML DEPENDENCIES ---
try:
    import tensorflow as tf
    Interpreter = tf.lite.Interpreter
except ImportError:
    # Fallback if full TF isn't installed (lighter runtime)
    from tflite_runtime.interpreter import Interpreter

# --- CONFIGURATION ---
PRIMARY_HAND = "Left" 
SMOOTHING_FACTOR = 0.2 
FRAME_REDUCTION = 100  
CONFIDENCE_THRESHOLD = 0.70 # Only speak if 70% sure
MODEL_PATH = "models/production/ISL_Model.tflite"
LABELS_PATH = "data/processed/labels.npy"

# --- MACOS PATCH ---
IS_MACOS = platform.system() == "Darwin"
if not IS_MACOS:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

pyautogui.FAILSAFE = False
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

# --- PHASE 1 CLASSES (Mouse) ---
class Gest(IntEnum):
    FIST = 0; PINKY = 1; RING = 2; MID = 4; LAST3 = 7; INDEX = 8; FIRST2 = 12
    THREE_FINGER = 14; LAST4 = 15; THUMB = 16; PALM = 31; V_GEST = 33
    TWO_FINGER_CLOSED = 34; PINCH_MAJOR = 35; PINCH_MINOR = 36

class HLabel(IntEnum): MINOR = 0; MAJOR = 1

class HandRecog:
    def __init__(self, hand_label):
        self.finger = 0; self.ori_gesture = Gest.PALM; self.prev_gesture = Gest.PALM
        self.frame_count = 0; self.hand_result = None; self.hand_label = hand_label
    
    def update_hand_result(self, hand_result): self.hand_result = hand_result

    def get_signed_dist(self, point):
        sign = -1
        if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y: sign = 1
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        return math.sqrt(dist)*sign
    
    def get_dist(self, point):
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        return math.sqrt(dist)
    
    def get_dz(self,point): return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)
    
    def set_finger_state(self):
        if self.hand_result == None: return
        points = [[8,5,0],[12,9,0],[16,13,0],[20,17,0]]
        self.finger = 0
        for idx,point in enumerate(points):
            dist = self.get_signed_dist(point[:2])
            dist2 = self.get_signed_dist(point[1:])
            try: ratio = round(dist/dist2,1)
            except: ratio = round(dist/0.01,1)
            self.finger = self.finger << 1
            if ratio > 0.5 : self.finger = self.finger | 1
    
    def get_gesture(self):
        if self.hand_result == None: return Gest.PALM
        current_gesture = Gest.PALM
        if self.finger in [Gest.LAST3,Gest.LAST4] and self.get_dist([8,4]) < 0.05:
            if self.hand_label == HLabel.MINOR : current_gesture = Gest.PINCH_MINOR
            else: current_gesture = Gest.PINCH_MAJOR
        elif Gest.FIRST2 == self.finger :
            point = [[8,12],[5,9]]
            dist1 = self.get_dist(point[0]); dist2 = self.get_dist(point[1]); ratio = dist1/dist2
            if ratio > 1.7: current_gesture = Gest.V_GEST
            else:
                if self.get_dz([8,12]) < 0.1: current_gesture =  Gest.TWO_FINGER_CLOSED
                else: current_gesture =  Gest.MID
        else: current_gesture =  self.finger
        if current_gesture == self.prev_gesture: self.frame_count += 1
        else: self.frame_count = 0
        self.prev_gesture = current_gesture
        if self.frame_count > 4 : self.ori_gesture = current_gesture
        return self.ori_gesture

class Controller:
    tx_old = 0; ty_old = 0; flag = False; grabflag = False; pinchmajorflag = False; pinchminorflag = False
    pinchstartxcoord = None; pinchstartycoord = None; pinchdirectionflag = None
    prevpinchlv = 0; pinchlv = 0; framecount = 0; prev_hand = None; pinch_threshold = 0.3
    last_screenshot_time = 0; last_app_switch_time = 0; last_sign_mode_toggle = 0
    
    def getpinchylv(hand_result): return round((Controller.pinchstartycoord - hand_result.landmark[8].y)*10,1)
    def getpinchxlv(hand_result): return round((hand_result.landmark[8].x - Controller.pinchstartxcoord)*10,1)
    
    def changesystembrightness():
        if IS_MACOS:
            if Controller.pinchlv > 0:
                for _ in range(min(int(abs(Controller.pinchlv)) + 1, 3)): os.system("osascript -e 'tell application \"System Events\" to key code 144'")
            else:
                for _ in range(min(int(abs(Controller.pinchlv)) + 1, 3)): os.system("osascript -e 'tell application \"System Events\" to key code 145'")
    
    def changesystemvolume():
        vol_change = Controller.pinchlv / 50.0 
        if IS_MACOS:
            try:
                cmd = "osascript -e 'output volume of (get volume settings)'"
                current_vol = int(subprocess.check_output(cmd, shell=True).strip())
                new_vol = int(current_vol + (vol_change * 100))
                os.system(f"osascript -e 'set volume output volume {max(0, min(100, new_vol))}'")
            except: pass
    
    def scrollVertical(): pyautogui.scroll(10 if Controller.pinchlv>0.0 else -10)
    def scrollHorizontal(): pyautogui.keyDown('shift'); pyautogui.scroll(10 if Controller.pinchlv>0.0 else -10); pyautogui.keyUp('shift')

    def get_position(hand_result):
        point = 9 
        raw_x = hand_result.landmark[point].x; raw_y = hand_result.landmark[point].y
        wCam, hCam = int(GestureController.CAM_WIDTH), int(GestureController.CAM_HEIGHT)
        wScr, hScr = pyautogui.size()
        x1 = raw_x * wCam; y1 = raw_y * hCam
        x3 = np.interp(x1, (FRAME_REDUCTION, wCam - FRAME_REDUCTION), (0, wScr))
        y3 = np.interp(y1, (FRAME_REDUCTION, hCam - FRAME_REDUCTION), (0, hScr))
        if Controller.prev_hand is None: Controller.prev_hand = [x3, y3]; return (int(x3), int(y3))
        curr_x = Controller.prev_hand[0] + (x3 - Controller.prev_hand[0]) * SMOOTHING_FACTOR
        curr_y = Controller.prev_hand[1] + (y3 - Controller.prev_hand[1]) * SMOOTHING_FACTOR
        Controller.prev_hand = [curr_x, curr_y]
        return (int(curr_x), int(curr_y))

    def pinch_control_init(hand_result):
        Controller.pinchstartxcoord = hand_result.landmark[8].x; Controller.pinchstartycoord = hand_result.landmark[8].y
        Controller.pinchlv = 0; Controller.prevpinchlv = 0; Controller.framecount = 0

    def pinch_control(hand_result, controlHorizontal, controlVertical):
        if Controller.framecount == 5:
            Controller.framecount = 0; Controller.pinchlv = Controller.prevpinchlv
            if Controller.pinchdirectionflag == True: controlHorizontal()
            elif Controller.pinchdirectionflag == False: controlVertical()
        lvx =  Controller.getpinchxlv(hand_result); lvy =  Controller.getpinchylv(hand_result)
        if abs(lvy) > abs(lvx) and abs(lvy) > Controller.pinch_threshold:
            Controller.pinchdirectionflag = False
            if abs(Controller.prevpinchlv - lvy) < Controller.pinch_threshold: Controller.framecount += 1
            else: Controller.prevpinchlv = lvy; Controller.framecount = 0
        elif abs(lvx) > Controller.pinch_threshold:
            Controller.pinchdirectionflag = True
            if abs(Controller.prevpinchlv - lvx) < Controller.pinch_threshold: Controller.framecount += 1
            else: Controller.prevpinchlv = lvx; Controller.framecount = 0

    def handle_controls(gesture, hand_result):  
        x,y = None,None
        if gesture != Gest.PALM : x,y = Controller.get_position(hand_result)
        if gesture != Gest.FIST and Controller.grabflag: Controller.grabflag = False; pyautogui.mouseUp(button = "left")
        if gesture != Gest.PINCH_MAJOR and Controller.pinchmajorflag: Controller.pinchmajorflag = False
        if gesture != Gest.PINCH_MINOR and Controller.pinchminorflag: Controller.pinchminorflag = False

        if gesture == Gest.V_GEST: Controller.flag = True; pyautogui.moveTo(x, y, duration = 0)
        elif gesture == Gest.INDEX and Controller.flag: pyautogui.click(); Controller.flag = False 
        elif gesture == Gest.MID and Controller.flag: pyautogui.click(button='right'); Controller.flag = False 
        elif gesture == Gest.FIST:
            if not Controller.grabflag : Controller.grabflag = True; pyautogui.mouseDown(button = "left")
            pyautogui.moveTo(x, y, duration = 0)
        elif gesture == Gest.TWO_FINGER_CLOSED and Controller.flag: pyautogui.doubleClick(); Controller.flag = False
        elif gesture == Gest.PINKY:
            if time.time() - Controller.last_screenshot_time > 2.0: pyautogui.hotkey('command', 'shift', '3'); Controller.last_screenshot_time = time.time()
        elif gesture == Gest.THREE_FINGER:
             if time.time() - Controller.last_app_switch_time > 2.0: pyautogui.hotkey('command', 'tab'); Controller.last_app_switch_time = time.time()
        elif gesture == Gest.PINCH_MINOR:
            if Controller.pinchminorflag == False: Controller.pinch_control_init(hand_result); Controller.pinchminorflag = True
            Controller.pinch_control(hand_result,Controller.scrollHorizontal, Controller.scrollVertical)
        elif gesture == Gest.PINCH_MAJOR:
            if Controller.pinchmajorflag == False: Controller.pinch_control_init(hand_result); Controller.pinchmajorflag = True
            Controller.pinch_control(hand_result,Controller.changesystembrightness, Controller.changesystemvolume)

# --- PHASE 2 CLASS (Sign Language Engine) ---
class ISLEngine:
    def __init__(self, model_path, labels_path):
        print(f"[ISL] Loading model from {model_path}...")
        try:
            # Load TFLite Model
            self.interpreter = Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            # Load Labels
            self.labels_map = np.load(labels_path, allow_pickle=True).item()
            # Invert map: {0: 'Hello', 1: 'Help'}
            self.id_to_label = {v: k for k, v in self.labels_map.items()}
            print("[ISL] Brain Loaded Successfully.")
            self.is_loaded = True
        except Exception as e:
            print(f"[ISL] ERROR: Could not load model. {e}")
            self.is_loaded = False

    def extract_features(self, results):
        # EXACT SAME LOGIC AS DATA_EXTRACTOR.PY
        if results.pose_landmarks:
            pose = np.array([[res.x, res.y, res.z] for res in results.pose_landmarks.landmark[:24]]).flatten()
        else: pose = np.zeros(24 * 3)
        if results.left_hand_landmarks:
            lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten()
        else: lh = np.zeros(21 * 3)
        if results.right_hand_landmarks:
            rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten()
        else: rh = np.zeros(21 * 3)
        return np.concatenate([pose, lh, rh])

    def predict(self, sequence_buffer):
        if not self.is_loaded: return "Model Error", 0.0
        
        # Prepare Data
        input_data = np.expand_dims(sequence_buffer, axis=0).astype(np.float32)
        
        # Inference
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        
        # Result
        prediction_id = np.argmax(output_data)
        confidence = np.max(output_data)
        
        predicted_word = self.id_to_label.get(prediction_id, "Unknown")
        return predicted_word, confidence

# --- MAIN CONTROLLER ---
class GestureController:
    gc_mode = 1
    cap = None; is_signing_mode = False 
    sequence_buffer = []; CAM_WIDTH = 0; CAM_HEIGHT = 0
    
    def __init__(self):
        print("[INIT] Launching GestureController...")
        GestureController.sequence_buffer = collections.deque(maxlen=30) # 30 Frames Window

        # Initialize ISL Engine
        self.isl_engine = ISLEngine(MODEL_PATH, LABELS_PATH)

        GestureController.cap = cv2.VideoCapture(0)
        if not GestureController.cap.isOpened(): GestureController.cap = cv2.VideoCapture(1)
        GestureController.cap.set(3, 640); GestureController.cap.set(4, 480)
        GestureController.CAM_WIDTH = GestureController.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        GestureController.CAM_HEIGHT = GestureController.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def toggle_mode(self):
        # Debounce toggle (prevents double switching)
        if time.time() - Controller.last_sign_mode_toggle > 1.0:
            GestureController.is_signing_mode = not GestureController.is_signing_mode
            Controller.last_sign_mode_toggle = time.time()
            mode_text = "SIGN LANGUAGE" if GestureController.is_signing_mode else "MOUSE CONTROL"
            print(f"[MODE SWITCH] Now in: {mode_text}")
            # Optional: Speak mode change via Jarvis logic (if connected) or just system beep
            os.system('tput bel') 

    def start(self):
        handmajor = HandRecog(HLabel.MAJOR); handminor = HandRecog(HLabel.MINOR)

        with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
            while GestureController.cap.isOpened() and GestureController.gc_mode:
                success, image = GestureController.cap.read()
                if not success: continue
                
                image = cv2.flip(image, 1)
                
                # --- KEYBOARD SHORTCUT TO TOGGLE MODES (Press 'q') ---
                # In final version, this can be a specific gesture
                key = cv2.waitKey(5) & 0xFF
                if key == ord('q'): self.toggle_mode()
                if key == 13: break # Enter to exit

                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image_rgb.flags.writeable = False
                results = holistic.process(image_rgb)
                image_rgb.flags.writeable = True

                # --- MODE 1: MOUSE CONTROL ---
                if not GestureController.is_signing_mode:
                    # Draw Active Zone
                    cv2.rectangle(image, (FRAME_REDUCTION, FRAME_REDUCTION), 
                                  (int(GestureController.CAM_WIDTH) - FRAME_REDUCTION, int(GestureController.CAM_HEIGHT) - FRAME_REDUCTION), 
                                  (255, 0, 255), 2)
                    
                    mouse_hand = results.left_hand_landmarks if PRIMARY_HAND == "Left" else results.right_hand_landmarks
                    secondary_hand = results.right_hand_landmarks if PRIMARY_HAND == "Left" else results.left_hand_landmarks

                    if mouse_hand:
                        handmajor.update_hand_result(mouse_hand)
                        handmajor.set_finger_state()
                        gest_name = handmajor.get_gesture()
                        Controller.handle_controls(gest_name, handmajor.hand_result)
                        mp_drawing.draw_landmarks(image, mouse_hand, mp_holistic.HAND_CONNECTIONS)
                    
                    if secondary_hand:
                        handminor.update_hand_result(secondary_hand)
                        handminor.set_finger_state()
                        gest_name = handminor.get_gesture()
                        if gest_name == Gest.PINCH_MINOR or gest_name == Gest.PINCH_MAJOR:
                             Controller.handle_controls(gest_name, handminor.hand_result)
                        mp_drawing.draw_landmarks(image, secondary_hand, mp_holistic.HAND_CONNECTIONS)

                # --- MODE 2: SIGN LANGUAGE ---
                else:
                    # UI Indicator
                    cv2.rectangle(image, (0,0), (640, 60), (0,0,0), -1)
                    cv2.putText(image, "SIGN MODE (Press 'q' to exit)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Draw Skeleton
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)
                    mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
                    mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)

                    # Collection & Inference
                    if results.pose_landmarks: # Only record if body is visible
                        keypoints = self.isl_engine.extract_features(results)
                        GestureController.sequence_buffer.append(keypoints)
                        
                        if len(GestureController.sequence_buffer) == 30:
                            word, conf = self.isl_engine.predict(GestureController.sequence_buffer)
                            
                            # Display Prediction
                            color = (0, 255, 0) if conf > CONFIDENCE_THRESHOLD else (0, 0, 255)
                            label_text = f"{word} ({int(conf*100)}%)"
                            cv2.putText(image, label_text, (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                            
                            if conf > CONFIDENCE_THRESHOLD:
                                print(f"[DETECTED] {word}")
                                # In Phase 3, we will send this 'word' to Jarvis to speak out loud.

                cv2.imshow('Gesture Controller', image)
                    
        GestureController.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    gc = GestureController()
    gc.start()