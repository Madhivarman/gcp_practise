import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp_de_exp_pubsub.json'

#set project_id and topic_name
project_id = 'gcp-de-exp'
topic_name = 'streaming_image'

subscription_name = 'upload_bucket'