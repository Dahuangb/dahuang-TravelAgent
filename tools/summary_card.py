def calc_total_distance(attractions, restaurants, hotel_lat, hotel_lng):
    """轻量级：只算酒店↔景点↔餐厅↔酒店 大段距离"""
    from math import radians, cos, sin, sqrt, atan2

    def dist_m(lat1, lng1, lat2, lng2):
        R = 6371000
        φ1, φ2 = radians(lat1), radians(lat2)
        Δφ = radians(lat2 - lat1)
        Δλ = radians(lng2 - lng1)
        a = sin(Δφ/2)**2 + cos(φ1)*cos(φ2)*sin(Δλ/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    coords = [[hotel_lat, hotel_lng]]
    if attractions:
        coords.append([float(attractions[0].get("lat", hotel_lat)), float(attractions[0].get("lng", hotel_lng))])
    if restaurants:
        coords.append([float(restaurants[0].get("lat", hotel_lat)), float(restaurants[0].get("lng", hotel_lng))])
    coords.append([hotel_lat, hotel_lng])

    total_m = 0
    for i in range(len(coords) - 1):
        total_m += dist_m(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
    return round(total_m / 1000, 2)      # km