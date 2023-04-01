import cv2
import numpy as np

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
