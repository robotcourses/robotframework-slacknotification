*** Settings ***
Library    ../RobotSlackNotification/
    ...    test_title=Teste Robot
    ...    environment=TEST
    ...    cicd_url=https://cicd.com/123456

*** Test Cases ***
Teste Com Sucesso
    Log    Este é um teste que vai passar
    Should Be Equal    ${1}    ${1}

Teste Com Falha 1
    Log    Este é um teste que vai falhar
    Should Be Equal    ${1}    ${2}

Teste Com Falha 2
    Log    Este é um teste que vai falhar
    Should Be Equal    ${1}    ${2}

Teste Com Falha 3
    Log    Este é um teste que vai falhar
    Should Be Equal    ${1}    ${2}

Teste Pulado
    [Tags]    robot:skip
    Log    Este teste será pulado
    Should Be Equal    ${1}    ${1} 
