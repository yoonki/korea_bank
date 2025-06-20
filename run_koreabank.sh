#!/bin/bash
# 한국은행 주요통계 시각화 자동 실행 스크립트

# 운영체제에 따라 pip 명령어 선택
if [[ "$(uname)" == "Darwin" ]]; then
    echo "맥(Mac) 환경이 감지되었습니다. pip3로 패키지를 설치합니다."
    PIP_CMD="pip3"
else
    echo "윈도우(Windows) 또는 기타 환경이 감지되었습니다. pip로 패키지를 설치합니다."
    PIP_CMD="pip"
fi

# 필요한 패키지 설치
$PIP_CMD install -r requirements.txt
# Streamlit 앱 실행
streamlit run app.py 