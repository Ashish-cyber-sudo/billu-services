from math import radians, sin, cos, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return round(R * c, 2) 
# def filter_services_by_distance(services, user_lat, user_lon, max_distance):
#     filtered_services = []
#     for service in services:
#         provider_profile = service.provider
#         distance = calculate_distance(user_lat, user_lon, provider_profile.latitude, provider_profile.longitude)
#         if distance is not None and distance <= max_distance:
#             filtered_services.append(service)
#     return filtered_services