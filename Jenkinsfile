pipeline {

    agent {
        docker {
            image 'mall-test-env:1.0'
            reuseNode true
        }
    }

    parameters {

        string(
            name: 'ADMIN_URL',
            defaultValue: 'http://10.243.85.117:8080',
            description: 'Admin API 地址'
        )

        string(
            name: 'MEMBER_URL',
            defaultValue: 'http://10.243.85.117:8085',
            description: 'Member API 地址'
        )

        string(
            name: 'DB_HOST',
            defaultValue: '10.243.85.117',
            description: 'MySQL 地址'
        )

        string(
            name: 'REDIS_HOST',
            defaultValue: '10.243.85.117',
            description: 'Redis 地址'
        )
    }

     environment {

        PYTHONDONTWRITEBYTECODE = '1'
        PYTHONUNBUFFERED = '1'

        TEST_ENV = 'dev'

        ADMIN_URL = "${params.ADMIN_URL}"
        MEMBER_URL = "${params.MEMBER_URL}"

        DB_HOST = "${params.DB_HOST}"
        REDIS_HOST = "${params.REDIS_HOST}"

        MALL_URL = 'http://10.243.85.117:8080'
        PYTHONPATH = "${WORKSPACE}"
    }

    options{
        timestamps()
        disableConcurrentBuilds()
        timeout(time: 5, unit: 'MINUTES')

        buildDiscarder(
            logRotator(
               numToKeepStr: '10',
               artifactNumToKeepStr: '10'
            )
        )
    }

    stages {

       stage('Checkout') {

             options {
                timeout(time: 1, unit: 'MINUTES')
             }

             steps {
                 retry(3) {
                     checkout scm
                 }
             }
         }

        stage('Health Check') {
            steps {
                sh '''
                    echo "Checking mall service...,url ${MALL_URL}"
                '''
            }
        }

        stage('Environment Check') {
            steps{
                sh '''
                    echo "===== Jenkins Environment ====="
                    # export PYTHONPATH=$WORKSPACE
                    echo "ADMIN_URL=$ADMIN_URL"
                    echo "MENBER_URL=$MEMBER_URL"
                    echo "TEST_ENV=$TEST_ENV"

                    python -c "import os; print('Python ADMIN_URL:', os.getenv('ADMIN_URL'))"
                    python -c "from common.config.config_loader import config; print('Config admin.base_url:', config.get('admin.base_url'))"

                    python --version
                '''
            }
        }

        stage('Check Permission') {
            steps {
                sh '''
                    echo "========== Current User =========="
                    whoami || true
                    id

                    echo "========== Current Directory =========="
                    pwd

                    echo "========== Workspace =========="
                    ls -ld .
                    ls -la

                    echo "========== common =========="
                    ls -ld common || true

                    echo "========== common/logs =========="
                    ls -ld common/logs || true

                    echo "========== test.log =========="
                    ls -l common/logs/test.log || true
                '''
            }
        }

        stage('Prepare Allure') {
            steps {
                sh '''
                    rm -rf allure-results
                    mkdir -p allure-results

                    cat > allure-results/environment.properties <<EOF
                        Environment=dev
                        Application=mall
                        TestType=API Automation
                        Python=$(python --version 2>&1)
                    EOF

                '''
            }
        }

         stage('API Test') {
            steps {
                sh '''
                    export PYTHONPATH=$WORKSPACE

                    pytest -v --alluredir=allure-results --clean-alluredir
                '''
            }
        }
    }

    post {
        always {
            allure([
                includeProperties: false,
                jdk: '',
                results: [[path: 'allure-results']]
            ])

            archiveArtifacts(
                artifacts: 'allure-results/**/*',
                allowEmptyArchive: true
            )

        }

        success {
            echo 'API测试执行成功'
            mail(
                subject: "【测试成功】${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                    Jenkins 自动化测试执行完成。

                    项目：${env.JOB_NAME}
                    构建编号：#${env.BUILD_NUMBER}
                    构建结果：SUCCESS

                    请查看 Jenkins Console Output 和 Allure Report。

                    Jenkins：
                    ${env.BUILD_URL}

                    Allure 报告：
                    ${env.BUILD_URL}allure/
                    """,
                to: '2680654547@qq.com'
            )
        }

        failure {
            echo 'API测试存在失败用例'
             mail(
                subject: "【测试失败】${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                    Jenkins 自动化测试执行失败。

                    项目：${env.JOB_NAME}
                    构建编号：#${env.BUILD_NUMBER}
                    构建结果：FAILURE

                    请查看 Jenkins Console Output 和 Allure Report。

                    Jenkins：
                    ${env.BUILD_URL}

                    Allure 报告：
                    ${env.BUILD_URL}allure/
                    """,
                to: '2680654547@qq.com'
            )

        }

        cleanup {
            echo '========== CLEANUP =========='

            deleteDir()
        }

    }
}