from UIfile.SpeechRecognitionUI import Ui_SpeechRecognitionUI
import mySpeechRecognition
from PyQt5.QtCore import QTimer,pyqtSignal,QMutex,QThread,QWaitCondition,QObject
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap,QIcon,QCloseEvent
import time,threading


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

        self.timer = QTimer()
        self.timer.timeout.connect(self.run_record_once)


    def btn_speech_pause_start_clicked(self):
        '''当开始/暂停按钮按下时'''
        #当未开启语音识别或处于暂停状态时时
        if self.isSpeechRecognition_started == False:
            self.isSpeechRecognition_started = True      #更新标记
            self.btn_speech_pause_start.setIcon(QIcon('../ico/pause_128px_1183436_easyicon.net.ico'))          #更新按钮图标
            self.btn_speech_pause_start.setText('关闭')
            # self.speech_recognition_thread.start()
            self.timer.start(2000)

        #当已经开启了语音识别时
        elif self.isSpeechRecognition_started == True:
            self.isSpeechRecognition_started= False
            self.btn_speech_pause_start.setIcon(QIcon('../ico/play_128px_1183440_easyicon.net.ico'))       #更新按钮图标
            self.btn_speech_pause_start.setText('开始')
            self.timer.stop()


    def closeEvent(self, a0: QCloseEvent) -> None:
        '''当窗口关闭时触发函数'''
        self.when_closed.emit()
        self.dockWidget.close()
        self.timer.stop()

    def run_record_once(self):
        self.run()


    def run(self):
        self.speechRecognition.record()
        is_tellopy_order, order = self.speechRecognition.cognitive()  # 返回两个值，第一个用于确定是不是tellopy的以速度为参数的命令，第二个是以步长为参数的send型的命令

        # 当不是tellopy类型的命令时
        if is_tellopy_order == False:
            # 当命令有效时
            if order != 'False':
                print('发送成功')
                self.send_order_signal.emit(is_tellopy_order, order)  # 触发信号，发送命令
            else:
                return
        # 当是tellopy类型的命令时
        else:
            print('发送成功')
            self.send_order_signal.emit(is_tellopy_order, order)  # 触发信号，发送命令