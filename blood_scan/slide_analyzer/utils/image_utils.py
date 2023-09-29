import os
os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = str(pow(2,40))

import cv2
import numpy
from ultralytics import YOLO
import openflexure_microscope_client as ofm_client
from slide_analyzer.utils.ofm_utils import capture_full_image
from time import sleep

class WbcImageHandler():
    def __init__(self, coordinate_factors, id_tile_size, view_tile_size, save_loc, mode='done'):
        self.coordinate_factors = coordinate_factors
        self.id_tile_size = id_tile_size
        self.view_tile_size = view_tile_size
        self.save_loc = save_loc
        print(coordinate_factors, id_tile_size, view_tile_size, save_loc)
        imgs = self.get_tiles()
        if mode == "start":
            wbc_id = WbcIdentificationHandler(self.save_loc)
            self.identified_wbcs = wbc_id.identify_wbcs(imgs)

    def generate_wbc_imgs_and_cords(self):
        #TODO find wbcs split between images
        counter = 0
        final_wbcs = []
        for wbc_data in self.identified_wbcs:
            wbc_lst = wbc_data[0]
            if len(wbc_lst) > 0:
                for wbc in wbc_lst:
                    wbc_xyxy = self.make_wbc_xyxy(wbc.xyxy[0])
                    cropped_img = self.generate_wbc_img(wbc_xyxy, wbc_data[1], counter)
                    self.save_img(cropped_img, counter)
                    coordinates = self.get_wbc_coordinates(wbc_xyxy, wbc_data[1])
                    final_wbcs.append([f'{self.save_loc}/wbcs/{counter}.png', counter, coordinates])
                    counter += 1
        return final_wbcs

    def generate_wbc_img(self, wbc_xyxy, img_src, counter):
        margin = 20
        lower_x_bound = int(wbc_xyxy[0]-margin)
        if lower_x_bound < 0:
            lower_x_bound = 0
        lower_y_bound = int(wbc_xyxy[1]-margin)
        if lower_y_bound < 0:
            lower_y_bound = 0
        upper_x_bound = int(wbc_xyxy[2]+margin)
        if upper_x_bound > self.id_tile_size:
            upper_x_bound = self.id_tile_size
        upper_y_bound = int(wbc_xyxy[3]+margin)
        if upper_y_bound > self.id_tile_size:
            upper_y_bound = self.id_tile_size
        img = cv2.imread(f'{self.save_loc}/tiles_id/{img_src}')
        cropped_img = img[lower_y_bound:upper_y_bound, lower_x_bound:upper_x_bound]
        return cropped_img

    def get_wbc_coordinates(self, wbc_xyxy, src):
        lower_x_bound = int(wbc_xyxy[0])
        lower_y_bound = int(wbc_xyxy[1])
        upper_x_bound = int(wbc_xyxy[2])
        upper_y_bound = int(wbc_xyxy[3])
        x_coordinate = (upper_x_bound+lower_x_bound)/2
        y_coordinate = (upper_y_bound+lower_y_bound)/2

        these_coordinates = src.split('.')
        y_tile = int(these_coordinates[1])
        x_tile = int(these_coordinates[2])

        #basically % way across id image is cords * factor which is ratio of percent of image taken up by real stuff * tile size to go from percentage to acctual coordinate
        x = ((x_tile+(x_coordinate/self.id_tile_size))/self.coordinate_factors[0][0])*self.coordinate_factors[1][0]*self.view_tile_size
        y = -((y_tile+(y_coordinate/self.id_tile_size))/self.coordinate_factors[0][1])*self.coordinate_factors[1][1]*self.view_tile_size
        f_lower_x_bound = ((x_tile+(lower_x_bound/self.id_tile_size))/self.coordinate_factors[0][0])*self.coordinate_factors[1][0]*self.view_tile_size
        f_lower_y_bound = -((y_tile+(lower_y_bound/self.id_tile_size))/self.coordinate_factors[0][1])*self.coordinate_factors[1][1]*self.view_tile_size
        f_upper_x_bound = ((x_tile+(upper_x_bound/self.id_tile_size))/self.coordinate_factors[0][0])*self.coordinate_factors[1][0]*self.view_tile_size
        f_upper_y_bound = -((y_tile+(upper_y_bound/self.id_tile_size))/self.coordinate_factors[0][1])*self.coordinate_factors[1][1]*self.view_tile_size

        return [y, x, f_lower_x_bound, f_lower_y_bound, f_upper_x_bound, f_upper_y_bound]

    def make_wbc_xyxy(self, xyxy_data):
        wbc_xyxy = []
        wbc_xyxy.append(xyxy_data[0].item())
        wbc_xyxy.append(xyxy_data[1].item())
        wbc_xyxy.append(xyxy_data[2].item())
        wbc_xyxy.append(xyxy_data[3].item())
        return wbc_xyxy

    def save_img(self, img, counter):
        cv2.imwrite(f'{self.save_loc}/wbcs/{counter}.png', img)

    def add_wbc_img(self, img_id, lat_lower, lat_upper, lng_lower, lng_upper):
        lower_x_bound, lower_y_bound, upper_x_bound, upper_y_bound, img_x, img_y = self.get_wbc_bounds(self.coordinate_factors, lat_lower, lat_upper, lng_lower, lng_upper, self.id_tile_size, self.view_tile_size)
        img = cv2.imread(f'{self.save_loc}/tiles_id/0.{img_y}.{img_x}.png')
        cropped_img = img[lower_y_bound:upper_y_bound, lower_x_bound:upper_x_bound]
        cv2.imwrite(f'{self.save_loc}/wbcs/{img_id}.png', cropped_img)

    def get_wbc_bounds(self, coordinate_factors, lat_lower, lat_upper, lng_lower, lng_upper, tile_size, tile_size_2):
        #TODO create images across id tiles
        lower_x_bound = ((lng_upper*tile_size)*coordinate_factors[0][0])/coordinate_factors[1][0]/tile_size_2
        lower_y_bound = -((lat_lower*tile_size)*coordinate_factors[0][1])/coordinate_factors[1][1]/tile_size_2
        upper_x_bound = lng_lower/tile_size_2*tile_size*coordinate_factors[0][0]/coordinate_factors[1][0]
        upper_y_bound = -((lat_upper*tile_size)*coordinate_factors[0][1])/coordinate_factors[1][1]/tile_size_2

        x_tile = int(upper_x_bound/tile_size)
        upper_x_bound = int(upper_x_bound-x_tile*tile_size)
        x_tile = int(lower_x_bound/tile_size)
        lower_x_bound = int(lower_x_bound-x_tile*tile_size)
        if lower_x_bound > upper_x_bound:
            lower_x_bound = 0

        y_tile = int(upper_y_bound/tile_size)
        upper_y_bound = int(upper_y_bound-y_tile*tile_size)
        y_tile = int(lower_y_bound/tile_size)
        lower_y_bound = int(lower_y_bound-y_tile*tile_size)
        if lower_y_bound > upper_y_bound:
            lower_y_bound = 0

        return lower_x_bound, lower_y_bound, upper_x_bound, upper_y_bound, x_tile, y_tile

    def get_tiles(self, zoom_target=0):
        identify_tiles = []
        for tile in os.listdir(f'{self.save_loc}/tiles_id'):
            if tile[:1] == str(zoom_target):
                identify_tiles.append(tile)
        return identify_tiles

class WbcIdentificationHandler():
    def __init__(self, save_loc):
        self.save_loc = save_loc

    def identify_wbcs(self, imgs, confidence=0.3):
        #TODO scan for good areas of slide
        identified_wbcs = []
        model = YOLO('slide_analyzer/static/best.pt')
        for img in imgs:
            results = model(f'{save_loc}/tiles_id/{img}')
            boxes = []
            for box in results[0].boxes:
                if box.conf > confidence:
                    boxes.append(box)
            identified_wbcs.append([boxes, img])
        return identified_wbcs

class SlideCaptureHandler():
    def __init__(self, slide, microscope_ip, wbc_count, timeout, id_tile_size_x=3280, id_tile_size_y=2464):
        self.slide = slide
        self.ip = microscope_ip
        self.wbc_count = wbc_count
        self.microscope = ofm_client.find_first_microscope()
        self.original_position = self.microscope.position.copy()
        self.direction = 'pos'
        self.x_moves = 0
        self.target_x_moves = 8
        self.id_tile_size_y = id_tile_size_y
        self.id_tile_size_x = id_tile_size_x
        self.timeout = timeout
        self.counter = 0
        self.wbc_counter = 0
        self.all_identified_wbcs = []

    def next_capture(self):
        if self.wbc_counter < self.wbc_count and self.counter < self.timeout:
            identified_wbcs = self.wbc_capture()
            return identified_wbcs, self.wbc_counter, self.counter
        else:
            self.microscope.move(self.original_position)
            return 'complete', self.wbc_counter, self.counter

    def wbc_capture(self):
        img = self.capture_images()
        img.save(f'media/slide_{self.slide}/tiles_id/{self.counter}.png')
        wbc_id = WbcIdentificationHandler(self.slide, '_id')
        identified_wbcs_data = wbc_id.identify_wbcs([f'{self.counter}.png'])
        identified_wbcs = []
        for wbc in identified_wbcs_data:
            if len(wbc[0]) > 0:
                wbc_xyxy = self.make_wbc_xyxy(wbc[0][0].xyxy[0])
                wbc_img = self.generate_wbc_img(wbc_xyxy, f'{self.counter}.png')
                self.save_img(wbc_img, self.wbc_counter)
                identified_wbcs.append([self.wbc_counter, f'media/slide_{self.slide}/wbcs/{self.wbc_counter}.png'])
                self.wbc_counter += 1
        self.counter += 1
        self.move_pos()
        return identified_wbcs

    def capture_images(self, takes=3):
        imgs = []
        self.microscope.autofocus()
        img = self.run_img_cap()
        imgs.append(img)
        for i in range(0, takes-1):
            self.microscope.laplacian_autofocus({})
            img = self.run_img_cap()
            imgs.append(img)
        img = self.least_blurry(imgs)
        return img
        #return img with lowest laplace try to sticth...

    def least_blurry(self, imgs):
        least_blurry = ''
        least_blurry_value = 0
        for img in imgs:
            cv2img = pil_to_cv2(img)
            gray = cv2.cvtColor(cv2img, cv2.COLOR_BGR2GRAY)
            laplace = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplace > least_blurry_value:
                least_blurry = img
                least_blurry_value = laplace
        return least_blurry

    def run_img_cap(self):
        img = None
        while img == None:
            try:
                img = capture_full_image(self.microscope)
            except Exception as e:
                sleep(2)
                print(e)
        return img

    def move_pos(self):
        if self.x_moves == self.target_x_moves-1:
            self.reverse_direction()
            self.x_moves = 0
            self.move_y_pos()
        else:
            self.move_x_pos()
            self.x_moves += 1

    def reverse_direction(direction):
        if direction == 'pos':
            direction = 'neg'
        elif direction == 'neg':
            direction = 'pos'
        return direction

    def move_x_pos(self, x_step=2500):
        pos = self.microscope.position
        if self.direction == 'pos':
            pos['x'] += x_step
        if self.direction == 'neg':
            pos['x'] -= x_step
        self.microscope.move(pos)

    def move_y_pos(self, y_step=2500):
        pos = self.microscope.position
        pos['y'] += y_step
        self.microscope.move(pos)

    def reverse_direction(self):
        if self.direction == 'pos':
            self.direction = 'neg'
        elif self.direction == 'neg':
            self.direction = 'pos'

    def generate_wbc_img(self, wbc_xyxy, img_src):
        margin = 20
        lower_x_bound = int(wbc_xyxy[0]-margin)
        if lower_x_bound < 0:
            lower_x_bound = 0
        lower_y_bound = int(wbc_xyxy[1]-margin)
        if lower_y_bound < 0:
            lower_y_bound = 0
        upper_x_bound = int(wbc_xyxy[2]+margin)
        if upper_x_bound > self.id_tile_size_x:
            upper_x_bound = self.id_tile_size_x
        upper_y_bound = int(wbc_xyxy[3]+margin)
        if upper_y_bound > self.id_tile_size_y:
            upper_y_bound = self.id_tile_size_y
        img = cv2.imread(f'media/slide_{self.slide}/tiles_id/{img_src}')
        cropped_img = img[lower_y_bound:upper_y_bound, lower_x_bound:upper_x_bound]
        return cropped_img

    def make_wbc_xyxy(self, xyxy_data):
        wbc_xyxy = []
        wbc_xyxy.append(xyxy_data[0].item())
        wbc_xyxy.append(xyxy_data[1].item())
        wbc_xyxy.append(xyxy_data[2].item())
        wbc_xyxy.append(xyxy_data[3].item())
        return wbc_xyxy

    def save_img(self, img, counter):
        cv2.imwrite(f'media/slide_{self.slide}/wbcs/{counter}.png', img)

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

def pil_to_cv2(img):
    pil_image = img.convert('RGB')
    open_cv_image = numpy.array(pil_image)
    # Convert RGB to BGR
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image
