*** Settings ***
Library    ../../../../RobotSlackNotification/
...    test_title=With Test Failed
...    environment=HML
...    cicd_url=https://cicd.com/123456
Test Tags    pix_automatico

*** Test Cases ***
# Teste Com Sucesso
#     Log    Este é um teste que vai passar
#     Should Be Equal    ${1}    ${1}

Teste Com Falha 1
    Log    Este é um teste que vai falhar
    # Sleep    1s
    Should Be Equal    ${1}    ${2}

# Teste Com Falha 2
#     Log    Este é um teste que vai falhar
#     Sleep    1s
#     Should Be Equal    ${3}    ${4}

# Teste Com Falha 3
#     Log    Este é um teste que vai falhar
#     Sleep    1s
#     Should Be Equal    ${5}    ${6}

# Teste Pulado
#     [Tags]    robot:skip
#     Log    Este teste será pulado
#     Should Be Equal    ${1}    ${1} 
