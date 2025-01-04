import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# Zigbang API 호출 함수 (리스트 조회)
def get_officetel_data(params):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'origin': 'https://www.zigbang.com',
        'referer': 'https://www.zigbang.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-zigbang-platform': 'www',
    }

    try:
        response = requests.get('https://apis.zigbang.com/v2/items/officetel', params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 오류: {e}")
        return None

# Zigbang API 호출 함수 (아이템 상세 조회)
def get_item_details(item_id):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'origin': 'https://www.zigbang.com',
        'referer': 'https://www.zigbang.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-zigbang-platform': 'www',
    }

    params = {'version': '', 'domain': 'zigbang'}

    try:
        response = requests.get(f'https://apis.zigbang.com/v3/items/{item_id}', params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"아이템 상세 호출 오류: {e}")
        return None

# Streamlit 앱
def main():
    st.title("Zigbang 오피스텔 데이터 조회 및 분석")
    st.write("필터를 설정하여 Zigbang API에서 오피스텔 데이터를 조회하고 분석합니다.")

    # 사용자 입력
    deposit_min = st.number_input("최소 보증금", min_value=0, value=0, step=100)
    rent_min = st.number_input("최소 월세", min_value=0, value=0, step=10)
    sales_types = st.multiselect("거래 유형 선택", ["전세", "월세", "매매"], default=["전세", "월세", "매매"])

    lng_east = st.text_input("동쪽 경도", "127.04692252633676")
    lng_west = st.text_input("서쪽 경도", "127.02884177478633")
    lat_south = st.text_input("남쪽 위도", "37.51019474676496")
    lat_north = st.text_input("북쪽 위도", "37.520694651161314")
    geohash = st.text_input("지오해시", "wydm7")

    if st.button("데이터 조회"):
        with st.spinner("데이터를 가져오는 중..."):
            params = {
                'depositMin': deposit_min,
                'rentMin': rent_min,
                'salesTypes[0]': sales_types[0] if len(sales_types) > 0 else '',
                'salesTypes[1]': sales_types[1] if len(sales_types) > 1 else '',
                'salesTypes[2]': sales_types[2] if len(sales_types) > 2 else '',
                'lngEast': lng_east,
                'lngWest': lng_west,
                'latSouth': lat_south,
                'latNorth': lat_north,
                'geohash': geohash,
                'domain': 'zigbang',
                'checkAnyItemWithoutFilter': 'true',
                'withBuildings': 'true',
            }

            data = get_officetel_data(params)

            if data and "items" in data:
                st.success("데이터 조회 성공!")
                items = data["items"]
                detailed_data = []

                for item in items:
                    item_id = item.get("itemId")
                    details = get_item_details(item_id)
                    if details:
                        detailed_item = {
                            "Item ID": item_id,
                            "보증금": details.get("item", {}).get("price", {}).get("deposit", "N/A"),
                            "월세": details.get("item", {}).get("price", {}).get("rent", "N/A"),
                            "방 타입": details.get("item", {}).get("roomType", "N/A"),
                            "타이틀": details.get("item", {}).get("title", "N/A"),
                            "중개사무소 이름": details.get("realtor", {}).get("officeTitle", "N/A"),
                            "중개사무소 전화번호": details.get("realtor", {}).get("officePhone", "N/A"),
                            "단지 이름": details.get("danji", {}).get("name", "N/A"),
                        }
                        detailed_data.append(detailed_item)

                # 데이터를 데이터프레임으로 변환 후 표시
                df = pd.DataFrame(detailed_data)
                st.dataframe(df)

                # 보증금과 월세 데이터 (숫자 변환 및 정리)
                deposit_data = pd.to_numeric(df['보증금'], errors='coerce').dropna()
                rent_data = pd.to_numeric(df['월세'], errors='coerce').dropna()

                if len(deposit_data) == 0 or len(rent_data) == 0:
                    st.error("보증금 또는 월세 데이터가 유효하지 않습니다. 데이터 형식을 확인해주세요.")
                else:
                    # 그래프 생성
                    st.write("### 보증금 및 월세 분포와 정규분포")
                    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

                    # 보증금 히스토그램 및 정규분포
                    deposit_mean, deposit_std = norm.fit(deposit_data)
                    deposit_x = np.linspace(deposit_data.min(), deposit_data.max(), 1000)
                    deposit_pdf = norm.pdf(deposit_x, deposit_mean, deposit_std)

                    axes[0, 0].hist(deposit_data, bins=5, density=True, alpha=0.6, color='blue', edgecolor='black')
                    axes[0, 0].plot(deposit_x, deposit_pdf, 'r-', lw=2)
                    axes[0, 0].set_title(f"보증금 정규분포\n평균: {deposit_mean:.2f}, 표준편차: {deposit_std:.2f}")
                    axes[0, 0].set_xlabel("보증금")
                    axes[0, 0].set_ylabel("확률 밀도")

                    # 월세 히스토그램 및 정규분포
                    rent_mean, rent_std = norm.fit(rent_data)
                    rent_x = np.linspace(rent_data.min(), rent_data.max(), 1000)
                    rent_pdf = norm.pdf(rent_x, rent_mean, rent_std)

                    axes[0, 1].hist(rent_data, bins=5, density=True, alpha=0.6, color='green', edgecolor='black')
                    axes[0, 1].plot(rent_x, rent_pdf, 'r-', lw=2)
                    axes[0, 1].set_title(f"월세 정규분포\n평균: {rent_mean:.2f}, 표준편차: {rent_std:.2f}")
                    axes[0, 1].set_xlabel("월세")
                    axes[0, 1].set_ylabel("확률 밀도")

                    # 히스토그램만
                    axes[1, 0].hist(deposit_data, bins=5, edgecolor='black', alpha=0.7)
                    axes[1, 0].set_title("보증금 분포")
                    axes[1, 0].set_xlabel("보증금")
                    axes[1, 0].set_ylabel("빈도")

                    axes[1, 1].hist(rent_data, bins=5, edgecolor='black', alpha=0.7)
                    axes[1, 1].set_title("월세 분포")
                    axes[1, 1].set_xlabel("월세")
                    axes[1, 1].set_ylabel("빈도")

                    plt.tight_layout()
                    st.pyplot(fig)

            else:
                st.error("데이터를 가져올 수 없습니다.")

if __name__ == "__main__":
    main()
