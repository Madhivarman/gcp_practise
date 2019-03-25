#!/bin/bash

TOPICNAME='stream_camera_data'
SUBSCRIPTION_NAME='upload_bucket'
gcloud pubsub topics create $TOPICNAME
gcloud pubsub subscriptions create $SUBSCRIPTION_NAME --topic $TOPICNAME