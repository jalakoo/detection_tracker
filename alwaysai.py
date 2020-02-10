
import time
import edgeiq
import os
import delivery


def is_accelerator_available():
    """Detect if an Intel Neural Compute Stick accelerator is attached"""
    if edgeiq.find_usb_device(id_vendor=edgeiq.constants.NCS1_VID, id_product=edgeiq.constants.NCS1_PID) == True:
        return True
    if edgeiq.find_usb_device(edgeiq.constants.NCS1_VID, edgeiq.constants.NCS1_PID2) == True:
        return True
    if edgeiq.find_usb_device(edgeiq.constants.NCS2_VID, edgeiq.constants.NCS2_PID) == True:
        return True
    return False


def object_detector(model, should_log=True):
    """Return an object detector for a given model"""
    if model is None:
        raise Exception(
            "alwaysai.py: object_detector: model name parameter not found")
    od = edgeiq.ObjectDetection(model)
    e = engine()
    od.load(e)
    if should_log == True:
        print("alwaysai.py: object_detector: Engine: {}".format(od.engine))
        print("alwaysai.py: object_detector: Accelerator: {}\n".format(
            od.accelerator))
        print("alwaysai.py: object_detector: Model:\n{}\n".format(od.model_id))
    return od


def engine():
    """Switch Engine modes if an Intel accelerator is available"""
    if is_accelerator_available() == True:
        return edgeiq.Engine.DNN_OPENVINO
    return edgeiq.Engine.DNN

# TODO: Create a config class?


def config_from_json(json):
    """Check validity of JSON file to be used a configuration dictionary"""
    model_name = json.get('model_name', None)
    if model_name is None:
        raise ValueError('alwaysai.py: config_from_json: model_name missing')
    camera_id = json.get('video_camera_id', None)
    if camera_id is None:
        raise ValueError(
            'alwaysai.py: config_from_json: video_camera_id missing')
    return json


def start_detection_and_tracking_from_config(config):
    """
    Convenience to start detection and tracking based on configuration data
    """
    confidence = config.get('object_detection_confidence', .5)
    enable_streamer = config.get('enable_streamer', True)
    data_url = config.get('data_url', 'http://localhost:8888/data')
    images_url = config.get('images_url', 'http://localhost:8888/images')
    filter_for = config.get('filter_for', None)
    data_frames = config.get('send_data_frames', [0, -1])
    image_frames = config.get('send_image_frames', [0, -1])
    should_log = config.get('enable_logs', False)
    delivery.configure(data_url=data_url, images_url=images_url,
                       data_frames=data_frames, image_frames=image_frames, should_log=should_log)

    video = config.get('video_filename', None)
    if (video is None or video == ''):
        start_camera_detection_and_tracking(delivery, filter_for, model_name=config['model_name'], camera_id=config[
            "video_camera_id"], detection_confidence=confidence, enable_streamer=enable_streamer, should_log=should_log)
    else:
        start_file_detection_and_tracking(
            delivery, filter_for, model_name=config['model_name'], filename=video, detection_confidence=confidence, enable_streamer=enable_streamer, should_log=should_log)
    # start_camera_detection_and_tracking(url, model_name=config['model_name'], camera_id=config["video_camera_id"], detection_confidence=confidence, enable_streamer=enable_streamer)


def start_camera_detection_and_tracking(delivery_object, filter_for, model_name, camera_id=0, detection_confidence=.5, enable_streamer=True, streamer_show_labels=True, tracker_deregister_frames=20, tracker_max_distance=50, should_log=False):
    """Starts a detection loop"""
    obj_detect = object_detector(model_name)
    tracker = edgeiq.CentroidTracker(
        deregister_frames=tracker_deregister_frames, max_distance=tracker_max_distance
    )
    fps = edgeiq.FPS()

    try:
        # Enables video camera and streamer

        # TODO: add streamer disable feature here

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

                # TODO: Add filter option here

                frame = edgeiq.markup_image(
                    frame, results.predictions, show_labels=streamer_show_labels
                )

                # Generate text to display on streamer
                text.append("Model: {}".format(obj_detect.model_id))
                text.append(
                    "Inference time: {:1.3f} s".format(results.duration))

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

                    # if delivery.should_send_image(object_id):
                    #     # Extract image
                    #     face_image = edgeiq.cutout_image(frame, prediction.box)
                    #     # Send data to server
                    #     delivery.send_image(
                    #         object_id, prediction.label, face_image)
                    # elif delivery.should_send_data(object_id):
                    #     delivery.send_data(object_id, prediction.label)
                    
                    if delivery.should_send_data(object_id):
                        delivery.send_data(object_id, prediction.label)

                frame = edgeiq.markup_image(frame, predictions)
                streamer.send_data(frame, text)
                fps.update()
                if streamer.check_exit():
                    break

    finally:
        # stop fps counter and display information
        fps.stop()
        if should_log == True:
            print("[INFO] elapsed time: {:.2f}".format(
                fps.get_elapsed_seconds()))
            print("[INFO] approx. FPS: {:.2f}".format(fps.compute_fps()))
            print("Program Ending")


def start_file_detection_and_tracking(delivery_object, filter_for, model_name, filename, detection_confidence=.5, enable_streamer=True, streamer_show_labels=True, tracker_deregister_frames=20, tracker_max_distance=50, should_log=False):
    """Starts a detection loop"""
    obj_detect = object_detector(model_name)
    tracker = edgeiq.CentroidTracker(
        deregister_frames=tracker_deregister_frames, max_distance=tracker_max_distance
    )
    fps = edgeiq.FPS()

    try:
        # Enables video camera and streamer

        # TODO: add streamer disable feature here

        with edgeiq.FileVideoStream(filename) as video_stream, edgeiq.Streamer() as streamer:

            # Start tracking of frames per second
            fps.start()

            # loop detection
            while True:
                frame = video_stream.read()
                text = []
                # Run detection
                # detect human faces
                results = obj_detect.detect_objects(
                    frame, confidence_level=detection_confidence
                )

                # TODO: Add filter option here

                frame = edgeiq.markup_image(
                    frame, results.predictions, show_labels=streamer_show_labels
                )

                # Generate text to display on streamer
                text.append("Model: {}".format(obj_detect.model_id))
                text.append(
                    "Inference time: {:1.3f} s".format(results.duration))

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

                    # if delivery.should_send_image(object_id):
                    #     # Extract image
                    #     face_image = edgeiq.cutout_image(frame, prediction.box)
                    #     # Send data to server
                    #     delivery.send_image(
                    #         object_id, prediction.label, face_image)
                    # elif delivery.should_send_data(object_id):
                    #     delivery.send_data(object_id, prediction.label)

                    if delivery.should_send_data(object_id):
                        delivery.send_data(object_id, prediction.label)

                frame = edgeiq.markup_image(frame, predictions)
                streamer.send_data(frame, text)
                fps.update()
                if streamer.check_exit():
                    break

    finally:
        # stop fps counter and display information
        fps.stop()
        if should_log == True:
            print("[INFO] elapsed time: {:.2f}".format(
                fps.get_elapsed_seconds()))
            print("[INFO] approx. FPS: {:.2f}".format(fps.compute_fps()))
            print("Program Ending")
