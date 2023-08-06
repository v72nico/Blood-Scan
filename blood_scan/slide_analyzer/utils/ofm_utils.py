from openflexure_microscope_client import *
import os
import requests
import json
import PIL
import io

def capture_full_image(self, params: dict = None):
    """Capture an image at full resolution and return it as PIL image object"""
    payload = {
        "use_video_port": False,
        "bayer": False,
        "filename": "py_capture",
        "temporary" : True
    }
    if params:
        payload.update(params)
    r = requests.post(self.base_uri + "/actions/camera/capture", json=payload)
    r.raise_for_status()
    captures_response = requests.get(self.base_uri + "/captures")
    captures_response.raise_for_status()
    json_response = json.loads(captures_response.content)
    target_id = ''
    for img_json in json_response[::-1]:
        if img_json['name'] == 'py_capture.jpeg':
            target_id = img_json['id']
            break
    img_response = requests.get(self.base_uri + f"/captures/{target_id}/download/py_capture.jpeg")
    img_response.raise_for_status()
    image = PIL.Image.open(io.BytesIO(img_response.content))
    return image

def main():
    top_file = 0
    files = os.listdir('capture set')
    for file in files:
        if int(file[8:-4]) >= top_file:
            top_file = int(file[8:-4])+1

    microscope = find_first_microscope()
    img = microscope.capture_full_image()
    #img = microscope.capture_image_to_disk({"resize": {"width": '3280', "height": '2464'}})
    img.save(f'capture set/capture_{str(top_file)}.jpg')
