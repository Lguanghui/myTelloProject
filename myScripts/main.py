from PyQt5 import QtCore,QtGui
from PyQt5.QtCore import QTimer,QCoreApplication,Qt,pyqtSignal
from PyQt5.QtWidgets import QApplication,QMainWindow,QMessageBox,QLabel,QWidget
from PyQt5.QtGui import QImage,QPixmap,QIcon
from UIfile.MainWindow2 import Ui_MainWindow
from myTello import myTello
import mySpeechRecognition_UI,myGesture_UI
import sys,datetime
import cv2,threading
import TelloCV_ball_people
import AlphaPose_control

class mainWindow(QMainWindow,Ui_MainWindow):
    sent_move_distance_per_step = pyqtSignal(int)       #向子窗口发送当前设置的步长
    def __init__(self):
        super(mainWindow, self).__init__()
        self.setupUi(self)

        #子窗口
        self.speechRecognitionUI = mySpeechRecognition_UI.mySpeechRecognition_UI()      #语音识别窗口
        self.gestureUI = myGesture_UI.myGesture_UI()            #手势控制窗口

        # #加载中
        # self.loadingUI = myLoadingUI.myLoading_UI(self)
        # self.loadingUI_thread = loading_thread(self.loadingUI)
        # self.loadingUI_thread.setDaemon(True)
        # self.loadingUI_thread.start()

        self.iniUI()
        self.statusBar_init()       #初始化状态栏
        self.signal_slot_init() #初始化控件触发与反应函数
        self.Video_show_init()      #有关视频显示的初始化

        self.RMTT = False       #标记是否连接到RMTT拓展板

        self.date_fmt = '%Y-%m-%d_%H%M%S'       #日期格式


    def iniUI(self):
        '''有关控件的初始化'''
        self.power = False      #标记是否打开了"电源"，刚开始电源键是关闭的

        self.move_distance_per_step = 20         # 设置初始的每次给出移动命令后移动的步长
        self.speed = 25         #设置移动速度'

        #同步设置主界面速度与步长的初始值
        self.horizontalSlider_setSpeed.setValue(self.speed)
        self.horizontalSlider_set_MoveDistancePerStep.setValue(self.move_distance_per_step)


    def Video_show_init(self):
        '''有关视频显示的初始化'''
        self.is_show_initial_frame = True   #标记是否显示原始视频
        self.Tello_frame = None         #存储Tello传回来的图像

        self.timer_initial_video_show = QTimer(self)        #用于显示原始图像的倒计时
        self.timer_initial_video_show.timeout.connect(self.show_initial_frame)

        self.channel = 3

    def signal_slot_init(self):
        '''各信号的初始化'''
        self.pushButton_power.clicked.connect(self.powerBtn_clicked)       #当电源键被按下时
        self.pushButton_emergency_brake.clicked.connect(self.emergancyBtn_clicked)      #紧急制动按钮
        self.horizontalSlider_set_MoveDistancePerStep.valueChanged.connect(self.update_distance_per_step)   #每次移动步长的更新
        self.horizontalSlider_setSpeed.valueChanged.connect(self.update_speed)      #移动速度的更新

        #来自语音控制窗口相关的信号处理
        self.radioButton_speech_control.clicked.connect(self.open_speechRecognition_Window)     #当按下语音控制按钮时打开语音控制界面
        self.speechRecognitionUI.when_closed.connect(self.speechRecognitionUI_closed)       #当关闭语音控制界面时的触发函数
        self.speechRecognitionUI.send_order_signal.connect(self.speech_control)     #订阅来自子窗口返回的语音命令
        self.speechRecognitionUI.speech_recognition_thread.send_LED_state.connect(self.update_LED_state)        #订阅改变LED状态的消息

        #手势控制相关信号
        self.actiongestureControl.triggered.connect(self.open_gestureUI)        #打开手势控制窗口
        self.gestureUI.signal_send_order_to_Tello.connect(self.process_gesture_order)       #处理手势控制的发过来的命令
        self.sent_move_distance_per_step.connect(self.gestureUI.get_move_distance_per_step)     #主窗口步长变化时，更新子窗口的步长

        #目标跟踪相关信号
        self.actiongreenBall.triggered.connect(self.start_ball_track)       #开始球跟踪
        self.timer_ball_track = QTimer()
        self.timer_ball_track.timeout.connect(self.show_ball_track_img_and_control_tello)

        self.timer_face_track = QTimer()
        self.actionpeople.triggered.connect(self.start_face_track)  #开始人脸跟踪
        self.timer_face_track.timeout.connect(self.show_face_track_img_and_control_tello)

        #体态控制
        self.actionpostureControl.triggered.connect(self.start_pose_control)
        self.timer_pose_control = QTimer()
        self.timer_pose_control.timeout.connect(self.show_pose_control_result)
        self.AlphaPose_control = AlphaPose_control.AlphaPose_control()


        #关闭已打开功能
        self.actioncloseALL.triggered.connect(self.close_ALL_functions)

        # 拍照
        self.pushButton_take_photo.clicked.connect(self.take_picture)

        # 录像
        self.pushButton_video_record.clicked.connect(self.record_video)
        self.start_video_record = False



    def update_speed(self):
        '''速度设置更新函数'''
        self.speed = self.horizontalSlider_setSpeed.value()

    def update_distance_per_step(self):
        '''步长设置更新函数'''
        self.move_distance_per_step = self.horizontalSlider_set_MoveDistancePerStep.value()

        self.sent_move_distance_per_step.emit(self.move_distance_per_step)      #同时向子窗口发送现在的步长

    def power_pushed_reply(self):
        '''按下按钮时的弹窗，确保已经连接到Tello的WiFi'''
        reply = QMessageBox(QMessageBox.Warning,'warning','请先确保已连接到Tello的Wi-Fi')
        No = reply.addButton(self.tr('未连接'),QMessageBox.NoRole)
        Yes = reply.addButton(self.tr('已连接(无拓展板)'),QMessageBox.YesRole)
        RMTT = reply.addButton(self.tr('已连接(有拓展板)'),QMessageBox.YesRole)
        reply.exec_()
        if reply.clickedButton() == No:
            return False
        elif reply.clickedButton() == Yes:
            return True
        elif reply.clickedButton() == RMTT:
            self.RMTT = True
            return True

    def powerBtn_clicked(self):
        '''电源键按下的出发动作'''
        #若此时电源处于关闭状态
        if self.power == False:
            reply = self.power_pushed_reply()
            if not reply:
                return
            else:
                try:
                    self.Tello = myTello()  # 定义一个扩展tello实例，里面有更多的功能
                    self.about_tello_init()

                    self.connect_status_label_value.setText('连接成功')
                    self.power = True   #标记电源为打开状态

                    #更新电源图标
                    self.pushButton_power.setIcon(QIcon(QPixmap("../ico/power_button_442px_1301172_easyicon_red.net.png")))

                    self.timer_initial_video_show.start(100)

                except:
                    self.connect_status_label_value.setText('连接失败')

        #如果此时电源处于打开状态
        elif self.power == True:
            self.power = False
            if self.Tello != None:
                self.Tello.land()       #确保着陆
                self.timer_initial_video_show.stop()        #停止显示图像的计时
                self.timer_ball_track.stop()
                self.timer_face_track.stop()
                self.TelloCV.tracking = False
                self.label_show_video_frame.clear()     #清空显示
                self.Tello.sock.close()     #关闭socket，避免下次打开时冲突
                self.Tello.quit()       #关闭Tello的各线程
                del self.Tello      #释放Tello实例
            self.pushButton_power.setIcon(QIcon(QPixmap("../ico/power_button_442px_1301172_easyicon.net.png")))     #更新电源图标
            self.connect_status_label_value.setText('请按电源键尝试建立连接')        #更新状态栏

    def emergancyBtn_clicked(self):
        '''紧急刹车'''
        if self.power:
            self.Tello.send('emergency')
        else:
            self.status.showMessage('请先连接Tello',2000)

    def statusBar_init(self):
        '''状态栏的初始化函数'''
        self.status = self.statusBar()
        self.connect_status_label = QLabel('连接状态：')
        self.connect_status_label_value = QLabel('请按电源键尝试建立连接')
        self.status.addPermanentWidget(self.connect_status_label,stretch=0,)
        self.status.addPermanentWidget(self.connect_status_label_value,stretch=0)


    def about_tello_init(self):
        '''关于tello的初始化函数'''

        # self.Tello.send('command')  #直接进入手动控制模式
        #存储飞行状态数据
        self.prev_flight_data = None
        #订阅飞行状态数据更新，并显示到LCDNumber上
        self.Tello.subscribe(self.Tello.EVENT_FLIGHT_DATA,self.flight_data_handler)

        #订阅拍照后发回来的照片
        self.Tello.subscribe(self.Tello.EVENT_FILE_RECEIVED,self.handle_flight_received)

        self.TelloCV = TelloCV_ball_people.TelloCV(self.Tello)


    def __radioBtn_speechRecogniton_clicked(self):
        '''语音识别按钮被按下的反馈函数'''
        pass

    def keyPressEvent(self, event):
        '''键盘监听函数——当按下键时'''
        """
        W S A D:前 后 左 右
        Tab:起飞
        L:降落
        P:悬停
        H:在手上落下
        U I :向上 向下
        J K:顺时针旋转 逆时针旋转
        Z:前空翻
        X:后空翻
        C:左空翻
        V:右空翻
        """
        if self.power == True:
            #判断各事件
            if event.key() == Qt.Key_Tab:
                self.status.showMessage('起飞')
                # self.Tello.send('takeoff')
                self.Tello.takeoff()
            elif event.key() == Qt.Key_P:
                self.status.showMessage('悬停')
                self.Tello.forward(0)
                self.Tello.backward(0)
                self.Tello.left(0)
                self.Tello.right(0)
            elif event.key() == Qt.Key_H:
                self.status.showMessage('在手上着落')
                self.Tello.palm_land()
            elif event.key() == Qt.Key_W:
                self.status.showMessage('向前')
                self.Tello.forward(int(self.speed))
            elif event.key() == Qt.Key_A:
                self.status.showMessage('向左')
                self.Tello.left(int(self.speed))
            elif event.key() == Qt.Key_S:
                self.status.showMessage('向后')
                self.Tello.backward(int(self.speed))
            elif event.key() == Qt.Key_D:
                self.status.showMessage('向右')
                self.Tello.right(int(self.speed))
            elif event.key() == Qt.Key_U:
                self.status.showMessage('向上')
                self.Tello.up(self.speed)
            elif event.key() == Qt.Key_I:
                self.status.showMessage('向下')
                self.Tello.down(self.speed)
            elif event.key() == Qt.Key_J:
                self.status.showMessage('顺时针旋转')
                self.Tello.clockwise(self.speed)
            elif event.key() == Qt.Key_K:
                self.status.showMessage('逆时针旋转')
                self.Tello.counter_clockwise(self.speed)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        '''键盘监听函数——当按键释放时'''
        if self.power == True:
            if event.key()  == Qt.Key_W:
                self.Tello.forward(0)
                self.status.clearMessage()
            elif event.key() == Qt.Key_A:
                self.Tello.left(0)
                self.status.clearMessage()
            elif event.key() == Qt.Key_S:
                self.Tello.backward(0)
                self.status.clearMessage()
            elif event.key() == Qt.Key_D:
                self.Tello.right(0)
                self.status.clearMessage()
            elif event.key() == Qt.Key_U:
                self.status.clearMessage()
                self.Tello.up(0)
            elif event.key() == Qt.Key_I:
                self.status.clearMessage()
                self.Tello.down(0)
            elif event.key() == Qt.Key_J:
                self.status.clearMessage()
                self.Tello.clockwise(0)
            elif event.key() == Qt.Key_K:
                self.status.clearMessage()
                self.Tello.counter_clockwise(0)
            elif event.key() == Qt.Key_Z:
                self.status.showMessage('前空翻',1000)
                self.Tello.flip_forward()
                # self.Tello.send('flip f')
            elif event.key() == Qt.Key_X:
                self.status.showMessage('后空翻',1000)
                self.Tello.flip_back()
            elif event.key() == Qt.Key_C:
                self.status.showMessage('左空翻',1000)
                self.Tello.flip_left()
            elif event.key() == Qt.Key_V:
                self.status.showMessage('右空翻',1000)
                self.Tello.flip_right()
            elif event.key() == Qt.Key_L:
                self.status.showMessage('降落')
                self.Tello.land()
            elif event.key() == Qt.Key_G:
                self.status.showMessage('抛飞模式')
                self.Tello.send('throwfly')


    def flight_data_handler(self,event, sender, data):
        '''处理飞行状态数据的变化'''
        text = str(data)
        text_list = text.split('|')
        state_data = {}
        #如果状态数据发生变化了，更新数据
        if text != self.prev_flight_data:
            for item in text_list:
                key = ''
                value = ''
                flag = False
                for x in item:
                    if x == ' ':
                        continue
                    elif x == ':':
                        flag = True
                    else:
                        if not flag:
                            key = key + x
                        else:
                            value = value + x
                state_data[key] = value #添加到字典中
            self.update_lcdNumbers(state_data)
            # print(state_data)
            self.prev_flight_data = text

    def update_lcdNumbers(self,data:dict):
        '''更新LCD，显示飞行状态，包括剩余电量、'''
        for key in data:
            if key == 'ALT':
                self.lcdNumber_Height.display(data[key])
            elif key == 'SPD':
                self.lcdNumber_speed.display(data[key])
            elif key == 'BAT':
                #设置一下不同的电量对应不同的LCD颜色
                if int(data[key]) < 70 and int(data[key]) >= 30:
                    self.lcdNumber_battery.setStyleSheet("color:rgb(255, 212, 0);")   #黄色,中等电量
                elif int(data[key]) >= 70:
                    self.lcdNumber_battery.setStyleSheet("color:rgb(33, 255, 6);")  #绿色，充足电量
                else:
                    self.lcdNumber_battery.setStyleSheet("color:rgb(255, 0, 22);")  #红色，电量不足
                self.lcdNumber_battery.display(data[key])
            elif key == 'WIFI':
                self.lcdNumber_WiFi.display((data[key]))


    def open_speechRecognition_Window(self):
        '''语音控制按钮被按下的反应'''
        if self.power == False:
            QMessageBox.warning(self, 'warning', "请先按电源键建立连接", buttons=QMessageBox.Ok)
            self.radioButton_speech_control.setChecked(False)
            self.radioButton_keyBoard_control.setChecked(True)
            return
        self.speechRecognitionUI.show()     #显示子窗口
        self.speechRecognitionUI.dockWidget.setFloating(True)   #把浮动窗口浮动了

    def speechRecognitionUI_closed(self):
        '''语音窗口关闭时的反应'''
        self.radioButton_speech_control.setChecked(False)       #更新按钮状态
        self.radioButton_keyBoard_control.setChecked(True)

    def speech_control(self,is_tellopy_order,order):
        '''语音控制Tello'''
        print('Tello收到命令')
        if is_tellopy_order == False:
            _ = self.Tello.send(order)
        else:
            if order == 'T':
                # self.Tello.send('takeoff')
                self.Tello.takeoff()
                # self.Tello.send('command')
            elif order == 'H':
                self.Tello.palm_land()
            elif order == 'U':
               self.Tello.up(self.speed)
            elif order == 'L':
               self.Tello.left(self.speed)
            elif order == 'R':
                # self.Tello.send('land')
                self.Tello.land()
            elif order == 'S':
                self.Tello.backward(self.speed)
            elif order == 'D':
                self.Tello.right(self.speed)
            elif order == 'P':
                self.Tello.send('stop')
                self.Tello.forward(0)
                self.Tello.backward(0)
                self.Tello.left(0)
                self.Tello.right(0)
                self.Tello.up(0)
                self.Tello.down(0)
                self.Tello.clockwise(0)
                self.Tello.counter_clockwise(0)
            elif order == 'FF':
                self.Tello.flip_forward()
                # self.Tello.send('flip f')
            elif order == 'FS':
                self.Tello.flip_back()
                # self.Tello.send('flip b')
            elif order == 'FL':
                self.Tello.flip_left()
                # self.Tello.send('flip l')
            elif order == 'FR':
                self.Tello.flip_right()
                # self.Tello.send('flip r')

    def update_LED_state(self,state:str):
        '''更新顶部LED的状态'''
        if self.RMTT == True:
            if state == 'recording':
                self.Tello.send('EXT led br 1.5 255 0 255')
            elif state == 'executing':
                self.Tello.send('EXT led 65 105 225')
        else:
            return


    def open_gestureUI(self):
        '''打开手势控制窗口'''
        if self.power:
            self.gestureUI.show()
            self.gestureUI.dockWidget_HintHelp.setFloating(True)
            self.sent_move_distance_per_step.emit(self.move_distance_per_step)
        else:
            QMessageBox.warning(self, 'warning', "请先按电源键建立连接", buttons=QMessageBox.Ok)

    def process_gesture_order(self,result : str, order : str):
        '''处理手势控制命令'''
        #无效命令
        if order == 'land':
            self.Tello.land()
        elif order == 'landhand':
            self.Tello.palm_land()
        else:
            if order in ('cw 90','ccw 90','stop','takeoff','command'):
                #这些命令不需要得到步长
                self.Tello.send(order)
            else:
                self.Tello.send(order + ' ' + str(self.move_distance_per_step))


    def show_initial_frame(self):
        '''显示来自无人机的原始视频图像'''
        #只有当电源打开以及"显示无人机图像"标记为真的时候才会显示图像
        if self.is_show_initial_frame and self.power:
            #显示原始无人机相机画面
            self.img_w = self.label_show_video_frame.width()
            self.img_h = self.label_show_video_frame.height()
            self.Tello_frame = self.Tello.get_video_frame()

            #检查是不是还没有跳完帧或者是不是没有解码成功
            #假如解码失败
            if self.Tello_frame == 'decode error':
                self.status.showMessage('解码失败')
                return
            #解码成功但正在跳帧
            else:
                if self.Tello_frame == '':
                    return
                else:
                    if self.start_video_record:
                        frame_BGR = cv2.cvtColor(self.Tello_frame, cv2.COLOR_RGB2BGR)
                        self.Video_Writer.write(frame_BGR)
                    self.Tello_frame = cv2.resize(self.Tello_frame, (self.img_w, self.img_h))           #将图像大小设置为显示窗口的大小
                    pixmap = QPixmap.fromImage(QImage(self.Tello_frame.data,self.img_w,self.img_h,self.channel*self.img_w,QImage.Format_RGB888))
                    self.label_show_video_frame.setPixmap(pixmap)

    def start_ball_track(self):
        '''开始绿球跟踪'''
        if self.power:
            #关闭显示原始图像
            self.is_show_initial_frame = False
            self.timer_initial_video_show.stop()

            #关闭其他功能
            self.timer_face_track.stop()
            self.timer_pose_control.stop()


            #开始跟踪并显示跟踪图像
            self.status.showMessage('已开启绿球跟踪功能')
            self.TelloCV.tracking = True
            self.timer_ball_track.start(100)
        else:
            QMessageBox.warning(self, 'warning', "请先按电源键建立连接", buttons=QMessageBox.Ok)

    def show_ball_track_img_and_control_tello(self):
        '''跟踪绿球并显示跟踪图像'''
        self.img_w = self.label_show_video_frame.width()
        self.img_h = self.label_show_video_frame.height()
        frame = self.Tello.get_video_frame()
        if frame == '':
            return
        else:
            image = self.TelloCV.ball_process_frame(frame)
            image = cv2.resize(image, (self.img_w, self.img_h))           #将图像大小设置为显示窗口的大小
            pixmap = QPixmap.fromImage(QImage(image.data, self.img_w, self.img_h, 3 * self.img_w, QImage.Format_BGR888))
            self.label_show_video_frame.setPixmap(pixmap)

    def close_ALL_functions(self):
        '''关闭跟踪、手势控制、体态控制等功能，并开始显示原始图像'''
        #关闭
        self.timer_ball_track.stop()
        self.timer_face_track.stop()
        self.timer_pose_control.stop()

        #打开原始图像显示
        self.is_show_initial_frame = True
        self.timer_initial_video_show.start(100)

        self.TelloCV.tracking = False

    def start_face_track(self):
        '''开始人脸跟踪'''
        if self.power:
            #关闭显示原始图像
            self.is_show_initial_frame = False
            self.timer_initial_video_show.stop()

            #关闭其他功能
            self.timer_ball_track.stop()
            self.timer_pose_control.stop()

            #开始跟踪并显示跟踪图像
            self.TelloCV.tracking = True
            self.status.showMessage('已开启人脸跟踪功能')
            self.timer_face_track.start(100)
        else:
            QMessageBox.warning(self, 'warning', "请先按电源键建立连接", buttons=QMessageBox.Ok)

    def show_face_track_img_and_control_tello(self):
        '''跟踪人脸并显示跟踪图像'''
        self.img_w = self.label_show_video_frame.width()
        self.img_h = self.label_show_video_frame.height()
        frame = self.Tello.get_video_frame()
        if frame == '':
            return
        else:
            image = self.TelloCV.face_process_frame(frame)
            image = cv2.resize(image, (self.img_w, self.img_h))  # 将图像大小设置为显示窗口的大小
            pixmap = QPixmap.fromImage(QImage(image.data, self.img_w, self.img_h, 3 * self.img_w, QImage.Format_BGR888))
            self.label_show_video_frame.setPixmap(pixmap)

    def handle_flight_received(self, event, sender, data):
        """把拍照得到的照片存下来，存放在Pictures文件夹里"""
        path = '../Pictures/tello-%s.jpeg' % (
            datetime.datetime.now().strftime(self.date_fmt))
        with open(path, 'wb') as out_file:
            out_file.write(data)
        print('Saved photo to %s' % path)


    def take_picture(self):
        '''拍照'''
        if self.power:
            self.Tello.take_picture()
        else:
            QMessageBox.warning(self, 'warning', "请先按电源键建立连接", buttons=QMessageBox.Ok)

    def record_video(self):
        '''录像'''
        if self.power:
            if not self.start_video_record:
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                self.Video_Writer = cv2.VideoWriter('Tello-Video-%s.avi'% (datetime.datetime.now().strftime(self.date_fmt)),fourcc, 20.0, (self.Tello.width,self.Tello.height))
                self.start_video_record = True
                self.pushButton_video_record.setText('录像中')

            else:
                self.start_video_record = False
                self.pushButton_video_record.setText('')

                self.Video_Writer.release()

    def start_pose_control(self):
        '''开始体态控制'''
        if self.power:
            #关闭显示原始图像
            self.is_show_initial_frame = False
            self.timer_initial_video_show.stop()

            #关闭其他功能
            self.timer_ball_track.stop()
            self.timer_face_track.stop()
            self.TelloCV.tracking = False

            #开始体态控制
            self.status.showMessage('已开启体态控制功能')
            self.timer_pose_control.start(300)
            # 加载模型
            self.PoseModel = self.AlphaPose_control.downModel()

        else:
            QMessageBox.warning(self, 'warning', "请先按电源键建立连接", buttons=QMessageBox.Ok)

    def show_pose_control_result(self):
        '''显示体态控制图像'''

        self.img_w = self.label_show_video_frame.width()
        self.img_h = self.label_show_video_frame.height()

        img_path = '../AlphaPose/duan_alphapose/photo/'
        image = self.Tello.get_video_frame()
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        cv2.imwrite(img_path + 'frame.jpg', image)  # 保存图片

        # 载入图片
        img_names = self.AlphaPose_control.GetImage(self.AlphaPose_control.args)

        # alphapose处理
        point_results = self.AlphaPose_control.Alphapose(img_names, self.PoseModel)

        # 分析动作
        if point_results is not None:
            try:
                pose,result_img = self.AlphaPose_control.PoseFind(point_results)
                print(pose)
            except:
                self.AlphaPose_control.del_files(img_path)  # 删除文件夹内图片
                return
            result_img= cv2.resize(result_img, (self.img_w, self.img_h))  # 将图像大小设置为显示窗口的大小
            pixmap = QPixmap.fromImage(QImage(result_img.data, self.img_w, self.img_h, 3 * self.img_w, QImage.Format_BGR888))
            self.label_show_video_frame.setPixmap(pixmap)
            self.AlphaPose_control.del_files(img_path)  # 删除文件夹内图片
        else:
            self.AlphaPose_control.del_files(img_path)  # 删除文件夹内图片
            return




if __name__ == '__main__':
    QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    mainWin = mainWindow()
    mainWin.show()
    sys.exit(app.exec())