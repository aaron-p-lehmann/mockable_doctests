pipeline {
  agent any
  stages {
    stage('Test and Lint') {
      steps {
        sh 'tox -- --cov --cov-report xml'
      }
    }
    stage('Publish Reports') {
      steps {
        step([
          $class: 'CoberturaPublisher',
          autoUpdateHealth: false,
          autoUpdateStability: false,
          coberturaReportFile: 'coverage.xml',
          failUnhealthy: false,
          failUnstable: false,
          maxNumberOfBuilds: 0,
          onlyStable: false,
          sourceEncoding: 'ASCII',
          zoomCoverageChart: false
        ])
      }
    }
  }
}
