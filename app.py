import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Streamlit 앱 제목
st.title("한국은행 주요통계 API 시각화")

# 사용자에게 API 키 입력받기
apikey = st.text_input('한국은행 Open API 키를 입력하세요', value='', type='default')

# API 키가 입력되어야만 아래 코드 실행
if apikey:
    # 한국은행 ECOS API URL 설정
    url = f'https://ecos.bok.or.kr/api/KeyStatisticList/{apikey}/xml/kr/1/100'
    # API URL 표시
    st.write(f"API URL: {url}")

    # API로부터 데이터 요청
    response = requests.get(url)
    xml_data = response.content.decode('utf-8')

    # XML 데이터 파싱
    root = ET.fromstring(xml_data)
    rows = []
    for row in root.iter('row'):
        data = {child.tag: child.text for child in row}
        rows.append(data)

    # 파싱한 데이터를 데이터프레임으로 변환
    df = pd.DataFrame(rows)

    # 날짜(YYYYMM) 컬럼이 있으면 datetime 타입으로 변환 후, 날짜 범위 선택 위젯 제공
    if 'YYYYMM' in df.columns:
        # YYYYMM을 datetime으로 변환 (예: 202401 -> 2024-01-01)
        df['YYYYMM'] = pd.to_datetime(df['YYYYMM'], format='%Y%m', errors='coerce')
        # 데이터 내 최소/최대 날짜 구하기
        min_date = df['YYYYMM'].min()
        max_date = df['YYYYMM'].max()
        # Streamlit에서 날짜 범위 입력받기
        start_date, end_date = st.date_input('날짜 범위 선택', [min_date, max_date], min_value=min_date, max_value=max_date)
        # 사용자가 선택한 날짜 범위로 데이터 필터링
        mask = (df['YYYYMM'] >= pd.to_datetime(start_date)) & (df['YYYYMM'] <= pd.to_datetime(end_date))
        df = df.loc[mask]

    # 전체 데이터 표로 출력
    st.subheader("전체 데이터 표")
    st.dataframe(df)

    # CLASS_NAME, KEYSTAT_NAME, DATA_VALUE 컬럼이 모두 있을 때만 시각화 진행
    if 'CLASS_NAME' in df.columns and 'KEYSTAT_NAME' in df.columns and 'DATA_VALUE' in df.columns:
        # 분류 기준 선택: CLASS_NAME 또는 KEYSTAT_NAME
        select_basis = st.radio('분류 기준을 선택하세요', ['CLASS_NAME', 'KEYSTAT_NAME'])
        
        # 선택 기준에 따라 다중선택 위젯 제공
        if select_basis == 'CLASS_NAME':
            options = df['CLASS_NAME'].unique()
            selected_options = st.multiselect('CLASS_NAME을(를) 선택하세요 (다중 선택 가능)', options, default=options[:1])
            df1 = df[df['CLASS_NAME'].isin(selected_options)]
        else:
            options = df['KEYSTAT_NAME'].unique()
            selected_options = st.multiselect('KEYSTAT_NAME을(를) 선택하세요 (다중 선택 가능)', options, default=options[:1])
            df1 = df[df['KEYSTAT_NAME'].isin(selected_options)]

        # Y축 스케일(일반/로그) 선택
        scale_type = st.radio('Y축 스케일을 선택하세요', ['일반 스케일', '로그 스케일'])
        # 그래프 타입(혼합/분할) 선택
        plot_type = st.radio('그래프 타입을 선택하세요', ['한 그래프에 그룹(혼합)', 'CLASS_NAME별로 분할(subplot)'])
        # DATA_VALUE를 숫자형으로 변환
        df1['DATA_VALUE'] = pd.to_numeric(df1['DATA_VALUE'], errors='coerce')

        # CLASS_NAME/KEYSTAT_NAME별로 그래프 타입(막대/선) 선택 위젯
        class_graph_types = {}
        for opt in selected_options:
            class_graph_types[opt] = st.selectbox(f"{opt}의 그래프 타입을 선택하세요", ['막대그래프', '선그래프'], key=f"graph_type_{opt}")

        # 시각화: 기준에 따라 x/y축 다르게 설정
        if select_basis == 'CLASS_NAME':
            group_col = 'CLASS_NAME'
            x_col = 'KEYSTAT_NAME'
        else:
            group_col = 'KEYSTAT_NAME'
            x_col = 'CLASS_NAME'

        # 2개 선택 시 좌/우 Y축 혼합 그래프
        if plot_type == '한 그래프에 그룹(혼합)' and len(selected_options) == 2:
            opt1, opt2 = selected_options
            subdf1 = df1[df1[group_col] == opt1]
            subdf2 = df1[df1[group_col] == opt2]
            fig = go.Figure()
            # 첫 번째 (좌측 Y축)
            if class_graph_types[opt1] == '막대그래프':
                fig.add_trace(go.Bar(x=subdf1[x_col], y=subdf1['DATA_VALUE'], name=opt1, text=subdf1['DATA_VALUE'], yaxis='y1'))
            else:
                fig.add_trace(go.Scatter(x=subdf1[x_col], y=subdf1['DATA_VALUE'], name=opt1, mode='lines+markers', text=subdf1['DATA_VALUE'], yaxis='y1'))
            # 두 번째 (우측 Y축)
            if class_graph_types[opt2] == '막대그래프':
                fig.add_trace(go.Bar(x=subdf2[x_col], y=subdf2['DATA_VALUE'], name=opt2, text=subdf2['DATA_VALUE'], yaxis='y2', marker_color='#EF553B'))
            else:
                fig.add_trace(go.Scatter(x=subdf2[x_col], y=subdf2['DATA_VALUE'], name=opt2, mode='lines+markers', text=subdf2['DATA_VALUE'], yaxis='y2', line=dict(color='#EF553B')))
            fig.update_layout(
                title=f"{select_basis} 2개 혼합(좌/우 Y축)",
                yaxis=dict(title=opt1, type='log' if scale_type=='로그 스케일' else 'linear'),
                yaxis2=dict(title=opt2, overlaying='y', side='right', type='log' if scale_type=='로그 스케일' else 'linear'),
                xaxis=dict(title=x_col),
                legend=dict(x=0.01, y=0.99)
            )
            st.plotly_chart(fig)
        elif plot_type == '한 그래프에 그룹(혼합)':
            fig = go.Figure()
            for opt in selected_options:
                subdf = df1[df1[group_col] == opt]
                if class_graph_types[opt] == '막대그래프':
                    fig.add_trace(go.Bar(x=subdf[x_col], y=subdf['DATA_VALUE'], name=opt, text=subdf['DATA_VALUE']))
                else:
                    fig.add_trace(go.Scatter(x=subdf[x_col], y=subdf['DATA_VALUE'], name=opt, mode='lines+markers', text=subdf['DATA_VALUE']))
            fig.update_layout(title=f"선택한 {select_basis}별 주요통계 (혼합)", barmode='group')
            if scale_type == '로그 스케일':
                fig.update_yaxes(type='log')
            st.plotly_chart(fig)
        else:
            # subplot(분할) 그래프
            fig = make_subplots(rows=len(selected_options), cols=1, shared_xaxes=True, subplot_titles=selected_options)
            for idx, opt in enumerate(selected_options):
                subdf = df1[df1[group_col] == opt]
                if class_graph_types[opt] == '막대그래프':
                    fig.add_trace(go.Bar(x=subdf[x_col], y=subdf['DATA_VALUE'], name=opt, text=subdf['DATA_VALUE']), row=idx+1, col=1)
                else:
                    fig.add_trace(go.Scatter(x=subdf[x_col], y=subdf['DATA_VALUE'], name=opt, mode='lines+markers', text=subdf['DATA_VALUE']), row=idx+1, col=1)
            fig.update_layout(title=f"{select_basis}별 주요통계 (분할, 혼합)")
            if scale_type == '로그 스케일':
                fig.update_yaxes(type='log')
            st.plotly_chart(fig)
    else:
        # 필수 컬럼이 없을 때 경고 메시지
        st.warning('CLASS_NAME, KEYSTAT_NAME, DATA_VALUE 컬럼이 데이터에 없습니다.')
else:
    st.info('먼저 한국은행 Open API 키를 입력해 주세요.')