import av
import numpy
import tellopy
import cv2
import os
import json
import math
import time
import sys
import traceback

import torch
from torch.autograd import Variable
import torch.nn.functional as F
import torchvision.transforms as transforms

import torch.nn as nn
import torch.utils.data
import numpy as np
from AlphaPose.opt import opt

from AlphaPose.dataloader import ImageLoader, DetectionLoader, DetectionProcessor, DataWriter, Mscoco
from AlphaPose.yolo.util import write_results, dynamic_write_results
from AlphaPose.SPPE.src.main_fast_inference import *

import os
import sys
from tqdm import tqdm
import time
from AlphaPose.fn import getTime

class  AlphaPose_control:
    # 设置参数
    args = opt
    args.inputpath = '../AlphaPose/duan_alphapose/photo/'
    args.outputpath = '../AlphaPose/duan_alphapose/'
    args.sp = True
    args.dataset = 'coco'

    img_path = args.inputpath

    if not args.sp:
        torch.multiprocessing.set_start_method('forkserver', force=True)
        torch.multiprocessing.set_sharing_strategy('file_system')
    def __init__(self):
        pass

    # 获取图像
    def GetImage(self,args):
        inputpath = args.inputpath
        inputlist = args.inputlist
        mode = args.mode

        if not os.path.exists(args.outputpath):
            os.mkdir(args.outputpath)

        for root, dirs, files in os.walk(inputpath):
            im_names = files
        return im_names

    # 下载模型
    def downModel(self):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # Load pose model
        print('Loading YOLO model...')
        pose_dataset = Mscoco()
        if self.args.fast_inference:
            pose_model = InferenNet_fast(4 * 1 + 1, pose_dataset)
        else:
            pose_model = InferenNet(4 * 1 + 1, pose_dataset)
        pose_model.to(device)
        pose_model.eval()

        return pose_model

    # 处理图像，提取关键点
    def Alphapose(self,im_names, pose_model, ):
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # Load input images
        data_loader = ImageLoader(im_names, batchSize=self.args.detbatch, format='yolo').start()

        # Load detection loader
        sys.stdout.flush()
        det_loader = DetectionLoader(data_loader, batchSize=self.args.detbatch).start()
        det_processor = DetectionProcessor(det_loader).start()
        runtime_profile = {
            'dt': [],
            'pt': [],
            'pn': []
        }

        # Init data writer
        writer = DataWriter(self.args.save_video).start()

        data_len = data_loader.length()
        im_names_desc = tqdm(range(data_len))

        batchSize = self.args.posebatch
        for i in im_names_desc:
            start_time = getTime()
            with torch.no_grad():
                (inps, orig_img, im_name, boxes, scores, pt1, pt2) = det_processor.read()
                if boxes is None or boxes.nelement() == 0:
                    writer.save(None, None, None, None, None, orig_img, im_name.split('/')[-1])
                    continue
                ckpt_time, det_time = getTime(start_time)
                runtime_profile['dt'].append(det_time)
                # Pose Estimation

                datalen = inps.size(0)
                leftover = 0
                if (datalen) % batchSize:
                    leftover = 1
                num_batches = datalen // batchSize + leftover
                hm = []
                for j in range(num_batches):
                    inps_j = inps[j * batchSize:min((j + 1) * batchSize, datalen)].to(device)
                    hm_j = pose_model(inps_j)
                    hm.append(hm_j)
                hm = torch.cat(hm)
                ckpt_time, pose_time = getTime(ckpt_time)
                runtime_profile['pt'].append(pose_time)
                hm = hm.cpu()
                writer.save(boxes, scores, hm, pt1, pt2, orig_img, im_name.split('/')[-1])

                ckpt_time, post_time = getTime(ckpt_time)
                runtime_profile['pn'].append(post_time)

            if self.args.profile:
                # TQDM
                im_names_desc.set_description(
                    'det time: {dt:.3f} | pose time: {pt:.2f} | post processing: {pn:.4f}'.format(
                        dt=np.mean(runtime_profile['dt']), pt=np.mean(runtime_profile['pt']),
                        pn=np.mean(runtime_profile['pn']))
                )

        print('Finish Model Running.')
        if (self.args.save_img or self.args.save_video) and not self.args.vis_fast:
            print('===========================> Rendering remaining images in the queue...')
            print(
                '===========================> If this step takes too long, you can enable the --vis_fast flag to use fast rendering (real-time).')
        while (writer.running()):
            pass
        writer.stop()
        final_result = writer.results()
        # write_json(final_result, args.outputpath)
        try:
            if final_result[0]['result']:
                return final_result[0]['result'][0]['keypoints']
            else:
                return None
        except:
            return None

    # 根据关键点分析动作，绘制图像
    def PoseFind(self,point_results):
        '''point_result是关键点信息，一个tensor数组
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

        # 登记LH左手、LE左肘、LS左肩、RH右手、RE右肘、RS右肩数据
        # LS_X = int(numbers[0]['keypoints'][15])
        LS_Y = int(point_results[5][1].item())
        # RS_X = int(numbers[0]['keypoints'][18])
        RS_Y = int(point_results[6][1].item())

        # LE_X = int(numbers[0]['keypoints'][21])
        LE_Y = int(point_results[7][1].item())
        # RE_X = int(numbers[0]['keypoints'][24])
        RE_Y = int(point_results[8][1].item())

        # LH_X = int(numbers[0]['keypoints'][27])
        LH_Y = int(point_results[9][1].item())
        # RH_X = int(numbers[0]['keypoints'][30])
        RH_Y = int(point_results[10][1].item())

        # 以双眼间距的两倍作为参照
        Leye_x = int(point_results[1][0].item())
        Leye_y = int(point_results[1][1].item())
        Reye_x = int(point_results[2][0].item())
        Reye_y = int(point_results[2][1].item())
        len = int(math.sqrt(math.pow(Leye_x - Reye_x, 2) + math.pow(Leye_y - Reye_y, 2))) * 2

        # 判断姿势
        pose = 0
        if LH_Y - LE_Y >= len and LE_Y - LS_Y >= len and RH_Y - RE_Y >= len and RE_Y - RS_Y >= len:
            pose = 1  # 双垂
            print('---------------------------双垂--------------------------')
        if LE_Y - LH_Y >= len and abs(LE_Y - LS_Y) <= len and RE_Y - RH_Y >= len and abs(RE_Y - RS_Y) <= len:
            pose = 2  # 双平举
            print('---------------------------双平举--------------------------')
        if LS_Y - LE_Y >= len and LE_Y - LH_Y >= len and RS_Y - RE_Y >= len and RE_Y - RH_Y >= len:
            pose = 3  # 双高举
            print('---------------------------双高举--------------------------')
        if abs(LH_Y - LE_Y) <= len and abs(LE_Y - LS_Y) <= len and abs(RH_Y - RE_Y) <= len and abs(RE_Y - RS_Y) <= len:
            pose = 4  # 双伸
            print('---------------------------双伸--------------------------')
        if abs(LH_Y - LE_Y) <= len and abs(LE_Y - LS_Y) <= len and RE_Y - RH_Y >= len and abs(RE_Y - RS_Y) <= len:
            pose = 5  # 左伸右平举
            print('---------------------------左伸右平举--------------------------')
        if abs(LH_Y - LE_Y) <= len and abs(LE_Y - LS_Y) <= len and RH_Y - RE_Y >= len and RE_Y - RS_Y >= len:
            pose = 6  # 左伸右垂
            print('---------------------------左伸右垂--------------------------')
        if LE_Y - LH_Y >= len and abs(LE_Y - LS_Y) <= len and abs(RH_Y - RE_Y) <= len and abs(RE_Y - RS_Y) <= len:
            pose = 7  # 左平举右伸
            print('---------------------------左平举右伸--------------------------')
        if LH_Y - LE_Y >= len and LE_Y - LS_Y >= len and abs(RH_Y - RE_Y) <= len and abs(RE_Y - RS_Y) <= len:
            pose = 8  # 左垂右伸
            print('---------------------------左垂右伸--------------------------')
        if LS_Y - LE_Y >= len and LE_Y - LH_Y >= len and RH_Y - RE_Y >= len and RE_Y - RS_Y >= len:
            pose = 9  # 左高举右垂
            print('---------------------------左高举右垂--------------------------')
        if LH_Y - LE_Y >= len and LE_Y - LS_Y >= len and RS_Y - RE_Y >= len and RE_Y - RH_Y >= len:
            pose = 10  # 右高举左垂
            print('---------------------------右高举左垂--------------------------')
        else:
            pass

            # 绘制关键点可视化
            # 0鼻子，1左眼，2右眼，3左耳，4右耳，5左肩，6右肩，7左肘，8右肘，9左腕，10右腕，11左臀，12右臀，13左膝，14右膝，15左踝，16右踝
            point_list = [(int(point_results[0][0].item()), int(point_results[0][1].item())),
                          (int(point_results[1][0].item()), int(point_results[1][1].item())),
                          (int(point_results[2][0].item()), int(point_results[2][1].item())),
                          (int(point_results[3][0].item()), int(point_results[3][1].item())),
                          (int(point_results[4][0].item()), int(point_results[4][1].item())),
                          (int(point_results[5][0].item()), int(point_results[5][1].item())),
                          (int(point_results[6][0].item()), int(point_results[6][1].item())),
                          (int(point_results[7][0].item()), int(point_results[7][1].item())),
                          (int(point_results[8][0].item()), int(point_results[8][1].item())),
                          (int(point_results[9][0].item()), int(point_results[9][1].item())),
                          (int(point_results[10][0].item()), int(point_results[10][1].item())),
                          (int(point_results[11][0].item()), int(point_results[11][1].item())),
                          (int(point_results[12][0].item()), int(point_results[12][1].item())),
                          (int(point_results[13][0].item()), int(point_results[13][1].item())),
                          (int(point_results[14][0].item()), int(point_results[14][1].item())),
                          (int(point_results[15][0].item()), int(point_results[15][1].item())),
                          (int(point_results[16][0].item()), int(point_results[16][1].item()))]
            img = cv2.imread(self.img_path + 'frame.jpg')
            for point in point_list:
                cv2.circle(img, point, 1, (0, 0, 255), 4)

            # 绘制关键点连线
            cv2.line(img, point_list[0], point_list[1], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[0], point_list[2], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[1], point_list[3], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[2], point_list[4], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[9], point_list[7], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[7], point_list[5], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[5], point_list[6], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[6], point_list[8], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[8], point_list[10], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[5], point_list[11], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[6], point_list[12], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[11], point_list[12], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[11], point_list[13], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[13], point_list[15], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[12], point_list[14], (0, 255, 0), 1, 4)
            cv2.line(img, point_list[14], point_list[16], (0, 255, 0), 1, 4)

            # cv2.imshow('AlphaPose', img)
            # cv2.waitKey(1)
            return pose,img

    # 删除文件函数，用于清空文件夹内图像
    def del_files(self,path_file):
        ls = os.listdir(path_file)
        for i in ls:
            f_path = os.path.join(path_file, i)
            # 判断是否是一个目录,若是,则递归删除
            if os.path.isdir(f_path):
                self.del_files(f_path)
            else:
                os.remove(f_path)

