import requests
import time
import logger
import cv2
import base64

'''
Handles delivery of data to specified endpoint
'''

DELIVERED = {}
CACHE = {}
DATA_URL = ''
IMAGES_URL = ''
DATA_FRAMES = [1, -1]
IMAGE_FRAMES = [1, 3]
SHOULD_LOG = False


def configure(data_url, images_url, data_frames, image_frames, should_log=False):
    """Settings"""
    global DATA_URL
    global IMAGES_URL
    global DATA_FRAMES
    global IMAGE_FRAMES
    global SHOULD_LOG
    DATA_URL = data_url
    IMAGES_URL = images_url
    DATA_FRAMES = data_frames
    IMAGE_FRAMES = image_frames
    SHOULD_LOG = should_log


def send_data(id, label):
    """Send just tracking meta data to target endpoint"""
    print('delivery.py: send_data')
    payload = {"object_id": id, "timestamp": time.time(), "label": label}
    global DATA_URL
    global SHOULD_LOG
    return send(url=DATA_URL, data=payload, files=None, should_log=SHOULD_LOG)


def send_image(id, label, image):
    """Send image of object to target endpoint"""
    global IMAGES_URL
    global SHOULD_LOG
    if image is None:
        logger.log('delivery.py: send_image: no image passed to send command', SHOULD_LOG)
        return None
    payload = {"object_id": id, "timestamp": time.time(), "label": label}

    # Attempting to use matplotlib
    # Failing here because image is a numpy array. Possible solution: https://stackoverflow.com/questions/52908088/send-an-image-as-numpy-array-requests-post
    # buf = io.BytesIO()
    # plt.imsave(buf, image, format='png')
    # image_data = buf.getvalue()
    # filesToUpload = {'image':(image_data, open(image_data, 'rb'), "multipart/form-data")}
    # ISSUE: ValueError: embedded null byte

    # Attempting to write directly with open() into a multipart form
    # filesToUpload = {'image': (image, open(
    #     image, 'rb'), "multipart/form-data")}
    # TypeError: Can't convert 'numpy.ndarray' object to str implicitly

    # Attempting to use PIL
    # image_pil = PIL.Image.fromarray(image)
    # filesToUpload = {'image': (image_pil, open(
    #     image_pil, 'rb'), "multipart/form-data")}
    # See `issues.md` for all failures related to importing PIL/Pillow

    # Attempting to write directly
    # upload_info = {'id': '1234', 'country': 'zzz'}
    # filepath = "/tmp/test.zip"
    # json_data = simplejson.dumps(upload_info)
    # json_input = StringIO(json_data)
    # fileobj = open(filepath, 'rb')
    # files = {'file': ('test.zip', fileobj), 'json_data': json_input}
    # return send(IMAGES_URL, payload, filesToUpload, SHOULD_LOG)

    # Eric's route
    # Encode image as jpeg
    image = cv2.imencode('.jpg', image)[1].tobytes()
    # Encode image in base64 representation and remove utf-8 encoding
    image = base64.b64encode(image).decode('utf-8')
    image = "data:image/jpeg;base64,{}".format(image)
    filesToUpload = {'image':image}
    # filesToUpload = {'image': (image, open(
    #     image, 'rb'), "multipart/form-data")}
    return send(IMAGES_URL, payload, filesToUpload, SHOULD_LOG)

def send(url, data=None, files=None, should_log=False):
    """Construct a post request and deliver"""
    try:
        r = requests.post(url=url, data=data)
        #r = requests.post(url=url, data=data, files=files)
        if r.status_code != 200:
            logger.log('delivery.py: send: post response code: {}, reason: {}'.format(
                    r.status_code, r.reason), should_log)
            return r
        logger.log('delivery.py: send: successful', should_log)
        return r
    except requests.exceptions.ConnectionError:
        logger.log('Connection refused for connection to: {}'.format(url), should_log)
        return 'Connection refused'
    except:
        logger.log('Unknown post request error for connection to: {}'.format(url), should_log)
        return 'Unknown post request error'

# Current
# app.py: /face_detected: request: <Request 'http://localhost:8888/face_detected' [POST]>
# app.py: /face_detected: request: data: b''
# app.py: /face_detected: request: json: None
# app.py: /face_detected: request: files: ImmutableMultiDict([])
# app.py: /face_detected: request: headers: Content-Type: application/x-www-form-urlencoded
# User-Agent: PostmanRuntime/7.21.0
# Accept: */*
# Cache-Control: no-cache
# Postman-Token: ef060ccc-1e33-48bf-acd2-c6fda160efae
# Host: localhost:8888
# Accept-Encoding: gzip, deflate
# Cookie: connect.sid=s%3A3jPfcHFcBbMNro4lgc5BNQ2Pt8eEJbMG.70lB52ce0K7BA0xHtB9N9aPwUK4YQQ8UrmJWxlcIhU8
# Content-Length: 135104
# Connection: keep-alive
# app.py: /face_detected: exception: 'ImmutableMultiDict' object is not callable
# 127.0.0.1 - - [26/Jan/2020 09:16:24] "POST /face_detected HTTP/1.1" 200 -


def should_send_data(id):
    """Convenience to determine if data should be sent to server"""
    global DATA_FRAMES
    global CACHE
    global SHOULD_LOG
    return should_send(id, DATA_FRAMES, CACHE, SHOULD_LOG)


def should_send_image(id):
    """Convenience to determine if image should be sent to server"""
    global IMAGE_FRAMES
    global CACHE
    global SHOULD_LOG
    return should_send(id, IMAGE_FRAMES, CACHE, SHOULD_LOG)


def should_send(id, frames, cache, should_log):
    """
    Determine if data for detected object should be sent.
    frames will come in as a 2 item array like [1,3] which
    specifies what frames should be sent to the server. [1,3] would
    indicate that the first 3 frames of an object detected should
    be sent. Something like [3,3] would indicate not send
    data unless the object was seen for at least 3 frames, then to
    only send that 3rd frame. This allows for blip filtering
    and to send a limited sequence of images if desired. -1 in the
    second array position like [2,-1] would indicate sending ALL
    data for a detected object from the 2nd frame onwards.
    """
    start_frame = frames[0]
    end_frame = frames[1]
    if start_frame < 0:
        # Don't send anything
        # logger.log('delivery.py: should_send: FALSE for: id:{}: cache:{}'.format(id, cache), should_log)
        return False

    global SHOULD_LOG
    match = cache.get(id)
    if match is None:
        # No record for this id yet
        # Create new record
        match = {'frames_seen': 0}
    frames_seen = match['frames_seen']
    new_frames_seen = frames_seen + 1
    match['frames_seen'] = new_frames_seen
    cache[id] = match
    if new_frames_seen < start_frame:
        # logger.log('delivery.py: should_send: FALSE for: id:{}: cache:{}'.format(id, cache), should_log)
        return False
    if (end_frame != -1 and new_frames_seen > end_frame):
        return False
    logger.log('delivery.py: should_send: TRUE for: id:{}: cache:{}'.format(id, cache), should_log)
    return True