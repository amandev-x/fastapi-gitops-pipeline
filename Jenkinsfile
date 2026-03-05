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
        stage("Deploy to Dev") {
            steps {
                script {
                    deployToEnv("dev", IMAGE_TAG)
                }
            }
        }
        stage("Deploy to Staging") {
            steps {
                script {
                    deployToEnv("staging", IMAGE_TAG)
                }
            }
        }
        stage("Approve production deployment") {
            steps {
                timeout(time: 24, unit: 'HOURS') {
                    input message: "✅ Dev & Staging passed. Deploy version ${IMAGE_TAG} to Production?", ok: "Deploy to Prod"
                }
            }
        }
        stage("Deploy to Prod") {
            steps {
                script {
                    deployToEnv("prod", IMAGE_TAG)
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
                        git fetch origin
                        git checkout gitops
                        git pull origin gitops
                        git config user.name "Jenkins CI"
                        git config user.email "jenkins-ci@local"

                        if grep -q "${DOCKER_IMAGE}:${IMAGE_TAG}" k8s/dev/deployment.yml; then
                            echo "Reverting image from ${IMAGE_TAG} to ${LAST_DEPLOYED_TAG}"
                            sed -i "s|image: ${DOCKER_IMAGE}:${IMAGE_TAG}|image: ${DOCKER_IMAGE}:${LAST_DEPLOYED_TAG}|g" k8s/dev/deployment.yml
                            git add k8s/
                            git commit -m "Rollback to ${LAST_DEPLOYED_TAG} due to failed health check" || true
                            git push https://${GIT_USER}:${GIT_PASS}@github.com/amandev-x/fastapi-gitops-pipeline.git HEAD:gitops
                            echo "✅ Rollback committed! ArgoCD will sync version ${LAST_DEPLOYED_TAG}"
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

// --- Helper Function for Promotion ---
def deployToEnv(envName, tag) {
    echo "🚀 Deploying version ${tag} to ${envName}..."
    withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
        sh '''
          git fetch origin
          git checkout gitops
          git pull origin gitops
        '''
        env.LAST_DEPLOYED_TAG = sh (
            script: 'grep "image:" k8s/dev/deployment.yml | cut -d ":" -f3'
        )
        echo "📌 Last deployed tag was: ${env.LAST_DEPLOYED_TAG}"
        
        sh """
          git fetch origin
          git checkout gitops
          git pull origin gitops
          
          # Update image and version for specific environment
          sed -i "s|image: ${DOCKER_IMAGE}:.*|image: ${DOCKER_IMAGE}:${tag}|g" k8s/${envName}/deployment.yml
          sed -i "s|VERSION=.*|VERSION=${tag}|g" k8s/${envName}/deployment.yml

          git config user.name "Jenkins-CI"
          git config user.email "jenkins-ci@local"
          git add k8s/${envName}/

          if ! git diff --cached --quiet; then
                git commit -m "Promote ${tag} to ${envName} [skip ci]"
                git push https://\${GIT_USER}:\${GIT_PASS}@github.com/amandev-x/fastapi-gitops-pipeline.git HEAD:gitops
          fi
        """

        echo "Waiting for ArgoCD to sync ${envName}..."
        sleep 20 
    
        echo "Checking health of ${envName}..."
        def status = sh(
            script: "kubectl rollout status deployment/fastapi-app -n ${envName} --timeout=90s",
            returnStatus: true
        )
    
        if (status != 0) {
            error("❌ ${envName} deployment failed! Stopping pipeline to protect next environments.")
        }
    }
}
