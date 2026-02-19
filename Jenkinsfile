pipeline {
    agent any 

    environment {
        DOCKER_IMAGE = "amandabral9954/fastapi-app"
        IMAGE_TAG = "${BUILD_NUMBER}"   
    }

    stages {
        stage("Checkout SCM") {
            steps {
                checkout scm 
            }
        }
        stage("Test") {
            steps {
                echo 'Running Tests'
                sh '''
                cd app 
                pip3 install -r requirements.txt
                pytest test_main.py -v
                '''
            }
        }
        stage("Build Docker Image") {
            steps {
                echo "Building docker image with tag: ${IMAGE_TAG}"
                sh 'docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} .'
                sh 'docker tag ${DOCKER_IMAGE}:${IMAGE_TAG} ${DOCKER_IMAGE}:latest'
            }
        }
    }
}