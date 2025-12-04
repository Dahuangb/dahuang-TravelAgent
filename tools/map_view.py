import folium
from streamlit_folium import st_folium

def draw_route(hotel, attractions, restaurants, hotel_lat, hotel_lng):
    """极限轻量：只画 1 酒店 + 1 景点 + 1 餐厅 + 1 连线"""
    # 1. 起点：酒店（防御式）
    m = folium.Map(location=[hotel_lat, hotel_lng], zoom_start=14)
    folium.Marker([hotel_lat, hotel_lng], popup=hotel.get("name", "酒店"), icon=folium.Icon(color="green")).add_to(m)

    # 2. 只画第一个景点（避免几千个 Marker）
    if attractions:
        a = attractions[0]   # 只取 1 个
        lat = float(a.get("lat", hotel_lat))
        lng = float(a.get("lng", hotel_lng))
        folium.Marker([lat, lng], popup=a.get("name", "景点"), icon=folium.Icon(color="blue")).add_to(m)

    # 3. 只画第一个餐厅
    if restaurants:
        r = restaurants[0]   # 只取 1 个
        lat = float(r.get("lat", hotel_lat))
        lng = float(r.get("lng", hotel_lng))
        folium.Marker([lat, lng], popup=r.get("name", "餐厅"), icon=folium.Icon(color="red")).add_to(m)

    # 4. 只画一条连线：酒店→景点→餐厅→回酒店（4 点 3 段）
    coords = [[hotel_lat, hotel_lng]]
    if attractions:
        coords.append([float(attractions[0].get("lat", hotel_lat)), float(attractions[0].get("lng", hotel_lng))])
    if restaurants:
        coords.append([float(restaurants[0].get("lat", hotel_lat)), float(restaurants[0].get("lng", hotel_lng))])
    coords.append([hotel_lat, hotel_lng])
    folium.PolyLine(coords, color="blue", weight=2.5, opacity=0.8).add_to(m)

    return m