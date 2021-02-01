# Tello智能信息处理平台
## 介绍
1. 此平台基于python语言开发，可用于控制大疆公司的Tello系列无人机，并利用无人机的摄像头、红外等传感器完成一系列视觉功能，包括：目标检测与跟踪（绿色小球与人脸）、手势控制、体态控制等。
也可控制Tello进行拍照、录像，以及做出一些花式动作。
   
2. 项目文件中，`myScripts`文件夹涵盖了主要的代码文件，包括主程序`main.py`。`UIfile`文件夹涵盖了程序的各窗口初始代码（从`.ui`类型文件转化而来）。
    `ico`文件夹包含了各窗口界面用到的图标。

## 环境和移植方法

开发环境为python + QtDesigner，主要在macOS下进行开发，可移植到其他系统上。

使用到的python库包括：pyQt5,av,pytorch,baidu-aip,opencv-python等。

运行我们的代码时，请先确保计算机连接到Tello的Wi-Fi，然后运行main.py。当使用在终端中使用命令
```shell
python3 main.py
```
直接运行时，可能会出现错误。这时请将`myScripts`文件夹中的内容移动到整个项目的根目录中，再尝试上面的命令。
当直接在PyCharm等IDE中运行时，一般不需要上述操作。

## 功能

### 无人机控制
通过此平台控制Tello无人机的方式有两种，一种是默认的键盘控制，第二种是语音控制。键盘控制一直处于开启状态。每个键盘键位对应的
功能请参考`User_Guide.pdf`。

使用语音控制时，还需再将网线连接到计算机上（因为Tello Wi-Fi不能上网）。

### 视觉功能

#### 人脸跟踪

在菜单栏开启人脸跟踪功能后，无人机会搜寻人脸目标（最好只有一个），然后靠近人脸并保持在一定的安全距离内，且能够随着人脸的移动而移动。

<div align=center>
<img src="https://github.com/Lguanghui/myTelloProject/tree/master/image/face_track.png"/>
</div>



#### 绿球跟踪

与人脸跟踪类似，开启此功能后，无人机能够跟随绿色小球（不要太小）。

#### 

## 不足

由于项目中使用了av库，我们无法在windows以及macOS系统上通过pyinstaller生成exe等可执行文件。

## 鸣谢