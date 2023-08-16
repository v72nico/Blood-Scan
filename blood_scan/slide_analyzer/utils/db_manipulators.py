from slide_analyzer.models import *
from slide_analyzer.utils.utils import string_to_coordinate_factors, add_wbc_img

class MicroscopeHandler():
    def make_microscope_data(ip, target_wbc, field_limit, slide):
        if len(MicroscopeUse.objects.filter(ip=ip)) == 0:
            microscope = MicroscopeUse(ip=ip, in_use=False, slide=slide, current_wbc=0, target_wbc=target_wbc, current_field=0, target_field=field_limit)
            microscope.save()

    def toggle_microscope_use(ip):
        microscope = MicroscopeUse.objects.get(ip=ip)
        if microscope.in_use == False:
            microscope.in_use = True
        elif microscope.in_use == True:
            microscope.in_use = False
        microscope.save()

class ActionHandler():
    def __init__(self):
        pass

    def handle_action(self, request, action, slide):
        if action == 'key_update':
            key_update(request)
        if slide != None and slide != '' and slide != 'null':
            if action == 'morphology_update':
                self.morphology_update(request, slide)
            if action == 'type_update':
                self.type_update(request, slide)
            if action == 'delete_wbc':
                self.delete_wbc(request, slide)
            if action == 'add_wbc':
                self.add_wbc(request, slide)
            if action == 'update_wbc':
                self.update_wbc(request, slide)
            if action == 'delete_slide':
                self.delete_slide(slide)

    def update_wbc(self, request, slide):
        img_id = request.GET["id"]
        print(img_id)
        this_type = WBCImg.objects.filter(slide=slide, imgID=img_id).get().type
        self.delete_wbc(request, slide)
        self.add_wbc(request, slide, wbc_type=this_type)

    def delete_slide(self, slide):
        Slide.objects.filter(number=slide).delete()
        WBCImg.objects.filter(slide=slide).delete()
        shutil.rmtree(f"media/slide_{slide}")

    def add_wbc(self, request, slide, wbc_type="unsorted"):
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
        new_wbc = WBCImg(type=wbc_type, src=f'media/slide_{slide}/wbcs/{img_id}.png', slide=slide, imgID=img_id, lat=lat, lng=lng, lat_lower=lat_lower, lat_upper=lat_upper, lng_lower=lng_lower, lng_upper=lng_upper)
        new_wbc.save()

    def delete_wbc(self, request, slide):
        img_id = request.GET["id"]
        item = WBCImg.objects.get(imgID=img_id, slide=slide)
        item.delete()

    def morphology_update(self, request, slide):
        morphology = request.GET["morphology"]
        grade = request.GET["grade"]
        item = Slide.objects.get(number=slide)
        morphology_str = item.morphology
        new_morphology_str = self.change_morphology_str(morphology_str, morphology, grade)
        item.morphology = new_morphology_str
        item.save()

    def type_update(self, request, slide):
        img_id = request.GET["id"]
        type = request.GET["type"]
        item = WBCImg.objects.get(imgID=img_id, slide=slide)
        item.type = type
        item.save()

    def key_update(self, request):
        key_bind = request.GET["key_bind"]
        type = type = request.GET["type"]
        slide = -1
        item = WBCDiffConfig.objects.get(type=type)
        item.key_bind = key_bind
        item.save()
    def change_morphology_str(self, morphology_str, morphology, grade):
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
