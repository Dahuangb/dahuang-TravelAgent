import os, requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional
import math

BAIDU_AK = os.getenv("BAIDU_AK") or "raNbXCNaFAkXvEWv18eQkL9jTol2Wfj2"

class AttractionSearchInput(BaseModel):
    lat: float = Field(description="纬度")
    lng: float = Field(description="经度")
    radius: int = Field(5000, description="搜索半径（米）")

class AttractionTool(BaseTool):
    name: Optional[str] = "attraction_search"
    description: Optional[str] = "根据经纬度搜索周边景点（Top-20，百度地图版）"
    args_schema: Optional[type] = AttractionSearchInput

    def _calculate_distance(self, lat1, lng1, lat2, lng2):
        """计算两点间距离（米）"""
        R = 6371000  # 地球半径（米）
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def _run(self, lat: float, lng: float, radius: int = 10000):
        url = "http://api.map.baidu.com/place/v2/search"
        params = {
            "ak": BAIDU_AK,
            "query": "景点",
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

        spots = []
        for poi in r.get("results", []):
            # 计算距离
            poi_lat = poi.get("location", {}).get("lat", lat)
            poi_lng = poi.get("location", {}).get("lng", lng)
            distance = int(self._calculate_distance(lat, lng, poi_lat, poi_lng))
            
            # 获取详细信息
            detail_info = poi.get("detail_info", {})
            
            # 获取价格/门票信息（百度地图在detail_info中可能包含price字段）
            price = detail_info.get("price", None)
            
            # 获取开放时间
            open_time = detail_info.get("open_time", "暂无")
            if not open_time:
                open_time = "暂无"
            
            # 获取评分
            rating = detail_info.get("overall_rating", None)
            if rating:
                try:
                    rating = float(rating)
                except:
                    rating = None
            
            # 获取景点类型
            poi_type = poi.get("type", "")
            # 从type中提取景点类型（如"风景名胜;公园"）
            attraction_type = "景点"
            if poi_type:
                types = poi_type.split(";")
                for t in types:
                    if "风景名胜" in t or "公园" in t or "博物馆" in t or "寺庙" in t or "古镇" in t:
                        attraction_type = t.replace("风景名胜;", "").replace(";", " ")
                        break
            
            # 获取标签/特色
            tag = detail_info.get("tag", "")
            if not tag:
                tag = detail_info.get("type", "")
            if not tag:
                tag = ""
            
            # 获取电话
            phone = detail_info.get("phone", "")
            if not phone:
                phone = poi.get("telephone", "")
            
            # 生成推荐描述（基于名称和类型）
            description = ""
            name = poi.get("name", "")
            if "公园" in name or "公园" in attraction_type:
                description = "适合休闲散步、拍照打卡的公园景点"
            elif "博物馆" in name or "博物馆" in attraction_type:
                description = "文化历史类景点，适合了解当地文化"
            elif "寺庙" in name or "寺庙" in attraction_type:
                description = "宗教文化景点，适合祈福和参观"
            elif "古镇" in name or "古镇" in attraction_type:
                description = "传统古镇，体验当地民俗文化"
            elif "山" in name or "山" in attraction_type:
                description = "自然风光景点，适合登山观景"
            elif "湖" in name or "湖" in attraction_type or "水" in name:
                description = "水景风光，适合休闲观光"
            else:
                description = "值得一游的景点"
            
            # 推荐游玩时长（基于景点类型）
            recommended_duration = "1-2小时"
            if "博物馆" in attraction_type or "古镇" in attraction_type:
                recommended_duration = "2-3小时"
            elif "公园" in attraction_type:
                recommended_duration = "1-2小时"
            elif "山" in attraction_type:
                recommended_duration = "3-4小时"
            
            # 如果API没有返回价格，根据景点类型和评分估算门票价格
            if not price or price == "" or price == "免费":
                # 基于评分的门票估算（元）
                if rating and rating >= 4.5:
                    estimated_price = 80 + (rating - 4.5) * 40  # 4.5分以上：80-120元
                elif rating and rating >= 4.0:
                    estimated_price = 50 + (rating - 4.0) * 60  # 4.0-4.5分：50-80元
                elif rating and rating >= 3.5:
                    estimated_price = 30 + (rating - 3.5) * 40  # 3.5-4.0分：30-50元
                else:
                    estimated_price = 20  # 3.5分以下：20元
                
                # 检查名称中是否包含"免费"、"公园"等关键词
                name_lower = poi.get("name", "").lower()
                if "免费" in name_lower or "公园" in name_lower or "广场" in name_lower:
                    estimated_price = 0
                
                if estimated_price == 0:
                    price = "免费"
                    price_value = 0
                else:
                    price = f"¥{int(estimated_price)}"
                    price_value = int(estimated_price)
            else:
                # 尝试从价格字符串中提取数字
                import re
                if "免费" in str(price).lower():
                    price_value = 0
                    price = "免费"
                else:
                    price_match = re.search(r'(\d+)', str(price))
                    if price_match:
                        price_value = int(price_match.group(1))
                        price = f"¥{price_value}"
                    else:
                        price_value = 50  # 默认值
                        price = f"¥{price_value}"
            
            # 尝试获取平台增强信息（可选，如果失败不影响主流程）
            platform_info = {}
            try:
                from tools.platform_info_tool import PlatformInfoTool
                platform_tool = PlatformInfoTool()
                platform_info = platform_tool._run(
                    name=poi.get("name", ""),
                    city="",  # 城市信息需要从外部传入
                    poi_type="attraction"
                )
                # 合并平台信息到推荐描述
                if platform_info.get("enhanced_description"):
                    description = f"{description} | {platform_info['enhanced_description']}"
            except:
                pass  # 如果获取平台信息失败，使用原有描述
            
            spots.append({
                "景点名称": poi.get("name", "未知"),
                "评分": rating,
                "门票": price,
                "门票数值": price_value,  # 添加数值字段用于计算
                "开放时间": str(open_time),
                "距离(米)": distance,
                "地址": poi.get("address", ""),
                "景点类型": attraction_type,
                "标签/特色": tag if tag else "暂无",
                "电话": phone if phone else "暂无",
                "推荐描述": description,
                "推荐游玩时长": recommended_duration,
                "平台信息": platform_info,  # 添加平台信息
                "location": f"{poi_lng},{poi_lat}"  # 保持与原有格式兼容：经度,纬度
            })
        
        # 按距离排序
        spots.sort(key=lambda x: x["距离(米)"])
        return spots if spots else [{"error": "未找到周边景点"}]