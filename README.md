# DETECTION TRACKER
This app runs a model detection and centroid tracker using alwaysAI. Images and meta data are then forwarded to an endpoint specified by it's configuration.

## CONFIG JSON
This is a json configuration that can be included in the `alwaysai.target.json` file to configure detection and delivery settings. It has the following schema:

```
  "config": {
    "model_name": "alwaysai/res10_300x300_ssd_iter_140000",
    "endpoint_url": "http://localhost:8888",
    "video_camera_id": 0,
    "video_filename": "",
    "enable_streamer": true,
    "enable_logs": true,
    "filter_for": [],
    "object_detect_period": 30,
    "object_detect_confidence": 70,
    "centroid_deregister_frames": 30,
    "centroid_max_distance": 50,
    "send_image_frames": [
      1,
      3
    ],
    "send_data_frames": [
      1,
      -1
    ]
  }
  ```

Only the `model_name` and `endpoint_url` is required, all other keys are optional for overriding the built-in defaults.

KEY |  VALUE TYPE | DESCRIPTION | DEFAULT | REQUIRED | IMPLEMENTED
---- | ---- | ---- | ----- | ---- | ---- |
model_name | string | Name of desired model from [alwaysAI's model catalog]() | None | Yes | Yes
endpoint_url | string | Server url to send data and images to | None | Yes | Yes
video_camera_id | number | Id index of an attached camera. 0 is the usual index | 0 | No | Yes
video_filename | string | Path to a video file to use instead of using an attached camera. This will supercede the camera settings and attempt to load the give video file. | None | No | Yes
enable_streamer | boolean | Whether or not to turn on the debug streamer | true | No | No
enable_logs | boolean | Whether or not to turn on simple console log outputs | true | No | Yes
filter_for | string array | Optional array of label names to filter predictions for. Model specific | Empty array | No | No
object_detect_period | number | | 30 | No | Yes
object_detect_confidence | number | | 70 | No | Yes
centroid_deregister_frames | number | | 30 | No | Yes
centroid_max_distance | number | | 50 | No | Yes
send_image_frames | number array | Array of frame numbers to send. 1 for the first index would be the first frame an object was detected. Changing it to something like 3, means the first 2 frames of the detection will be ignored, which can be used to filter out blips. -1 for the first index indicates that no image frames should be sent. -1 for second index equals unlimited (send all). So something like [1,3] would only send image data for the first 3 frames | [1,3] | No | No
send_data_frames | number array | Array of frame numbers to send metadata for. 1 for the first indicates the first frame of a detected object will be sent. -1 for the first index indicates no data frames should be sent. -1 for the second index equals unlimited (send all data). Meta data includes an object_id, and timestamp only | [1, -1] | No | Yes

## CHANGELOG
v0.1.0