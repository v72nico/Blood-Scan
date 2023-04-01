import cv2
import os
from ultralytics import YOLO

def identify_wbcs(slide, imgs, save_loc='', confidence=0.3):
    #TODO scan for good areas of slide
    identified_wbcs = []
    model = YOLO('slide_analyzer/static/best.pt')
    for img in imgs:
        results = model(f'media/slide_{slide}/tiles{save_loc}/{img}')
        boxes = []
        for box in results[0].boxes:
            if box.conf > confidence:
                boxes.append(box)
        identified_wbcs.append([boxes, img])
    return identified_wbcs

def generate_wbc_imgs_and_cords(slide, identified_wbcs, coordinate_factors, save_loc='', tile_size=256, tile_size_2=0):
    #TODO find wbcs split between images
    counter = 0
    src_lst = []
    for wbc_data in identified_wbcs:
        wbc_lst = wbc_data[0]
        if len(wbc_lst) > 0:
            for wbc in wbc_lst:
                wbc_xyxy = make_wbc_xyxy(wbc.xyxy[0])
                generate_wbc_img(wbc_xyxy, wbc_data[1], slide, save_loc, counter, tile_size)
                coordinates = get_wbc_coordinates(wbc_xyxy, wbc_data[1], coordinate_factors, tile_size, tile_size_2)
                src_lst.append([f'media/slide_{slide}/wbcs/{counter}.png', counter, coordinates])
                counter += 1
    return src_lst

def make_wbc_xyxy(xyxy_data):
    wbc_xyxy = []
    wbc_xyxy.append(xyxy_data[0].item())
    wbc_xyxy.append(xyxy_data[1].item())
    wbc_xyxy.append(xyxy_data[2].item())
    wbc_xyxy.append(xyxy_data[3].item())
    return wbc_xyxy

def generate_wbc_img(wbc_xyxy, img_src, slide, save_loc, counter, tile_size):
    margin = 20
    lower_x_bound = int(wbc_xyxy[0]-margin)
    if lower_x_bound < 0:
        lower_x_bound = 0
    lower_y_bound = int(wbc_xyxy[1]-margin)
    if lower_y_bound < 0:
        lower_y_bound = 0
    upper_x_bound = int(wbc_xyxy[2]+margin)
    if upper_x_bound > tile_size:
        upper_x_bound = tile_size
    upper_y_bound = int(wbc_xyxy[3]+margin)
    if upper_y_bound > tile_size:
        upper_y_bound = tile_size
    img = cv2.imread(f'media/slide_{slide}/tiles{save_loc}/{img_src}')
    cropped_img = img[lower_y_bound:upper_y_bound, lower_x_bound:upper_x_bound]
    cv2.imwrite(f'media/slide_{slide}/wbcs/{counter}.png', cropped_img)

def get_wbc_coordinates(wbc_xyxy, src, coordinate_factors, tile_size, tile_size_2):
        lower_x_bound = int(wbc_xyxy[0])
        lower_y_bound = int(wbc_xyxy[1])
        upper_x_bound = int(wbc_xyxy[2])
        upper_y_bound = int(wbc_xyxy[3])
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

def add_wbc_img(slide, img_id, coordinate_factors, lat_lower, lat_upper, lng_lower, lng_upper):
    lower_x_bound, lower_y_bound, upper_x_bound, upper_y_bound, this_x, this_y = get_wbc_bounds(coordinate_factors, lat_lower, lat_upper, lng_lower, lng_upper, 2464, 256)
    img = cv2.imread(f'media/slide_{slide}/tiles_id/0.{this_y}.{this_x}.png')
    cropped_img = img[lower_y_bound:upper_y_bound, lower_x_bound:upper_x_bound]
    cv2.imwrite(f'media/slide_{slide}/wbcs/{img_id}.png', cropped_img)

def get_wbc_bounds(coordinate_factors, lat_lower, lat_upper, lng_lower, lng_upper, tile_size, tile_size_2):
    #TODO create images across id tiles
    lower_x_bound = int(((lng_upper*tile_size)*coordinate_factors[0][0])/coordinate_factors[1][0]/tile_size_2)
    lower_y_bound = int(-((lat_lower*tile_size)*coordinate_factors[0][1])/coordinate_factors[1][1]/tile_size_2)
    upper_x_bound = int(((lng_lower*tile_size)*coordinate_factors[0][0])/coordinate_factors[1][0]/tile_size_2)
    upper_y_bound = int(-((lat_upper*tile_size)*coordinate_factors[0][1])/coordinate_factors[1][1]/tile_size_2)
    this_x = int(upper_x_bound/tile_size)
    upper_x_bound = upper_x_bound%tile_size
    lower_x_bound = lower_x_bound%tile_size
    if lower_x_bound > upper_x_bound:
        lower_x_bound = 0
    this_y = int(upper_y_bound/tile_size)
    upper_y_bound = upper_y_bound%tile_size
    lower_y_bound = lower_y_bound%tile_size
    if lower_y_bound > upper_y_bound:
        lower_y_bound = 0
    return lower_x_bound, lower_y_bound, upper_x_bound, upper_y_bound, this_x, this_y

def get_tiles(slide, save_loc, zoom_target=0):
    identify_tiles = []
    for tile in os.listdir(f'media/slide_{slide}/tiles{save_loc}'):
        if tile[:1] == str(zoom_target):
            identify_tiles.append(tile)
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

def coordinate_factors_to_string(coordinate_factors):
    cf_str = str(coordinate_factors[0][0])+'|'
    cf_str += str(coordinate_factors[0][1])+'|'
    cf_str += str(coordinate_factors[1][0])+'|'
    cf_str += str(coordinate_factors[1][1])
    return cf_str

def string_to_coordinate_factors(cf_str):
    split_cf_str = cf_str.split('|')
    coordinate_factors = [[], []]
    coordinate_factors[0].append(int(split_cf_str[0]))
    coordinate_factors[0].append(int(split_cf_str[1]))
    coordinate_factors[1].append(float(split_cf_str[2]))
    coordinate_factors[1].append(float(split_cf_str[3]))
    return coordinate_factors
