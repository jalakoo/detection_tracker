
import edgeiq
import os

def is_accelerator_available():
    if edgeiq.find_usb_device(id_vendor=edgeiq.constants.NCS1_VID, id_product=edgeiq.constants.NCS1_PID) == True:
        return True
    if edgeiq.find_usb_device(edgeiq.constants.NCS1_VID, edgeiq.constants.NCS1_PID2) == True:
        return True
    if edgeiq.find_usb_device(edgeiq.constants.NCS2_VID, edgeiq.constants.NCS2_PID) == True:
        return True
    return False


def object_detector(model, should_log= True):
    # print("alwaysai_helper.py: object_detector")
    if model is None:
        raise Exception(
            "alwaysai_helper.py: object_detector: model name parameter not found")
    od = edgeiq.ObjectDetection(model)
    e = engine()
    od.load(e)
    if should_log == True:
        print("alwaysai_helper.py: object_detector: Engine: {}".format(od.engine))
        print("alwaysai_helper.py: object_detector: Accelerator: {}\n".format(od.accelerator))
        print("alwaysai_helper.py: object_detector: Model:\n{}\n".format(od.model_id))
    return od

def engine():
    if is_accelerator_available() == True:
        return edgeiq.Engine.DNN_OPENVINO
    return edgeiq.Engine.DNN

# TODO: Create a config class?
def config_from_json(json):
    """Current just checking validity of JSON"""
    model_name = json.get('model_name', None)
    if model_name is None:
        raise ValueError('alwaysai.py: config_from_json: model_name missing')
    camera_id = json.get('video_camera_id', None)
    if camera_id is None:
        raise ValueError('alwaysai.py: config_from_json: video_camera_id missing')
    return json


import time

def start_camera_detection_and_tracking_from_config(config):
    confidence = config.get('object_detection_confidence', .5)
    enable_streamer = config.get('enable_streamer', True)
    start_camera_detection_and_tracking(model_name=config['model_name'], camera_id=config["video_camera_id"], detection_confidence=confidence, enable_streamer=enable_streamer)

def start_camera_detection_and_tracking(model_name, camera_id=0, detection_confidence=.5, enable_streamer=True, streamer_show_labels=True, tracker_deregister_frames=20, tracker_max_distance=50):

    obj_detect = object_detector(model_name)
    tracker = edgeiq.CentroidTracker(
        deregister_frames=tracker_deregister_frames, max_distance=tracker_max_distance
    )
    fps = edgeiq.FPS()

    try:
        #  Why doesn't this work?
        # webcam = edgeiq.WebcamVideoStream(cam=camera_id)
        # streamer = edgeiq.Streamer()
        with edgeiq.WebcamVideoStream(cam=camera_id) as webcam, edgeiq.Streamer() as streamer:
            # Allow webcam to warm up
            time.sleep(2.0) 
            fps.start()

            # loop detection
            while True:
                frame = webcam.read()
                text = []
                # Run detection
                # detect human faces
                results = obj_detect.detect_objects(
                    frame, confidence_level=detection_confidence
                )
                frame = edgeiq.markup_image(
                    frame, results.predictions, show_labels=streamer_show_labels
                )

                # Generate text to display on streamer
                text.append("Model: {}".format(obj_detect.model_id))
                text.append("Inference time: {:1.3f} s".format(results.duration))

                predictions = []
                objects = tracker.update(results.predictions)
                # predictions = results.predictions
                for (object_id, prediction) in objects.items():
                    # print(vars(prediction))
                    text.append(
                        "{}: {}: {:2.2f}%".format(
                            object_id, prediction.label, prediction.confidence * 100
                        )
                    )
                    predictions.append(prediction)

                frame = edgeiq.markup_image(frame, predictions)
                streamer.send_data(frame, text)
                fps.update()
                if streamer.check_exit():
                    break

    finally:
        # stop fps counter and display information
        fps.stop()
        print("[INFO] elapsed time: {:.2f}".format(fps.get_elapsed_seconds()))
        print("[INFO] approx. FPS: {:.2f}".format(fps.compute_fps()))
        print("Program Ending")