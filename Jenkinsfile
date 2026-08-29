pipeline {

    agent {
        docker {
                image 'mall-test-env:1.0'
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