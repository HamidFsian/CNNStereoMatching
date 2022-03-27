from __future__ import print_function
import argparse
import os
import random
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torch.nn.functional as F
import numpy as np
import time
import math
from models import *
import cv2
from PIL import Image


parser = argparse.ArgumentParser(description='PSMNet')
parser.add_argument('--middlebury', default='2014',
                    help='middlebury version')
parser.add_argument('--datapath', default=r"C:/Users/itta_/Documents/python_projects/StereoMatching/KITTI2015/testing2/",
                    help='select model')
parser.add_argument('--loadmodel', default='./trained/pretrained_model_KITTI2015.tar',
                    help='loading model')
parser.add_argument('--leftimg', default= './000001_10.png',
                    help='load model')
parser.add_argument('--rightimg', default= './000001_10.png',
                    help='load model')                                      
parser.add_argument('--model', default='stackhourglass',
                    help='select model')
parser.add_argument('--maxdisp', type=int, default=192,
                    help='maxium disparity')
parser.add_argument('--no-cuda', action='store_true', default=False,
                    help='enables CUDA training')
parser.add_argument('--seed', type=int, default=1, metavar='S',
                    help='random seed (default: 1)')
args = parser.parse_args()
args.cuda = not args.no_cuda and torch.cuda.is_available()

torch.manual_seed(args.seed)
#if args.cuda:
    #torch.cuda.manual_seed(args.seed)

if args.middlebury == '2014':
   from dataloader import middlebury_loader as DA

test_left_img, test_right_img = DA.dataloader(args.datapath)

if args.model == 'stackhourglass':
    model = stackhourglass(args.maxdisp)


model = nn.DataParallel(model, device_ids=[0])
model.cpu()

if args.loadmodel is not None:
    print('load PSMNet')
    state_dict = torch.load('trained/pretrained_model_KITTI2015.tar',map_location ='cpu')
    model.load_state_dict(state_dict['state_dict'])

print('Number of model parameters: {}'.format(sum([p.data.nelement() for p in model.parameters()])))

def test(imgL,imgR):
        model.eval()

          

        with torch.no_grad():
            disp = model(imgL,imgR)

        disp = torch.squeeze(disp)
        pred_disp = disp.data.cpu().numpy()

        return pred_disp


def main():

        normal_mean_var = {'mean': [0.485, 0.456, 0.406],
                            'std': [0.229, 0.224, 0.225]}
        infer_transform = transforms.Compose([transforms.ToTensor(),
                                              transforms.Normalize(**normal_mean_var)])    

        for inx in range(len(test_left_img)):

            imgL_o = Image.open(test_left_img[inx]).convert('RGB')
            imgR_o = Image.open(test_right_img[inx]).convert('RGB')

            

            imgL = infer_transform(imgL_o)
            imgR = infer_transform(imgR_o)         

            # pad to width and hight to 16 times
            if imgL.shape[1] % 16 != 0:
                times = imgL.shape[1]//16       
                top_pad = (times+1)*16 -imgL.shape[1]
            else:
                top_pad = 0

            if imgL.shape[2] % 16 != 0:
                times = imgL.shape[2]//16                       
                right_pad = (times+1)*16-imgL.shape[2]
            else:
                right_pad = 0    

            imgL = F.pad(imgL,(0,right_pad, top_pad,0)).unsqueeze(0)
            imgR = F.pad(imgR,(0,right_pad, top_pad,0)).unsqueeze(0)

            start_time = time.time()
            pred_disp = test(imgL,imgR)
            print('time = %.2f' %(time.time() - start_time))

            if top_pad !=0 or right_pad != 0:
                img = pred_disp[top_pad:,:-right_pad]
            else:
                img = pred_disp

            img = (img*256).astype('uint16')
            img = Image.fromarray(img)
            img.save(test_left_img[inx].split('/')[-1])

if __name__ == '__main__':
   main()






