import delivery
import cv2

URL = 'http://localhost:8888/test'

def load_image(filepath):
    """Load an image for testing"""
    return cv2.imread(filepath)

def test_delivery_with_active_server():
    global URL
    image = load_image('audrey.jpg')
    assert image is not None
    print('test_delivery.py: test_delivery_with_active_server: image:{}'.format(image))
    r = delivery.send(0, image, URL)
    assert r is not None
    assert r.status_code == 200