import time
import datetime
import os
import numpy
import av
import cv2
from ball_tracker import ball_tracker
from myTello import myTello
from cv2 import dnn
from face_tracker import face_tracker

class TelloCV(object):
    """
    TelloTracker builds keyboard controls on top of TelloPy as well
    as generating images from the video stream and enabling opencv support
    """

    def __init__(self,Tello:myTello):
        self.prev_flight_data = None
        self.record = False
        self.tracking = False
        self.keydown = False
        self.date_fmt = '%Y-%m-%d_%H%M%S'
        self.speed = 20
        self.speed2 = 10
        self.drone = Tello
        # self.init_drone()

        self.caffe_prototxt_path = "../Face_Distance/model/RFB-320.prototxt"
        self.caffe_model_path = "../Face_Distance/model/RFB-320.caffemodel"
        self.net = dnn.readNetFromCaffe(self.caffe_prototxt_path, self.caffe_model_path)

        # container for processing the packets into frames
        # self.container = av.open(self.drone.get_video_stream())
        # self.vid_stream = self.drone.container.streams.video[0]
        self.out_file = None
        self.out_stream = None
        self.out_name = None
        self.start_time = time.time()

        # tracking a color
        green_lower = (30, 50, 50)
        green_upper = (80, 255, 255)
        #red_lower = (0, 50, 50)
        # red_upper = (20, 255, 255)
        # blue_lower = (110, 50, 50)
        # upper_blue = (130, 255, 255)
        self.track_cmd = ""
        self.ball_tracker = ball_tracker(self.drone.height,
                               self.drone.width,
                               green_lower, green_upper)

        self.face_tracker = face_tracker(self.drone.height,
                               self.drone.width,)

    # def init_drone(self):
    #     """Connect, uneable streaming and subscribe to events"""
    #     # self.drone.log.set_level(2)
    #     # self.drone.connect()
    #     # self.drone.start_video()
    #     self.drone.subscribe(self.drone.EVENT_FLIGHT_DATA,
    #                          self.flight_data_handler)
    #     self.drone.subscribe(self.drone.EVENT_FILE_RECEIVED,
    #                          self.handle_flight_received)


    def ball_process_frame(self, frame):
        """convert frame to cv2 image and show"""
        image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        # image = self.write_hud(image)
        if self.record:
            self.record_vid(frame)

        xoff, yoff, zoff = self.ball_tracker.track(image)
        image = self.ball_tracker.draw_arrows(image)

        distance = 100
        cmd = ""
        if self.tracking:
            if xoff < -distance:
                cmd = "counter_clockwise"
            elif xoff > distance:
                cmd = "clockwise"
            elif yoff < -distance:
                cmd = "down"
            elif yoff > distance:
                cmd = "up"
            elif zoff < -25:
                cmd = "backward"
            elif zoff > 25:
                cmd = "forward"
            else:
                if self.track_cmd is not "":
                    getattr(self.drone, self.track_cmd)(0)
                    self.track_cmd = ""

        if cmd is not self.track_cmd:
            if cmd is not "":
                if cmd == "forward" or cmd == "backward":
                    print("track command forward:", cmd)
                    getattr(self.drone, cmd)(self.speed2)
                    self.track_cmd = cmd
                else:
                    print("track command other:", cmd)
                    getattr(self.drone, cmd)(self.speed)
                    self.track_cmd = cmd
        return image

    def face_process_frame(self, frame):
        """convert frame to cv2 image and show"""
        image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        # image = self.write_hud(image)
        # cv2.imshow("test",image)
        # cv2.waitKey(1)
        if self.record:
            self.record_vid(frame)

        xoff, yoff, zoff = self.face_tracker.track(image, self.net)
        # image = self.tracker_face.draw_arrows(image)
        #print(zoff)

        distance = 80
        cmd = ""
        # if count!=0:
        #     if self.track_cmd is not "":
        #         getattr(self.drone, self.track_cmd)(0)
        #         self.track_cmd = ""
        #     return image
        if self.tracking:
            if xoff < -distance:
                cmd = "counter_clockwise"
            elif xoff > distance:
                cmd = "clockwise"
            elif yoff < -distance:
                cmd = "down"
            elif yoff > distance:
                cmd = "up"
            elif zoff < -15:
                cmd = "backward"
                # self.backtimes = self.backtimes + 1
                # print("backtimes={}".format(self.backtimes))
            elif zoff > 15:
                cmd = "forward"
                # self.fortimes = self.fortimes + 1
                # print("fortimes={}".format(self.fortimes))
            else:
                if self.track_cmd is not "":
                    getattr(self.drone, self.track_cmd)(0)
                    self.track_cmd = ""

        if cmd is not self.track_cmd:
            if cmd is not "":
                if cmd == "forward" or cmd == "backward":
                    print("track command forward:", cmd)
                    getattr(self.drone, cmd)(self.speed2)
                    self.track_cmd = cmd
                else:
                    print("track command other:", cmd)
                    getattr(self.drone, cmd)(self.speed)
                    self.track_cmd = cmd

        return image


    def write_hud(self, frame):
        """Draw drone info, tracking and record on frame"""
        stats = self.prev_flight_data.split('|')
        stats.append("Tracking:" + str(self.tracking))
        if self.drone.zoom:
            stats.append("VID")
        else:
            stats.append("PIC")
        if self.record:
            diff = int(time.time() - self.start_time)
            mins, secs = divmod(diff, 60)
            stats.append("REC {:02d}:{:02d}".format(mins, secs))

        for idx, stat in enumerate(stats):
            text = stat.lstrip()
            cv2.putText(frame, text, (0, 30 + (idx * 30)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.0, (255, 0, 0), lineType=30)
        return frame

    def toggle_recording(self, speed):
        """Handle recording keypress, creates output stream and file"""
        if speed == 0:
            return
        self.record = not self.record

        if self.record:
            datename = [os.getenv('HOME'), datetime.datetime.now().strftime(self.date_fmt)]
            self.out_name = '{}/Pictures/tello-{}.mp4'.format(*datename)
            print("Outputting video to:", self.out_name)
            self.out_file = av.open(self.out_name, 'w')
            self.start_time = time.time()
            self.out_stream = self.out_file.add_stream(
                'mpeg4', self.drone.vid_stream.rate)
            self.out_stream.pix_fmt = 'yuv420p'
            self.out_stream.width = self.drone.vid_stream.width
            self.out_stream.height = self.drone.vid_stream.height

        if not self.record:
            print("Video saved to ", self.out_name)
            self.out_file.close()
            self.out_stream = None

    def record_vid(self, frame):
        """
        convert frames to packets and write to file
        """
        new_frame = av.VideoFrame(
            width=frame.width, height=frame.height, format=frame.format.name)
        for i in range(len(frame.planes)):
            new_frame.planes[i].update(frame.planes[i])
        pkt = None
        try:
            pkt = self.out_stream.encode(new_frame)
        except IOError as err:
            print("encoding failed: {0}".format(err))
        if pkt is not None:
            try:
                self.out_file.mux(pkt)
            except IOError:
                print('mux failed: ' + str(pkt))

    def take_picture(self, speed):
        """Tell drone to take picture, image sent to file handler"""
        if speed == 0:
            return
        self.drone.take_picture()

    def palm_land(self, speed):
        """Tell drone to land"""
        if speed == 0:
            return
        self.drone.palm_land()

    def toggle_tracking(self, speed):
        """ Handle tracking keypress"""
        if speed == 0:  # handle key up event
            return
        self.tracking = not self.tracking
        print("tracking:", self.tracking)
        return

    def toggle_zoom(self, speed):
        """
        In "video" mode the self.drone sends 1280x720 frames.
        In "photo" mode it sends 2592x1936 (952x720) frames.
        The video will always be centered in the window.
        In photo mode, if we keep the window at 1280x720 that gives us ~160px on
        each side for status information, which is ample.
        Video mode is harder because then we need to abandon the 16:9 display size
        if we want to put the HUD next to the video.
        """
        if speed == 0:
            return
        self.drone.set_video_mode(not self.drone.zoom)

    def flight_data_handler(self, event, sender, data):
        """Listener to flight data from the drone."""
        text = str(data)
        if self.prev_flight_data != text:
            self.prev_flight_data = text

    def handle_flight_received(self, event, sender, data):
        """Create a file in ~/Pictures/ to receive image from the drone"""
        path = '%s/Pictures/tello-%s.jpeg' % (
            os.getenv('HOME'),
            datetime.datetime.now().strftime(self.date_fmt))
        with open(path, 'wb') as out_file:
            out_file.write(data)
        print('Saved photo to %s' % path)
