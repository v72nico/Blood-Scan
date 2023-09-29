import cv2
import numpy as np

class Tiler():
    def __init__(self, raw_img, tile_size, max_scale=None, save_loc=''):
        self.original_img = cv2.imread(raw_img)
        self.tile_size = tile_size
        self.save_loc = save_loc
        if max_scale == None:
            self.max_scale = self.get_scale()
        else:
            self.max_scale = max_scale

    def tile_image(self):
        part_coordinate_factors = []
        for i in range(self.max_scale,-1,-1):
            scale_part_coordinate_factors = self.tile_img_at_scale(i)
            if scale_part_coordinate_factors != []:
                part_coordinate_factors = scale_part_coordinate_factors

        return self.max_scale, part_coordinate_factors

    def tile_img_at_scale(self, this_scale):
        resize_factor = self.max_scale-this_scale
        resized_img = self.resize_img(resize_factor)

        part_coordinate_factors = []
        if this_scale == 0:
            scale_0_size = self.get_scale_0_size(len(resized_img[0]), len(resized_img))
            scale_0_xy = self.get_percent_img_used(len(resized_img[0]), len(resized_img))
            part_coordinate_factors = [scale_0_size, scale_0_xy]

        self.tile_core_img(resized_img, this_scale)
        #REMAINDER
        self.tile_remainder_img(resized_img, this_scale)

        return part_coordinate_factors

    def get_scale_0_size(self, x_len, y_len):
        cord_y_len = int(y_len/self.tile_size)+1
        cord_x_len = int(x_len/self.tile_size)+1
        scale_0_size = [cord_x_len, cord_y_len]

        return scale_0_size

    def get_percent_img_used(self, x_len, y_len):
        scale_0_xy = []
        cord_y_len = int(y_len/self.tile_size)+1
        cord_x_len = int(x_len/self.tile_size)+1
        scale_0_xy.append((x_len+1)/(self.tile_size*cord_x_len))
        scale_0_xy.append((y_len+1)/(self.tile_size*cord_y_len))

        return scale_0_xy

    def get_scale(self):
        scale = 0
        for i in range(0,10):
            this_scale = self.tile_size*2**i
            if len(self.original_img) > this_scale or len(self.original_img[0]) > this_scale:
                scale = i+1
        return scale

    def resize_img(self, resize_factor):
        if resize_factor != 0:
            y_resize = int(len(self.original_img)/(2**resize_factor))
            x_resize = int(len(self.original_img[0])/(2**resize_factor))
            new_img = cv2.resize(self.original_img, (x_resize, y_resize))
        else:
            new_img = self.original_img
        return new_img

    def tile_core_img(self, img, layer):
        y_len = int(len(img)/self.tile_size)
        x_len = int(len(img[0])/self.tile_size)
        for j in range(0,x_len):
            for l in range(0,y_len):
                tile = img[self.tile_size*l:self.tile_size*l+self.tile_size, self.tile_size*j:self.tile_size*j+self.tile_size]
                self.save_img(tile, l, j, layer)

    def tile_remainder_img(self, img, layer):
        y_len = int(len(img)/self.tile_size)
        x_len = int(len(img[0])/self.tile_size)
        x_remainder = len(img[0])%self.tile_size
        y_remainder = len(img)%self.tile_size
        if y_remainder > 0:
            for j in range(0, x_len):
                this_tile = img[y_len*self.tile_size:y_len*self.tile_size+y_remainder, self.tile_size*j:self.tile_size*j+self.tile_size]
                final_tile = np.zeros((self.tile_size,self.tile_size,3), np.uint8)
                final_tile[:, :] = (0,0,0)
                final_tile[:this_tile.shape[0], :this_tile.shape[1]] = this_tile
                self.save_img(final_tile, y_len, j, layer)
        if x_remainder > 0:
            for j in range(0, y_len):
                this_tile = img[self.tile_size*j:self.tile_size*j+self.tile_size, x_len*self.tile_size:x_len*self.tile_size+x_remainder]
                final_tile = np.zeros((self.tile_size,self.tile_size,3), np.uint8)
                final_tile[:, :] = (0,0,0)
                final_tile[:this_tile.shape[0], :this_tile.shape[1]] = this_tile
                self.save_img(final_tile, j, x_len, layer)
        if x_remainder > 0 and y_remainder > 0:
            this_tile = img[y_len*self.tile_size:y_len*self.tile_size+y_remainder, x_len*self.tile_size:x_len*self.tile_size+x_remainder]
            final_tile = np.zeros((self.tile_size,self.tile_size,3), np.uint8)
            final_tile[:, :] = (0,0,0)
            final_tile[:this_tile.shape[0], :this_tile.shape[1]] = this_tile
            self.save_img(final_tile, y_len, x_len, layer)

    def save_img(self, tile, y, x, z):
        cv2.imwrite(f'{save_loc}/{z}.{y}.{x}.png', tile)
