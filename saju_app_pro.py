import streamlit as st
import google.generativeai as genai
import os
import datetime
from korean_lunar_calendar import KoreanLunarCalendar
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# 2. 페이지 설정
st.set_page_config(
    page_title="AI 사주 & 성명학 심층 분석",
    page_icon="🔮",
    layout="wide"
)

# 3. 유틸리티 함수 (계산 로직)
def get_60ganzhi_list():
    gan = list("갑을병정무기경신임계")
    zhi = list("자축인묘진사오미신유술해")
    ganzhi = []
    for i in range(60):
        ganzhi.append(gan[i % 10] + zhi[i % 12])
    return ganzhi

def calculate_day_ganzhi(year, month, day):
    target_date = datetime.date(year, month, day)
    base_date = datetime.date(1900, 1, 1) # 갑술일 기준
    days_diff = (target_date - base_date).days
    ganzhi_index = (days_diff + 10) % 60
    return get_60ganzhi_list()[ganzhi_index]

def convert_to_solar(year, month, day, calendar_type):
    if calendar_type == "양력":
        return year, month, day
    calendar = KoreanLunarCalendar()
    is_intercalation = (calendar_type == "음력(윤달)")
    calendar.setLunarDate(year, month, day, is_intercalation)
    return calendar.solarYear, calendar.solarMonth, calendar.solarDay

# 4. 프롬프트 생성 함수 (핵심 수정 부분)
def generate_advanced_prompt(name_h, name_c, gender, s_year, s_month, s_day, o_cal, o_date, time, ilju):
    prompt = f"""
    당신은 대한민국 최고의 명리학자이자 성명학 전문가입니다.
    아래 팩트(Facts)를 바탕으로 사주와 이름의 조화를 분석하고 2026년 운세를 '심층 분석'하세요.

    [1. 사용자 기본 정보]
    - 이름: {name_h} (한자: {name_c if name_c else '미입력'})
    - 성별: {gender}
    - 생년월일: {o_date} ({o_cal}) -> 양력 변환: {s_year}년 {s_month}월 {s_day}일
    - 태어난 시간: {time}
    - **[핵심 팩트] 계산된 일주(Day Pillar)**: {ilju} (이 값은 절대적 기준입니다.)

    [2. 분석 요청 사항 - 상세히 작성할 것]
    다음 3단계로 나누어 명확하고 통찰력 있게 답변해 주세요. 마크다운 형식을 사용하여 가독성을 높이세요.

    ## 1단계: 사주 원국과 대운 분석 (선천운 정밀 진단)
    1. **사주팔자(四柱八字) 구성**:
       - 연주, 월주, 일주(확정값: {ilju}), 시주를 표나 리스트로 정리하세요.
       - **중요**: 각 기둥의 천간/지지가 내 일간(나)에게 어떤 **십신(비견, 겁재, 식신, 상관, 편재, 정재, 편관, 정관, 편인, 정인)**에 해당하는지 반드시 함께 표기하세요.
    2. **오행 분석**:
       - 목, 화, 토, 금, 수의 분포를 파악하고 **과다한 오행**과 **결핍된 오행**을 지적하세요.
       - 이에 따른 기질적 특징(성격)을 설명하세요.
    3. **대운(大運)의 흐름**:
       - 현재 대운(10년 운)이 나에게 유리한 흐름(용신/희신운)인지, 불리한 흐름(기신운)인지 분석하세요.

    ## 2단계: 성명학 분석 (이름의 보완력)
    * 이름 '{name_h}'의 **발음 오행**이 사주의 부족한 기운을 채워주고 있는지 분석하세요.
    * (한자가 있다면) 한자의 **자원 오행**이 1단계에서 분석한 용신(필요한 기운)과 일치하는지 평가하세요.
    * 결론적으로 이 이름이 개운(운을 좋게 함)에 도움이 되는지 판단하세요.

    ## 3단계: 2026년 병오년(丙午年) 심층 운세
    *2026년의 붉은 말(적토마)의 기운이 내 사주와 만났을 때를 예측합니다.*
    
    1. **운세 총론**: 2026년 병오년의 천간(丙)과 지지(午)가 내 사주 원국과 맺는 **합(合)·충(沖)·형(刑)** 관계를 분석하여 한 문장으로 요약하세요.
    2. **테마별 상세 운세**:
       - **💰 재물운**: 돈의 흐름, 투자 적기, 손실 위험, 횡재수 여부
       - **🏢 직업/사업운**: 승진, 이직, 창업, 관재구설(소송/다툼) 가능성
       - **❤️ 애정/대인관계**: 연애운, 결혼운, 부부 관계, 귀인의 등장 여부
       - **💪 건강운**: 화(火) 기운의 태과/부족에 따른 주의할 신체 부위 및 관리법
    3. **월별 흐름 팁**: 2026년 중 가장 운이 좋은 시기(달)와 조심해야 할 시기를 구체적으로 짚어주세요.
    """
    return prompt

# 5. 사이드바 UI
with st.sidebar:
    st.title("📝 사용자 정보 입력")
    
    st.markdown("### 1. 이름 정보")
    name_hangul = st.text_input("한글 이름", placeholder="예: 홍길동")
    name_hanja = st.text_input("한자 이름 (선택)", placeholder="예: 洪吉童")
    
    st.markdown("---")
    st.markdown("### 2. 사주 정보")
    gender = st.radio("성별", ["남자", "여자"])
    
    col1, col2 = st.columns(2)
    with col1:
        birth_year = st.number_input("생년", 1900, 2030, 1990)
    with col2:
        birth_month = st.number_input("생월", 1, 12, 1)
    birth_day = st.number_input("생일", 1, 31, 1)
    
    calendar_type = st.selectbox("양력/음력", ["양력", "음력(평달)", "음력(윤달)"])
    
    is_birth_time_unknown = st.checkbox("태어난 시간을 모름")
    if not is_birth_time_unknown:
        birth_time = st.time_input("태어난 시간", datetime.time(12, 00))
        birth_time_str = birth_time.strftime("%H시 %M분")
    else:
        birth_time_str = "모름"

    analyze_btn = st.button("운세 & 성명 심층 풀이", type="primary")

# 6. 메인 로직
st.title("🔮 AI 사주 & 성명학 정밀 분석")
st.markdown("""
당신의 사주 원국에 **십신(十神)과 대운(大運)**을 더해 더욱 정밀하게 분석합니다.  
또한, **2026년 병오년**의 재물, 직업, 건강 운세를 상세하게 예측해 드립니다.
""")
st.divider()

if analyze_btn:
    if not API_KEY:
        st.error("API Key 오류: .env 파일을 확인해주세요.")
    elif not name_hangul:
        st.warning("이름을 입력해주세요.")
    else:
        try:
            # 1. 계산 로직 실행
            solar_y, solar_m, solar_d = convert_to_solar(birth_year, birth_month, birth_day, calendar_type)
            calculated_ilju = calculate_day_ganzhi(solar_y, solar_m, solar_d)
            
            st.success(f"✅ 데이터 확정: [{name_hangul}]님 / 일주: {calculated_ilju} / 양력: {solar_y}.{solar_m}.{solar_d}")
            
            # 2. AI 모델 설정 및 호출
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel('gemini-3-pro-preview')
            
            original_date_str = f"{birth_year}년 {birth_month}월 {birth_day}일"
            
            full_prompt = generate_advanced_prompt(
                name_hangul, name_hanja, gender, 
                solar_y, solar_m, solar_d, 
                calendar_type, original_date_str, birth_time_str,
                calculated_ilju
            )
            
            with st.spinner(f"🔍 {name_hangul}님의 대운과 2026년 운세를 심층 분석 중입니다..."):
                response = model.generate_content(full_prompt, stream=True)
                
                output_container = st.empty()
                full_text = ""
                for chunk in response:
                    full_text += chunk.text
                    output_container.markdown(full_text)
                    
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")