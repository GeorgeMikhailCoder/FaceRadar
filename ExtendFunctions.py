from math import sqrt
import cv2
from face_recognition import face_locations

def differ(oldFace, newFace) -> float:
# коэффициент разницы положений лиц, отношение расстояний между центрами к самой короткой стороне
    (top0, right0, bottom0, left0) = oldFace
    (top1, right1, bottom1, left1) = newFace
    amax = min([(abs(bottom0 - top0)),
                (abs(bottom1 - top1)),
                (abs(right0 - left0)),
                (abs(right1 - left1))
                ]) # минимальная сторона прямоугольника (меньшего лица)
    center0 = [top0 + (bottom0 - top0)/2, left0 + (right0 - left0)/2]
    center1 = [top1 + (bottom1 - top1)/2, left1 + (right1 - left1)/2]

    centerDif = sqrt(
        pow(center1[0] - center0[0], 2) +
        pow(center1[1] - center0[1], 2)
    )
    return centerDif/amax

def drawRect1(frame, face, kx, ky):
# draw in order to face_recognition
# Scale back up face locations since the frame we detected in was scaled to 1/4 size
        (top, right, bottom, left) = face
        top *= int(1/ky)
        right *= int(1/kx)
        bottom *= int(1/ky)
        left *= int(1/kx)
        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        return frame

def koefSmall(face, kx, ky, camWidth, camHeight):
    (top, right, bottom, left) = face
    return 1 / 2 * ((bottom - top) / (camHeight * ky) + (right - left) / (camWidth * kx))

def isTooSmall(face, kMinFace, kx, ky, camWidth, camHeight):
    return koefSmall(face, kx, ky, camWidth, camHeight) < kMinFace

def ltwh2trbl(ltwh):
    (left, top, width, heigh) = ltwh
    return (top, left + width, top + heigh, left)
    # return ltwh

def showImage(title, image):
    img = cv2.resize(image, (640, 480))
    cv2.imshow(title, img)


def face2struct(rectFaces):
    return [
        {
            "rect": rect,
            "notInCam": 0
        }
        for rect in rectFaces
    ]

def struct2face(structFaces):
    return [
        st["rect"]
        for st in structFaces
    ]

def makeFaceLocationsElder(faceLocations, maxKadrEmpty):
    for face in faceLocations:
        face["notInCam"] += 1
        if face["notInCam"] > maxKadrEmpty:
            faceLocations.remove(face)
            # удаляет первое вхождение face, одинаковых прямоугольников не бывает
    return faceLocations

