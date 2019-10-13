import socket
import threading
import time
import datetime

class LTSDrone():
    """Wrapper class to interact with the Tello drone."""

    TELLO_COMMAND_PORT = 8889
    TELLO_VIDEO_PORT = 11111
    TELLO_STATE_PORT = 8890

    def __init__(self, local_ip='', local_port=8889, state_interval=0.2, command_timeout=1.0, tello_ip='192.168.10.1'):
        """
        Binds to the local IP/port and puts the Tello into command mode.

        :param local_ip (str): Local IP address to bind.
        :param local_port (int): Local port to bind.
        :param command_timeout (int|float): Number of seconds to wait for a response to a command.
        :param tello_ip (str): Tello IP.
        :param tello_port (int): Tello port.
        """
        # Parameters
        self.state_interval = state_interval
        self.command_timeout = command_timeout

        # Data
        self.abort_flag = False
        
        self.response_last_update = None
        self.response = None # Store the last command response
        self.state_last_update = None
        self.state = {} # Store the last states

        self.tello_address = (tello_ip, self.TELLO_COMMAND_PORT)
        self.local_state_port = self.TELLO_STATE_PORT
        self.local_video_port = self.TELLO_VIDEO_PORT

        # Sockets
        
        # 1) Sockets for sending commands
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 2) Sockets for receiving stats
        self.socket_state = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 3) if needed: socket for video

        # Bind
        self.socket.bind((local_ip, local_port))
        self.socket_state.bind((local_ip, self.local_state_port))
        # Bind video socket if needed
       
        # Threads
        self.receive_ack_thread = threading.Thread(target=self._receive_ack)
        self.receive_ack_thread.daemon = True
        self.receive_ack_thread.start()
        self.receive_state_thread = threading.Thread(target=self._receive_state)
        self.receive_state_thread.daemon = True
        self.receive_state_thread.start()

    def __del__(self):
        ''' Clean objects and close all sockets before deleting this object.
        '''
        self.socket.close()
        self.socket_state.close()
        # Clsoe video socket is needed

    def _receive_ack(self):
        ''' Listen to responses from the Tello
        Runs as a thread, sets self.response to whatever the Tello last returned.
        '''
        while True:
            try:
                data, ip = self.socket.recvfrom(1518)
                if data:
                    self.response = data.decode(encoding="utf-8")
                self.response_last_update = datetime.datetime.now()
            except socket.error as error:
                print('Ack Socket Failed: {}'.format(error))

    def _receive_state(self):
        ''' Listen to the state from the Tello
        Runs as a thread, sets self.state to whatever the Tello last returned.
        '''
        while True:
            try:
                data, ip = self.socket_state.recvfrom(1024)
                if data:
                    data = data.decode(encoding="utf-8")
                    if ';' in data:
                        states = data.replace(';\r\n','').split(';')
                        #self.state = {s.split(':')[0]:s.split(':')[1] for s in states}
                        self.states = states
                
                self.state_last_update = datetime.datetime.now() # Put in last if
                time.sleep(self.state_interval)
            except socket.error as error:
                print('State Socket Failed: {}'.format(error))

    def send_command(self, command):
        ''' Send a command to the Tello and wait for a response
        :param command: Command to send.
        :return (str): Response from Tello.
        '''
        print('>> Send Command: {}'.format(command))

        # Prepare Timeout Timer
        self.abort_flag = False
        timer = threading.Timer(self.command_timeout, self.set_abort_flag)

        # Send Command
        self.socket.sendto(command.encode(encoding='utf-8'), self.tello_address)

        # Start Timer
        timer.start()
        while self.response is None:
            if self.abort_flag is True:
                break
        timer.cancel()

        # Check Response
        if self.response is None:
            command_response = 'none_response'
        else:
            command_response = self.response

        # Reset self.response and return the command_response 
        self.response = None

        return command_response

    def set_abort_flag(self):
        ''' Sets the self.abort_flag to True.
        Used by the timer in send_command to indicate 
        that a response timeout has occurred
        '''
        self.abort_flag = True

    # Tello Control Commands
    # ########################################

    def go(self):
        ''' Enter the SDK mode.
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.send_command('command')

    def start_stream(self):
        ''' Starts the video stream.
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.send_command('streamon')

    def stop_stream(self):
        ''' Stops the video stream.
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.send_command('streamoff')

    def start_mission_detect(self, mdirection=2):
        ''' Start the Mission Pad detection.
        Args:
            mdirection (int): The Mission Pad direction detection mode
                0 = Enable downward detection only
                1 = Enable forward detection only
                2 = Enable both forward and downward detection
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        response_mon = self.send_command('mon')
        response_mdirection = self.send_command('mdirection {}'.format(mdirection))

    def stop_mission_detect(self, mdirection=2):
        ''' Stops the Mission Pad detection.
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.send_command('moff')

    def set_speed(self, speed=10):
        ''' Set the speed of the Tello.
        Args:
            speed (int): Speed between 10 and 100.
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        speed = max(speed, 10)
        speed = min(speed, 100)
        return self.send_command('speed {}'.format(speed))

    # Tello Flight Commands
    # ########################################

    def takeoff(self):
        ''' Takeoff.
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.send_command('takeoff')

    def land(self):
        ''' Land.
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.send_command('land')

    def stop(self):
        ''' Stops the current maneuver and hovers in place.
        Note: works at any time.
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.send_command('stop')

    def emergency(self):
        ''' Stops all motores immediatly.
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.send_command('emergency')


    def rotate_cw(self, degrees):
        ''' Rotate clockwise.
        Args:
            degrees (int): Degrees to rotate, 1 to 360.
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.send_command('cw {}'.format(degrees))

    def rotate_ccw(self, degrees):
        ''' Rotate counter-clockwise
        Args:
            degrees (int): Degrees to rotate, 1 to 360.
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.send_command('ccw {}'.format(degrees))


    def flip(self, direction):
        ''' Flips in a direction.
        Args:
            direction (str): Direction to flip, 'l', 'r', 'f', 'b'.
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.send_command('flip {}'.format(direction))

    def move(self, direction, distance):
        ''' Moves in a direction for a distance.
        Args:
            direction (str): Direction to move, 'forward', 'back', 'right' or 'left'.
            distance (int|float): Distance to move in cm. (20-500cm)
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        distance = min(distance, 500)
        distance = max(distance, 20)
        return self.send_command('{} {}'.format(direction, distance))

    def move_backward(self, distance):
        ''' Moves backward for a distance.
        Args:
            distance (int|float): Distance to move in cm. (20-500cm)
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.move('back', distance)
    
    def move_forward(self, distance):
        ''' Moves forward for a distance.
        Args:
            distance (int|float): Distance to move in cm. (20-500cm)
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.move('forward', distance)

    def move_left(self, distance):
        ''' Moves left for a distance.
        Args:
            distance (int|float): Distance to move in cm. (20-500cm)
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.move('left', distance)

    def move_right(self, distance):
        ''' Moves right for a distance.
        Args:
            distance (int|float): Distance to move in cm. (20-500cm)
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.move('right', distance)

    def move_up(self, distance):
        ''' Moves up for a distance.
        Args:
            distance (int|float): Distance to move in cm. (20-500cm)
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.move('up', distance)

    def move_down(self, distance):
        ''' Moves down for a distance.
        Args:
            distance (int|float): Distance to move in cm. (20-500cm)
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.move('down', distance)

    def go_location(self, x, y, z, speed):
        ''' Fly to "x", "y" and "z" coordinates at "speed" (cm/s).
            Args:
            x (int): Value between -500 and 500
            y (int): Value between -500 and 500
            z (int): Value between -500 and 500
            speed (int/float): Speed between 10-100
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        '''
        return self.send_command('go {} {} {} {}'.format(x, y, z, speed))

    def curve(self, x1, y1, z1, x2, y2, z2, speed):
        ''' Fly at a curve according to the two given coordinates 
        at “speed” (cm/s). If the arc radius is not within a 
        range of 0.5-10 meters, it will respond with an error.
        Note: “x”, “y”, and “z” values can’t be set between 
        -20 – 20 simultaneously.
        Args:
            x1 (int): Value between -500 and 500
            y1 (int): Value between -500 and 500
            z1 (int): Value between -500 and 500
            x2 (int): Value between -500 and 500
            y2 (int): Value between -500 and 500
            z2 (int): Value between -500 and 500
            speed (int/float): Speed between 10-60
        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        Example:
        curve(100, 0, 50, 50, 50, 150, 20)
        '''
        return self.send_command('curve {} {} {} {} {} {} {}'.format(x1, y1, z1, x2, y2, z2, speed))
    

    # Tello State
    # ########################################

    def get_wifi(self):
        ''' Returns the Wi-Fi SNR.
        '''
        return self.send_command('wifi?')

    def get_sdk(self):
        ''' Returns the Tello SDK version.
        '''
        return self.send_command('sdk?')

    def get_serial_number(self):
        ''' Returns the Tello serial number.
        '''
        return self.send_command('sn?')

    def get_flight_time(self):
        ''' Returns the number of seconds elapsed during flight.
        Returns:
            int: Seconds elapsed during flight.
        '''
        flight_time = self.send_command('time?')
        return self.__try_to_int(flight_time)

    def get_battery(self):
        ''' Returns percent battery life remaining.
        Returns:
            int: Percent battery life remaining.
        '''
        battery = self.send_command('battery?')
        return self.__try_to_int(battery)

    def get_speed(self):
        ''' Returns the current speed.
        Returns:
            int: Current speed in KPH.
        '''
        speed = self.send_command('speed?')
        try:
            speed = round((float(speed) / 27.7778), 1)
        except:
            pass
        return speed

    def get_last_state(self):
        ''' Return the latest state as a dictionary.
        - mid  = the ID of the Mission Pad detected. If no Mission Pad is detected, a -1 message will be received instead.
        - x    = the x coordinate detected on the Mission Pad. If there is no Mission Pad, a 0 message will be received instead.
        - y    = the y coordinate detected on the Mission Pad. If there is no Mission Pad, a 0 message will be received instead.
        - z    = the z coordinate detected on the Mission Pad. If there is no Mission Pad, a 0 message will be received instead.
        - pitch  = the degree of the attitude pitch.
        - roll   = the degree of the attitude roll.
        - yaw    = the degree of the attitude yaw.
        - vgx    = the speed of x axis.
        - vgy    = the speed of the y axis.
        - vgz    = the speed of the z axis.
        - templ  = the lowest temperature in degree Celsius.
        - temph  = the highest temperature in degree Celsius.
        - tof    = the time of flight distance in cm.
        - h      = the height in cm.
        - bat    = the percentage of the current battery level.
        - baro   = the barometer measurement in cm.
        - time   = the amount of time the motor has been used.
        - agx    = the acceleration of the x axis.
        - agy    = the acceleration of the y axis.
        - agz    = the acceleration of the z axis.
        '''
        print(self.state_last_update)
        return self.state


    def get_height(self):
        '''Get via state'''
        pass

    def get_tof(self):
        '''Get via state'''
        pass

    def get_baro(self):
        '''Get via state'''
        pass

    def get_temperature(self):
        '''Get via state'''
        pass

    def get_attitude(self):
        '''Get via state'''
        pass

    def get_acceleration(self):
        '''Get via state'''
        pass

    # Helper
    # ########################################

    def __try_to_int(self, value):
        try:
            value = int(value)
        except:
            pass
        return value
