import cv2
import numpy as np
import os
from ultralytics import YOLO

def tile_image(raw_img, slide, tile_size=256, scale=None, save_loc=''):
    original_img = cv2.imread(raw_img)
    if scale == None:
        scale = get_scale(original_img, tile_size)

    part_coordinate_factors = []
    layer_0_xy = []
    layer_target_xy = []
    for i in range(scale,-1,-1):
        scale_part_coordinate_factors = tile_img_at_scale(i, scale, original_img, slide, tile_size, save_loc)
        if scale_part_coordinate_factors != []:
            part_coordinate_factors = scale_part_coordinate_factors

    return scale, part_coordinate_factors

def tile_img_at_scale(this_scale, scale, original_img, slide, tile_size, save_loc):
    resize_factor = scale-this_scale
    img = resize_img(original_img, resize_factor)

    part_coordinate_factors = []
    if this_scale == 0:
        scale_0_size = get_scale_0_size(len(img[0]), len(img), tile_size)
        scale_0_xy = get_percent_img_used(len(img[0]), len(img), tile_size)
        part_coordinate_factors = [scale_0_size, scale_0_xy]

    tile_core_img(img, this_scale, slide, tile_size, save_loc)
    #REMAINDER
    tile_remainder_img(img, this_scale, slide, tile_size, save_loc)

    return part_coordinate_factors

def get_scale_0_size(x_len, y_len, tile_size):
    cord_y_len = int(y_len/tile_size)+1
    cord_x_len = int(x_len/tile_size)+1
    scale_0_size = [cord_x_len, cord_y_len]

    return scale_0_size

def get_percent_img_used(x_len, y_len, tile_size):
    scale_0_xy = []
    cord_y_len = int(y_len/tile_size)+1
    cord_x_len = int(x_len/tile_size)+1
    scale_0_xy.append(x_len/(tile_size*cord_x_len))
    scale_0_xy.append(y_len/(tile_size*cord_y_len))

    return scale_0_xy


def get_scale(img, tile_size):
    scale = 0
    for i in range(0,10):
        this_scale = tile_size*2**i
        if len(img) > this_scale or len(img[0]) > this_scale:
            scale = i+1
    return scale

def resize_img(img, resize_factor):
    if resize_factor != 0:
        y_resize = int(len(img)/(2**resize_factor))
        x_resize = int(len(img[0])/(2**resize_factor))
        new_img = cv2.resize(img, (x_resize, y_resize))
    else:
        new_img = img
    return new_img

def tile_core_img(img, layer, slide, tile_size, save_loc):
    y_len = int(len(img)/tile_size)
    x_len = int(len(img[0])/tile_size)
    for j in range(0,x_len):
        for l in range(0,y_len):
            cv2.imwrite(f'media/slide_{slide}/tiles{save_loc}/{layer}.{l}.{j}.png', img[tile_size*l:tile_size*l+tile_size, tile_size*j:tile_size*j+tile_size])

def tile_remainder_img(img, layer, slide, tile_size, save_loc):
    y_len = int(len(img)/tile_size)
    x_len = int(len(img[0])/tile_size)
    x_remainder = len(img[0])%tile_size
    y_remainder = len(img)%tile_size
    if y_remainder > 0:
        for j in range(0, x_len):
            this_tile = img[y_len*tile_size:y_len*tile_size+y_remainder, tile_size*j:tile_size*j+tile_size]
            final_tile = np.zeros((tile_size,tile_size,3), np.uint8)
            final_tile[:, :] = (0,0,0)
            final_tile[:this_tile.shape[0], :this_tile.shape[1]] = this_tile
            cv2.imwrite(f'media/slide_{slide}/tiles{save_loc}/{layer}.{y_len}.{j}.png', final_tile)
    if x_remainder > 0:
        for j in range(0, y_len):
            this_tile = img[tile_size*j:tile_size*j+tile_size, x_len*tile_size:x_len*tile_size+x_remainder]
            final_tile = np.zeros((tile_size,tile_size,3), np.uint8)
            final_tile[:, :] = (0,0,0)
            final_tile[:this_tile.shape[0], :this_tile.shape[1]] = this_tile
            cv2.imwrite(f'media/slide_{slide}/tiles{save_loc}/{layer}.{j}.{x_len}.png', final_tile)
    if x_remainder > 0 and y_remainder > 0:
        this_tile = img[y_len*tile_size:y_len*tile_size+y_remainder, x_len*tile_size:x_len*tile_size+x_remainder]
        final_tile = np.zeros((tile_size,tile_size,3), np.uint8)
        final_tile[:, :] = (0,0,0)
        final_tile[:this_tile.shape[0], :this_tile.shape[1]] = this_tile
        cv2.imwrite(f'media/slide_{slide}/tiles{save_loc}/{layer}.{y_len}.{x_len}.png', final_tile)

def identify_wbcs(slide, imgs, save_loc='', confidence=0.3):
    #TODO scan for good areas of slide
    identified_wbcs = []
    model = YOLO('static/best.pt')
    for img in imgs:
        results = model(f'media/slide_{slide}/tiles{save_loc}/{img}')
        boxes = []
        for box in results[0].boxes:
            if box.conf > confidence:
                boxes.append(box)
        identified_wbcs.append([boxes, img])
    return identified_wbcs

def generate_wbc_imgs(slide, identified_wbcs, coordinate_factors, save_loc='', tile_size=256, tile_size_2=0):
    #TODO find wbcs split between images
    margin = 20
    counter = 0
    src_lst = []
    for wbc_data in identified_wbcs:
        wbc_lst = wbc_data[0]
        if len(wbc_lst) > 0:
            for wbc in wbc_lst:
                wbc_xyxy = wbc.xyxy[0]
                lower_x_bound = int(wbc_xyxy[0].item()-margin)
                if lower_x_bound < 0:
                    lower_x_bound = 0
                lower_y_bound = int(wbc_xyxy[1].item()-margin)
                if lower_y_bound < 0:
                    lower_y_bound = 0
                upper_x_bound = int(wbc_xyxy[2].item()+margin)
                if upper_x_bound > tile_size:
                    upper_x_bound = tile_size
                upper_y_bound = int(wbc_xyxy[3].item()+margin)
                if upper_y_bound > tile_size:
                    upper_y_bound = tile_size
                img = cv2.imread(f'media/slide_{slide}/tiles{save_loc}/{wbc_data[1]}')
                cropped_img = img[lower_y_bound:upper_y_bound, lower_x_bound:upper_x_bound]
                cv2.imwrite(f'media/slide_{slide}/wbcs/{counter}.png', cropped_img)

                coordinates = get_wbc_coordinates(wbc_xyxy, wbc_data[1], coordinate_factors, tile_size, tile_size_2)

                src_lst.append([f'media/slide_{slide}/wbcs/{counter}.png', counter, coordinates])
                counter += 1
    return src_lst

def get_wbc_coordinates(wbc, src, coordinate_factors, tile_size, tile_size_2):
        lower_x_bound = int(wbc[0].item())
        lower_y_bound = int(wbc[1].item())
        upper_x_bound = int(wbc[2].item())
        upper_y_bound = int(wbc[3].item())
        x_coordinate = (upper_x_bound+lower_x_bound)/2
        y_coordinate = (upper_y_bound+lower_y_bound)/2

        these_coordinates = src.split('.')
        this_y = int(these_coordinates[1])
        this_x = int(these_coordinates[2])

        #basically % way across id image is cords * factor which is ratio of percent of image taken up by real stuff * tile size to go from percentage to acctual coordinate
        x = ((this_x+(x_coordinate/tile_size))/coordinate_factors[0][0])*coordinate_factors[1][0]*tile_size_2
        y = -((this_y+(y_coordinate/tile_size))/coordinate_factors[0][1])*coordinate_factors[1][1]*tile_size_2
        f_lower_x_bound = ((this_x+(lower_x_bound/tile_size))/coordinate_factors[0][0])*coordinate_factors[1][0]*tile_size_2
        f_lower_y_bound = -((this_y+(lower_y_bound/tile_size))/coordinate_factors[0][1])*coordinate_factors[1][1]*tile_size_2
        f_upper_x_bound = ((this_x+(upper_x_bound/tile_size))/coordinate_factors[0][0])*coordinate_factors[1][0]*tile_size_2
        f_upper_y_bound = -((this_y+(upper_y_bound/tile_size))/coordinate_factors[0][1])*coordinate_factors[1][1]*tile_size_2

        return [y, x, f_lower_x_bound, f_lower_y_bound, f_upper_x_bound, f_upper_y_bound]

def get_tiles(slide, save_loc, zoom_target=0):
    identify_tiles = []
    for tile in os.listdir(f'media/slide_{slide}/tiles{save_loc}'):
        if tile[:1] == str(zoom_target):
            identify_tiles.append(tile)
    print(identify_tiles)
    return identify_tiles

def save_upload(f):
    with open('media/upload.png', 'wb+') as d:
        for chunk in f.chunks():
            d.write(chunk)

def calc_coordinate_factors(coordinate_factors_tiles, coordinate_factors_full_res):
    coordinate_factors = []
    coordinate_factors.append(coordinate_factors_full_res[0])
    coordinate_factors.append([coordinate_factors_tiles[1][0]/coordinate_factors_full_res[1][0], coordinate_factors_tiles[1][1]/coordinate_factors_full_res[1][1]])
    return coordinate_factors
