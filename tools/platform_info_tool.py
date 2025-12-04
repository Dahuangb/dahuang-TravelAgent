"""
通过Web搜索获取携程、马蜂窝、大众点评、小红书等平台的详细信息
这是一个增强工具，用于补充百度地图API返回的信息不足问题
"""
import os
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import re

class PlatformInfoInput(BaseModel):
    name: str = Field(description="景点或餐厅名称")
    city: str = Field(description="所在城市")
    poi_type: str = Field(description="类型：attraction 或 restaurant")

class PlatformInfoTool(BaseTool):
    name: Optional[str] = "platform_info"
    description: Optional[str] = "通过搜索获取携程、马蜂窝、大众点评、小红书等平台的评价和详细信息"
    args_schema: Optional[type] = PlatformInfoInput

    def _parse_search_results(self, search_text: str, platform: str) -> Dict:
        """从搜索结果文本中提取信息"""
        info = {
            "rating": None,
            "review_count": None,
            "key_points": [],
            "summary": ""
        }
        
        # 尝试提取评分（如"4.5分"、"4.8/5"等）
        rating_patterns = [
            r'(\d+\.?\d*)\s*分',
            r'评分[：:]\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*/\s*5',
        ]
        for pattern in rating_patterns:
            match = re.search(pattern, search_text)
            if match:
                try:
                    info["rating"] = float(match.group(1))
                    break
                except:
                    pass
        
        # 提取评价数量
        count_patterns = [
            r'(\d+)\s*条评价',
            r'(\d+)\s*个评价',
            r'评价[：:]\s*(\d+)',
        ]
        for pattern in count_patterns:
            match = re.search(pattern, search_text)
            if match:
                try:
                    info["review_count"] = int(match.group(1))
                    break
                except:
                    pass
        
        # 提取关键词（如"推荐"、"必去"、"好吃"等）
        keywords = ["推荐", "必去", "值得", "不错", "好吃", "美味", "打卡", "网红"]
        for keyword in keywords:
            if keyword in search_text:
                info["key_points"].append(keyword)
        
        # 生成摘要（取前200字符）
        if len(search_text) > 200:
            info["summary"] = search_text[:200] + "..."
        else:
            info["summary"] = search_text
        
        return info

    def _run(self, name: str, city: str, poi_type: str) -> Dict:
        """获取平台增强信息"""
        enhanced_info = {
            "携程": {"rating": None, "review_count": None, "summary": "", "key_points": []},
            "马蜂窝": {"rating": None, "review_count": None, "summary": "", "key_points": []},
            "大众点评": {"rating": None, "review_count": None, "summary": "", "key_points": []},
            "小红书": {"rating": None, "review_count": None, "summary": "", "key_points": []},
            "enhanced_description": "",
            "recommended_tags": []
        }
        
        # 构建搜索查询
        if poi_type == "attraction":
            queries = {
                "携程": f"{name} {city} 携程 景点 评价",
                "马蜂窝": f"{name} {city} 马蜂窝 攻略 游记",
                "大众点评": f"{name} {city} 大众点评 景点",
                "小红书": f"{name} {city} 小红书 打卡 攻略"
            }
        else:  # restaurant
            queries = {
                "携程": f"{name} {city} 携程 餐厅 美食",
                "马蜂窝": f"{name} {city} 马蜂窝 美食",
                "大众点评": f"{name} {city} 大众点评 餐厅 美食",
                "小红书": f"{name} {city} 小红书 美食 推荐"
            }
        
        # 注意：这里需要在实际运行时调用web_search工具
        # 由于当前环境限制，我们返回一个结构化的结果
        # 实际使用时，应该：
        # from web_search import web_search  # 或使用MCP
        # for platform, query in queries.items():
        #     search_results = web_search(query)
        #     enhanced_info[platform] = self._parse_search_results(search_results, platform)
        
        # 生成增强描述
        descriptions = []
        for platform, data in enhanced_info.items():
            if platform != "enhanced_description" and platform != "recommended_tags":
                if data.get("rating"):
                    descriptions.append(f"{platform}评分{data['rating']}分")
                if data.get("summary"):
                    descriptions.append(data["summary"][:50])
        
        enhanced_info["enhanced_description"] = " | ".join(descriptions[:3]) if descriptions else ""
        
        return enhanced_info

