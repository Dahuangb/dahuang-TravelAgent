import streamlit as st
from datetime import date, timedelta
from models.trip_schema import TripRequest
from tools.city_tool import CityTool
from datetime import date, timedelta, datetime
from streamlit_folium import st_folium
import random

noise = lambda: random.uniform(-0.02, 0.02)  ##2公里的微小扰动
# ---------- 会话初始化 ----------
if "page" not in st.session_state:
    st.session_state.page = "form"

# ---------- 页面配置 ----------
st.set_page_config(
    page_title="dahuang-TravelAgent",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🧳"
)

# ---------- 自定义样式 ----------
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    .info-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #1f77b4;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #1f77b4;
    }
    .trip-day {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- 页面标题 ----------
st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.title("🧳 dahuang-TravelAgent")
st.subheader("一个基于大模型的旅游智能推荐助手")
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.page == "form":
    # ---------- 侧边栏表单 ----------
    with st.sidebar:
        st.header("📝 旅行需求")
        st.markdown("---")
        
        st.markdown("### 🚗 基本信息")
        departure = st.text_input("出发城市", "北京", help="请输入您的出发城市")
        destination = st.text_input("目的城市", "苏州", help="请输入您要前往的目的地")
        
        st.markdown("### 📅 出行时间")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("出发日期", value=date.today(), key="start")
        with col2:
            end_date = st.date_input("返回日期", value=date.today() + timedelta(days=2), key="end")
        
        # 验证日期
        if end_date <= start_date:
            st.warning("⚠️ 返回日期必须晚于出发日期")
        
        st.markdown("### 👥 出行人数")
        col1, col2 = st.columns(2)
        with col1:
            adults = st.number_input("成人人数", min_value=1, max_value=10, value=2, help="1-10人")
        with col2:
            children = st.number_input("儿童人数", min_value=0, max_value=10, value=1, help="0-10人")
        
        st.markdown("### 💰 预算信息")
        budget = st.number_input("总预算（元）", min_value=100, step=500, value=5000, help="请输入您的总预算")
        
        st.markdown("### ✨ 个性化需求")
        personal = st.text_area(
            "个性化需求",
            placeholder="例如：喜欢历史文化、偏好安静环境、需要无障碍设施等...",
            help="请描述您的特殊需求或偏好"
        )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 重置", use_container_width=True):
                st.session_state.page = "form"
                st.rerun()
        with col2:
            if st.button("🚀 生成推荐", type="primary", use_container_width=True):
                # 验证日期
                if end_date <= start_date:
                    st.error("返回日期必须晚于出发日期，请重新选择")
                else:
                    # 把参数一次性存进 session_state，避免 NameError
                    st.session_state.req = dict(
                        departure=departure,
                        destination=destination,
                        start_date=start_date,
                        end_date=end_date,
                        adults=adults,
                        children=children,
                        budget=budget,
                        personal=personal
                    )
                    st.session_state.page = "result"
                    st.rerun()
    
    # ---------- 主页面内容 ----------
    st.markdown("""
    ### 👋 欢迎使用 dahuang-TravelAgent！
    
    这是一个智能旅游推荐助手，可以根据您的需求为您规划完美的旅行行程。
    
    **✨ 主要功能：**
    - 🏨 智能酒店推荐
    - 🏞️ 精选景点推荐
    - 🍴 特色餐厅推荐
    - 📅 自动行程规划
    - 💰 预算智能分配
    
    **📝 使用步骤：**
    1. 在左侧边栏填写您的旅行需求
    2. 点击"生成推荐"按钮
    3. 查看为您定制的旅行方案
    
    ---
    """)
    
    # 示例展示
    with st.expander("📖 查看示例", expanded=False):
        st.markdown("""
        **示例需求：**
        - 出发城市：北京
        - 目的城市：苏州
        - 出行日期：今天 ～ 后天
        - 人数：2大1小
        - 预算：5000元
        - 个性化需求：喜欢历史文化、偏好安静环境
        """)

elif st.session_state.page == "result":
    # 取出参数
    req_data = st.session_state.req
    try:
        req = TripRequest(**req_data)  # ✅ 仅此一行
    except Exception as e:
        st.error(f"参数校验失败：{e}")
        st.stop()
    
    # ---------- 返回按钮 ----------
    if st.button("← 返回修改需求", type="secondary"):
        st.session_state.page = "form"
        st.rerun()
    
    st.markdown("---")
    
    # ---------- 需求摘要卡片 ----------
    with st.container():
        st.markdown("### 📋 您的旅行需求")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("出发地", req.departure)
        with col2:
            st.metric("目的地", req.destination)
        with col3:
            trip_days = (req.end_date - req.start_date).days + 1
            st.metric("出行天数", f"{trip_days}天")
        with col4:
            st.metric("总预算", f"¥{req.budget}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"👥 **人数**：{req.adults} 大 {req.children} 小 | 📅 **日期**：{req.start_date} ～ {req.end_date}")
        with col2:
            if req.personal:
                st.info(f"✨ **个性化需求**：{req.personal}")
            else:
                st.info("✨ **个性化需求**：无特殊要求")
    
    st.markdown("---")
    
    # ---------- 使用标签页组织内容 ----------
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏙️ 城市信息", "🏨 酒店选择", "🏞️ 景点推荐", "🍴 餐厅推荐", "📅 行程规划"])
    
    # 2. 查询目的地城市信息
    with st.spinner("正在查询城市信息..."):
        tool = CityTool()
        result = tool._run(req.destination)
        if "error" in result:
            st.warning(f"城市信息获取失败：{result['error']}")
        else:
            with tab1:
                st.success("✅ 城市信息查询成功！")
                st.markdown(f"### 🌍 {req.destination}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("纬度", f"{result['latitude']:.2f}°")
                with col2:
                    st.metric("经度", f"{result['longitude']:.2f}°")
                with col3:
                    st.metric("时区", result['timezone'])
                
                st.markdown("---")
                st.markdown(f"**📖 城市简介**")
                # 使用大模型生成城市简介
                with st.spinner("正在生成城市简介..."):
                    from chains.city_intro_chain import get_city_introduction
                    city_intro = get_city_introduction(req.destination)
                    st.info(city_intro)
    # 3. 自选酒店（锚点）
    with tab2:
        with st.spinner("正在搜索周边酒店..."):
            from tools.hotel_tool import HotelTool

            hotels = HotelTool()._run(lat=result['latitude'], lng=result['longitude'])
            if hotels and "error" not in hotels[0]:
                st.markdown("### 🏨 推荐酒店")
                # 让用户选一家
                hotel_options = [f"{h['酒店名称']} | ¥{h['价格']} | ⭐{h['评分']}" for h in hotels]
                selected = st.selectbox("请选择您要入住的酒店", hotel_options, index=0, key="hotel_select")
                selected_idx = hotel_options.index(selected)
                hotel = hotels[selected_idx]  # 真实 Top-N 对象

                # 真实坐标 & 名字
                hotel_lat = float(hotel.get("lat", result['latitude']))
                hotel_lng = float(hotel.get("lng", result['longitude']))
                hotel_name = hotel["酒店名称"]

                st.success(f"✅ 已选择：**{hotel_name}**")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("价格", f"¥{hotel['价格']}")
                with col2:
                    st.metric("评分", f"⭐{hotel['评分']}")
                with col3:
                    st.metric("距离市中心", f"{hotel['距离(米)']}m")
                
                st.info(f"📍 **地址**：{hotel['地址']}")
            else:
                st.warning("⚠️ 暂无周边酒店数据")
                # 兜底：用城市中心
                hotel_lat, hotel_lng, hotel_name = result['latitude'], result['longitude'], "市中心酒店"
                hotel = {"酒店名称": hotel_name, "价格数值": 200}  # 默认价格
                st.info(f"将使用默认位置：{hotel_name}")
    # 4. 查询周边景点 + 短期记忆（点赞/删除）
    # 先获取景点数据（在标签页外部，确保作用域正确）
    with st.spinner("正在搜索周边景点..."):
        from tools.attraction_tool import AttractionTool
        from tools.platform_info_tool import PlatformInfoTool

        attractions_raw = AttractionTool()._run(lat=result['latitude'], lng=result['longitude'])
    
    with tab3:
        attractions = attractions_raw
        
        # 可选：为Top-3景点获取平台增强信息
        if attractions and "error" not in attractions[0]:
            platform_tool = PlatformInfoTool()
            for i, attr in enumerate(attractions[:3]):  # 只为前3个获取，避免API调用过多
                try:
                    platform_info = platform_tool._run(
                        name=attr["景点名称"],
                        city=req.destination,
                        poi_type="attraction"
                    )
                    attr["平台信息"] = platform_info
                    # 合并到推荐描述
                    if platform_info.get("enhanced_description"):
                        attr["推荐描述"] = f"{attr.get('推荐描述', '')} | {platform_info['enhanced_description']}"
                except Exception as e:
                    pass  # 如果失败，不影响主流程
        
        if attractions and "error" not in attractions[0]:
            # ---------- 短期记忆 ----------
            if "liked_attractions" not in st.session_state:
                st.session_state.liked_attractions = set()
            if "removed_attractions" not in st.session_state:
                st.session_state.removed_attractions = set()

            # 过滤已删除
            filtered = [a for a in attractions if a["景点名称"] not in st.session_state.removed_attractions]

            # 排序：点赞的置顶，其余保持原序
            def sort_key(a):
                return (0 if a["景点名称"] in st.session_state.liked_attractions else 1, attractions.index(a))

            filtered.sort(key=sort_key)

            st.markdown("### 🏞️ 推荐景点")
            st.caption("💡 提示：您可以点赞喜欢的景点（会优先安排），或删除不感兴趣的景点")
            
            for idx, a in enumerate(filtered[:5], 1):  # 只展示 Top-5
                is_liked = a["景点名称"] in st.session_state.liked_attractions
                like_icon = "❤️" if is_liked else "🤍"
                
                with st.expander(f"{idx}. {a['景点名称']} ⭐{a.get('评分', 'N/A')} {like_icon}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"📍 **地址**：{a.get('地址', '暂无')}")
                        st.markdown(f"🎫 **门票**：{a.get('门票', '免费')}")
                        st.markdown(f"⏰ **开放时间**：{a.get('开放时间', '暂无')}")
                        st.markdown(f"📌 **类型**：{a.get('景点类型', '景点')}")
                        st.markdown(f"⏱️ **推荐游玩时长**：{a.get('推荐游玩时长', '1-2小时')}")
                        if a.get('推荐描述'):
                            st.markdown(f"💡 **推荐理由**：{a.get('推荐描述', '')}")
                        if a.get('标签/特色') and a.get('标签/特色') != '暂无':
                            st.markdown(f"🏷️ **特色标签**：{a.get('标签/特色', '')}")
                    with col2:
                        if is_liked:
                            if st.button("取消点赞", key=f"unlike_{a['景点名称']}", use_container_width=True):
                                st.session_state.liked_attractions.discard(a["景点名称"])
                                st.rerun()
                        else:
                            if st.button("❤️ 点赞", key=f"like_{a['景点名称']}", use_container_width=True):
                                st.session_state.liked_attractions.add(a["景点名称"])
                                st.rerun()
                        if st.button("🗑️ 删除", key=f"del_{a['景点名称']}", use_container_width=True):
                            st.session_state.removed_attractions.add(a["景点名称"])
                            st.rerun()
                        st.metric("距离", f"{a.get('距离(米)', 0)}m")
        else:
            st.warning("⚠️ 暂无周边景点数据")
    # 5. 查询周边餐厅
    # 先获取餐厅数据（在标签页外部，确保作用域正确）
    with st.spinner("正在搜索周边餐厅..."):
        from tools.restaurant_tool import RestaurantTool
        from tools.platform_info_tool import PlatformInfoTool

        restaurants_raw = RestaurantTool()._run(lat=result['latitude'], lng=result['longitude'])
    
    with tab4:
        restaurants = restaurants_raw
        
        # 可选：为Top-3餐厅获取平台增强信息
        if restaurants and "error" not in restaurants[0]:
            platform_tool = PlatformInfoTool()
            for i, rest in enumerate(restaurants[:3]):  # 只为前3个获取，避免API调用过多
                try:
                    platform_info = platform_tool._run(
                        name=rest["餐厅名称"],
                        city=req.destination,
                        poi_type="restaurant"
                    )
                    rest["平台信息"] = platform_info
                    # 合并到推荐描述
                    if platform_info.get("enhanced_description"):
                        rest["推荐描述"] = f"{rest.get('推荐描述', '')} | {platform_info['enhanced_description']}"
                except Exception as e:
                    pass  # 如果失败，不影响主流程
        if restaurants and "error" not in restaurants[0]:
            st.markdown("### 🍴 推荐餐厅")
            st.caption("💡 为您精选的Top-5餐厅，将根据行程自动安排用餐时间")
            
            for idx, r in enumerate(restaurants[:5], 1):
                with st.expander(f"{idx}. {r['餐厅名称']} ⭐{r.get('评分', 'N/A')}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"📍 **地址**：{r.get('地址', '暂无')}")
                        st.markdown(f"💰 **人均消费**：¥{r.get('人均(元)', '暂无')}")
                        st.markdown(f"🍽️ **菜系**：{r.get('菜系/标签', '暂无')}")
                        st.markdown(f"⏰ **营业时间**：{r.get('营业时间', '暂无')}")
                        if r.get('推荐描述'):
                            st.markdown(f"💡 **推荐理由**：{r.get('推荐描述', '')}")
                        if r.get('推荐招牌菜'):
                            st.markdown(f"🍜 **推荐招牌菜**：{r.get('推荐招牌菜', '')}")
                        if r.get('电话') and r.get('电话') != '暂无':
                            st.markdown(f"📞 **电话**：{r.get('电话', '')}")
                    with col2:
                        st.metric("距离", f"{r.get('距离(米)', 0)}m")
        else:
            st.warning("⚠️ 暂无周边餐厅数据")
    # 6. 预算分配和行程规划
    with tab5:
        # 6.1 预算分配
        with st.spinner("正在生成预算分配..."):
            from chains.budget_chain import budget_chain, parser

            plan = budget_chain.invoke({
                "departure": req.departure,
                "destination": req.destination,
                "adults": req.adults,
                "children": req.children,
                "start_date": req.start_date,
                "end_date": req.end_date,
                "budget": req.budget,
                "format_instructions": parser.get_format_instructions(),
            })

            st.markdown("### 💰 预算分配建议")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("住宿", f"¥{plan.accommodation}")
            with col2:
                st.metric("餐饮", f"¥{plan.restaurant}")
            with col3:
                st.metric("交通", f"¥{plan.transport}")
            with col4:
                st.metric("门票", f"¥{plan.attraction}")
            with col5:
                st.metric("备用", f"¥{plan.contingency}")

            st.info(f"💡 **分配说明**：{plan.reason}")
        
        st.markdown("---")
        
        trip_days = (req.end_date - req.start_date).days + 1  # 含首尾
        st.markdown(f"### 📅 行程安排（共 {trip_days} 天）")
        # 7. 生成行程（需要先处理景点和餐厅数据）
        with st.spinner("正在准备行程数据..."):
            from tools.route_planner import greedy_daily_schedule
            from tools.route_planner import score_activity

            # 使用从标签页外部获取的原始数据
            # 注意：attraction_tool 和 restaurant_tool 返回的 location 格式是 "lng,lat"（经度,纬度）
            attractions_list = attractions_raw if attractions_raw and "error" not in (attractions_raw[0] if attractions_raw else {}) else []
            restaurants_list = restaurants_raw if restaurants_raw and "error" not in (restaurants_raw[0] if restaurants_raw else {}) else []
            
            attractions = [
                {
                    "name": a["景点名称"],
                    "lat": float(a.get("location", f"{result['longitude']},{result['latitude']}").split(",")[1]) + noise(),
                    "lng": float(a.get("location", f"{result['longitude']},{result['latitude']}").split(",")[0]) + noise(),
                    "category": "attraction",
                    "门票数值": a.get("门票数值", 0)  # 保留门票价格信息
                }
                for a in attractions_list
            ]
            restaurants = [
                {
                    "name": r["餐厅名称"],
                    "lat": float(r.get("location", f"{result['longitude']},{result['latitude']}").split(",")[1]) + noise(),
                    "lng": float(r.get("location", f"{result['longitude']},{result['latitude']}").split(",")[0]) + noise(),
                    "category": "restaurant",
                    "人均数值": r.get("人均数值", 50)  # 保留人均价格信息
                }
                for r in restaurants_list
            ]
        
        # 8. 生成全程行程（动态天数，含所有 Day）
        all_days = []
        avail_attractions = attractions.copy()  # 剩余景点
        avail_restaurants = restaurants.copy()  # 剩余餐厅

        # 获取酒店价格（从hotel字典中提取）
        hotel_price = hotel.get("价格数值", 200)  # 默认200元/晚
        if not hotel_price or hotel_price == 0:
            hotel_price = 200
        
        # 使用进度条显示生成进度
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for day in range(1, trip_days + 1):
            progress = day / trip_days
            progress_bar.progress(progress)
            status_text.text(f"正在规划 Day {day}/{trip_days} 行程...")
            
            with st.spinner(f"正在使用AI规划 Day{day} 行程..."):
                from chains.day_plan_chain import plan_day_with_llm
                
                hotel_name = hotel["酒店名称"]
                
                # 使用大模型规划行程
                try:
                    llm_selection = plan_day_with_llm(
                        day=day,
                        destination=req.destination,
                        personal_requirements=req.personal,
                        avail_attractions=avail_attractions[:15],  # 限制数量避免token过多
                        avail_restaurants=avail_restaurants[:15],
                        hotel_name=hotel_name,
                        adults=req.adults,
                        children=req.children
                    )
                except Exception as e:
                    st.warning(f"AI规划失败，使用备用算法：{e}")
                    llm_selection = None
                
                # 生成实际行程
                # 设置合理的开始时间（早上8点），而不是00:00:00
                start_time = datetime.combine(req.start_date, datetime.min.time().replace(hour=8, minute=0)) + timedelta(days=day - 1)
                day_plan, plan_reason = greedy_daily_schedule(
                    hotel_lat, hotel_lng, hotel_name,
                    avail_attractions,  # 剩余景点
                    avail_restaurants,  # 剩余餐厅
                    day_start=start_time,
                    day=day,  # 真实日期编号
                    hotel_price=hotel_price,  # 传递酒店价格
                    adults=req.adults,  # 传递成人人数
                    children=req.children,  # 传递儿童人数
                    destination=req.destination,  # 传递目的地
                    personal_requirements=req.personal,  # 传递个性化需求
                    llm_selection=llm_selection  # 传递大模型选择
                )
                
                all_days.append(day_plan)
                
                # 改进行程展示
                with st.container():
                    st.markdown(f"#### 📅 Day {day} - {start_time.strftime('%Y年%m月%d日')}")
                    
                    # 显示行程安排理由
                    if plan_reason:
                        st.info(f"💡 {plan_reason}")
                    
                    # 使用卡片样式展示行程
                    for idx, act in enumerate(day_plan.activities, 1):
                        # 修复时间显示：如果跨天，显示完整日期
                        start_str = act.start.strftime('%H:%M')
                        if act.end.date() != act.start.date():
                            end_str = act.end.strftime('%m-%d %H:%M')
                        else:
                            end_str = act.end.strftime('%H:%M')
                        
                        # 根据活动类型选择图标
                        if act.category == "attraction":
                            icon = "🏞️"
                        elif act.category == "meal":
                            icon = "🍴"
                        elif act.category == "accommodation":
                            icon = "🏨"
                        else:
                            icon = "📍"
                        
                        # 显示活动
                        col1, col2 = st.columns([1, 10])
                        with col1:
                            st.markdown(f"**{start_str}**")
                        with col2:
                            transport_info = ""
                            if act.transport_mode == "步行" and act.transport_duration > 0:
                                transport_info = f" 🚶 {act.transport_duration}分钟"
                            st.markdown(f"{icon} **{act.name}** {transport_info}")
                            if act.end != act.start:
                                st.caption(f"预计结束时间：{end_str}")
                
                st.markdown("---")
                
                # 每天剔除已选 → 下一天去不同地方
                for a in day_plan.activities:
                    if a.category == "attraction":
                        # 找到对应的景点并移除
                        found = None
                        for x in avail_attractions:
                            if x["name"] == a.name:
                                found = x
                                break
                        if found:
                            avail_attractions.remove(found)
                    if a.category == "meal":
                        # 从餐厅名称中提取餐厅名（去掉"午餐 - "或"晚餐 - "前缀）
                        rest_name = a.name.replace("午餐 - ", "").replace("晚餐 - ", "")
                        found = None
                        for x in avail_restaurants:
                            if x["name"] == rest_name:
                                found = x
                                break
                        if found:
                            avail_restaurants.remove(found)
        
        # 清除进度条
        progress_bar.empty()
        status_text.empty()
        
        # 9. 全日期 Markdown 导出（所有 Day）
        st.markdown("---")
        with st.spinner("正在生成行程单..."):
            from tools.export_md import export_full_md

            md_text = export_full_md(all_days)  # 传入「所有 Day」
            st.download_button(
                label="📥 下载全程行程单（Markdown）",
                data=md_text,
                file_name=f"{req.destination}行程单.md",
                mime="text/markdown",
                use_container_width=True
            )

        # 12. 总花费汇总（字段已存在）
        st.markdown("---")
        st.markdown("### 💰 总花费汇总")
        with st.spinner("正在计算总花费..."):
            # 计算住宿总费用（按总天数）
            trip_days = (req.end_date - req.start_date).days + 1
            total_accommodation = hotel_price * trip_days
            
            # 计算其他费用（每天累加）
            total_restaurant = sum(plan.restaurant for plan in all_days)
            total_transport = sum(plan.transport for plan in all_days)
            total_attraction = sum(plan.attraction for plan in all_days)
            total_contingency = sum(plan.contingency for plan in all_days)
            
            # 总费用
            total_cost = total_accommodation + total_restaurant + total_transport + total_attraction + total_contingency
            
            # 预算对比
            budget_usage = (total_cost / req.budget) * 100 if req.budget > 0 else 0
            budget_status = "✅ 在预算内" if total_cost <= req.budget else "⚠️ 超出预算"
            
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1:
                st.metric("住宿", f"¥{total_accommodation}")
            with col2:
                st.metric("餐饮", f"¥{total_restaurant}")
            with col3:
                st.metric("交通", f"¥{total_transport}")
            with col4:
                st.metric("门票", f"¥{total_attraction}")
            with col5:
                st.metric("备用", f"¥{total_contingency}")
            with col6:
                st.metric("总计", f"¥{total_cost}", delta=f"{budget_status}")
            
            # 预算使用情况
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("预算总额", f"¥{req.budget}")
            with col2:
                st.metric("预计花费", f"¥{total_cost}")
            with col3:
                remaining = req.budget - total_cost
                st.metric("剩余预算", f"¥{remaining}", delta=f"{budget_usage:.1f}%")
            
            if total_cost > req.budget:
                st.warning(f"⚠️ 预计花费（¥{total_cost}）超出预算（¥{req.budget}），超出 ¥{total_cost - req.budget}。建议调整行程或增加预算。")
            elif remaining > req.budget * 0.2:
                st.success(f"✅ 预算充足，还有 ¥{remaining} 可用于额外消费。")
            else:
                st.info(f"💡 预算使用率 {budget_usage:.1f}%，建议保留一些备用资金。")
    # # 14. 一键 PDF 导出（纯 Python，无系统依赖）
    # with st.spinner("正在生成 PDF..."):
    #     from weasyprint import HTML  # 纯 Python，无 wkhtmltopdf
    #     from tools.export_pdf import export_pdf
    #
    #     pdf_bytes = export_pdf(md_text)  # 前面已生成 md_text
    #     st.download_button(
    #         label="下载全程行程单（PDF）",
    #         data=pdf_bytes,
    #         file_name=f"{req.destination}行程单.pdf",
    #         mime="application/pdf",
    #         key=f"download_pdf_{day}"  # 唯一 key
    #     )

# 9. 地图可视化（先跳过，后续再开发）
# with st.spinner("正在绘制路线图..."):
#     from tools.map_view import draw_route
#     map_obj = draw_route(hotel, attractions, restaurants, hotel_lat, hotel_lng)
#     st.write("**🗺️ 真实路线图**")
#     st_folium(map_obj, width=700, height=500)
#     # 9. 生成 Day1 行程（只算 Day1 示例）
#     with st.spinner("正在排程 Day1..."):
#         day1 = greedy_daily_schedule(
#             hotel_lat, hotel_lng, hotel_name, attractions, restaurants,
#             day_start=datetime.combine(req.start_date, datetime.min.time())
#         )
#         st.write("**📅 Day1 行程**")
#         for act in day1.activities:
#             st.write(
#                 f"{act.start.strftime('%m-%d %H:%M')} - {act.end.strftime('%H:%M')}　{act.name}　🚶{act.transport_duration}min")
#
#     # 10. 总里程 & 总时长（轻量级）
#     with st.spinner("正在计算总里程..."):
#         from tools.summary_card import calc_total_distance
#
#         total_km = calc_total_distance(attractions, restaurants, hotel_lat, hotel_lng)
#         total_min = sum(act.transport_duration for act in day1.activities) / 60  # 仅 Day1 示例
#         st.write("**📊 全程总结**")
#         col1, col2 = st.columns(2)
#         with col1:
#             st.metric("总步行距离", f"{total_km} km")
#         with col2:
#             st.metric("总步行时长", f"{total_min:.1f} h")
