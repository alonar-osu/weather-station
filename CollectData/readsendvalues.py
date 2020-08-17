import Adafruit_DHT as dht
import time
import datetime
import sys
import json
import urllib2
import requests

import os
import pygame,sys
from pygame.locals import *
import pygame.camera

# 5 sec wait
time.sleep(5)

if len(sys.argv) > 1:
	log = sys.argv[1] == 'log'
else:
	log = False


# keep reading values from sensor
while True:
	print("at start")
	hum, tempC = dht.read_retry(dht.DHT22, 17)
	tempF = 9.0/5.0 * tempC + 32
	uv = None
	rain = None
	id = 1 # id of this weather station
	datetime = None

	if (hum is None or tempF is None):
		time.sleep(10)
		continue
	print("about to log values")
	if log:
		print 'Temp={0:0.1f}F Humidity={1:0.1f}%'.format(tempF,hum)
		print

	url = 'http://127.0.0.1:82/add/'
	payload = {'datetime':datetime, 'temp':tempF, 'humid':hum, 'uv':uv, 'rain':rain, 'id':id}

	request = urllib2.Request(url)
	request.add_header('Content-Type', 'application/json')
	print("sending request")
	response = urllib2.urlopen(request, json.dumps(payload))
	print("after response")

	# get picture from camera
	width = 640
	height = 480

	# init pygame
	pygame.init()
	pygame.camera.init()
	cam = pygame.camera.Camera("/dev/video0",(width, height))
	cam.start()

	# setup window
	windowSurfaceObj = pygame.display.set_mode((width,height),1,16)
	pygame.display.set_caption('Camera')

	# take a pic
	image = cam.get_image()
	cam.stop()

	# display picture
	catSurfaceObj = image
	windowSurfaceObj.blit(catSurfaceObj,(0,0))
	pygame.display.update()

	# remove old picture
	os.remove('picture.jpg')

	# save picture
	pygame.image.save(windowSurfaceObj, 'picture.jpg')

	with open('picture.jpg', 'rb') as f:
		print 'Uploading file with size: %d' % os.path.getsize('picture.jpg')
		r = requests.post('http://127.0.0.1:82/pic/', files={'picture.jpg':f})



	time.sleep(60)
