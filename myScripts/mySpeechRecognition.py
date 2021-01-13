import pyaudio  # 导入pyAudio的源代码文件，我们下面要用到，不用到就不用导入啦
import wave
from aip import AipSpeech

class mySpeechRecognition:
    def __init__(self):
        #初始化
        self.APP_ID = '23503942'  # 新建AiPSpeech
        self.API_KEY = 'ac19dxg6NCm3D00rreITDNSD'
        self.SECRET_KEY = 'sg43RzlyAq0tGtVYATfsEU9I0hAOBTYE'
        self.client = AipSpeech(self.APP_ID, self.API_KEY, self.SECRET_KEY)
        self.setControlKEYS()
        self.order = ''

    def setControlKEYS(self):
        """将识别出的识别出的指令转化为英文指令"""
        # 顺逆时针旋转还需要再二次判断一下
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

    def record(self):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16  # 量化位数
        CHANNELS = 1  # 采样管道数
        RATE = 16000  # 采样率
        RECORD_SECONDS = 3      #录音时间
        WAVE_OUTPUT_FILENAME = "../output.wav"  # 文件保存的名称
        p = pyaudio.PyAudio()  # 创建PyAudio的实例对象
        stream = p.open(format=FORMAT,  # 调用PyAudio实例对象的open方法创建流Stream
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
        frames = []  # 存储所有读取到的数据
        print('* 开始录音 >>>')  # 打印开始录音
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)  # 根据需求，调用Stream的write或者read方法
            frames.append(data)
        print('* 结束录音 >>>')  # 打印结束录音
        stream.close()  # 调用Stream的close方法，关闭流
        p.terminate()  # 调用pyaudio.PyAudio.terminate() 关闭会话
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')  # 写入wav文件里面
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

    def cognitive(self):
        def get_file_content(filePath):
            with open(filePath, 'rb') as fp:
                return fp.read()

        result = self.client.asr(get_file_content('../output.wav'), 'wav', 16000, {
            'dev_pid': 1537,  # 识别本地文件
        })
        result_text = result["result"][0]

        print("you said: " + result_text)

        return self.getOrder(result_text)

    def getOrder(self,result : str):
        """
        得到给无人机发送的指令
        :param result_text: 原始语音识别结果
        :return: 无人机命令
        """
        result_text = ''
        for item in result:
            if item in ('厘', '度', '米', '，', '。', '秒', '每'):  # 过滤一些关键字
                continue
            else:
                result_text = result_text + item
        #判断是否是tellopy命令
        if result_text in ('向前','向后','向左','向右','向上','向下','停','起飞','降落','向前翻滚','向后翻滚','向左翻滚','向右翻滚'):
            isTellopy_order = True
            self.order = self.controlKeys[result_text]
            return  isTellopy_order,self.order
        else:
            isTellopy_order = False
            command = ''
            value = ''
            for item in result_text:
                # if item in ('厘' , '度','米','，','。','秒','每'):     #过滤一些关键字
                #     continue
                if item.isalpha():
                    command = command + item
                else:
                    value = value + item
            if command in self.controlKeys.keys():
                #命令有效
                command = self.controlKeys[command]         #得到汉语对应的英文命令
            else:
                #命令无效
                self.order = 'False'
                return isTellopy_order,self.order
            self.order = command + ' ' + value
            return isTellopy_order,self.order


if __name__ == '__main__':
    sr = mySpeechRecognition()
    while True:
        sr.record()
        isTellopy_order, result = sr.cognitive()
        print(isTellopy_order,result)
