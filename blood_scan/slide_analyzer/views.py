from django.shortcuts import render
from django.http import HttpRequest
from slide_analyzer.models import *
import os, shutil
from slide_analyzer.utils import tile_image, identify_wbcs, get_tiles, generate_wbc_imgs, save_upload, calc_coordinate_factors
from slide_analyzer.forms import UploadForm

def home(request):
    return render(request, 'home.html', {})

def upload(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            slide = form.cleaned_data['slide']
            save_upload(request.FILES['file'])
            duplicate_slides = Slide.objects.filter(number=slide)
            if len(duplicate_slides) == 0:
                make_slide_data(slide)
            else:
                form.errors[''] = "Slide number already exists"
        return render(request, 'upload.html', {'form': form})
    if request.method == 'GET':
        form = UploadForm()
        return render(request, 'upload.html', {'form': form})

def make_slide_data(slide):
    make_slide_dirs(slide)
    max_zoom, coordinate_factors_tiles = tile_image('media/upload.png', slide)
    _, coordinate_factors_full_res = tile_image(f'media/upload.png', slide, tile_size=2464, scale=0, save_loc='_id')
    coordinate_factors = calc_coordinate_factors(coordinate_factors_tiles, coordinate_factors_full_res)

    thisSlide = Slide(number=slide, max_zoom=max_zoom)
    thisSlide.save()

    identify_tiles = get_tiles(slide, '_id')
    identified_wbcs = identify_wbcs(slide, identify_tiles, save_loc='_id')
    wbc_src_lst = generate_wbc_imgs(slide, identified_wbcs, coordinate_factors, save_loc='_id', tile_size=2464, tile_size_2=256)
    for wbc_src in wbc_src_lst:
        thisWBC = WBCImg(type="unsorted", slide=slide, imgID=wbc_src[1], src=wbc_src[0], lat=wbc_src[2][0], lng=wbc_src[2][1], lng_lower=wbc_src[2][2], lat_lower=wbc_src[2][3], lng_upper=wbc_src[2][4], lat_upper=wbc_src[2][5])
        thisWBC.save()

def make_slide_dirs(slide):
    os.makedirs(f'media/slide_{slide}/tiles')
    os.makedirs(f'media/slide_{slide}/tiles_id')
    os.makedirs(f'media/slide_{slide}/wbcs')

def wbc_view(request):
    slide = handle_query(request)
    wbc_data_lst = WBCImg.objects.filter(slide=slide)
    wbc_img_lst = []
    for i in range(0, len(wbc_data_lst)):
        wbc_img_lst.append([wbc_data_lst[i].src, wbc_data_lst[i].imgID, wbc_data_lst[i].type])
    wbc_types_data = WBCDiffConfig.objects.all()
    wbc_types, wbc_categories = get_wbc_types(wbc_types_data)
    return render(request, 'wbc_view.html', {'wbc_imgs': wbc_img_lst, 'wbc_types': wbc_types, 'wbc_categories': wbc_categories})

def slide_view(request):
    slide = handle_query(request)

    wbc_types_data = WBCDiffConfig.objects.all()
    wbc_types, wbc_categories = get_wbc_types(wbc_types_data)

    morphology_data = MorphologyConfig.objects.all()
    morphology_types, morphology_categories = get_morphology_types(morphology_data)

    wbc_counts = []
    wbc_img_lst = []
    max_zoom = 0
    slide_morphology = []
    if slide != None and slide != '':
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
    wbc_types = []
    wbc_categories = []
    for wbc_type in wbc_types_data:
        wbc_types.append([wbc_type.type, wbc_type.parent, wbc_type.key_bind])
        if wbc_type.parent != "None":
            if wbc_type.parent not in wbc_categories:
                wbc_categories.append(wbc_type.parent)
    return wbc_types, wbc_categories

def get_wbc_counts(wbc_img_data_lst):
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
    if action == 'morphology_update':
        morphology_update(request, slide)
    if action == 'type_update':
        type_update(request, slide)
    if action == 'key_update':
        key_update(request)
    if action == 'delete_wbc':
        delete_wbc(request, slide)
    if action == 'add_wbc':
        add_wbc(request, slide)

def add_wbc(request, slide):
    img_id = request.GET["id"]
    lat_lower = float(request.GET["lat_lower"])
    lat_upper = float(request.GET["lat_upper"])
    lng_lower = float(request.GET["lng_lower"])
    lng_upper = float(request.GET["lng_upper"])
    print(lat_upper)
    lng = (lng_upper+lng_lower)/2
    lat = (lat_upper+lat_lower)/2
    new_wbc = WBCImg(type='unsorted', src='', slide=slide, imgID=img_id, lat=lat, lng=lng, lat_lower=lat_lower, lat_upper=lat_upper, lng_lower=lng_lower, lng_upper=lng_upper)
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
