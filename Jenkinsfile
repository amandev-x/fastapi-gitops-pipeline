pipeline {
    agent any 

    environment {
        DOCKER_IMAGE = "amandabral9954/fastapi-app"
        IMAGE_TAG = "${BUILD_NUMBER}"   
        PREVIOUS_IMAGE_TAG = "${BUILD_NUMBER.toInteger() - 1}"
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
                rm -rf app/.pytest_cache
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
        stage("Updates K8s manifests") {
            steps {
                echo "Updating Kubernetes manifests with new image tag: ${IMAGE_TAG}"
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                sh '''
                 # Update image tag in all deployment files
                 sed -i 's|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${IMAGE_TAG}|g' k8s/dev/deployment.yml
                 sed -i 's|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${IMAGE_TAG}|g' k8s/staging/deployment.yml
                 sed -i 's|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${IMAGE_TAG}|g' k8s/prod/deployment.yml

                 # Update VERSION env var
                 sed -i 's|VERSION=.*|VERSION=${IMAGE_TAG}|g' k8s/dev/deployment.yml
                 sed -i 's|VERSION=.*|VERSION=${IMAGE_TAG}|g' k8s/staging/deployment.yml
                 sed -i 's|VERSION=.*|VERSION=${IMAGE_TAG}|g' k8s/prod/deployment.yml

                 # Commit and push changes
                 git config user.name "Jenkins CI"
                 git config user.email "jenkins-ci@local"
                 git add k8s/ 
                 git commit -m "Update image tag to ${IMAGE_TAG} [skip ci]" || true
                 git push https://\\${GIT_USER}:\\${GIT_PASS}@github.com/amandev-x/fastapi-gitops-pipeline.git HEAD:main
                '''
            }
        }
        }
        stage("Wait for ArgoCD sync") {
            steps {
                echo "Waiting for ArgoCD to sync"
                sh "sleep 60"
            }
        }
        stage("Health check") {
            steps {
                script {
                    echo "Checking deployment health..."
                    def healthCheckPassed = sh(
                        script: '''
                         # Check dev environment
                         for i in {1..10}; do
                           if curl -f http://localhost:30080/health; then
                             echo "Health check passed"
                             exit 0
                           fi
                           echo "Attempt $i failed, retrying..."
                           sleep 5
                         done
                         exit 1
                        ''',
                        returnStatus: true
                    )

                    if (healthCheckPassed != 0) {
                        error("Health check failed! Triggering rollback...")
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
        success {
            echo "Deployment successful! Version ${IMAGE_TAG} is healthy"
        }
        failure {
            script {
                echo "Deployment failed! Rolling back to previous version"
                if (env.BUILD_NUMBER.toInteger() > 1) {
                    sh '''
                      # Rollback manifests
                      sed -i 's|image: ${DOCKER_IMAGE}:${IMAGE_TAG}|image: ${DOCKER_IMAGE}:${PREVIOUS_IMAGE_TAG}|g' k8s/dev/deployment.yml

                      git config user.name "Jenkins CI"
                      git config user.email "jenkins-ci@local"
                      git add k8s/
                      git commit -m "Rollback to previous version ${PREVIOUS_IMAGE_TAG} due to failed health check" || true
                      git push https://${GIT_USER}:${GIT_PASS}@github.com/amandev-x/fastapi-gitops-pipeline.git HEAD:main
                    '''
                    echo "Rollback committed. ArgoCD will sync the previous version."
                } else {
                    echo "No previous version to rollback to."
                }
            }
        }
    }
}
