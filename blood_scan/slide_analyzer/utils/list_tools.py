def get_slide_numbers(slides):
    slide_numbers = []
    for slide in slides:
        slide_numbers.append(slide.number)
    return slide_numbers

def make_microscope_lst(microscope_data):
    microscopes = []
    for microscope in microscope_data:
        microscopes.append([microscope.ip, microscope.slide, microscope.current_wbc, microscope.target_wbc, microscope.current_field, microscope.target_field])
    return microscopes

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

def get_morphology(morphology_data):
    return_lst = []
    morphology_lst = morphology_data.split("|")[1:]
    for morphology in morphology_lst:
        morphology_type, morphology_value = morphology.split(":")
        return_lst.append([morphology_type, morphology_value])
    return return_lst
