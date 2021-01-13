import cv2
import numpy as np
class ball_tracker:
    """
    A basic color tracker, it will look for colors in a range and
    create an x and y offset valuefrom the midpoint
    """

    def __init__(self, height, width, color_lower, color_upper):
        self.color_lower = color_lower
        self.color_upper = color_upper
        self.midx = int(width / 2)
        self.midy = int(height / 2)
        self.midz = 50
        self.xoffset = 0
        self.yoffset = 0
        self.zoffset = 0.0
        self.knownWidth = 3
        self.focalLength = 500
        self.kernel = np.ones((5, 5), np.uint8)  # 卷积核

    def draw_arrows(self, frame):
        """Show the direction vector output in the cv2 window"""
        #cv2.putText(frame,"Color:", (0, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, 255, thickness=2)
        cv2.arrowedLine(frame, (self.midx, self.midy),
                        (self.midx + self.xoffset, self.midy - self.yoffset),
                        (0, 0, 255), 5)
        return frame
    def find_circle(self,frame):

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 转换为灰色通道
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  # 转换为HSV空间
        #  消除噪声
        mask = cv2.inRange(hsv,self.color_lower, self.color_upper)  # 设定掩膜取值范围
        opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)  # 形态学开运算
        #bila = cv2.bilateralFilter(mask, 10, 200, 200)  # 双边滤波消除噪声
        edges = cv2.Canny(opening, 50, 100)  # 边缘识别
        circles = cv2.HoughCircles(
            edges, cv2.HOUGH_GRADIENT, 1, 100, param1=100, param2=10, minRadius=10, maxRadius=100)
        if circles is not None:  # 如果识别出圆
            for circle in circles[0]:
                x = int(circle[0])
                y = int(circle[1])
                radius = int(circle[2])
                center = (x, y)
                return x,y,radius
        else:
            return 0,0,0

    def track(self, frame):
        x,y,radius=self.find_circle(frame)
        center=(x,y)
        if radius > 10:
            z = self.distance_to_camera(radius)
            print("distance={}".format(z))
            # draw the circle and centroid on the frame,
            # then update the list of tracked points
            cv2.circle(frame, (int(x), int(y)), int(radius),
                       (0, 255, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)

            self.xoffset = int(center[0] - self.midx)
            self.yoffset = int(self.midy - center[1])
            self.zoffset = z - self.midz
            print("zdistance{}".format(self.zoffset))
        else:
            self.xoffset = 0
            self.yoffset = 0
            self.zoffset = 0.0
        return self.xoffset, self.yoffset, self.zoffset

    def distance_to_camera(self, perWidth):
        """
        knownWidth：知道的目标宽度 厘米
        focalLength：摄像头焦距
        perWidth：检测框宽度  像素

        #焦距1.98mm 球的半径，球的实际半径"""
        return (self.knownWidth * self.focalLength) / perWidth
