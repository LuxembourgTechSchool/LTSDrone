from ltsdrone import LTSDrone
import os
from time import sleep

def drone_print(response):
    print('[Drone] {}'.format(response))

def report(message):
    ''' Only work on MacOS for now.
    '''
    drone_print(message)
    if os.name == 'posix':
        os.system('say ' + message)

def demo(drone):
    report('Demo is starting.')

    delay = 5

    r = drone.takeoff()
    drone_print(r)
    sleep(delay)

    r = drone.move_up(50)
    drone_print(r)
    sleep(delay)

    # Square without rotation

    r = drone.move_forward(100)
    drone_print(r)
    sleep(delay)

    r = drone.move_left(100)
    drone_print(r)
    sleep(delay)

    r = drone.move_backward(100)
    drone_print(r)
    sleep(delay)

    r = drone.move_right(100)
    drone_print(r)
    sleep(delay)

    # Square with rotation

    n = 4
    for i in range(n):
        print('Debug: {}/{}'.format(i+1, n))

        r = drone.move_forward(100)
        drone_print(r)
        sleep(delay)

        r = drone.rotate_ccw(90)
        drone_print(r)
        sleep(delay)

    # Land
    
    r = drone.land()
    drone_print(r)


def run():
    report('Running Demo Square.')

    drone = LTSDrone()

    report('Type ENTER to command the drone...')
    input()
    report('Entering command mode...')

    response = drone.go()
    drone_print(response)

    report('Type ENTER to takeoff and start the demo...')
    input()

    demo(drone)

    report('Demo Completed.')


if __name__ == '__main__':
    run()