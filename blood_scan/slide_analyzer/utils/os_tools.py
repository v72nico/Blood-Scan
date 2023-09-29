import os
import shutil

def make_slide_dirs(slide):
    ''' Create directories for slide data '''
    if os.path.isdir(f'media/slide_{slide}'):
        shutil.rmtree(f'media/slide_{slide}')
    os.mkdir(f'media/slide_{slide}')
    os.mkdir(f'media/slide_{slide}/tiles')
    os.mkdir(f'media/slide_{slide}/tiles_id')
    os.mkdir(f'media/slide_{slide}/wbcs')
