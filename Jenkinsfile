pipeline {
  agent any
  stages {
    stage('Build') {
      steps {
        sh '''#!/bin/bash
#Activate venv
source /opt/venv/jenkins-gs/bin/activate
pip install -r ./requirements/dev.txt'''
      }
    }
  }
}