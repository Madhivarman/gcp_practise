"""
    Python API to call Machine Learning Services on GCP. This code, explains
    how to create a training and predicting job in cloud Machine Learning Engine
    via python client. 
    
"""

import argparse
import subprocess
import datetime
import logging
import sys
import time

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from googleapiclient import errors 

import json
import os


#calling logs
logging.getLogger().setLevel(logging.INFO)

parser = argparse.ArgumentParser(
    description='Train classifier model using XGBoost'
)

parser.add_argument('--project-id', type=str,help='GCP Project ID')
parser.add_argument('--bucket', type=str,
        help='GCP Bucket to store results and models')
parser.add_argument('--region', type=str,
        default='us-central1',
        help='Enter the Region. Eg.., us-central1')
parser.add_argument('--trainFilePath', type=str,
        help='GCS Path for Train File')
    
parser.add_argument('--trainOutputPath', type=str,
        help='GCS Path for Train Output File')
    
parser.add_argument('--testFilePath', type=str,
        help='GCS Path for Test File')

parser.add_argument('--testOutputPath', type=str,
        help='GCS Path for Test Output File')

parser.add_argument('--target', type=str,
        help='Target Column')

parser.add_argument('--training_timeout', type=int, default=1200,
                    help='Timeout in seconds for AI platform model training job')

args = parser.parse_args()

PROJECT = args.project_id
BUCKET = args.bucket
REGION = args.region
TRAINING_TIMEOUT = args.training_timeout

logging.info("PARAMS\n")

logging.info("PROJECT ID:{pid} \n, BUCKET NAME:{bid} \n, REGION:{region}")

os.environ['BUCKET'] = BUCKET
os.environ['PROJECT'] = PROJECT
os.environ['REGION'] = REGION

subprocess.run("gcloud config set project $PROJECT", shell=True)
subprocess.run("gcloud config set compute/region $REGION", shell=True)

pkgname = '<package name>.tar.gz'

OUTDIR = "gs://{}/out/trained".format(BUCKET)
TRAINER_PATH = "gs://{}/srccode/dist/{}".format(BUCKET, pkgname)


# GOOGLE API TO SUBMIT CLOUD ML JOB
credentials = GoogleCredentials.get_application_default()
training_inputs = {'scaleTier':'BASIC',
        'packageUris':[TRAINER_PATH],
        'pythonModule':'xgboost_trainer.train',
        'args':[
            "<arguments to pass to the cloud-ml engine while training"
        ],
        'region': REGION,
        'jobDir':OUTDIR,
        'runtimeVersion':'1.14'}

timestamp = datetime.datetime.now().strftime('%y%m%d_%H%M%S%f')
job_name = "xgbClassifier_{}".format(timestamp)
job_spec = {'jobId':job_name, 'trainingInput':training_inputs}

api = discovery.build('ml', 'v1', credentials=credentials,cache_discovery=False)

project_id = 'projects/{}'.format(PROJECT)
credentials  = GoogleCredentials.get_application_default()
request = api.projects().jobs().create(body=job_spec, parent=project_id)

try:
        response = request.execute()
        #Handle successful request

except errors.HttpError as err:
        logging.error('There was an error creating the training job.'
                'check the details:')
        logging.error(err._get_reason())

#END GOOGLE API SUBMIT CMLE JOB

#START GOOGLE API CHECK STATUS OF CMLE JOB
jobName = 'your_job_name'
job_id = '{}/jobs/{}'.format(project_id, job_name)

request = api.projects().jobs().get(name=job_id)

response=None

counter=60

valid_status = ['SUCCEEDED','FAILED','CANCELLED']
job_status = False

while (counter <= TRAINING_TIMEOUT):
        try:
                time.sleep(60)
                response = request.execute()
                logging.info('Job Status for {}.{}: is {}'.format(
                        project_id, jobName, response['state']
                ))
                
                if (response['state'] in valid_status):
                        job_status = True
                        logging.info('TRAINING JOB STATUS'.format(response['state']))
                
                break
        
        except errors.HttpError as err:
                #something went wrong. Handle the exception in an appropriate
                # way for your application
                logging.error('There was an error getting the training job status'
                        'check the details:' )
                
                logging.error(err.__get_reason())
        
        counter += 60


if (job_status == False):
        logging.info('TIMEOUT IN TRAINING MODEL')
        raise Exception("TIMEOUT EXCEPTION IN MODEL TRAINING")


# START CREATE MODEL FOR GOOGLE API

timestamp = datetime.datetime.now().strftime('%y%m%d_%H%M%S')
model_name = "Classifier_{}".format(timestamp)
model_version = 'v1'
create_model_body = {'name': model_name,
        'description': "Initial Model Version..."}

response = api.projects().models().create(parent=project_id,
                                body=create_model_body).execute()

logging.info("MODEL CREATED", response)

# START CREATE MODEL GOOGLE API

time.sleep(120)

# START CREATING MODEL VERSION IN GOOGLE API

model_id = 'projects/{}/models/{}'.format(PROJECT, model_name)

model_location = 'gs://{}/out/trained/export/Servo/'.format(BUCKET)

shell_out = subprocess.run("gsutil ls gs://${BUCKET}/out/trained/export/Servo/ | tail -1",
                shell=True, stdout=subprocess.PIPE)

temp_loc = shell_out.stdout.decode("utf-8")
model_location = temp_loc.replace("\n", "")

create_model_version_body = {'name':model_version,
                        'deploymentUri': model_location,
                        'runtimeVersion': '1.14'}

response = api.projects().models().versions().create(parent=model_id,
                                        body=create_model_version_body).execute()


logging.info("MODEL VERSION CREATED", response)

#END CREATE MODEL VERSION GOOGLE API

time.sleep(120)


