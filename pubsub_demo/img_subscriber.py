import time
import json
import credentials as cr 
from google.cloud import pubsub_v1
from google.cloud import storage

"""
	Before uploading the image to bucket, the pub/sub service
	account should have access to the storage bucket, and other
	tools we going to use in this project
"""
#define variables for subscription method

subscriber = pubsub_v1.SubscriberClient()

#subscriber path
subscription_path = subscriber.subscription_path(
	cr.project_id, cr.subscription_name)

#define all bucket name
bucket_name = 'image_from_pubsub'
#bucket storage object name
storage_client = storage.Client(cr.project_id)

def upload_to_bucket(blob_name, filename):
	"""
		to upload the data into bucket,
		bucket.blob(destination_filename).upload_from_file(source_file_path)
	"""
	bucket = storage_client.get_bucket(bucket_name)
	blob = bucket.blob(blob_name).upload_from_filename(filename)

	return "file is uploaded into bucket"

num = 1

def callback(image_path):
	print("Message Received:{}".format(image_path))
	image_path.ack() #acknowledge the message that subscriber is received

	"""
		Image path is a data received from publisher content.It's type is
		received as JSON
	"""
	blob_name = image_path.data.split("/")[-1]
	msg = upload_to_bucket(blob_name, image_path.data)
	print(msg)

#subscribe
subscriber.subscribe(subscription_path, callback=callback)

print("Listening for Message on {}".format(subscription_path))

while True:
	time.sleep(60)