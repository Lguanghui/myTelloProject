from UIfile.SpeechRecognitionUI import Ui_SpeechRecognitionUI
import mySpeechRecognition
from PyQt5.QtCore import QTimer,pyqtSignal,QMutex,QThread,QWaitCondition,QObject
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QIcon,QCloseEvent
import threading

class speech_recognition_thread(QThread):
    '''语音识别线程'''
    send_speech_order_signal = pyqtSignal(bool, str)  # 发送识别出的命令
    send_LED_state = pyqtSignal(str)            #传递LED灯应该显示的状态，两个颜色交替闪烁表示正在录音，显示一个颜色表示正在执行命令
    def __init__(self):
        super(speech_recognition_thread, self).__init__()

        self.speechRecognition = mySpeechRecognition.mySpeechRecognition()

        self.daemon = True      #是否后台运行
        # self.paused = True      #暂停标志
        self.first_run = True   #标记

        self.threadLock = threading.Lock()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.run)

    def run(self):
        if self.first_run == True:
            self.first_run = False
            return
        else:
            self.threadLock.acquire()
            self.send_LED_state.emit('recording')       #正在录音
            self.speechRecognition.record()
            is_tellopy_order, order = self.speechRecognition.cognitive()  # 返回两个值，第一个用于确定是不是tellopy的以速度为参数的命令，第二个是以步长为参数的send型的命令
            self.send_LED_state.emit('executing')       #识别完成，准备执行命令

            # 当不是tellopy类型的命令时
            if is_tellopy_order == False:
                # 当命令有效时
                if order != 'False':
                    self.send_speech_order_signal.emit(is_tellopy_order, order)  # 触发信号，发送命令
                else:
                    self.threadLock.release()
                    return
            # 当是tellopy类型的命令时
            else:
                self.send_speech_order_signal.emit(is_tellopy_order, order)  # 触发信号，发送命令
            self.threadLock.release()


class mySpeechRecognition_UI(QWidget,Ui_SpeechRecognitionUI):
    '''拓展的语音识别窗口类'''
    send_order_signal = pyqtSignal(bool, str)  # 传递识别出的命令的信号，发给主窗口线程

    when_closed = pyqtSignal()  # 当窗口被关闭时发送信号
    def __init__(self):
        super(mySpeechRecognition_UI, self).__init__()
        self.setupUi(self)

        self.btn_speech_pause_start.clicked.connect(self.btn_speech_pause_start_clicked)        #开始/暂停按钮被按下时的触发动作

        self.speechRecognition = mySpeechRecognition.mySpeechRecognition()      #语音识别

        self.isSpeechRecognition_started = False     #标记语音识别是否开启

        self.speech_recognition_thread = speech_recognition_thread()        #语音识别线程
        self.speech_recognition_thread.daemon = True

        self.speech_recognition_thread.send_speech_order_signal.connect(self.send_order_to_Tello)       #发送命令到主进程

        self.speech_order_text_already_received_for_show = ''       #这个是要显示在子窗口下面的，已经发送给无人机的命令

        self.set_control_Keys()

        self.speech_recognition_thread.start()


    def btn_speech_pause_start_clicked(self):
        '''当开始/暂停按钮按下时'''
        #当未开启语音识别或处于暂停状态时时
        if self.isSpeechRecognition_started == False:
            self.isSpeechRecognition_started = True      #更新标记
            self.btn_speech_pause_start.setIcon(QIcon('../ico/pause_128px_1183436_easyicon.net.ico'))          #更新按钮图标
            self.btn_speech_pause_start.setText('关闭')

            # self.speech_recognition_thread.start()        #放到上面去了

            self.speech_recognition_thread.timer.start(3500)

        #当已经开启了语音识别时
        elif self.isSpeechRecognition_started == True:
            self.isSpeechRecognition_started= False
            self.btn_speech_pause_start.setIcon(QIcon('../ico/play_128px_1183440_easyicon.net.ico'))       #更新按钮图标
            self.btn_speech_pause_start.setText('开始')
            self.speech_recognition_thread.timer.stop()

    def send_order_to_Tello(self, is_tellopy_order, order):
        '''发送命令到主窗口线程'''
        if order == '':
            return
        print('发送成功')
        self.send_order_signal.emit(is_tellopy_order,order)

        #更新窗口下面的显示命令
        order_text = ''
        for key,val in self.controlKeys.items():
            if val == order:
                order_text = key
        self.speech_order_text_already_received_for_show ='\n' + '>>>' + ' ' + order_text
        self.sentOrders.append(self.speech_order_text_already_received_for_show)

    def closeEvent(self, a0: QCloseEvent) -> None:
        '''当窗口关闭时触发函数'''
        self.when_closed.emit()
        self.dockWidget.close()
        self.speech_recognition_thread.timer.stop()

    def set_control_Keys(self):
        self.controlKeys = {
            '起飞' : 'T',
            '降落' : 'R',
            '向左飞' : 'left',
            '向右飞' : 'right',
            '向前飞' : 'forward',
            '向后飞' : 'back',
            '向上飞' : 'up',
            '向下飞' : 'down',
            '顺时针旋转' : 'cw',
            '逆时针旋转' : 'ccw',
            '向前翻滚' : 'FF',
            '向后翻滚' : 'FB',
            '向左翻滚' : 'FL',
            '向右翻滚' : 'FR',
            '悬停' : 'stop',
            '速度设为' : 'speed',
            '玄霆' : 'stop',

            '向前' : 'W',
            '向后' : 'S',
            '向左' : 'A',
            '向右' : 'D',
            '向上' : 'U',
            '向下' : 'I',
            '停' : 'P',
            '在我手上降落' : 'H'
        }
