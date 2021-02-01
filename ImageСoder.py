from PIL import Image
import pandas as pd
import numpy as np

def json2Image(data):
    rj = data["red"]
    gj = data["green"]
    bj = data["blue"]

    fjr = pd.read_json(rj)
    fjg = pd.read_json(gj)
    fjb = pd.read_json(bj)

    rn = fjr.to_numpy()
    gn = fjg.to_numpy()
    bn = fjb.to_numpy()

    res = np.zeros((rn.shape[0], rn.shape[1], 3), dtype=np.uint8)

    res[:, :, 0] = rn
    res[:, :, 1] = gn
    res[:, :, 2] = bn

    f = Image.fromarray(res)
    return f

def arrayImage2json(arrayImage):
# перекодируем картинку в формат json
    a = arrayImage
    red = a[:, :, 0]
    gre = a[:, :, 1]
    blu = a[:, :, 2]

    rpd = DataFrame(data=red)
    gpd = DataFrame(data=gre)
    bpd = DataFrame(data=blu)

    rj = rpd.to_json()
    gj = gpd.to_json()
    bj = bpd.to_json()

    data = {
        "red": rj,
        "green": gj,
        "blue": bj
    }
    return data