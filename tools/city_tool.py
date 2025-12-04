import os
from typing import Optional

import requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

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

class CityInfoInput(BaseModel):
    city: str = Field(description="城市中文名")

class CityTool(BaseTool):
    name: Optional[str] = "city_info"
    description: Optional[str] = "查询城市经纬度、行政区划、简介（百度地图版）"
    args_schema: Optional[type] = CityInfoInput

    def _run(self, city: str):
        if not BAIDU_AK:
            return {"error": "未配置百度地图密钥（BAIDU_AK）。请在环境变量或 Streamlit secrets 中设置。"}

        # 1. 百度地图地理编码拿经纬度
        geo_url = "http://api.map.baidu.com/geocoding/v3/"
        params = {
            "ak": BAIDU_AK,
            "address": city,
            "output": "json"
        }
        r = requests.get(geo_url, params=params, timeout=5).json()
        if r.get("status") != 0 or not r.get("result") or not r["result"].get("location"):
            return {"error": f"百度地理编码失败：{r.get('message', 'unknown')}"}

        location = r["result"]["location"]
        lng = float(location["lng"])
        lat = float(location["lat"])

        # 2. 百度地图逆地理编码拿行政区划+简介
        regeo_url = "http://api.map.baidu.com/reverse_geocoding/v3/"
        params2 = {
            "ak": BAIDU_AK,
            "location": f"{lat},{lng}",  # 百度地图格式：纬度,经度
            "output": "json",
            "pois": 0  # 不返回周边POI
        }
        r2 = requests.get(regeo_url, params=params2, timeout=5).json()
        if r2.get("status") != 0 or not r2.get("result"):
            return {"error": f"百度逆地理编码失败：{r2.get('message', 'unknown')}"}

        address = r2["result"].get("formatted_address", "")  # 省市区拼接
        return {
            "city":      city,
            "latitude":  lat,
            "longitude": lng,
            "timezone":  "UTC+8",          # 国内统一
            "summary":   address or "暂无简介"
        }