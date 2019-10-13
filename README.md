# LTS Drone

Wrapper class to easily control the Ryze Tello Drone.

# Requirements

- Python 3

No other dependencies.

# Usage

    from ltsdrone import LTSDrone
    drone = LTSDrone()
    drone.go()
    drone.takeoff()

# Video

Video feed is not yet handled by the class.

To view the feed, start the stream using `drone.start_stream()` and then listen to the tello IP:Port using `ffmpeg` package for example:

    ffmpeg -i udp://192.168.10.1:11111 -f sdl "Tello Live Video Stream"

Or:

    ffplay -probesize 32 -i udp://192.168.10.1:11111 -framerate 30