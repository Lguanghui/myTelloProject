import os
import json
import math
import cv2

img_path = 'D:\\APPes\\Alphapose\\AlphaPose\\duan_alphapose\\photo\\'
posePoint_Path = 'D:\\APPes\\Alphapose\\AlphaPose\\duan_alphapose\\'
# python D:\APPes\Alphapose\AlphaPose\demo.py --indir 'D:\APPes\Alphapose\AlphaPose\tello_alphapose_duan\posephoto_duan\\' --outdir 'D:\\APPes\Alphapose\\AlphaPose\\tello_alphapose_duan\\' --sp
# python tello_alphapose_duan.py

#运行alphapose demo，提取人体关键点
command = 'python D:\APPes\Alphapose\AlphaPose\demo.py' +  ' --indir ' + img_path + ' --outdir ' + posePoint_Path + ' --sp'
os.system(command)

f_obj = open(posePoint_Path+'alphapose-results.json')#打开关键点信息
numbers = json.load(f_obj)

'''
// Result for COCO (17 body parts)
    {0,  "Nose"},
    {1,  "LEye"},
    {2,  "REye"},
    {3,  "LEar"},
    {4,  "REar"},
    {5,  "LShoulder"},
    {6,  "RShoulder"},
    {7,  "LElbow"},
    {8,  "RElbow"},
    {9,  "LWrist"},
    {10, "RWrist"},
    {11, "LHip"},
    {12, "RHip"},
    {13, "LKnee"},
    {14, "Rknee"},
    {15, "LAnkle"},
    {16, "RAnkle"},
'''
#登记LH左手、LE左肘、LS左肩、RH右手、RE右肘、RS右肩数据
LS_X = int(numbers[0]['keypoints'][15])
LS_Y = int(numbers[0]['keypoints'][16])#左肩
RS_X = int(numbers[0]['keypoints'][18])
RS_Y = int(numbers[0]['keypoints'][19])#右肩

LE_X = int(numbers[0]['keypoints'][21])
LE_Y = int(numbers[0]['keypoints'][22])#左肘
RE_X = int(numbers[0]['keypoints'][24])
RE_Y = int(numbers[0]['keypoints'][25])#右肘

LH_X = int(numbers[0]['keypoints'][27])
LH_Y = int(numbers[0]['keypoints'][28])#左腕
RH_X = int(numbers[0]['keypoints'][30])
RH_Y = int(numbers[0]['keypoints'][31])#右腕

#以双眼间距的两倍作为参照
Leye_x = int(numbers[0]['keypoints'][3])
Leye_y = int(numbers[0]['keypoints'][4])
Reye_x = int(numbers[0]['keypoints'][6])
Reye_y = int(numbers[0]['keypoints'][7])
len = int(math.sqrt(math.pow(Leye_x-Reye_x,2)+math.pow(Leye_y-Reye_y,2))) * 2

print(LH_Y,LE_Y,LS_Y)
print(RH_Y,RE_Y,RS_Y)
print(len)

#判断姿势
pose = 0
if LH_Y - LE_Y >= len and LE_Y - LS_Y >= len and RH_Y - RE_Y >= len and RE_Y - RS_Y >= len:
	pose = 1#双垂，降落
if LE_Y - LH_Y >= len and abs(LE_Y - LS_Y) <= len and RE_Y - RH_Y >= len and abs(RE_Y - RS_Y) <= len:
	pose = 2#双平举，起飞
if LS_Y - LE_Y >= len and LE_Y - LH_Y >= len and RS_Y - RE_Y >= len and RE_Y - RH_Y >= len:
	pose = 3#双高举，向上飞
if abs(LH_Y - LE_Y) <= len and abs(LE_Y - LS_Y) <= len and abs(RH_Y - RE_Y) <= len and abs(RE_Y - RS_Y) <= len:
	pose = 4#双伸，向下飞
if abs(LH_Y - LE_Y) <= len and abs(LE_Y - LS_Y) <= len and RE_Y - RH_Y >= len and abs(RE_Y - RS_Y) <= len:
	pose = 5#左伸右平举，前进
if abs(LH_Y - LE_Y) <= len and abs(LE_Y - LS_Y) <= len and RH_Y - RE_Y >= len and RE_Y - RS_Y >= len:
	pose = 6#左伸右垂，后进
if LE_Y - LH_Y >= len and abs(LE_Y - LS_Y) <= len and abs(RH_Y - RE_Y) <= len and abs(RE_Y - RS_Y) <= len:
	pose = 7#左平举右伸，左进
if LH_Y - LE_Y >= len and LE_Y - LS_Y >= len and abs(RH_Y - RE_Y) <= len and abs(RE_Y - RS_Y) <= len:
	pose = 8#左垂右伸，右进
if LS_Y - LE_Y >= len and LE_Y - LH_Y >= len and RH_Y - RE_Y >= len and RE_Y - RS_Y >= len:
	pose = 9#左高举右垂，左旋
if LH_Y - LE_Y >= len and LE_Y - LS_Y >= len and RS_Y - RE_Y >= len and RE_Y - RH_Y >= len:
	pose = 10#右高举左垂，右旋
else:
	pass
print(pose)


#绘制关键点可视化
# 0鼻子，1左眼，2右眼，3左耳，4右耳，5左肩，6右肩，7左肘，8右肘，9左腕，10右腕，11左臀，12右臀，13左膝，14右膝，15左踝，16右踝
point_list = [(int(numbers[0]['keypoints'][0]),int(numbers[0]['keypoints'][1])), (int(numbers[0]['keypoints'][3]),int(numbers[0]['keypoints'][4])),
				(int(numbers[0]['keypoints'][6]),int(numbers[0]['keypoints'][7])),(int(numbers[0]['keypoints'][9]),int(numbers[0]['keypoints'][10])),
				(int(numbers[0]['keypoints'][12]),int(numbers[0]['keypoints'][13])),(int(numbers[0]['keypoints'][15]),int(numbers[0]['keypoints'][16])),
				(int(numbers[0]['keypoints'][18]),int(numbers[0]['keypoints'][19])),(int(numbers[0]['keypoints'][21]),int(numbers[0]['keypoints'][22])),
				(int(numbers[0]['keypoints'][24]),int(numbers[0]['keypoints'][25])),(int(numbers[0]['keypoints'][27]),int(numbers[0]['keypoints'][28])),
				(int(numbers[0]['keypoints'][30]),int(numbers[0]['keypoints'][31])),(int(numbers[0]['keypoints'][33]),int(numbers[0]['keypoints'][34])),
				(int(numbers[0]['keypoints'][36]),int(numbers[0]['keypoints'][37])),(int(numbers[0]['keypoints'][39]),int(numbers[0]['keypoints'][40])),
				(int(numbers[0]['keypoints'][42]),int(numbers[0]['keypoints'][43])),(int(numbers[0]['keypoints'][45]),int(numbers[0]['keypoints'][46])),
				(int(numbers[0]['keypoints'][48]),int(numbers[0]['keypoints'][49]))]
img = cv2.imread(img_path+'frame.jpg')
for point in point_list:
	cv2.circle(img, point, 1, (0,0,255), 4)

cv2.line(img, point_list[0], point_list[1], (0,255,0), 1,4)
cv2.line(img, point_list[0], point_list[2], (0,255,0), 1,4)
cv2.line(img, point_list[1], point_list[3], (0,255,0), 1,4)
cv2.line(img, point_list[2], point_list[4], (0,255,0), 1,4)
cv2.line(img, point_list[9], point_list[7], (0,255,0), 1,4)
cv2.line(img, point_list[7], point_list[5], (0,255,0), 1,4)
cv2.line(img, point_list[5], point_list[6], (0,255,0), 1,4)
cv2.line(img, point_list[6], point_list[8], (0,255,0), 1,4)
cv2.line(img, point_list[8], point_list[10],  (0,255,0), 1,4)
cv2.line(img, point_list[5], point_list[11],  (0,255,0), 1,4)
cv2.line(img, point_list[6], point_list[12], (0,255,0), 1,4)
cv2.line(img, point_list[11], point_list[12],  (0,255,0), 1,4)
cv2.line(img, point_list[11], point_list[13],  (0,255,0), 1,4)
cv2.line(img, point_list[13], point_list[15], (0,255,0), 1,4)
cv2.line(img, point_list[12], point_list[14], (0,255,0), 1,4)
cv2.line(img, point_list[14], point_list[16], (0,255,0), 1,4)

cv2.imshow('result',img)
cv2.waitKey(0)

