#!/usr/bin

NAMESPACE=$1
DEPLOYMENT_NAME=$2
PREVIOUS_IMAGE=$3

echo "Rolling back deployment $DEPLOYMENT_NAME in namespace $NAMESPACE to image $PREVIOUS_IMAGE"

kubectl set image deployment/$DEPLOYMENT_NAME -n $NAMESPACE $DEPLOYMENT_NAME=$PREVIOUS_IMAGE

echo "Waiting for rollback to complete..."
kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE

echo "Rollback completed!"