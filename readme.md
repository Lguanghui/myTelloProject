# Tello智能信息处理平台

*若你的浏览器无法加载本页面中的图片，请将VPN软件设置为全局模式*

:warning::warning::warning::warning::warning::warning: WARNING :warning::warning::warning::warning::warning::warning:

由于大型模型文件无法上传到 GitHub，因此从 GitHub 下载的项目无法使用体态控制等功能（基础功能如拍照录像等不受影响）。如在编译过程中遇到因找不到模型而失败的问题，请将相关代码注释掉

:warning::warning::warning::warning::warning::warning: WARNING :warning::warning::warning::warning::warning::warning:

## 联系我们
Mail：liangguanghui@buaa.edu.cn

## 介绍
1. 此平台基于python语言开发，可用于控制大疆公司的Tello系列无人机，并利用无人机的摄像头、红外等传感器完成一系列视觉功能，包括：目标检测与跟踪（绿色小球与人脸）、手势控制、体态控制等。
也可控制Tello进行拍照、录像，以及做出一些花式动作。
   
<div align=center>
    <img src="https://github.com/Lguanghui/myTelloProject/raw/master/image/mainWin.png"/>
</div>
   
2. 项目文件中，`myScripts`文件夹涵盖了主要的代码文件，包括主程序`main.py`。`UIfile`文件夹涵盖了程序的各窗口初始代码（从`.ui`类型文件转化而来）。
    `ico`文件夹包含了各窗口界面用到的图标。

## 环境和移植方法

开发环境为python + QtDesigner，主要在macOS下进行开发，可移植到其他系统上。

使用到的python库包括：pyQt5,ffmpeg,av,pytorch,baidu-aip,opencv-python等。ffmpeg和av是用来解码视频的

运行我们的代码时，请先确保计算机连接到Tello的Wi-Fi，然后运行main.py。当在终端中使用命令
```shell
python3 main.py
```
直接运行时，可能会出现错误。这时请将`myScripts`文件夹中的内容移动到整个项目的根目录中，再尝试上面的命令。
当直接在PyCharm等IDE中运行时，一般不需要上述操作。

## 功能

### 无人机控制
通过此平台控制Tello无人机的方式有两种，一种是默认的键盘控制，第二种是语音控制。

#### 键盘控制

键盘控制一直处于开启状态。每个键盘键位对应的功能如下：

* `tab:`起飞
* `L/P/G/H:`降落/悬停/抛飞/手上降落
* `W/A/S/D:`向前/左/后/右
* `U/I:`向上/下
* `J/K:`顺/逆时针旋转
* `Z/X/C/V:`前/后/左/右空翻

#### 语音控制

使用语音控制时，还需再将网线连接到计算机上。这是因为，本项目中的语音识别功能使用了百度提供的语音识别API，使用时需联网获取识别结果。

**注意：当你使用语音控制功能时，请在百度智能云上申请一下语音识别技术API，并更改`myScripts/mySpeechRecognition.py`中的APP_ID、API_KEY、SECRET_KEY（我们的已经过期啦）**

有效语音指令如下：

* 起飞；
* 降落；
* 悬停；
* 向前/后/左/右/上/下飞x厘米（x=20~500)；
* 顺时针旋转x度（x=1~360)；
* 向前/后/左/右翻滚；
* 速度设为x厘米每秒（x=10~100)；
* 向前/后/左/右；(不建议，此指令会让无人机一直朝某个方向飞，直到得到“停”指令）；
* 停；

### 视觉功能

#### 人脸跟踪

在菜单栏开启人脸跟踪功能后，无人机会搜寻人脸目标（最好只有一个），然后靠近人脸并保持在一定的安全距离内，且能够随着人脸的移动而移动。

<div align=center>
    <img src="https://github.com/Lguanghui/myTelloProject/raw/master/image/face_track.png"/>
    <br>
    <p style="display: inline-block;border-bottom: 1px solid; color: rgba(145,145,128,0.89)">face_track</p>
</div>

#### 绿球跟踪

与人脸跟踪类似，开启此功能后，无人机能够跟随绿色小球（球不要太小）。

<div align=center>
    <img src="https://github.com/Lguanghui/myTelloProject/raw/master/image/ball_track.png"/>
    <br>
    <p>ball_track</p>
</div>

#### 手势控制

开启此功能后，会显示一个子窗口，并显示计算机摄像头视频流。识别出比划的手势后，无人机会做出相应的动作。为了避免连续识别并发出指令，我们设置了每次跳过一定帧数后再识别一次。

支持的手势如下：
* `双手合十：`启动；
* `大拇指向上：`起飞；
* `大拇指向下：`降落；
* `一/二/三/四/五/六：`向上/下/左/右/前/后飞x厘米；
* `七/八：`顺/逆时针旋转90度；
* `九：`悬停；

飞行速度与飞行步长与主界面中对滑块设置的值有关

与语音识别类似，我们的手势识别功能使用了百度提供的手势识别API，你需要更改`myScripts/myGesture.py`中的APP_ID、API_KEY、SECRET_KEY。

<div align=center>
    <img src="https://github.com/Lguanghui/myTelloProject/raw/master/image/gesture.png"/>
    <br>
    <p>ball_track</p>
</div>

#### 体态控制

我们加入这个功能的初衷是想通过人体的姿势来控制无人机。

<div align=center>
    <img src="https://github.com/Lguanghui/myTelloProject/raw/master/image/pose.png"/>
    <br>
    <p>posture</p>
</div>

但是我们没有时间去训练自己的轻量检测模型。我们寻找到了`AlphaPose`这个开源姿势检测库，并选择其中运行速度较快的一个模型融合进我们的平台中。
尽管如此，检测速度还是无法达到我们的预期。而且由于整个项目是在我的macOS系统上构建，无法使用CUDA加速计算，因此整体检测速度非常慢。

为了避免危险情况发生，我并没有为体态检测结果设置相应的无人机指令，只将体态检测结果显示在主界面上。

如果你感兴趣的话，可以在具备英伟达显卡和CUDA环境的计算机上重新将此功能构建一下，添加每种检测结果对应的无人机指令，主要代码在`myScripts/AlphaPose_control.py`中。

**注意：由于GitHub上传文件大小的限制，AlphaPose的模型文件我们无法上传至本仓库。假如你有需要的话，可以从下面的`AlphaPose`仓库里下载文件，或者联系我们获取。**

### 拍照和录像

在主界面点击拍照后，会将当前无人机原始画面以jpeg格式存储到本地。

点击录像后，程序开始将无人机原始画面以avi格式编码为视频流，再次点击录像按钮后，停止录像并将视频保存到本地。

## 不足

由于项目中使用了av库，我们无法在windows以及macOS系统上通过pyinstaller生成exe等可执行文件。

## 感谢

* [AlphaPose](https://github.com/MVIG-SJTU/AlphaPose)
