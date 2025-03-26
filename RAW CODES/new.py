import googlemaps
from datetime import datetime
import folium
from googlemaps.convert import decode_polyline  # ✅ Correct import

# Initialize Google Maps client with your API key
gmaps = googlemaps.Client(key='AIzaSyBRBeH0AcfEEg-hzaaORkDAcuaFfObTzMA')  # Replace with your actual API key

# Get user input for source and destination
source = input("Enter the source address: ")
destination = input("Enter the destination address: ")

# Geocode the source and destination addresses to get their coordinates
source_result = gmaps.geocode(source)
if not source_result:
    print(f"Error: Could not find location for '{source}'. Try a more specific address.")
    exit()
source_location = source_result[0]['geometry']['location']

destination_result = gmaps.geocode(destination)
if not destination_result:
    print(f"Error: Could not find location for '{destination}'. Try a more specific address.")
    exit()
destination_location = destination_result[0]['geometry']['location']

# Get real-time traffic-based directions
directions_result = gmaps.directions(
    origin=source,
    destination=destination,
    mode="driving",
    departure_time=datetime.now(),  # Real-time traffic data
    traffic_model='best_guess',
    alternatives=True  # Get multiple route options
)

# Initialize map at source location
m = folium.Map(location=[source_location['lat'], source_location['lng']], zoom_start=12)

# Define traffic-based colors
def get_traffic_color(traffic_value):
    if traffic_value < 10:
        return "green"  # Free traffic
    elif traffic_value < 20:
        return "yellow"  # Moderate traffic
    else:
        return "red"  # Heavy traffic

best_route_index = 0
min_duration = float('inf')

# Iterate through all route options
for i, route in enumerate(directions_result):
    leg = route['legs'][0]
    duration = leg['duration_in_traffic']['value']  
    route_color = get_traffic_color(duration // 60)  

    if duration < min_duration:
        min_duration = duration
        best_route_index = i

    # Extract polyline points for route
    polyline = route['overview_polyline']['points']
    decoded_points = decode_polyline(polyline)  
    coordinates = [(point['lat'], point['lng']) for point in decoded_points]  
    
    # Add route to map with travel time label
    folium.PolyLine(coordinates, color=route_color, weight=5, opacity=0.7).add_to(m)
    midpoint = coordinates[len(coordinates) // 2]  # Get midpoint for label
    folium.Marker(midpoint, icon=folium.DivIcon(html=f'<div style="font-size: 12px; color: black; background: white; padding: 3px;">{leg["duration_in_traffic"]["text"]}</div>')).add_to(m)

# Highlight best route in violet
best_route = directions_result[best_route_index]
best_polyline = best_route['overview_polyline']['points']
decoded_best_points = decode_polyline(best_polyline)  # ✅ Correct method
best_coordinates = [(point['lat'], point['lng']) for point in decoded_best_points]  # ✅ Correct format
folium.PolyLine(best_coordinates, color='purple', weight=6, opacity=1, dash_array='5, 5').add_to(m)

# Add markers for source and destination
folium.Marker([source_location['lat'], source_location['lng']], tooltip='Source', icon=folium.Icon(color='blue')).add_to(m)
folium.Marker([destination_location['lat'], destination_location['lng']], tooltip='Destination', icon=folium.Icon(color='red')).add_to(m)

# Save map to file and open it
map_filename = "traffic_map.html"
m.save(map_filename)
print(f"Map saved as {map_filename}. Open this file in a browser to view the routes.")
