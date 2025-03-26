import googlemaps
from datetime import datetime
import folium
import pandas as pd
from googlemaps.convert import decode_polyline

# Initialize Google Maps client
API_KEY = 'AIzaSyBRBeH0AcfEEg-hzaaORkDAcuaFfObTzMA'  # Replace with actual API key
gmaps = googlemaps.Client(key=API_KEY)

# User input for location details
country = input("Enter your current country: ")
state = input("Enter your current state: ")
city = input("Enter your current city: ")
source = input("Enter the source address: ")
destination = input("Enter the destination address: ")

# Append city, state, and country to make addresses more specific
source_full = f"{source}, {city}, {state}, {country}"
destination_full = f"{destination}, {city}, {state}, {country}"

# Geocode source and destination
source_result = gmaps.geocode(source_full)
destination_result = gmaps.geocode(destination_full)
if not source_result or not destination_result:
    print("Error: Could not geocode one of the locations.")
    exit()
source_location = source_result[0]['geometry']['location']
destination_location = destination_result[0]['geometry']['location']

# Get real-time traffic-based directions
directions_result = gmaps.directions(
    origin=source_full,
    destination=destination_full,
    mode="driving",
    departure_time=datetime.now(),
    traffic_model='best_guess',
    alternatives=True
)

# Initialize map
m = folium.Map(location=[source_location['lat'], source_location['lng']], zoom_start=12)

# Find best route (shortest duration in traffic)
best_route_index = 0
min_duration = float('inf')
for i, route in enumerate(directions_result):
    duration = route['legs'][0]['duration_in_traffic']['value']
    if duration < min_duration:
        min_duration = duration
        best_route_index = i

best_route = directions_result[best_route_index]
best_polyline = best_route['overview_polyline']['points']
decoded_best_points = decode_polyline(best_polyline)
all_coordinates = [(point['lat'], point['lng']) for point in decoded_best_points]

# Identify turning points
def detect_turning_points(coords, angle_threshold=30):
    turning_points = [coords[0]]  # First point is always a turning point
    for i in range(1, len(coords) - 1):
        prev_lat, prev_lng = coords[i - 1]
        curr_lat, curr_lng = coords[i]
        next_lat, next_lng = coords[i + 1]
        
        # Compute direction vectors
        v1 = (curr_lat - prev_lat, curr_lng - prev_lng)
        v2 = (next_lat - curr_lat, next_lng - curr_lng)
        
        # Compute angle change
        angle_change = abs((v1[0] * v2[0] + v1[1] * v2[1]) / (((v1[0]**2 + v1[1]**2)**0.5) * ((v2[0]**2 + v2[1]**2)**0.5)))
        
        if angle_change < 0.85:  # Roughly corresponds to a 30-degree turn
            turning_points.append((curr_lat, curr_lng))
    turning_points.append(coords[-1])  # Last point is always a turning point
    return turning_points

turning_points = detect_turning_points(all_coordinates)

# Add route and turning points to map
folium.PolyLine(all_coordinates, color='blue', weight=5, opacity=0.7).add_to(m)
for coord in all_coordinates:
    folium.CircleMarker(coord, radius=3, color='blue', fill=True, fill_color='blue').add_to(m)
for tp in turning_points:
    folium.Marker(tp, icon=folium.Icon(color='red')).add_to(m)

# Add markers for source and destination
folium.Marker([source_location['lat'], source_location['lng']], tooltip='Source', icon=folium.Icon(color='green')).add_to(m)
folium.Marker([destination_location['lat'], destination_location['lng']], tooltip='Destination', icon=folium.Icon(color='orange')).add_to(m)

# Save map to file
map_filename = "traffic_map.html"
m.save(map_filename)
print(f"Map saved as {map_filename}. Open this file in a browser to view the route.")

# Save to Excel
route_data = pd.DataFrame(all_coordinates, columns=["Latitude", "Longitude"])
turning_data = pd.DataFrame(turning_points, columns=["Latitude", "Longitude"])

with pd.ExcelWriter("route_coordinates.xlsx") as writer:
    route_data.to_excel(writer, sheet_name="All Coordinates", index=False)
    turning_data.to_excel(writer, sheet_name="Turning Points", index=False)

print("Route coordinates and turning points saved in 'route_coordinates.xlsx'")