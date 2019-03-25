#!/bin/bash

TOPICNAME='stream_camera_data'
SUBSCRIPTION_NAME='upload_bucket'
gcloud pubsub subscriptions delete $SUBSCRIPTION_NAME
gcloud pubsub topics delete $TOPICNAME