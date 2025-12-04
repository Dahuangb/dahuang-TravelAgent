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

class HotelSearchInput(BaseModel):
    lat: float = Field(description="纬度")
    lng: float = Field(description="经度")
    radius: int = Field(3000, description="搜索半径（米）")

class HotelTool(BaseTool):
    name: Optional[str] = "hotel_search"
    description: Optional[str] = "根据经纬度搜索周边酒店（Top-5，百度地图版）"
    args_schema: Optional[type] = HotelSearchInput

    def _calculate_distance(self, lat1, lng1, lat2, lng2):
        """计算两点间距离（米）"""
        R = 6371000  # 地球半径（米）
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def _run(self, lat: float, lng: float, radius: int = 3000):
        if not BAIDU_AK:
            return [{"error": "未配置百度地图密钥（BAIDU_AK）。请在环境变量或 Streamlit secrets 中设置。"}]

        url = "http://api.map.baidu.com/place/v2/search"
        params = {
            "ak": BAIDU_AK,
            "query": "酒店",
            "location": f"{lat},{lng}",  # 百度地图格式：纬度,经度
            "radius": radius,
            "output": "json",
            "scope": 2,  # 返回详细信息
            "page_size": 5,  # Top-5
            "page_num": 0
        }
        r = requests.get(url, params=params, timeout=5).json()
        if r.get("status") != 0:
            return [{"error": r.get("message", "unknown")}]

        hotels = []
        for poi in r.get("results", []):
            # 计算距离
            poi_lat = poi.get("location", {}).get("lat", lat)
            poi_lng = poi.get("location", {}).get("lng", lng)
            distance = int(self._calculate_distance(lat, lng, poi_lat, poi_lng))
            
            # 获取价格信息（百度地图在detail_info中可能包含price字段）
            detail_info = poi.get("detail_info", {})
            price = detail_info.get("price", None)
            
            # 获取评分
            rating = detail_info.get("overall_rating", None)
            if rating:
                try:
                    rating = float(rating)
                except:
                    rating = None
            
            # 如果API没有返回价格，根据评分和距离估算价格
            if not price or price == "" or price == "暂无":
                # 基于评分的价格估算（元/晚）
                if rating and rating >= 4.5:
                    estimated_price = 300 + (rating - 4.5) * 200  # 4.5分以上：300-500元
                elif rating and rating >= 4.0:
                    estimated_price = 200 + (rating - 4.0) * 200  # 4.0-4.5分：200-300元
                elif rating and rating >= 3.5:
                    estimated_price = 150 + (rating - 3.5) * 100  # 3.5-4.0分：150-200元
                else:
                    estimated_price = 100  # 3.5分以下：100元
                
                # 根据距离市中心调整（越近越贵）
                if distance < 1000:
                    estimated_price = int(estimated_price * 1.2)
                elif distance > 5000:
                    estimated_price = int(estimated_price * 0.8)
                
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
                    price_value = 200  # 默认值
                    price = f"¥{price_value}"
            
            hotels.append({
                "酒店名称": poi.get("name", "未知"),
                "评分": rating,
                "价格": price,
                "价格数值": price_value,  # 添加数值字段用于计算
                "距离(米)": distance,
                "地址": poi.get("address", ""),
                "lat": poi_lat,
                "lng": poi_lng
            })
        
        # 按距离排序
        hotels.sort(key=lambda x: x["距离(米)"])
        return hotels if hotels else [{"error": "未找到周边酒店"}]