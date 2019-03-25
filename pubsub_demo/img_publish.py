from google.cloud import pubsub_v1
import credentials as cr
import os


publisher = pubsub_v1.PublisherClient()

#topic will create under fully qualified identifier
topic_path = publisher.topic_path(cr.project_id, cr.topic_name)

#global name
image_path = '/home/madhi/Downloads/test1/'

for num, image in enumerate(os.listdir(image_path)):
	#image number
	#full_path
	full_path = image_path + image
	image_number = 'Image Id:{}'.format(image)

	#data must be byte String
	data = full_path.encode('utf-8')
	future = publisher.publish(topic_path, data=data)

	print("Published -> {} of Message Id:{}".format(full_path, future.result()))

	if num % 100 == 0 and num != 0:
		break


print("All Images has been Successfully Published!!!")
	


