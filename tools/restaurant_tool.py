import math
import os

import requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional

try:
    import streamlit as st  # type: ignore
except Exception:
    st = None  # type: ignore


def _get_baidu_ak() -> str | None:
    """优先从环境变量 / Streamlit secrets 中安全获取百度地图 AK。"""
    ak = os.getenv("BAIDU_AK")
    if ak:
        return ak
    if st is not None:
        try:
            return st.secrets.get("BAIDU_AK")  # type: ignore[attr-defined]
        except Exception:
            return None
    return None


BAIDU_AK = _get_baidu_ak()

class RestaurantSearchInput(BaseModel):
    lat: float = Field(description="纬度")
    lng: float = Field(description="经度")
    radius: int = Field(2000, description="搜索半径（米）")

class RestaurantTool(BaseTool):
    name:        Optional[str] = "restaurant_search"
    description: Optional[str] = "根据经纬度搜索周边餐厅（Top-20，百度地图版）"
    args_schema: Optional[type] = RestaurantSearchInput

    def _calculate_distance(self, lat1, lng1, lat2, lng2):
        """计算两点间距离（米）"""
        R = 6371000  # 地球半径（米）
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def _run(self, lat: float, lng: float, radius: int = 10000):
        if not BAIDU_AK:
            return [{"error": "未配置百度地图密钥（BAIDU_AK）。请在环境变量或 Streamlit secrets 中设置。"}]

        url = "http://api.map.baidu.com/place/v2/search"
        params = {
            "ak": BAIDU_AK,
            "query": "餐厅",
            "location": f"{lat},{lng}",  # 百度地图格式：纬度,经度
            "radius": radius,
            "output": "json",
            "scope": 2,  # 返回详细信息
            "page_size": 20,  # Top-20
            "page_num": 0
        }
        r = requests.get(url, params=params, timeout=5).json()
        if r.get("status") != 0:
            return [{"error": r.get("message", "unknown")}]

        restaurants = []
        for poi in r.get("results", []):
            # 计算距离
            poi_lat = poi.get("location", {}).get("lat", lat)
            poi_lng = poi.get("location", {}).get("lng", lng)
            distance = int(self._calculate_distance(lat, lng, poi_lat, poi_lng))
            
            # 获取详细信息
            detail_info = poi.get("detail_info", {})
            
            # 获取价格/人均信息（百度地图在detail_info中可能包含price字段）
            price = detail_info.get("price", None)
            
            # 获取菜系/标签（百度地图在detail_info中可能包含tag字段）
            tag = detail_info.get("tag", "")
            if not tag:
                # 如果没有tag，尝试从typename获取
                tag = poi.get("detail_info", {}).get("type", "")
            if not tag:
                tag = poi.get("type", "").split(";")[0] if poi.get("type") else ""
            if not tag:
                tag = "暂无"
            
            # 获取评分
            rating = detail_info.get("overall_rating", None)
            if rating:
                try:
                    rating = float(rating)
                except:
                    rating = None
            
            # 获取营业时间
            open_time = detail_info.get("open_time", "")
            if not open_time:
                open_time = "暂无"
            
            # 获取电话
            phone = detail_info.get("phone", "")
            if not phone:
                phone = poi.get("telephone", "")
            
            # 生成推荐描述（基于菜系和评分）
            description = ""
            tag_str = str(tag).lower()
            if "火锅" in tag_str:
                description = "适合聚餐的火锅店，氛围热闹"
            elif "日料" in tag_str or "日本" in tag_str:
                description = "日式料理，精致美味"
            elif "西餐" in tag_str:
                description = "西式餐厅，适合约会或商务"
            elif "川菜" in tag_str or "湘菜" in tag_str:
                description = "地道川湘菜，口味偏辣"
            elif "粤菜" in tag_str:
                description = "粤式餐厅，口味清淡"
            elif "快餐" in tag_str or "小吃" in tag_str:
                description = "快捷便利，适合简餐"
            else:
                description = "值得尝试的餐厅"
            
            # 根据评分调整描述
            if rating and rating >= 4.5:
                description += "，口碑极佳"
            elif rating and rating >= 4.0:
                description += "，口碑不错"
            
            # 推荐招牌菜（基于菜系）
            signature_dish = ""
            if "火锅" in tag_str:
                signature_dish = "推荐：特色锅底、新鲜食材"
            elif "日料" in tag_str:
                signature_dish = "推荐：刺身、寿司"
            elif "川菜" in tag_str:
                signature_dish = "推荐：麻婆豆腐、水煮鱼"
            elif "湘菜" in tag_str:
                signature_dish = "推荐：剁椒鱼头、小炒肉"
            elif "粤菜" in tag_str:
                signature_dish = "推荐：白切鸡、叉烧"
            else:
                signature_dish = "推荐：招牌菜"
            
            # 如果API没有返回价格，根据评分和菜系估算人均价格
            if not price or price == "" or price == "暂无":
                # 基于评分的人均估算（元）
                if rating and rating >= 4.5:
                    estimated_price = 80 + (rating - 4.5) * 40  # 4.5分以上：80-120元
                elif rating and rating >= 4.0:
                    estimated_price = 50 + (rating - 4.0) * 60  # 4.0-4.5分：50-80元
                elif rating and rating >= 3.5:
                    estimated_price = 30 + (rating - 3.5) * 40  # 3.5-4.0分：30-50元
                else:
                    estimated_price = 25  # 3.5分以下：25元
                
                # 根据菜系调整（火锅、日料等通常更贵）
                tag_str = str(tag).lower()
                if "火锅" in tag_str or "日料" in tag_str or "西餐" in tag_str:
                    estimated_price = int(estimated_price * 1.3)
                elif "快餐" in tag_str or "小吃" in tag_str:
                    estimated_price = int(estimated_price * 0.7)
                
                price = f"¥{int(estimated_price)}"
                price_value = int(estimated_price)  # 保存数值用于计算
            else:
                # 尝试从价格字符串中提取数字
                import re
                price_match = re.search(r'(\d+)', str(price))
                if price_match:
                    price_value = int(price_match.group(1))
                    price = f"¥{price_value}"
                else:
                    price_value = 50  # 默认值
                    price = f"¥{price_value}"
            
            # 平台增强信息将在app.py中异步获取，这里先留空
            platform_info = {}
            
            restaurants.append({
                "餐厅名称": poi.get("name", "未知"),
                "评分": rating,
                "人均(元)": price,
                "人均数值": price_value,  # 添加数值字段用于计算
                "菜系/标签": str(tag),
                "距离(米)": distance,
                "地址": poi.get("address", ""),
                "营业时间": str(open_time),
                "电话": phone if phone else "暂无",
                "推荐描述": description,
                "推荐招牌菜": signature_dish,
                "平台信息": platform_info,  # 添加平台信息字段
                "location": f"{poi_lng},{poi_lat}"  # 保持与原有格式兼容：经度,纬度
            })
        
        # 按距离排序
        restaurants.sort(key=lambda x: x["距离(米)"])
        return restaurants if restaurants else [{"error": "未找到周边餐厅"}]