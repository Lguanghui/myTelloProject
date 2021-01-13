import tellopy
import av
import cv2
import time
import numpy
import threading

class myTello(tellopy.Tello):
    def __init__(self):
        super(myTello, self).__init__()

        #建立连接
        self.connect()
        self.wait_for_connection(60.0)

        self.Tello_frame = ''  # 存储Tello传回来的图像
        try:
            self.container = av.open(self.get_video_stream())  # 解码视频流的容器
        except:
            self.Tello_frame = 'decode error'       #解码失败的返回值

        self.video_process_thread = threading.Thread(target=self.__Video_process)    #启动视频流处理线程
        # self.video_process_thread.setDaemon(True)

        self.vid_stream = self.container.streams.video[0]
        self.height = self.vid_stream.height
        self.width = self.vid_stream.width

        self.date_fmt = '%Y-%m-%d_%H%M%S'  # 日期格式

        self.video_process_thread.start()


    def send(self,message):
        """自己发送指令的函数"""
        try:
            self.sock.sendto(message.encode(), self.tello_addr)
            print("你输入的指令是: " + message)
            return True
        except Exception as e:
            print("传输错误: " + str(e))
            return False

    def get_video_frame(self):
        '''返回当前的Tello图像'''
        return self.Tello_frame

    def __Video_process(self):
        '''单独线程，一直解码并处理来自无人机的视频流'''
        frame_skip = 300        #跳过前300帧
        while True:
            for frame in self.container.decode(video=0):
                if 0 < frame_skip:
                    frame_skip = frame_skip - 1
                    continue
                start_time = time.time()
                # self.Tello_frame = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                self.Tello_frame =numpy.array(frame.to_image())     #不需要色彩空间转换
                cv2.waitKey(20)
                if frame.time_base < 1.0 / 60:
                    time_base = 1.0 / 60
                else:
                    time_base = frame.time_base
                frame_skip = int((time.time() - start_time) / time_base)
