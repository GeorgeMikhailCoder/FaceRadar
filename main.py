import cv2
import face_recognition
import requests
import sys
import argparse

# источник видеопотока, номер подключённой к системе камеры или ссылка на удалённую
# example:
# cameraSource = 0
# cameraSource = 'http://qwerty:12345@192.168.43.1:8080/video' # работает!
cameraSource = 'http://qwerty:12345@192.168.43.1:8080/video' # работает!


# лица, занимающие меньше X% по среднему арифметическому отношений ширины и высоты к экрану отсеиваются
kMinFace = 0.1

# коэффициенты масштабирования входного изображения перед обработкой
kx = 0.25
ky = 0.25

# обработка консольных параметров, перезапись констант, если они были переданы
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-wc', '--webcam', default=cameraSource)
    parser.add_argument('-kmin', default=kMinFace)
    parser.add_argument('-kx', default=kx)
    parser.add_argument('-ky', default=ky)
    namespace = parser.parse_args(sys.argv[1:])
    cameraSource = namespace.webcam
    kMinFace = float(namespace.kmin)
    kx = float(namespace.kx)
    ky = float(namespace.ky)

# video_capture = cv2.VideoCapture('rtsp://192.168.1.64/1')
video_capture = cv2.VideoCapture(cameraSource)

face_locations = []
while True:
    ret = video_capture.open()
    if not ret:
        print("Camera doesn't opened!")
        print(f"Address of webcam:  {cameraSource}")
    else:
        ret, frame = video_capture.read()
        if not ret:
            print("Video doesn't accepted!")
            print(f"Address of webcam:  {cameraSource}")
            break
        else:
            # ширина и высота экрана
            camWidth = video_capture.get(3)
            camHeight = video_capture.get(4)

            small_frame = cv2.resize(frame, (0, 0), fx=kx, fy=ky)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            if face_locations:
                (top, right, bottom, left) = face_locations[0]
                print(f"k = {1 / 2 * ((bottom - top) / (camHeight * ky) + (right - left) / (camWidth * kx))}")

            for (top, right, bottom, left) in face_locations:
                if 1/2*((bottom - top)/(camHeight*ky) + (right - left)/(camWidth*kx)) > kMinFace:
                    # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    # Draw a box around the face
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            cv2.imshow('Video', frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

video_capture.release()
cv2.destroyAllWindows()


def upload(image):
    session = requests.Session()
    url = '127.0.0.1'
    files = {'uploaded_photo': image}
    session.post(url, files=files)
    session.close()