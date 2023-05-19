from django.shortcuts import render
from django.http import HttpRequest
import os, shutil
import threading

from slide_analyzer.models import *
from slide_analyzer.utils.utils import WbcImageHandler, SlideCaptureHandler, save_upload, calc_coordinate_factors, coordinate_factors_to_string, string_to_coordinate_factors, add_wbc_img
from slide_analyzer.utils.tiling import Tiler
from slide_analyzer.forms import UploadForm, CaptureForm

def home(request):
    """ Handles get requests for home page """
    slide = handle_query(request)
    slides = Slide.objects.all()
    slide_numbers = get_slide_numbers(slides)
    return render(request, 'home.html', {'slides': slide_numbers})

def get_slide_numbers(slides):
    slide_numbers = []
    for slide in slides:
        slide_numbers.append(slide.number)
    return slide_numbers

def status(request):
    microscope_data = MicroscopeUse.objects.filter(in_use=True)
    microscopes = make_microscope_lst(microscope_data)
    return render(request, 'status.html', {'microscopes': microscopes})

def make_microscope_lst(microscope_data):
    microscopes = []
    for microscope in microscope_data:
        microscopes.append([microscope.ip, microscope.slide, microscope.current_wbc, microscope.target_wbc, microscope.current_field, microscope.target_field])
    return microscopes

def capture(request):
    if request.method == 'POST':
        form = CaptureForm(request.POST)
        if form.is_valid():
            slide = form.cleaned_data['slide']
            microscope_ip = form.cleaned_data['microscope_ip']
            wbc_count = form.cleaned_data['wbc_count']
            duplicate_slides = Slide.objects.filter(number=slide)
            make_microscope_data(microscope_ip, wbc_count, slide)
            microscope_in_use = MicroscopeUse.objects.get(ip=microscope_ip)
            if microscope_in_use.in_use == False:
                if len(duplicate_slides) == 0:
                    toggle_microscope_use(microscope_ip)
                    t = threading.Thread(target=make_slide_data_capture, args=[slide, microscope_ip, wbc_count], daemon=True)
                    t.start()
                else:
                    form.errors[''] = "Error: Slide number already exists"
            else:
                form.errors[''] = "Error: Microscope In Use"
        return render(request, 'capture.html', {'form': form})
    if request.method == 'GET':
        form = CaptureForm()
        return render(request, 'capture.html', {'form': form})

def make_microscope_data(ip, target_wbc, slide):
    if len(MicroscopeUse.objects.filter(ip=ip)) == 0:
        microscope = MicroscopeUse(ip=ip, in_use=False, slide=slide, current_wbc=0, target_wbc=target_wbc, current_field=0, target_field=100)
        microscope.save()

def toggle_microscope_use(ip):
    microscope = MicroscopeUse.objects.get(ip=ip)
    if microscope.in_use == False:
        microscope.in_use = True
    elif microscope.in_use == True:
        microscope.in_use = False
    microscope.save()

def make_slide_data_capture(slide, microscope_ip, wbc_count, timeout=100):
    make_slide_dirs(slide)
    thisSlide = Slide(number=slide, max_zoom=0, coordinate_factors='blank')
    thisSlide.save()
    microscope = MicroscopeUse.objects.get(ip=microscope_ip)
    try:
        CaptureHandler = SlideCaptureHandler(slide, microscope_ip, wbc_count, timeout)
        while True:
            wbc_data_lst, wbc_counter, counter = CaptureHandler.next_capture()
            microscope.current_wbc = wbc_counter
            microscope.current_field = counter
            microscope.save()
            if wbc_data_lst == 'complete':
                break
            for wbc_data in wbc_data_lst:
                thisWBC = WBCImg(type="unsorted", slide=slide, imgID=int(wbc_data[0]), src=wbc_data[1], lat=0, lng=0, lng_lower=0, lat_lower=0, lng_upper=0, lat_upper=0)
                thisWBC.save()
        microscope.delete()
    except Exception as e:
        print('Error:', e)
        microscope.delete()

def upload(request):
    """ Handle upload post requests by saving uploaded files and making slide data from uploaded images and returning upload form or get requests by returning upload form """
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            slide = form.cleaned_data['slide']
            save_upload(request.FILES['file'])
            duplicate_slides = Slide.objects.filter(number=slide)
            if len(duplicate_slides) == 0:
                make_slide_data_upload(slide)
            else:
                form.errors[''] = "Error: Slide number already exists"
        return render(request, 'upload.html', {'form': form})
    if request.method == 'GET':
        form = UploadForm()
        return render(request, 'upload.html', {'form': form})

def make_slide_data_upload(slide):
    """ Tile slide, save slide to database, identify wbcs and generate imgs and coordinates based on identifications """
    make_slide_dirs(slide)
    view_tiler = Tiler('media/upload.png', slide, 256)
    max_zoom, coordinate_factors_tiles = view_tiler.tile_image()
    identify_tiler = Tiler('media/upload.png', slide, 2464, max_scale=0, save_loc='_id')
    _, coordinate_factors_full_res = identify_tiler.tile_image()
    coordinate_factors = calc_coordinate_factors(coordinate_factors_tiles, coordinate_factors_full_res)

    cf_str = coordinate_factors_to_string(coordinate_factors)

    thisSlide = Slide(number=slide, max_zoom=max_zoom, coordinate_factors=cf_str)
    thisSlide.save()

    wbc_image_handler = WbcImageHandler(slide, coordinate_factors, 2464, 256, '_id')
    wbc_data_lst = wbc_image_handler.generate_wbc_imgs_and_cords()

    for wbc_data in wbc_data_lst:
        thisWBC = WBCImg(type="unsorted", slide=slide, imgID=wbc_data[1], src=wbc_data[0], lat=wbc_data[2][0], lng=wbc_data[2][1], lng_lower=wbc_data[2][2], lat_lower=wbc_data[2][3], lng_upper=wbc_data[2][4], lat_upper=wbc_data[2][5])
        thisWBC.save()

def make_slide_dirs(slide):
    ''' Create directories for slide data '''
    if os.path.isdir(f'media/slide_{slide}'):
        shutil.rmtree(f'media/slide_{slide}')
    os.mkdir(f'media/slide_{slide}')
    os.mkdir(f'media/slide_{slide}/tiles')
    os.mkdir(f'media/slide_{slide}/tiles_id')
    os.mkdir(f'media/slide_{slide}/wbcs')

def wbc_view(request):
    """ Handles get requests for WBC View pages by returing appriate slide data and WBC configs"""
    slide = handle_query(request)
    wbc_types_data = WBCDiffConfig.objects.all()
    wbc_types, wbc_categories = get_wbc_types(wbc_types_data)
    wbc_img_lst = []
    if slide != None and slide != '' and slide != 'null':
        wbc_data_lst = WBCImg.objects.filter(slide=slide)
        for i in range(0, len(wbc_data_lst)):
            wbc_img_lst.append([wbc_data_lst[i].src, wbc_data_lst[i].imgID, wbc_data_lst[i].type])
    return render(request, 'wbc_view.html', {'wbc_imgs': wbc_img_lst, 'wbc_types': wbc_types, 'wbc_categories': wbc_categories})

def slide_view(request):
    """ Handles get requests for Slide View pages by returing appriate slide data, WBC configs, and morphology configs """
    slide = handle_query(request)

    wbc_types_data = WBCDiffConfig.objects.all()
    wbc_types, wbc_categories = get_wbc_types(wbc_types_data)

    morphology_data = MorphologyConfig.objects.all()
    morphology_types, morphology_categories = get_morphology_types(morphology_data)

    wbc_counts = []
    wbc_img_lst = []
    max_zoom = 0
    slide_morphology = []
    if slide != None and slide != '' and slide != 'null':
        wbc_img_data_lst = WBCImg.objects.filter(slide=slide)
        wbc_img_lst = []
        for i in range(0, len(wbc_img_data_lst)):
            wbc_img_lst.append([wbc_img_data_lst[i].src, wbc_img_data_lst[i].imgID, wbc_img_data_lst[i].type, wbc_img_data_lst[i].lat, wbc_img_data_lst[i].lng, wbc_img_data_lst[i].lat_lower, wbc_img_data_lst[i].lng_lower, wbc_img_data_lst[i].lat_upper, wbc_img_data_lst[i].lng_upper])
        wbc_counts = get_wbc_counts(wbc_img_data_lst)

        slide_data = Slide.objects.filter(number=slide)
        if len(slide_data) > 0:
            slide_morphology_data = slide_data[0].morphology
            slide_morphology = get_morphology(slide_morphology_data)
            max_zoom = slide_data[0].max_zoom

    return render(request, 'slide_view.html', {'wbc_types': wbc_types, 'wbc_categories': wbc_categories, 'wbc_counts': wbc_counts, 'morphology_types': morphology_types, 'morphology_categories': morphology_categories, 'slide_morphology': slide_morphology, 'wbc_imgs': wbc_img_lst, 'slide': slide, 'max_zoom': max_zoom})

def get_wbc_types(wbc_types_data):
    """ Converts WBC config database data to a list of parent catagories and list of each type, category and key bind """
    wbc_types = []
    wbc_categories = []
    for wbc_type in wbc_types_data:
        if wbc_type.key_bind == None:
            this_key_bind = ''
        else:
            this_key_bind = wbc_type.key_bind
        wbc_types.append([wbc_type.type, wbc_type.parent, this_key_bind])
        if wbc_type.parent != "None":
            if wbc_type.parent not in wbc_categories:
                wbc_categories.append(wbc_type.parent)
    return wbc_types, wbc_categories

def get_wbc_counts(wbc_img_data_lst):
    """ Creates dictionary of amounts of each type of WBC from WBC image data """
    wbc_count = {}
    for wbc_img in wbc_img_data_lst:
        if wbc_img.type not in wbc_count:
            wbc_count[wbc_img.type] = 1
        else:
            wbc_count[wbc_img.type] += 1
    return wbc_count

def get_morphology_types(morphology_data):
    morphology_types = []
    morphology_categories = []
    for morphology_type in morphology_data:
        morphology_types.append([morphology_type.type, morphology_type.parent, morphology_type.quantitative])
        if morphology_type.parent not in morphology_categories:
            morphology_categories.append(morphology_type.parent)
    return morphology_types, morphology_categories

def handle_query(request):
    try:
        slide = request.GET["slide"]
    except:
        slide = None
    try:
        action = request.GET['action']
    except:
        action = None
    if action != None:
        handle_action(request, action, slide)
    return slide

def handle_action(request, action, slide):
    if action == 'key_update':
        key_update(request)
    if slide != None and slide != '' and slide != 'null':
        if action == 'morphology_update':
            morphology_update(request, slide)
        if action == 'type_update':
            type_update(request, slide)
        if action == 'delete_wbc':
            delete_wbc(request, slide)
        if action == 'add_wbc':
            add_wbc(request, slide)
        if action == 'delete_slide':
            delete_slide(slide)

def delete_slide(slide):
    Slide.objects.filter(number=slide).delete()
    WBCImg.objects.filter(slide=slide).delete()
    shutil.rmtree(f"media/slide_{slide}")

def add_wbc(request, slide):
    img_id = request.GET["id"]
    lat_lower = float(request.GET["lat_lower"])
    lat_upper = float(request.GET["lat_upper"])
    lng_lower = float(request.GET["lng_lower"])
    lng_upper = float(request.GET["lng_upper"])
    cf_str = Slide.objects.get(number=slide).coordinate_factors
    coordinate_factors = string_to_coordinate_factors(cf_str)
    add_wbc_img(slide, img_id, coordinate_factors, lat_lower, lat_upper, lng_lower, lng_upper)
    lng = (lng_upper+lng_lower)/2
    lat = (lat_upper+lat_lower)/2
    new_wbc = WBCImg(type='unsorted', src=f'media/slide_{slide}/wbcs/{img_id}.png', slide=slide, imgID=img_id, lat=lat, lng=lng, lat_lower=lat_lower, lat_upper=lat_upper, lng_lower=lng_lower, lng_upper=lng_upper)
    new_wbc.save()

def delete_wbc(request, slide):
    img_id = request.GET["id"]
    item = WBCImg.objects.get(imgID=img_id, slide=slide)
    item.delete()

def morphology_update(request, slide):
    morphology = request.GET["morphology"]
    grade = request.GET["grade"]
    item = Slide.objects.get(number=slide)
    morphology_str = item.morphology
    new_morphology_str = change_morphology_str(morphology_str, morphology, grade)
    item.morphology = new_morphology_str
    item.save()

def type_update(request, slide):
    img_id = request.GET["id"]
    type = request.GET["type"]
    item = WBCImg.objects.get(imgID=img_id, slide=slide)
    item.type = type
    item.save()

def key_update(request):
    key_bind = request.GET["key_bind"]
    type = type = request.GET["type"]
    slide = -1
    item = WBCDiffConfig.objects.get(type=type)
    item.key_bind = key_bind
    item.save()

def change_morphology_str(morphology_str, morphology, grade):
    spot = morphology_str.find("|" + morphology + ":")
    if spot == -1:
        morphology_str += "|" + morphology + ":" + grade
    else:
        end = morphology_str.find("|", spot+1)
        if end == -1:
            end = len(morphology_str)
        start = spot
        morphology_str = morphology_str[:start] + "|" + morphology + ":" + grade + morphology_str[end:]
    return morphology_str

def get_morphology(morphology_data):
    return_lst = []
    morphology_lst = morphology_data.split("|")[1:]
    for morphology in morphology_lst:
        morphology_type, morphology_value = morphology.split(":")
        return_lst.append([morphology_type, morphology_value])
    return return_lst
