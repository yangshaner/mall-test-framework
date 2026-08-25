pipeline {

    agent {
        docker {
            image 'python:3.12'
        }
    }

    environment {
        MALL_URL = 'http://192.168.1.8:8080'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python --version
                    pip install --no-cache-dir -r requirements.txt

                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    echo "Checking mall service..."

                    curl -f ${MALL_URL}
                '''
            }
        }

        stage('API Test') {
            steps {
                sh '''
                    pytest \
                    -v \
                    --alluredir=allure-results
                '''
            }
        }
    }

    post {

        always {

            allure(
                includeProperties: false,
                jdk: '',
                results: [
                    [path: 'allure-results']
                ]
            )
        }

        success {
            echo 'API测试执行成功'
        }

        failure {
            echo 'API测试存在失败用例'
        }
    }
}