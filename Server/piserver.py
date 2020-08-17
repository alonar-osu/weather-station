from flask import Flask
import pymysql
import datetime
from flask import jsonify
from flask import flash, request
import json
import urllib2
import os

app = Flask(__name__)
db = pymysql.connect("localhost", "alona", "raspas", "weather")


@app.route('/')
def index():
	return 'Hello world! from flask'

@app.route('/addone/')
def add():
	cursor = db.cursor()
	sql = "INSERT INTO weatherdata (datetime, temp, humid, UV, rain, rpiID) VALUES (%s, %s, %s, %s, %s, %s)"
	cursor.execute(sql, (datetime.datetime.now(), 27, 1.112, 2,3,4))
	db.commit()
	return "Done"

@app.route('/add/', methods=['POST'])
def add_measurement():
	try:
		jsondata = request.json
		print(jsondata)
		when = datetime.datetime.now()
		temp = jsondata['temp']
		humid = jsondata['humid']
		uv = jsondata['uv']
		rain = jsondata['rain']
		id = jsondata['id']

		#validate values received
		if not when:
			when = None
		if not temp:
			temp = None
		if not humid:
			humid = None
		if not uv:
			uv = None
		if not rain:
			rain = None
		if not id:
			id = None

		if request.method == 'POST':
			db = pymysql.connect("localhost", "alona", "raspas", "weather")
			cursor = db.cursor()
			sql = "INSERT INTO weathervals(datetime, temp, humid, uv, rain, id) VALUES (%s, %s, %s, %s, %s, %s)"
			data = (when, temp, humid, uv, rain, id)
			cursor.execute(sql, (when, temp, humid,uv,rain,id))
			db.commit()

			cursor.execute("SELECT * FROM alarms")
			numrows = cursor.rowcount
			for x in xrange(0, numrows):
				row = cursor.fetchone()
				alarm_id = row[0]
				sensor_type = row[1]
				alarm_trigger = row[2]
				threshold = row[3]
				is_active = row[4]
				sms_num = row[5]

				# alarms
				check_alarm(sensor_type, alarm_trigger, alarm_id, threshold, is_active, temp, humid, sms_num)
								
			return 'response'
		else:
			return 'not found'
	except Exception as e:
		print(e)
		return 'Exception'
	finally:
		cursor.close()
		db.close()

@app.route('/data/')
def download_data(): 

	db = pymysql.connect("localhost", "alona", "raspas", "weather")
	cursor = db.cursor()
	cursor.execute("SELECT datetime, temp, humid, id FROM weathervals")
	rows = cursor.fetchall()
	csv_response = ""
	index = 0
	for row in rows:
		index = index + 1
		csv_response = csv_response + str(index) + "," + str(row[0]) + "," + str(row[1]) + "," + str(row[2]) + "," + str(row[3]) + "\n"

	response = app.response_class(
		response=csv_response,
		status=200,
		mimetype='text/csv'
	)
	return response



UPLOAD_DIRECTORY = "uploadedfiles"

@app.route("/pic/", methods=["POST"])
def post_file():

    path = os.getcwd() + "/" + UPLOAD_DIRECTORY
    if not os.path.isdir(path):    
        try:
            os.mkdir(path)
        except OSError:
            print("Failed to create directory: %s" % path)

 
    if 'picture.jpg' in request.files:
        f = request.files['picture.jpg']
        output_filepath = path + "/picture.jpg"
        os.remove(output_filepath)
        f.save(output_filepath)
        print "picture saved"


	#return 201 CREATED
	return "", 201



def update_db(value_is_active, alarm_id):

	alarm_active = "1" if value_is_active else "0"
	cursor = db.cursor()
	cursor.execute("""UPDATE alarms SET is_active = %s WHERE id = %s;""", (alarm_active, alarm_id))
	db.commit()

def check_alarm(sensor_type, alarm_trigger, alarm_id, threshold, is_active, temp, humid, sms_num):
	if sensor_type == 'humid':
		value = humid
		alarm_id = 1
	elif sensor_type == 'temp':
		value = temp
		alarm_id = 2

	if is_active:
		if (alarm_trigger == 'g' and value < threshold) or (alarm_trigger == 'l' and value > threshold):
			# set is_active to FALSE
			update_db(False, alarm_id)

			text = 'alarm for ' + sensor_type + ' is now turned off - Check your weather at: http://192.168.86.125:5000/local'
			#send sms via POST request
			send_sms(text, sms_num)

	else:
		if alarm_trigger == 'g' and value > threshold:
			#set is_active to TRUE in db
			update_db(True, alarm_id)

			text = sensor_type + ' is above threshold! - Check your weather at: http://192.168.86.125:5000/local'
			# send sms via POST request
			send_sms(text, sms_num)

		elif alarm_trigger == 'l' and value < threshold:
			#set is_active to TRUE in db
			update_db(True, alarm_id)

			text = sensor_type + ' is below threshold! - Check your weather at: http://192.168.86.125:5000/local'
			# send sms via POST request
			send_sms(text, sms_num)

def send_sms(text, sms_num):
			url = 'https://rest.nexmo.com/sms/json'
			payload = {'from':'18185385217', 'to':sms_num, 'text':text, 'api_key':'d8aad2c9', 'api_secret':'mZ3ojRWWEYmnPIuK'} 

			request = urllib2.Request(url)
			request.add_header('Content-Type', 'application/json')

			response = urllib2.urlopen(request, json.dumps(payload))
			print("response is", response)


if __name__=='__main__':
	app.run(debug=True, port=82, host='0.0.0.0')
