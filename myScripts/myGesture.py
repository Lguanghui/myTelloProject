from aip import AipBodyAnalysis
from cv2 import imencode
class myGesture:
    """
    实现手势识别，缺点是只能用open函数读取本地照片
    """
    # APPID AK SK
    __APP_ID = '23524317'
    __API_KEY = 'gezpEkWBPsa63SE7gRf4Lzlv'
    __SECRET_KEY = '7urulBhtACXBsnq5YWWNwt4m15mLrj4V'

    def __init__(self):
        self.__client = AipBodyAnalysis(self.__APP_ID, self.__API_KEY, self.__SECRET_KEY)

    def __recognition(self,image):
        img_str = imencode('.jpg', image)[1].tobytes()
        imagesResult = self.__client.gesture(img_str)
        return imagesResult
    def __getResult(self,images):
        result = ''     #空代表无效命令
        #用try解决报错问题
        try:
            if len(images['result']) == 0:
                return result
            else:
                if images['result'][0]['classname'] == 'Prayer':
                    result = "开始"
                elif images['result'][0]['classname'] == 'Thumb_up':
                    result = "起飞"
                elif images['result'][0]['classname'] == 'Thumb_down':
                    result = "降落"
                elif images['result'][0]['classname'] == 'One':
                    result = "向上"
                elif images['result'][0]['classname'] == 'Two':
                    result = "向下"
                elif images['result'][0]['classname'] == 'Three':
                    result = "向左"
                elif images['result'][0]['classname'] == 'Four':
                    result = "向右"
                elif images['result'][0]['classname'] == 'Five':
                    result = "向前"
                elif images['result'][0]['classname'] == 'Six':
                    result = "向后"
                elif images['result'][0]['classname'] == 'Seven':
                    result = "顺时针旋转90度"
                elif images['result'][0]['classname'] == 'Eight':
                    result = "逆时针旋转90度"
                elif images['result'][0]['classname'] == 'Nine':
                    result = "悬停"
                elif images['result'][0]['classname'] == 'Fist':
                    result = "在手上降落"
                else:
                    result = ''
                return result
        except:
            return ''

    def getOrder(self,images):
        """
        返回指令含义以及发送给无人机的指令，假如result或command为空字符串的话，代表无效指令
        :param images: 原始图像帧
        :return: (result,command)
        """
        imagesResult = self.__recognition(images)
        result = self.__getResult(imagesResult)
        command = self.__action(result)

        return (result,command)


    def __action(self,result):
        """如果返回为空字符串的话代表无效指令"""
        command = ''
        if result == "开始":
            command = "command"
        elif result == "起飞":
            command = "takeoff"
        elif result == "降落":
            command = "land"
        elif result == "向上":
            command = "up"
        elif result == "向下":
            command = "down"
        elif result == "向左":
            command = "left"
        elif result == "向右":
            command = "right"
        elif result == "向前":
            command = "forward"
        elif result == "向后":
            command = "back"
        elif result == "顺时针旋转90度":
            command = "cw 90"
        elif result == "逆时针旋转90度":
            command = "ccw 90"
        elif result == "悬停":
            command = "stop"

        elif result == '':
            command = ''
        elif result == '在手上降落':
            command = 'landhand'

        return command