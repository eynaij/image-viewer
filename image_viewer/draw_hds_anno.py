import cv2
import random
import numpy as np
import os, sys
import argparse
import json
from collections import OrderedDict

color_tables = {
  0: OrderedDict([
       ('normal', (0, 255, 0)),
       ('ignore', (0, 255, 255)),
     ]),
  1: OrderedDict([
       ('full_visible', (0, 255, 0)),
       ('occluded', (255, 0, 0)),
       ('heavily_occluded', (0, 0, 255)),
       ('invisible', (0, 255, 255))
     ]),
  2: {
       'person': OrderedDict([
         ('Pedestrian', (0, 255, 0)),
         ('Cyclist', (255, 0, 0)),
         ('Others', (0, 255, 255))
        ]),
       'vehicle': OrderedDict([
         ('SUV', (255,0,0)),
         ('Sedan_Car', (0,255,0)), 
         ('Special_vehicle', (0,0,255)), 
         ('BigTruck',(255,252,25)),
         ('Bus', (9,113,178)),
         ('Lorry', (160,42,178)),
         ('MiniVan', (255,194,25)),
         ('Vehicle_others', (0,255,255)),
         ('Bike', (63,89,19)),
         ('Motor-Tricycle',(0,184,255)),
         ('Motorcycle', (55,178,22)), 
         ('Tricycle',(20,204,151)),
         ('Non-Motor Vehicle_others',(0,128,255)),
         ('Unknown', (255,255,255)),
         ('other', (0,255,255))
       ]),
       'traffic_sign': OrderedDict([
         ('T_Indicate', (0, 255, 0)),
         ('T_Warning', (0, 255, 255)),
         ('T_Prohibit', (0, 0, 255)),
         ('Interchange_Street_Sign', (255, 0, 0)),
         ('assistance_signs', (255,0,255)), # SK only
         ('sign_back', (128,128,128)), # SK only
         ('Other', (255, 255, 0))
       ]),
       'Traffic_light_shell': {
          'China': OrderedDict([
            ('on', (0,255,0)),
            ('off', (0,0,255)),
            ('unknown', (0,255,255)),
          ]),
          'SK': OrderedDict([
          ])
       }
     }
}
mode_strings = {
  0: 'Ignore',
  1: 'Occlusion',
  2: 'Type'
}

def draw_legend(colors, show_mode=2, board_width=250, board_height=200):
  startx = 10
  starty = 10
  board = np.ones((board_height+40, board_width, 3), dtype='uint8')
  cv2.putText(board,'Mode-%d: %s' %(show_mode, mode_strings[show_mode]), (startx, starty+20), cv2.FONT_HERSHEY_PLAIN , 1.5, (255, 255, 255), 2)
  starty += 25
  for i, name in enumerate(colors):
    clr = colors[name]
    x1, x2, y1, y2 = startx, startx+20, starty, starty + 20
    pts = np.array([(x1,y1), (x2,y1), (x2,y2), (x1,y2)]).reshape((-1,2))
    cv2.fillPoly(board, [pts], (255,255,255))
    cv2.rectangle(board, (x1,y1),(x2,y2), clr, 2)
    thick = 2
    cv2.putText(board, name, (startx+25, starty+18), cv2.FONT_HERSHEY_PLAIN, 1.5, clr, thick)
    starty += 25
  return board

def draw_annotation(im, anno, classname, thickness=2, show_mode=0, show_legend=True, type_set='China'):
  colors = color_tables[show_mode]
  if show_mode == 2:
    colors = colors[classname]
    if classname == 'Traffic_light_shell':
      colors = colors[type_set]
  if classname in anno:
    for obj in anno[classname]:
        box = obj['data']
        attrs = obj['attrs']
        ignore = 'normal'
        if 'ignore' in attrs and attrs['ignore'] == 'yes':
          ignore = 'ignore'
        if ignore == 'ignore' and show_mode != 0: continue
        occ = attrs.get('occlusion', 'full_visible')
        if classname in ['person', 'vehicle']:
          obj_type = attrs.get('type', '')
        elif classname == 'traffic_sign':
          obj_type = attrs.get('main_type', '')
        elif classname == 'Traffic_light_shell':
          obj_type = attrs.get('Type', '')
        if show_mode == 0:
          color = colors[ignore]
        elif show_mode == 1:
          color = colors[occ]
        elif show_mode == 2:
          color = colors[obj_type] if obj_type != '' else (0, 0, 0)
        x1, y1, x2, y2 = box
        cv2.rectangle(im,  (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)
  if show_legend:
    legend_start_x = 1000
    legend_start_y = 20
    alpha = 0.5
    legend = draw_legend(colors, show_mode, 250, len(colors) * 25)
    im[legend_start_y:legend_start_y+legend.shape[0], legend_start_x:legend_start_x+legend.shape[1], :] = \
      im[legend_start_y:legend_start_y+legend.shape[0], legend_start_x:legend_start_x+legend.shape[1], :] * alpha \
      + legend * (1-alpha)
  return im

def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('--hds_json', help="annotation file.")
  parser.add_argument('--image_dir', help="image directory.")
  parser.add_argument('--output_dir', help="output directory.")
  parser.add_argument('--classname', default='vehicle', help="classname in hds json file to visualize")
  parser.add_argument('--random_type_colors', action='store_true', help="use random type colors")
  args = parser.parse_args()
  return args

if __name__ == '__main__':
    args = parse_args()
    anno_l = open(args.hds_json).readlines()
    if args.image_dir is None:
      img_dir = args.hds_json[:-5] + '/'
    else:
      img_dir = args.image_dir
    out_dir = args.output_dir
    if out_dir is not None and not os.path.exists(out_dir):
      os.makedirs(out_dir)
    idx = 0
    show_mode = 0
    show_legend = True
    while True:
      anno = json.loads(anno_l[idx])
      imname = anno['image_key']
      imfile = os.path.join(img_dir, imname)
      print(imfile)
      im = cv2.imread(imfile)
      im = draw_annotation(im, anno, args.classname, 2, show_mode, show_legend)
      cv2.putText(im,'(%d/%d):%s' %(idx + 1, len(anno_l), imname), (20, 20), cv2.FONT_HERSHEY_PLAIN , 1, (255, 0, 0), 1)
      if out_dir is not None:
        cv2.imwrite(out_dir + '/' + os.path.basename(imname), im)
      cv2.imshow('im', im)
      key = chr(cv2.waitKey(-1) % 256)
      if key in ['q', 'Q', chr(27)]:
        break
      elif key in ['=', ' ']:
        idx = min(len(anno_l) - 1, idx + 1)
      elif key in ['-']:
        idx = max(0, idx - 1)
      elif key in [']']:
        idx = min(len(anno_l) - 1, idx + 10)
      elif key in ['[']:
        idx = max(0, idx - 10)
      elif key in ['\'']:
        idx = min(len(anno_l) - 1, idx + 100)
      elif key in [';']:
        idx = max(0, idx - 100)
      elif key in ['0', '1', '2']:
        show_mode = int(key)
      elif key in ['l']:
        show_legend = not show_legend
