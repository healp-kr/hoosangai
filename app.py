import streamlit as st
import os
import re
from google import genai
from google.genai import types

# 페이지 설정
st.set_page_config(page_title="재무제표 설명 도우미", layout="wide")

# 스타일 설정
st.markdown("""
    <style>
    .main { background-color: #FDFCFB; }
    .stButton>button { background-color: #059669; color: white; border-radius: 12px; }
    .card { background-color: white; padding: 20px; border-radius: 20px; border: 1px solid #f0f0f0; margin-bottom: 20px; }
    .summary-card { background-color: #059669; color: white; padding: 25px; border-radius: 25px; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# API 키 설정 (환경 변수 또는 Streamlit Secrets 사용)
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY가 설정되지 않았습니다.")
    st.stop()

client = genai.Client(api_key=api_key)

def parse_section(text, title):
    pattern = rf"\[{title}\]\s*([\s\S]*?)(?=\n\[|$)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extract_number(text, label):
    pattern = rf"(?:^|\n|\*|\s)*\*?\*?{label}\*?\*?\s*[:：]\s*([^\n\*]*)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else "정보 없음"

def clean_list(text):
    lines = text.split('\n')
    return [re.sub(r'^[-•]\s*', '', line).strip() for line in lines if line.strip().startswith(('-', '•'))]

st.title("📊 재무제표 설명 도우미")
st.subheader("어려운 재무제표, AI가 쉽고 명확하게 풀어드립니다.")

mode = st.radio("모드 선택", ["단일 분석", "기업 비교"], horizontal=True)

if mode == "단일 분석":
    company_name = st.text_input("기업명을 입력하세요", placeholder="예: 삼성전자, 테슬라...")
    if st.button("분석하기") and company_name:
        with st.spinner("최신 재무 데이터를 분석 중입니다..."):
            prompt = f"""
            당신은 재무제표를 초보자도 이해할 수 있게 풀어주는 “재무제표 설명 도우미”입니다.
            기업명: "{company_name}"
            
            다음 원칙을 지켜서 분석해주세요:
            1. 최신 재무제표를 검색해서 핵심 내용을 정리하세요.
            2. [쉽게 보는 결론]은 반드시 5단계 형식으로 작성하세요.
            
            출력 형식:
            [핵심 요약]
            - (내용)
            [좋은 점]
            - (내용)
            [아쉬운 점]
            - (내용)
            [체크할 점]
            - (내용)
            [쉽게 보는 결론]
            1. (상태 요약)
            2. (매력 포인트)
            3. (리스크 요인)
            4. (매수 조건)
            5. (최종 추천 의견 및 한 줄 평)
            [주요 숫자 요약]
            매출: (수치)
            영업이익: (수치)
            순이익: (수치)
            부채: (수치)
            자본: (수치)
            영업현금흐름: (수치)
            [재무제표 데이터]
            (상세 데이터)
            """
            
            response = client.models.generate_content(
                model="gemini-2.0-flash", # 또는 gemini-3-flash-preview
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            raw_text = response.text
            
            # UI 렌더링
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"<div class='summary-card'><h3>핵심 요약</h3>{'<br>'.join(['• ' + p for p in clean_list(parse_section(raw_text, '핵심 요약'))])}</div>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.success("✅ 좋은 점")
                    for p in clean_list(parse_section(raw_text, "좋은 점")): st.write(f"• {p}")
                with c2:
                    st.error("⚠️ 아쉬운 점")
                    for p in clean_list(parse_section(raw_text, "아쉬운 점")): st.write(f"• {p}")
                
                st.info("🔍 체크할 점")
                for p in clean_list(parse_section(raw_text, "체크할 점")): st.write(f"• {p}")

            with col2:
                st.markdown("<div class='card'><h3>📈 주요 숫자</h3>", unsafe_allow_html=True)
                num_section = parse_section(raw_text, "주요 숫자 요약")
                st.metric("매출", extract_number(num_section, "매출"))
                st.metric("영업이익", extract_number(num_section, "영업이익"))
                st.metric("순이익", extract_number(num_section, "순이익"))
                st.markdown("</div>", unsafe_allow_html=True)

            st.divider()
            st.subheader("💡 쉽게 보는 결론 (5단계 추천)")
            conclusion_raw = parse_section(raw_text, "쉽게 보는 결론")
            steps = [l.strip() for l in conclusion_raw.split('\n') if re.match(r'^\d+\.', l.strip())]
            for step in steps:
                st.markdown(f"**{step}**")

else:
    # 기업 비교 모드 로직 (유사하게 구현 가능)
    st.write("기업 비교 모드는 단일 분석과 유사한 로직으로 구현됩니다.")

st.caption("본 서비스는 AI 분석 정보이며 투자 책임은 본인에게 있습니다.")
