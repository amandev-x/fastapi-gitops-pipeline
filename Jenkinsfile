pipeline {
    agent any 

    environment {
        DOCKER_IMAGE = "amandabral9954/fastapi-app"
        IMAGE_TAG = "${BUILD_NUMBER}"   
        PREVIOUS_IMAGE_TAG = "${BUILD_NUMBER.toInteger() - 1}"
    }

    stages {
        stage('Check skip ci') {
            steps {
                script {
                    def commitAuthor = sh(script: 'git log -1 --pretty=%an',
                    returnStdout: true).trim()

                    def commitMsg = sh(script: 'git log -1 --pretty=%B',
                    returnStdout: true).trim()

                    echo "Commit Author: ${commitAuthor}"
                    echo "Commit Message: ${commitMsg}"

                    if (commitAuthor == 'Jenkins-CI' || commitMsg.contains('[skip ci]')) {
                        currentBuild.result = 'NOT_BUILT'
                        error("Skipping pipeline — commit made by Jenkins-CI")
                    }
                }
            }
        }
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
        stage("Build Docker Image and load to kind cluster") {
            steps {
                echo "Building docker image with tag: ${IMAGE_TAG}"
                sh 'docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} .'
                sh 'docker tag ${DOCKER_IMAGE}:${IMAGE_TAG} ${DOCKER_IMAGE}:latest'

                echo "Loading image into kind cluster"
                sh 'kind load docker-image ${DOCKER_IMAGE}:${IMAGE_TAG} --name gitops'
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
                 sed -i "s|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${IMAGE_TAG}|g" k8s/dev/deployment.yml
                 sed -i "s|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${IMAGE_TAG}|g" k8s/staging/deployment.yml
                 sed -i "s|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${IMAGE_TAG}|g" k8s/prod/deployment.yml

                 # Update VERSION env var
                 sed -i "s|VERSION=.*|VERSION=${IMAGE_TAG}|g" k8s/dev/deployment.yml
                 sed -i "s|VERSION=.*|VERSION=${IMAGE_TAG}|g" k8s/staging/deployment.yml
                 sed -i "s|VERSION=.*|VERSION=${IMAGE_TAG}|g" k8s/prod/deployment.yml

                 # Commit and push changes
                 git config user.name "Jenkins-CI"
                 git config user.email "jenkins-ci@local"
                 git add k8s/ 
                 # Check if there are actual changes before commiting
                 if ! git diff --cached --quiet; then
                 echo "Changes detected, committing..."
                git commit -m "Update image tag to ${IMAGE_TAG} [skip ci]"
                git push https://${GIT_USER}:${GIT_PASS}@github.com/amandev-x/fastapi-gitops-pipeline.git HEAD:main
                else
                  echo "No changes to commit, skipping push."
                fi
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
                    def status = sh(
                        script: "kubectl rollout status deployment/fastapi-app -n dev --timeout=90s",
                        returnStatus: true
                    )

                    if (status != 0) {
                        echo "❌ Rollout failed or timed out!"
                        error("Deployment unhealthy. The 'failure' block will now trigger rollback.")
                    } else {
                        echo "✅ SUCCESS: New version ${IMAGE_TAG} is live and healthy in Dev!"
                    }
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline completed"
            echo "Cleaning up test artifacts"
            sh '''
            rm -rf app/venv 
            rm -rf app/__pycache__
            rm -rf app/test/__pycache__
            '''
        }
        success {
            echo "✅ Deployment successful! Version ${IMAGE_TAG} is healthy and running."
        }
        failure {
        script {
            echo "🔴 DEPLOYMENT FAILED! Initiating rollback..."
            if (env.BUILD_NUMBER.toInteger() > 1) {
                withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                    sh '''
                        git config user.name "Jenkins CI"
                        git config user.email "jenkins-ci@local"

                        if grep -q "${DOCKER_IMAGE}:${IMAGE_TAG}" k8s/dev/deployment.yml; then
                            echo "Reverting image from ${IMAGE_TAG} to ${PREVIOUS_IMAGE_TAG}"
                            sed -i "s|image: ${DOCKER_IMAGE}:${IMAGE_TAG}|image: ${DOCKER_IMAGE}:${PREVIOUS_IMAGE_TAG}|g" k8s/dev/deployment.yml
                            git add k8s/
                            git commit -m "Rollback to ${PREVIOUS_IMAGE_TAG} due to failed health check" || true
                            git push https://${GIT_USER}:${GIT_PASS}@github.com/amandev-x/fastapi-gitops-pipeline.git HEAD:main
                            echo "✅ Rollback committed! ArgoCD will sync version ${PREVIOUS_IMAGE_TAG}"
                        else
                            echo "⚠️  Image tag not found in deployment.yml, skipping rollback"
                        fi
                    '''
                }
            } else {
                echo "⚠️  No previous version available to rollback to (this is build #1)"
            }
        }
    }
}
}
