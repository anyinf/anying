import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 設定網頁標題與寬度佈局
st.set_page_config(page_title="投手春季聯賽數據分析 Dashboard", layout="wide")
st.title("⚾ 投手春季聯賽數據分析儀表板")

# 📊 棒球專用局數進位轉換器 (加裝究極安全護盾)
def convert_innings(val):
    try:
        if val is None:
            return 0.0
        val_str = str(val).strip()
        if val_str == "" or val_str.lower() in ["nan", "none"]:
            return 0.0
        val_float = float(val_str)
        integer_part = int(val_float)
        decimal_part = round(val_float - integer_part, 1)
        if decimal_part == 0.1:
            return integer_part + 0.3333
        elif decimal_part == 0.2:
            return integer_part + 0.6667
        else:
            return val_float
    except:
        return 0.0

# 🔢 安全轉數字工具
def safe_to_numeric(val):
    try:
        if val is None:
            return 0.0
        val_str = str(val).strip()
        if val_str == "" or val_str.lower() in ["nan", "none"]:
            return 0.0
        return float(val_str)
    except:
        return 0.0

# ==================== 1. 側邊欄：手動檔案上傳 ====================
st.sidebar.header("📁 數據檔案輸入")
uploaded_file = st.sidebar.file_uploader("請上傳您的投手 Excel 檔案 (.xlsx)", type=["xlsx"])

# ==================== 2. 判斷檔案是否存在 ====================
if uploaded_file is None:
    st.info("👋 您好！請先在左側邊欄點擊或拖曳上傳您的 Excel 檔案。上傳後即可開始切換功能分析！")
else:
    try:
        # 讀取 Excel
        df = pd.read_excel(uploaded_file)
        
        # 🌟 核心修復：強制將所有欄位名稱全部轉換成乾淨的去空白字串
        df.columns = [str(col).strip() for col in df.columns]
        
        # 強制修復可能缺失或型態錯誤的核心欄位，避免後續繪圖計算噴 TypeError
        core_cols = ['總球數', '好球數', '壞球數', '奪三振', '四死球', '被安打', '自責分', '最速']
        for col in core_cols:
            if col in df.columns:
                df[col] = df[col].apply(safe_to_numeric)
            else:
                df[col] = 0.0
        
        # 安全計算真實局數
        if '局數' in df.columns:
            df['真實局數'] = df['局數'].apply(convert_innings)
        else:
            df['真實局數'] = 0.0
            
        st.sidebar.success("🎉 檔案上傳成功！")
        st.sidebar.write("---")
        
        # ==================== 3. 側邊欄主要功能切換 ====================
        st.sidebar.header("⚙️ 功能切換選單")
        main_function = st.sidebar.radio(
            "請選擇您要查看的功能：",
            ["1. 投手的數據分析", "2. 投手春聯表現"]
        )
        
        # 強制將球員姓名都當成字串處理
        if '出賽球員' in df.columns:
            df['出賽球員'] = df['出賽球員'].astype(str).str.strip()
            all_pitchers = sorted([p for p in df['出賽球員'].unique() if p not in ['nan', 'None', '']])
        else:
            all_pitchers = []
            
        # ==================== 功能一：投手的數據分析 ====================
        if main_function == "1. 投手的數據分析":
            st.markdown("## 🎯 投手核心數據與指標比例")
            
            if len(all_pitchers) == 0:
                st.warning("⚠️ 您的 Excel 檔案中找不到『出賽球員』這一欄，請檢查欄位名稱是否正確。")
            else:
                selected_pitcher_1 = st.sidebar.selectbox("請選擇要分析的投手：", all_pitchers, key="func_1")
                
                p_df = df[df['出賽球員'] == selected_pitcher_1]
                
                total_balls = p_df['總球數'].sum()
                total_strikes = p_df['好球數'].sum()
                total_bad_balls = p_df['壞球數'].sum()
                total_so = p_df['奪三振'].sum()
                total_bb = p_df['四死球'].sum()
                total_h = p_df['被安打'].sum()
                total_er = p_df['自責分'].sum()
                total_ip = p_df['真實局數'].sum()
                max_speed = p_df['最速'].max()
                
                era = (total_er * 9 / total_ip) if total_ip > 0 else 0.0
                whip = ((total_h + total_bb) / total_ip) if total_ip > 0 else 0.0
                
                st.markdown(f"### 目前檢視選手：**{selected_pitcher_1}**")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("自責分率 (ERA)", f"{era:.2f}")
                col2.metric("每局被上壘率 (WHIP)", f"{whip:.2f}")
                col3.metric("最快球速 (MAX)", f"{int(max_speed)} km/h" if max_speed > 0 else "無數據")
                col4.metric("累積投球局數", f"{total_ip:.1f} 局")
                
                st.write("---")
                
                # 建立圓餅圖數據
                pie_data = pd.DataFrame({
                    '指標項目': ['好球數', '壞球數', '奪三振(個)', '四死球(個)', '被安打(支)'],
                    '數量': [total_strikes, total_bad_balls, total_so, total_bb, total_h]
                })
                
                fig_pie = px.pie(
                    pie_data, 
                    values='數量', 
                    names='指標項目', 
                    title=f"【{selected_pitcher_1}】個人投球好壞球與事件比例分布",
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
        # ==================== 功能二：投手春聯表現 ====================
        elif main_function == "2. 投手春聯表現":
            st.markdown("## 📈 投手春聯個別壓制力評估")
            
            if len(all_pitchers) == 0:
                st.warning("⚠️ 您的 Excel 檔案中找不到『出賽球員』這一欄，請檢查欄位名稱是否正確。")
            else:
                selected_pitcher_2 = st.sidebar.selectbox("請選擇要查看春聯表現的選手：", all_pitchers, key="func_2")
                
                pitcher_stats = []
                for pitcher, group in df.groupby('出賽球員'):
                    if pd.isna(pitcher) or str(pitcher).strip() in ['nan', 'None', '']: 
                        continue
                    t_balls = group['總球數'].sum()
                    t_strikes = group['好球數'].sum()
                    t_er = group['自責分'].sum()
                    t_ip = group['真實局數'].sum()
                    
                    s_rate = (t_strikes / t_balls * 100) if t_balls > 0 else 0.0
                    era = (t_er * 9 / t_ip) if t_ip > 0 else 0.0
                    
                    pitcher_stats.append({
                        '投手': pitcher,
                        '好球率 (%)': round(s_rate, 1),
                        '防禦率 (ERA)': round(era, 2),
                        '總球數': t_balls,
                        '累積投球局數': round(t_ip, 1)
                    })
                
                summary_df = pd.DataFrame(pitcher_stats)
                
                if not summary_df.empty:
                    target_label = f"🎯 {selected_pitcher_2} (目前選手)"
                    summary_df['焦點標記'] = summary_df['投手'].apply(
                        lambda x: target_label if str(x) == str(selected_pitcher_2) else '其他聯賽球員'
                    )
                    
                    st.markdown(f"### 正在追蹤：**{selected_pitcher_2}** 在全隊的壓制力落點")
                    
                    fig_scatter = px.scatter(
                        summary_df,
                        x='好球率 (%)',
                        y='防禦率 (ERA)',
                        text='投手',
                        size='總球數',
                        color='焦點標記',
                        title=f"春季聯賽全隊投手控球與壓制力分佈 (目前觀測: {selected_pitcher_2})",
                        labels={
                            '好球率 (%)': '好球率 (%) → 越高代表控球越好', 
                            '防禦率 (ERA)': '防禦率 (ERA) ↓ 越低代表壓制力越強'
                        },
                        color_discrete_map={target_label: '#FF4B4B', '其他聯賽球員': '#1C83E1'},
                        hover_data=['累積投球局數']
                    )
                    
                    fig_scatter.update_traces(textposition='top center')
                    fig_scatter.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.warning("目前無足夠的投手數據來繪製分佈圖。")

    except Exception as e:
        st.error(f"❌ 初始化時發生未知錯誤。詳細錯誤訊息: {e}")