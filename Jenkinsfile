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
        stage("Deploy to Dev") {
            steps {
                script {
                    deployToEnv("dev", IMAGE_TAG)
                }
            }
        }
        stage("Push to Dockerhub") {
            steps {
                echo "✅ Dev passed! Pushing verified image to DockerHub..."
                script {
                    docker.withRegistry('', 'dockerhub-credentials') {
                        sh "docker push ${DOCKER_IMAGE}:${IMAGE_TAG}"
                    }
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
            echo "✅ All environments healthy! Promoting ${IMAGE_TAG} to latest..."
            script {
                docker.withRegistry('', 'dockerhub-credentials') {
                    sh "docker push ${DOCKER_IMAGE}:latest"
                }
            }
            // Save last stable tag to gitops branch
            withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
                sh """
                  git fetch origin
                  git checkout gitops
                  git pull origin gitops
                  git config user.name "Jenkins-CI"
                  git config user.email "jenkins-ci@local"

                  # Save current successful build tag
                  echo "${IMAGE_TAG}" > .last_stable_tag

                  git add .last_stable_tag
                  git commit -m "Save last stable tag: ${IMAGE_TAG} [skip ci]" || true
                  git push https://\${GIT_USER}:\${GIT_PASS}@github.com/amandev-x/fastapi-gitops-pipeline.git HEAD:gitops
                """
                }
            }
        failure {
        script {
            echo "🔴 DEPLOYMENT FAILED! Initiating rollback..."
            }
        }
    }
}

// --- Helper Function for Promotion ---
def deployToEnv(envName, tag) {
    echo "🚀 Deploying version ${tag} to ${envName}..."
    withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
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
            rollBack(envName)
            error("❌ ${envName} deployment failed! Stopping pipeline to protect next environments.")
        }
        echo "✅ ${envName} is healthy!"
    }
}

def rollBack(envName) {
    echo "🔴 Rolling back ${envName}..."
    withCredentials([usernamePassword(credentialsId: 'github-credentials', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_PASS')]) {
        sh """
          git fetch origin
          git checkout gitops
          git pull origin gitops
          git config user.name "Jenkins-CI"
          git config user.email "jenkins-ci@local"

          # ✅ Read last stable tag from file — never points to a failed build
            if [ ! -f .last_stable_tag ]; then
            echo "⚠️  No stable tag found, skipping rollback"
            exit 0
            fi

            STABLE_TAG=\$(cat .last_stable_tag)
            echo "Last stable tag: \$STABLE_TAG"
            echo "Current failed tag: ${IMAGE_TAG}"

            # Don't rollback if stable tag is same as current
            if [ "\$STABLE_TAG" = "${IMAGE_TAG}" ]; then
            echo "⚠️  Stable tag is same as current, skipping rollback"
            exit 0
            fi

            if grep -q "${DOCKER_IMAGE}:${IMAGE_TAG}" k8s/${envName}/deployment.yml; then
                echo "Reverting image from ${IMAGE_TAG} to \${STABLE_TAG}"
                sed -i "s|image: ${DOCKER_IMAGE}:${IMAGE_TAG}|image: ${DOCKER_IMAGE}:\${STABLE_TAG}|g" k8s/${envName}/deployment.yml
                git add k8s/
                git commit -m "Rollback to \${STABLE_TAG} due to failed health check" || true
                git push https://${GIT_USER}:${GIT_PASS}@github.com/amandev-x/fastapi-gitops-pipeline.git HEAD:gitops
                echo "✅ ${envName} Rollback committed! ArgoCD will sync version \${STABLE_TAG}"
            else
                echo "⚠️  No previous version available to rollback"
            fi
          """
    }
}
