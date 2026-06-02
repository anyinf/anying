import streamlit as st
import pandas as pd
import os
import time
from datetime import date
from PIL import Image

# ================= 0. 設定頁面佈局 =================
st.set_page_config(layout="wide", page_title="球員傷害紀錄系統-雲端版", page_icon="🏃‍♂️")

# ================= 1. Google Sheets 網址直連設定 =================
# 這是你的 Google 試算表 ID
SHEET_ID = "1R3DcQytURBd2YNc2hv5A6-zECprYQMUFa2wFIpB9gcA"

# 使用 Pandas 內建格式，不需要安裝任何額外套件！
INJURY_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=injury_records"
MEDICAL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=medical_records"

# 圖片儲存暫留本機
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_images")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- 球員名單 ---
PLAYER_LIST = [
    "許少捷", "顏子謙", "吳誌珈", "林承恩(大)","李雚喆","林誠恩","葉一鋐","王弘彥","朱宸益","李冠中","王浩臣","曾顯恩","陳培力",
    "高恆恩","林丞圻","李佳昊","林承恩(小)","廖元億","尹蓋·法拉斯","吳星樺","李振綸","張甯翔","李聖韓","陳培安","徐巳凱","李振陽",
    "林浩震","蔣林昱辰","余彥偉","陳宏宇","楊博隆","王弘恩","邱承葦","吳天豪","王聖恩","陳逸恩","葉澄泰","邱彥祖","高士凱","黃皓揚"
]

# ================= 2. 雲端資料載入與儲存函數 (免套件版) =================
@st.cache_data(ttl=5)  
def load_cloud_data(url, date_column):
    try:
        # 直接用 pandas 抓取雲端 CSV 格式
        df = pd.read_csv(url)
        if df is not None and not df.empty:
            df = df.dropna(how="all")
            
            if "ID" in df.columns and not df.empty:
                df["ID"] = pd.to_numeric(df["ID"], errors='coerce').fillna(0).astype(int)
                
            if date_column in df.columns and not df.empty:
                df[date_column] = df[date_column].astype(str)
                df = df.sort_values(by=date_column, ascending=False).reset_index(drop=True)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"讀取雲端失敗。請確保你的 Google 試算表分頁名稱完全正確，且已開啟「知道連結的任何人皆可檢視」。錯誤: {e}")
        return pd.DataFrame()

def save_cloud_data(df, url_type):
    # 因為免套件版是用 URL 唯讀抓取，若要在網頁端寫入，我們提供引導
    st.error("💡 提示：目前為安全唯讀模式。如需新增/修改資料，請直接打開你的 Google 試算表填寫，網頁會在 5 秒內自動同步更新！")
    st.info(f"🔗 你的試算表後台網址： https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
    return False

# 重新從雲端拉取最新資料
df_records = load_cloud_data(INJURY_URL, "發生日期")
df_medical = load_cloud_data(MEDICAL_URL, "就醫時間")

if "current_image" not in st.session_state:
    st.session_state["current_image"] = None

# ================= 3. 側邊欄功能導覽 =================
st.sidebar.title("📌 導覽選單")
menu = st.sidebar.radio("請選擇功能：", ["傷害紀錄查詢", "就醫紀錄檢視"])

st.sidebar.divider()
st.sidebar.success("☁️ 雲端同步模式 (免套件免維護)")

st.title("🏃‍♂️ 球員傷害紀錄資料庫系统 (雲端直連版)")
st.divider()

# ================= 功能一：傷害紀錄管理 =================
if menu == "傷害紀錄查詢":
    
    # ---- 區塊 A：關鍵字搜尋 ----
    st.header("🔍 查詢球員紀錄")
    search_options = ["全部顯示"] + PLAYER_LIST
    selected_player = st.selectbox("選擇球員姓名進行查詢：", options=search_options)

    if not df_records.empty:
        if selected_player != "全部顯示":
            filtered_df = df_records[df_records["球員姓名"] == selected_player]
            st.subheader(f"「{selected_player}」的歷史紀錄 (依時間由新到舊)：")
        else:
            filtered_df = df_records
            st.subheader("顯示所有紀錄 (依時間由新到舊)：")

        if not filtered_df.empty:
            st.dataframe(filtered_df[["ID", "球員姓名", "受傷部位與敘述", "發生日期", "目前狀態"]], use_container_width=True, hide_index=True)
        else:
            st.info("目前沒有符合的紀錄。")
    else:
        st.info("雲端資料庫目前沒有任何傷害紀錄，或試算表分頁名稱非 `injury_records`。")

    st.divider()

    # ---- 引導直接去雲端輸入 ----
    st.header("➕ 新增傷害紀錄")
    st.info("請直接點選下方按鈕前往 Google 試算表手動輸入資料。輸入完後，本網頁會在 5 秒內自動更新，讓大家在這裡搜尋！")
    st.link_button("👉 打開 Google 試算表新增資料", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")

# ================= 功能二：新增就醫紀錄 =================
elif menu == "就醫紀錄檢視":
    st.header("🩺 就醫診療紀錄")
    
    st.info("請直接點選下方按鈕前往 Google 試算表手動輸入就醫資料。輸入完後，本網頁會在 5 秒內自動更新！")
    st.link_button("👉 打開 Google 試算表新增資料", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")

    # ---- 歷史就醫紀錄摘要檢視 ----
    st.divider()
    st.subheader("📋 歷史就醫紀錄檢視 (依時間由新到舊)")
    
    if not df_medical.empty:
        cols_for_display = ["姓名", "就醫時間", "診斷結果"]
        st.dataframe(df_medical[cols_for_display], use_container_width=True, hide_index=True)
        
        st.write("---")
        st.caption("👈 點擊左側「查看/點開照片」按鈕，即可在下方放大觀看完整證明。")
        for i, row in df_medical.iterrows():
            with st.container():
                btn_cols = st.columns([0.2, 0.8])
                with btn_cols[0]:
                    img_path = row["圖片路徑"]
                    if img_path and str(img_path) != 'None' and os.path.exists(str(img_path)):
                        if st.button("查看/點開照片", key=f"view_img_{i}"):
                            st.session_state["current_image"] = img_path
                    else:
                        st.caption(" ( 無照片 ) ")
                with btn_cols[1]:
                    st.caption(f"📅 {row['就醫時間']} | 👤 {row['姓名']}: {row['診斷結果'][:40]}...")

        # 圖片顯示區域
        if st.session_state["current_image"]:
            st.divider()
            st.subheader("🖼️ 完整就醫證明照片")
            img_path = st.session_state["current_image"]
            try:
                img = Image.open(img_path)
                st.image(img, caption="就醫證明照片預覽", use_container_width=True)
            except Exception as e:
                st.error(f"無法開啟圖片: {e}")
            if st.button("關閉照片", key="close_img"):
                st.session_state["current_image"] = None
                st.rerun()
    else:
        st.info("目前沒有就醫紀錄，或試算表分頁名稱非 `medical_records`。")