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
                python3 -m venv venv 
                . venv/bin/activate
                pip3 install -r requirements.txt
                pytest test_main.py -v
                '''
            }
        }
        stage('Cleanup Test environment') {
            steps {
                echo "Cleaning up test artifacts"
                sh '''
                rm -rf app/venv 
                rm -rf app/__pycache__
                rm -rf app/test/__pycache__
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
        stage("Push to Docker Hub") {
            steps {
                echo "Pushing docker image with tag: ${IMAGE_TAG}"
                script {
                    docker.withRegistry('', 'dockerhub-credentials') {
                        sh "docker push ${DOCKER_IMAGE}:${IMAGE_TAG}"
                        sh "docker push ${DOCKER_IMAGE}:latest"
                    }
                }
            }
        }
    }

    post {
        always {
            echo "Cleaning up test artifacts"
            sh '''
            rm -rf app/venv 
            rm -rf app/__pycache__
            rm -rf app/test/__pycache__
            '''
        }
    }
}