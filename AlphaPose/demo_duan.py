import torch
from torch.autograd import Variable
import torch.nn.functional as F
import torchvision.transforms as transforms

import torch.nn as nn
import torch.utils.data
import numpy as np
from opt import opt

from dataloader import ImageLoader, DetectionLoader, DetectionProcessor, DataWriter, Mscoco
from yolo.util import write_results, dynamic_write_results
from SPPE.src.main_fast_inference import *

import os
import sys
from tqdm import tqdm
import time
from fn import getTime

from pPose_nms import pose_nms, write_json

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# args = opt
# 设置参数
args = opt
args.inputpath = '/Users/yunyi/Desktop/AlphaPose/duan_alphapose/photo'
args.outputpath = '/Users/yunyi/Desktop/AlphaPose/duan_alphapose'
args.sp = True
args.dataset = 'coco'

if not args.sp:
    torch.multiprocessing.set_start_method('forkserver', force=True)
    torch.multiprocessing.set_sharing_strategy('file_system')

inputpath = args.inputpath
inputlist = args.inputlist
mode = args.mode

if not os.path.exists(args.outputpath):
	os.mkdir(args.outputpath)

for root, dirs, files in os.walk(inputpath):
    im_names = files
print(im_names)

# Load input images
data_loader = ImageLoader(im_names, batchSize=args.detbatch, format='yolo').start()

# Load detection loader
print('Loading YOLO model..')
sys.stdout.flush()
det_loader = DetectionLoader(data_loader, batchSize=args.detbatch).start()
det_processor = DetectionProcessor(det_loader).start()

# Load pose model
print('Load pose model...')
pose_dataset = Mscoco()
if args.fast_inference:
	pose_model = InferenNet_fast(4 * 1 + 1, pose_dataset)
else:
	pose_model = InferenNet(4 * 1 + 1, pose_dataset)
pose_model.to(device)
pose_model.eval()

runtime_profile = {
	'dt': [],
	'pt': [],
	'pn': []
}

# Init data writer
writer = DataWriter(args.save_video).start()

data_len = data_loader.length()
im_names_desc = tqdm(range(data_len))

batchSize = args.posebatch
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
			inps_j = inps[j*batchSize:min((j +  1)*batchSize, datalen)].to(device)
			hm_j = pose_model(inps_j)
			hm.append(hm_j)
		hm = torch.cat(hm)
		ckpt_time, pose_time = getTime(ckpt_time)
		runtime_profile['pt'].append(pose_time)
		hm = hm.cpu()
		writer.save(boxes, scores, hm, pt1, pt2, orig_img, im_name.split('/')[-1])

		ckpt_time, post_time = getTime(ckpt_time)
		runtime_profile['pn'].append(post_time)
	
	if args.profile:
		# TQDM
		im_names_desc.set_description(
		'det time: {dt:.3f} | pose time: {pt:.2f} | post processing: {pn:.4f}'.format(
			dt=np.mean(runtime_profile['dt']), pt=np.mean(runtime_profile['pt']), pn=np.mean(runtime_profile['pn']))
		)

print('Finish Model Running.')
while(writer.running()):
	pass
writer.stop()
final_result = writer.results()
# print(final_result[0]['result'][0]['keypoints'][0][1].item())
# print(writer[0]['result'])
# print(final_result)
if final_result[0]['result']:
	print('yes')
else:
	print('none')
write_json(final_result, args.outputpath)
