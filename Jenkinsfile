// Jenkinsfile
pipeline {
    agent any

    environment {
        TEST_ENV = 'test'
        PYTHONPATH = "${env.WORKSPACE}"
    }

    parameters {
        choice(
            name: 'TEST_MODE',
            choices: ['all', 'smoke', 'admin', 'product', 'order', 'marketing'],
            description: '选择测试模式'
        )
        string(
            name: 'TEST_ENV',
            defaultValue: 'dev',
            description: '测试环境'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                sh '''
                    python3 -m pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    def test_args = ''
                    if (params.TEST_MODE == 'smoke') {
                        test_args = '-m smoke'
                    } else if (params.TEST_MODE != 'all') {
                        test_args = "testcases/admin/test_${params.TEST_MODE}.py"
                    }

                    sh """
                        export TEST_ENV=${params.TEST_ENV}
                        pytest ${test_args} \
                            --alluredir=reports/allure-results \
                            --html=reports/test_report.html \
                            --self-contained-html \
                            -v \
                            --tb=short
                    """
                }
            }
        }

        stage('Generate Allure Report') {
            steps {
                sh '''
                    allure generate reports/allure-results -o reports/allure-report --clean
                '''
            }
        }

        stage('Archive Reports') {
            steps {
                archiveArtifacts artifacts: 'reports/*.html, reports/allure-report/**/*', allowEmptyArchive: true
            }
        }
    }

    post {
        always {
            // 发送通知
            emailext(
                subject: "Mall API Test Report - ${env.JOB_NAME} - Build ${env.BUILD_NUMBER}",
                body: """
                    <h2>测试报告</h2>
                    <p>项目: ${env.JOB_NAME}</p>
                    <p>构建: ${env.BUILD_NUMBER}</p>
                    <p>状态: ${currentBuild.currentResult}</p>
                    <p>Allure报告: <a href="${env.BUILD_URL}allure-report/">点击查看</a></p>
                    <p>HTML报告: <a href="${env.BUILD_URL}artifact/reports/test_report.html">点击查看</a></p>
                """,
                to: 'test-team@example.com',
                attachmentsPattern: 'reports/*.html'
            )
        }
        failure {
            // 企业微信通知
            sh '''
                curl -X POST 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY' \
                    -H 'Content-Type: application/json' \
                    -d "{
                        \"msgtype\": \"markdown\",
                        \"markdown\": {
                            \"content\": \"## 测试失败\n> 项目: ${JOB_NAME}\n> 构建: ${BUILD_NUMBER}\n> 状态: ${currentBuild.currentResult}\n> [查看报告](${BUILD_URL}allure-report/)\"
                        }
                    }"
            '''
        }
    }
}