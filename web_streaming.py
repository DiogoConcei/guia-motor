import cv2

class StreamError(Exception):
    pass

class WebStream:
    def __init__(self, cam, ws):
        self.cam = cam
        self.ws = ws

    def stream(self):
        ret, frame = self.cam.read()

        if not ret:
            raise StreamError("Falha em obter o frame")

        success, encoded_image = cv2.imencode('.jpg', frame)

        image_bytes = encoded_image.tobytes()
        self.ws.send(image_bytes)


