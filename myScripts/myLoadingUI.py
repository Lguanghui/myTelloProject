from UIfile.loadingUI import Ui_Loading_win
from PyQt5.QtWidgets import QWidget,QMainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMovie

class myLoading_UI(QWidget,Ui_Loading_win):
    def __init__(self,mainWindow : QMainWindow):
        super(myLoading_UI, self).__init__()
        self.setupUi(self)

        # 获取主窗口的坐标
        self.m_winX = mainWindow.x()
        self.m_winY = mainWindow.y()

        self.m_win_w = mainWindow.width()
        self.m_win_h = mainWindow.height()

        self.move((self.m_winX + self.m_win_w)/2, self.m_winY + self.m_win_h/2)  # 移动加载界面到主窗口的中心
        # 设置窗口无边框|对话框|置顶模式
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # 设置背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 加载动画
        self.loading_gif = QMovie('../ico/5-160914192R6-51.gif')
        self.label.setMovie(self.loading_gif)
        self.loading_gif.start()