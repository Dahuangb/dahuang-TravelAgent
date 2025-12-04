import math
from datetime import datetime, timedelta
from models.day_plan import Activity, DayPlan
import random

SPEED_WALK = 80  # 米/分钟


def distance_meters(lat1, lng1, lat2, lng2):
    # 简化球面距离（km→m）
    # 使用 Haversine 公式计算两点间的大圆距离
    from math import radians, cos, sin, sqrt, atan2
    R = 6371000  # 地球半径（米）
    
    # 验证坐标范围（防御性检查）
    if not (-90 <= lat1 <= 90) or not (-90 <= lat2 <= 90):
        raise ValueError(f"纬度超出范围: lat1={lat1}, lat2={lat2}")
    if not (-180 <= lng1 <= 180) or not (-180 <= lng2 <= 180):
        raise ValueError(f"经度超出范围: lng1={lng1}, lng2={lng2}")
    
    φ1, φ2 = radians(lat1), radians(lat2)
    Δφ = radians(lat2 - lat1)
    Δλ = radians(lng2 - lng1)
    a = sin(Δφ / 2) ** 2 + cos(φ1) * cos(φ2) * sin(Δλ / 2) ** 2
    distance = R * 2 * atan2(sqrt(a), sqrt(1 - a))
    
    # 如果距离异常大（超过1000公里），可能是坐标错误
    if distance > 1000000:  # 1000公里
        raise ValueError(f"计算出的距离异常大: {distance/1000:.2f}km，可能是坐标错误")
    
    return distance


def score_activity(current_lat, current_lng, current_time, left_minutes, poi):
    # 返回分数、交通时间、推荐停留时长
    try:
        d = distance_meters(current_lat, current_lng, poi["lat"], poi["lng"])
    except (ValueError, KeyError) as e:
        # 如果距离计算失败，返回一个较大的默认值，避免程序崩溃
        print(f"警告：距离计算失败: {e}, 使用默认值")
        d = 1000  # 默认1公里
    
    # 计算步行时间，确保至少为1分钟（即使距离很小也要显示）
    t_trans = max(1, int(d / SPEED_WALK))  # 步行分钟，至少1分钟
    t_stay = 60 if poi["category"] == "attraction" else 45
    if poi["category"] == "restaurant":
        t_stay = 60
    score = max(0, left_minutes - t_trans - t_stay)
    return score, t_trans, t_stay


def greedy_daily_schedule(hotel_lat, hotel_lng, hotel_name, avail_attractions, avail_restaurants, day_start, day, 
                          hotel_price=200, adults=2, destination="", personal_requirements="", children=0,
                          llm_selection=None):
    """使用大模型决策的每日行程规划 + 费用计算
    
    Args:
        hotel_price: 酒店每晚价格（元）
        adults: 成人人数
        children: 儿童人数
        destination: 目的地城市
        personal_requirements: 个性化需求
        llm_selection: 大模型选择的行程（DayPlanSelection对象）
    """
    activities = []
    current_time = day_start
    current_lat, current_lng = hotel_lat, hotel_lng

    # 费用累计
    total_attraction_cost = 0  # 门票费用
    total_restaurant_cost = 0  # 餐饮费用
    total_transport_cost = 0   # 交通费用（步行免费，但预留出租车费用）

    # 1. 酒店入住
    activities.append(Activity(name=f"入住 {hotel_name}", start=current_time, end=current_time + timedelta(minutes=30),
                               category="hotel"))
    current_time += timedelta(minutes=30)

    # 2. 根据大模型选择找到对应的景点和餐厅
    morning_attr = None
    lunch_rest = None
    afternoon_attr = None
    dinner_rest = None
    
    if llm_selection:
        # 查找上午景点
        for attr in avail_attractions:
            if attr["name"] == llm_selection.morning_attraction.name:
                morning_attr = attr
                break
        
        # 查找午餐餐厅
        for rest in avail_restaurants:
            if rest["name"] == llm_selection.lunch.name:
                lunch_rest = rest
                break
        
        # 查找下午景点
        for attr in avail_attractions:
            if attr["name"] == llm_selection.afternoon_attraction.name:
                afternoon_attr = attr
                break
        
        # 查找晚餐餐厅
        for rest in avail_restaurants:
            if rest["name"] == llm_selection.dinner.name:
                dinner_rest = rest
                break
    
    # 如果大模型选择失败，回退到贪心算法
    if not morning_attr or not lunch_rest or not afternoon_attr or not dinner_rest:
        # 回退逻辑：使用贪心算法
        avail_attr = avail_attractions.copy()
        avail_rest = avail_restaurants.copy()
        
        left_minutes_am = int((current_time.replace(hour=12, minute=0) - current_time).total_seconds() / 60)
        morning_attr = max(avail_attr, key=lambda a: score_activity(current_lat, current_lng, current_time, left_minutes_am, a)[0])
        lunch_rest = random.choice(avail_rest)
        avail_attr.remove(morning_attr)
        
        left_minutes_pm = int((current_time.replace(hour=18, minute=0) - current_time.replace(hour=12, minute=0) - timedelta(minutes=60)).total_seconds() / 60)
        afternoon_attr = max(avail_attr, key=lambda a: score_activity(current_lat, current_lng, current_time.replace(hour=12, minute=0) + timedelta(minutes=60), left_minutes_pm, a)[0])
        dinner_candidates = [r for r in avail_rest if r != lunch_rest]
        dinner_rest = random.choice(dinner_candidates if dinner_candidates else avail_rest)

    # 3. 上午景点
    left_minutes_am = int((current_time.replace(hour=12, minute=0) - current_time).total_seconds() / 60)
    score_am, t_trans_am, t_stay_am = score_activity(current_lat, current_lng, current_time, left_minutes_am, morning_attr)
    activities.append(
        Activity(name=morning_attr["name"], start=current_time, end=current_time + timedelta(minutes=t_trans_am + t_stay_am),
                 transport_mode="步行", transport_duration=t_trans_am, category="attraction"))
    # 计算门票费用（成人全价，儿童半价，通常1.2米以下免费但这里统一按半价计算）
    ticket_price_am = morning_attr.get("门票数值", 0)
    total_attraction_cost += int(ticket_price_am * adults + ticket_price_am * 0.5 * children)
    current_lat, current_lng = morning_attr["lat"], morning_attr["lng"]
    current_time += timedelta(minutes=t_trans_am + t_stay_am)

    # 4. 午餐
    lunch_time = current_time.replace(hour=12, minute=0) if current_time.hour < 12 else current_time
    # 确保午餐有步行距离（从上午景点到午餐餐厅）
    t_lunch, _, _ = score_activity(current_lat, current_lng, lunch_time, 60, lunch_rest)
    # 确保步行时间至少为1分钟（即使距离很小）
    t_lunch = max(1, t_lunch)
    activities.append(Activity(name=f"午餐 - {lunch_rest['name']}", start=lunch_time,
                               end=lunch_time + timedelta(minutes=60),
                               transport_mode="步行", transport_duration=t_lunch, category="meal"))
    # 计算午餐费用（成人全价，儿童半价）
    lunch_price = lunch_rest.get("人均数值", 50)
    total_restaurant_cost += int(lunch_price * adults + lunch_price * 0.5 * children)
    current_time = lunch_time + timedelta(minutes=60)
    current_lat, current_lng = lunch_rest["lat"], lunch_rest["lng"]

    # 5. 下午景点
    left_minutes_pm = int((current_time.replace(hour=18, minute=0) - current_time).total_seconds() / 60)
    score_pm, t_trans_pm, t_stay_pm = score_activity(current_lat, current_lng, current_time, left_minutes_pm, afternoon_attr)
    activities.append(
        Activity(name=afternoon_attr["name"], start=current_time, end=current_time + timedelta(minutes=t_trans_pm + t_stay_pm),
                 transport_mode="步行", transport_duration=t_trans_pm, category="attraction"))
    # 计算门票费用（成人全价，儿童半价）
    ticket_price_pm = afternoon_attr.get("门票数值", 0)
    total_attraction_cost += int(ticket_price_pm * adults + ticket_price_pm * 0.5 * children)
    current_lat, current_lng = afternoon_attr["lat"], afternoon_attr["lng"]
    current_time += timedelta(minutes=t_trans_pm + t_stay_pm)

    # 6. 晚餐
    dinner_time = current_time.replace(hour=18, minute=0) if current_time.hour < 18 else current_time
    # 确保晚餐有步行距离（从下午景点到晚餐餐厅）
    t_dinner, _, _ = score_activity(current_lat, current_lng, dinner_time, 60, dinner_rest)
    # 确保步行时间至少为1分钟（即使距离很小）
    t_dinner = max(1, t_dinner)
    activities.append(
        Activity(name=f"晚餐 - {dinner_rest['name']}", start=dinner_time,
                 end=dinner_time + timedelta(minutes=60), transport_mode="步行",
                 transport_duration=t_dinner, category="meal"))
    # 计算晚餐费用（成人全价，儿童半价）
    dinner_price = dinner_rest.get("人均数值", 50)
    total_restaurant_cost += int(dinner_price * adults + dinner_price * 0.5 * children)
    current_time = dinner_time + timedelta(minutes=60)
    current_lat, current_lng = dinner_rest["lat"], dinner_rest["lng"]

    # 7. 返回酒店功能已删除（因为距离计算不稳定，导致时间异常）
    # 行程在晚餐后结束，用户自行返回酒店
    
    # 计算交通费用（预留出租车费用，如果距离较远）
    # 只计算步行活动的距离
    total_distance = sum(act.transport_duration * 80 / 1000 for act in activities 
                        if act.transport_mode == "步行" and act.transport_duration > 0)  # 公里
    if total_distance > 5:  # 如果总步行距离超过5公里，预留出租车费用
        total_transport_cost = int((total_distance - 5) * 2)  # 每公里2元

    # 住宿费用：只在第一天计算，其他天为0（因为已经按总天数计算）
    # 注意：住宿费用应该在总费用计算时单独处理，这里每天设为0
    accommodation_cost = 0  # 住宿费用按总天数单独计算，不在这里累加

    # 计算备用金（总费用的10%，不含住宿）
    daily_total = total_restaurant_cost + total_transport_cost + total_attraction_cost
    contingency_cost = int(daily_total * 0.1)

    # 保存大模型的选择理由（如果有）
    plan_reason = ""
    if llm_selection:
        plan_reason = f"""
**行程安排理由：**
- 上午景点：{llm_selection.morning_attraction.reason}
- 午餐：{llm_selection.lunch.reason}
- 下午景点：{llm_selection.afternoon_attraction.reason}
- 晚餐：{llm_selection.dinner.reason}
- 整体安排：{llm_selection.overall_reason}
"""

    return DayPlan(
        day=day,
        activities=activities,
        accommodation=int(accommodation_cost),
        restaurant=int(total_restaurant_cost),
        transport=int(total_transport_cost),
        attraction=int(total_attraction_cost),
        contingency=int(contingency_cost)
    ), plan_reason
