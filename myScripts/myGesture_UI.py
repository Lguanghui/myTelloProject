from UIfile.gestureUI import Ui_gestureUI
from PyQt5.QtCore import QTimer,pyqtSignal,QMutex,QThread,QWaitCondition,QObject
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QIcon,QCloseEvent
from PyQt5.QtGui import QImage,QPixmap
import myGesture
import cv2

class myGesture_UI(QWidget,Ui_gestureUI):
    signal_send_order_to_Tello = pyqtSignal(str,str)
    def __init__(self):
        super(myGesture_UI, self).__init__()
        self.setupUi(self)

        self.dockWidget_HintHelp.setFloating(False)

        self.channel = 3

        self.timer = QTimer(self)       #定时器
        self.timer.timeout.connect(self.show_and_get_order)

        self.cap = cv2.VideoCapture()  # 读取电脑摄像头图像

        self.pushButton_start_and_close.clicked.connect(self.start_or_stop)       #开始按钮触发动作

        self.myGesture = myGesture.myGesture()      #手势识别

        self.frame_skip = 20        #每次跳过这么多帧数才识别一次
        self.frame_skiped = self.frame_skip   #已经跳过的帧数，每隔一段时间清零，初始应该是最大值

        # 进度条
        self.progressBar.setMaximum(self.frame_skip)
        self.progressBar.setValue(self.frame_skip)

        #显示已经发送的命令
        self.order_already_sent = ''

        self.move_distance_per_step = 20        #先设置一个初始值，但它会随主窗口步长的调整而变化


    def start_or_stop(self):
        '''显示电脑摄像头图像并开始识别'''
        # 如果此时未打开手势控制
        if self.timer.isActive() == False:
            self.cap.open(0)
            self.pushButton_start_and_close.setText('关闭手势控制')
            self.timer.start(100)        #计时开始

        # 如果此时已经打开了手势控制
        else:
            self.timer.stop()       #计时结束
            self.cap.release()      #释放
            self.label_PC_Cam_frame_show.clear()        #清空显示
            self.pushButton_start_and_close.setText('开始手势控制')

    def show_and_get_order(self):
        self.img_w = self.label_PC_Cam_frame_show.width()
        self.img_h = self.label_PC_Cam_frame_show.height()
        ret,frame = self.cap.read()
        if ret == True:
            frame = cv2.resize(frame, (self.img_w, self.img_h))  # 要保证要显示的图像大小和显示窗口大小一致
            # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pixmap = QPixmap.fromImage(QImage(frame.data,self.img_w,self.img_h,self.channel*self.img_w,QImage.Format_BGR888))
            self.label_PC_Cam_frame_show.setPixmap(pixmap)

            if self.frame_skiped >= self.frame_skip:
                self.progressBar.setValue(self.frame_skip)
                self.label_is_ready.setText('就绪')
                result,order = self.myGesture.getOrder(frame)   #得到识别结果和命令

                #假如命令有效
                if order != '':
                    self.signal_send_order_to_Tello.emit(result,order)     #发送命令
                    self.frame_skiped = 0           #更新已经跳过的帧数
                    self.progressBar.setValue(self.frame_skiped)
                    self.label_is_ready.setText('跳帧中')
                    self.update_textBrower(result,order)
                    return
                else:
                    return

            else:
                self.frame_skiped += 1
                self.progressBar.setValue(self.frame_skiped)
                return

    def closeEvent(self, a0: QCloseEvent) -> None:
        '''窗口关闭时触发的动作'''
        self.dockWidget_HintHelp.close()
        self.timer.stop()
        self.cap.release()  # 释放

    def get_move_distance_per_step(self,distance : int):
        '''得到设置的步长'''
        self.move_distance_per_step = distance

    def update_textBrower(self,result,order):
        '''更新显示已经发送的命令'''
        if order in ('cw 90','ccw 90','stop','takeoff','command','land','landhand'):
            #这些不需要得到步长
            self.order_already_sent = '\n' + '>>> ' + result

        else:
            # 这些需要得到步长
            self.order_already_sent = '\n' + '>>> ' + result + ' ' +  str(self.move_distance_per_step) + ' ' + '厘米'
        self.textBrowser_order_already_sent.append(self.order_already_sent)

        #更新显示
        # self.textBrowser_order_already_sent.setText(self.order_already_sent)