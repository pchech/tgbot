from PIL import Image, ImageDraw #Подключим необходимые библиотеки.
import random
import Algorithmia
import posixpath
from skimage.io import imread	
from skimage import img_as_float
from sklearn.cluster import KMeans
import io
import numpy as np

class Filter:
    def black_white_filter(self,dir):
        image = Image.open(dir) #Открываем изображениеH.
        draw = ImageDraw.Draw(image) #Создаем инструмент для рисования.
        width = image.size[0] #Определяем ширину.
        height = image.size[1] #Определяем высоту.
        pix = image.load() #Выгружаем значения пикселей.
        factor = 1
        for i in range(width):
            for j in range(height):
                a = pix[i, j][0]
                b = pix[i, j][1]
                c = pix[i, j][2]
                S = a + b + c
                if (S > (((255 + factor) // 2) * 3)):
                    a, b, c = 255, 255, 255
                else:
                    a, b, c = 0, 0, 0
                draw.point((i, j), (a, b, c))
        return image
    def sepia(self,dir,parameters):
        image = Image.open(dir)  # Открываем изображениеH.
        draw = ImageDraw.Draw(image) #Создаем инструмент для рисования.
        width = image.size[0] #Определяем ширину.
        height = image.size[1] #Определяем высоту.
        pix = image.load() #Выгружаем значения пикселей.
        depth = parameters
        for i in range(width):
            for j in range(height):
                a = pix[i, j][0]
                b = pix[i, j][1]
                c = pix[i, j][2]
                S = (a + b + c) // 3
                a = S + depth * 2
                b = S + depth
                c = S
                if (a > 255):
                    a = 255
                if (b > 255):
                    b = 255
                if (c > 255):
                    c = 255
                draw.point((i, j), (a, b, c))
        return image

    def negative(self,dir):
        image = Image.open(dir)  # Открываем изображениеH.
        draw = ImageDraw.Draw(image) #Создаем инструмент для рисования.
        width = image.size[0] #Определяем ширину.
        height = image.size[1] #Определяем высоту.
        pix = image.load() #Выгружаем значения пикселей.
        for i in range(width):
            for j in range(height):
                a = pix[i, j][0]
                b = pix[i, j][1]
                c = pix[i, j][2]
                draw.point((i, j), (255 - a, 255 - b, 255 - c))
        return image

    def brightnessChange(self,dir,parameters):
        image = Image.open(dir)  # Открываем изображениеH.
        draw = ImageDraw.Draw(image) #Создаем инструмент для рисования.
        width = image.size[0] #Определяем ширину.
        height = image.size[1] #Определяем высоту.
        pix = image.load() #Выгружаем значения пикселей.
        factor = parameters
        for i in range(width):
            for j in range(height):
                a = pix[i, j][0] + factor
                b = pix[i, j][1] + factor
                c = pix[i, j][2] + factor
                if (a < 0):
                    a = 0
                if (b < 0):
                    b = 0
                if (c < 0):
                    c = 0
                if (a > 255):
                    a = 255
                if (b > 255):
                    b = 255
                if (c > 255):
                    c = 255
                draw.point((i, j), (a, b, c))
        return image

    def add_noise(self,dir,parameters):
        image = Image.open(dir)  # Открываем изображениеH.
        draw = ImageDraw.Draw(image) #Создаем инструмент для рисования.
        width = image.size[0] #Определяем ширину.
        height = image.size[1] #Определяем высоту.
        pix = image.load() #Выгружаем значения пикселей.
        factor = parameters
        for i in range(width):
            for j in range(height):
                rand = random.randint(-factor, factor)
                a = pix[i, j][0] + rand
                b = pix[i, j][1] + rand
                c = pix[i, j][2] + rand
                if (a < 0):
                    a = 0
                if (b < 0):
                    b = 0
                if (c < 0):
                    c = 0
                if (a > 255):
                    a = 255
                if (b > 255):
                    b = 255
                if (c > 255):
                    c = 255
                draw.point((i, j), (a, b, c))
        return image

class Colorizer:
    def __init__(self,api_key,collection_name):
        self.client = Algorithmia.client(api_key)
        self.collection_name = collection_name
    def action(self,data):
        #mass = filepath.split("/")
        self.client.file("data://.my/"+self.collection_name+"/testimg.png").put(data)
        input = {
            "image": "data://.my/"+self.collection_name+"/testimg.png"
        }
        algo = self.client.algo('deeplearning/ColorfulImageColorization/1.1.13')
        out = algo.pipe(input).result
        t800Bytes = self.client.file(out['output']).getBytes()
        return t800Bytes
		
def find_color(i):
    cluster=res[i]
    mean=[]
    for j in range(X.shape[0]):
        if res[j]==cluster:
            mean.append(X[j])
    R=0
    G=0
    B=0
    for j in mean:
        R+=j[0]
        G+=j[1]
        B+=j[2]
    return list([R/len(mean),G/len(mean),B/len(mean)])
	
def change_color(img):
	image=imread(img)
	image=img_as_float(image)
	X = image.reshape(image.shape[0] * image.shape[1], 3)
	clt=KMeans(random_state=241,init='k-means++',n_clusters=4)
	clt.fit(X)
	res=clt.predict(X)
	centre=clt.cluster_centers_
	new_X=[]
	for i in range(X.shape[0]):
		new_X.append(centre[res[i]])
	new_image = np.array(new_X).reshape(image.shape[0], image.shape[1], 3)
	imgByteArr = io.BytesIO()
	new_image.save(imgByteArr,format = 'PNG')
	imgByteArr = imgByteArr.getvalue()
	return imgByteArr