import googlemaps
from datetime import datetime
import folium
import pandas as pd
from googlemaps.convert import decode_polyline
from geopy.distance import geodesic

# Initialize Google Maps client
API_KEY = 'AIzaSyBRBeH0AcfEEg-hzaaORkDAcuaFfObTzMA'  # Replace with actual API key
gmaps = googlemaps.Client(key=API_KEY)

# User input for location details
country = input("Enter your current country: ")
state = input("Enter your current state: ")
city = input("Enter your current city: ")
source = input("Enter the source address: ")
destination = input("Enter the destination address: ")

# Get restaurant information using coordinates only
restaurant_lat = float(input("Enter the restaurant latitude: "))
restaurant_lng = float(input("Enter the restaurant longitude: "))

# Use reverse geocoding to get restaurant details based on coordinates
restaurant_location = {'lat': restaurant_lat, 'lng': restaurant_lng}
restaurant_result = gmaps.reverse_geocode((restaurant_lat, restaurant_lng))

# Extract restaurant name from place result
# Try to extract the most relevant name from the results
restaurant_name = "Unknown Restaurant"  # Default name
if restaurant_result:
    # First try to get place name from address components
    for component in restaurant_result[0].get('address_components', []):
        if 'point_of_interest' in component.get('types', []) or 'establishment' in component.get('types', []):
            restaurant_name = component.get('long_name', "Unknown Restaurant")
            break
    
    # If no name found in address components, use formatted address
    if restaurant_name == "Unknown Restaurant":
        # Try to extract business name from the formatted address
        formatted_address = restaurant_result[0].get('formatted_address', '')
        # Often the business name is the first part before the comma in formatted address
        if ',' in formatted_address:
            restaurant_name = formatted_address.split(',')[0].strip()

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

# Get real-time traffic-based directions with alternatives
directions_result = gmaps.directions(
    origin=source_full,
    destination=destination_full,
    mode="driving",
    departure_time=datetime.now(),
    traffic_model='best_guess',
    alternatives=True,  # Request alternative routes
)

print(f"Found {len(directions_result)} possible routes from source to destination.")

# Initialize map
m = folium.Map(location=[source_location['lat'], source_location['lng']], zoom_start=12)

# Find best route (shortest duration in traffic)
best_route_index = 0
min_duration = float('inf')
all_routes_coordinates = []

for i, route in enumerate(directions_result):
    duration = route['legs'][0]['duration_in_traffic']['value']
    if duration < min_duration:
        min_duration = duration
        best_route_index = i
    
    # Store all routes for later use
    route_polyline = route['overview_polyline']['points']
    decoded_route_points = decode_polyline(route_polyline)
    route_coordinates = [(point['lat'], point['lng']) for point in decoded_route_points]
    all_routes_coordinates.append(route_coordinates)

# Display all possible routes in sky blue first (so they appear below the main route)
for i, route_coords in enumerate(all_routes_coordinates):
    if i != best_route_index:  # Skip the best route for now, will add it with different color
        # Add route line in sky blue
        folium.PolyLine(
            route_coords, 
            color='skyblue',  # Sky blue for alternative routes
            weight=3,
            opacity=0.6,
            tooltip=f'Alternative Route {i+1}'
        ).add_to(m)
        print(f"Alternative route {i+1} distance: {directions_result[i]['legs'][0]['distance']['text']}, " 
              f"duration: {directions_result[i]['legs'][0]['duration_in_traffic']['text']}")

# Now work with the best route
best_route_coords = all_routes_coordinates[best_route_index]
print(f"Preferred route distance: {directions_result[best_route_index]['legs'][0]['distance']['text']}, "
      f"duration: {directions_result[best_route_index]['legs'][0]['duration_in_traffic']['text']}")

# Identify turning points for the best route
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

turning_points = detect_turning_points(best_route_coords)

# Check if restaurant is on the preferred route
def is_restaurant_on_route(restaurant_coords, route_coords, threshold=500):
    """
    Check if a restaurant is reasonably close to the route.
    
    Args:
        restaurant_coords: (lat, lng) of the restaurant
        route_coords: List of (lat, lng) coordinates of the route
        threshold: Maximum distance in meters to consider "on the route"
    
    Returns:
        tuple: (is_on_route, min_distance, closest_point)
    """
    min_distance = float('inf')
    closest_point = None
    
    # Check the direct distance to each point on the route
    for point in route_coords:
        distance = geodesic(restaurant_coords, point).meters
        if distance < min_distance:
            min_distance = distance
            closest_point = point
    
    # Check if the minimum distance is below threshold
    is_on_route = min_distance < threshold
    
    return is_on_route, min_distance, closest_point

restaurant_coords = (restaurant_location['lat'], restaurant_location['lng'])
on_route, distance, closest_point = is_restaurant_on_route(restaurant_coords, best_route_coords)

# Add the preferred route in dark blue - add this AFTER the alternative routes but BEFORE the markers
folium.PolyLine(
    best_route_coords, 
    color='darkblue',  # Dark blue for preferred route
    weight=5,
    opacity=0.8,
    tooltip='Preferred Route (Fastest)'
).add_to(m)

# Create a legend for the map
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; right: 50px; width: 200px; height: 180px; 
            border:2px solid grey; z-index:9999; font-size:14px;
            background-color:white; padding: 10px;
            border-radius: 5px;">
    <p style="margin-top: 0;"><b>Legend</b></p>
    <p style="margin-bottom: 5px;">
        <i class="fa fa-square" style="color:darkblue;"></i> Preferred Route
    </p>
    <p style="margin-bottom: 5px;">
        <i class="fa fa-square" style="color:skyblue;"></i> Alternative Routes
    </p>
    <p style="margin-bottom: 5px;">
        <i class="fa fa-circle" style="color:#5D4037;"></i> Restaurant
    </p>
    <p style="margin-bottom: 5px;">
        <i class="fa fa-circle" style="color:red;"></i> Turning Points
    </p>
    <p style="margin-bottom: 5px;">
        <i class="fa fa-map-marker" style="color:green;"></i> Start
    </p>
    <p style="margin-bottom: 5px;">
        <i class="fa fa-map-marker" style="color:orange;"></i> Destination
    </p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Add restaurant marker with dark brown styling
folium.CircleMarker(
    restaurant_coords,
    radius=8,
    color='#5D4037',  # Dark brown outline
    fill=True,
    fill_color='#5D4037',  # Dark brown fill
    fill_opacity=0.9,
    tooltip='Restaurant'
).add_to(m)

# Get restaurant address for additional display info
restaurant_address = restaurant_result[0].get('formatted_address', 'Address unavailable') if restaurant_result else 'Address unavailable'

# Add restaurant marker with icon and including restaurant name in the popup
folium.Marker(
    restaurant_coords,
    popup=folium.Popup(f"<b>{restaurant_name}</b><br>{restaurant_address}<br>Distance from route: {distance:.2f}m", max_width=300),
    tooltip=restaurant_name,
    icon=folium.Icon(color='darkpurple', icon='cutlery', prefix='fa')
).add_to(m)

# Add connection line from restaurant to closest point on route
if on_route:
    print(f"Restaurant '{restaurant_name}' is on the way. It is approximately {distance:.2f} meters from the preferred route.")
    
    # Draw a line from the closest route to the restaurant
    folium.PolyLine([closest_point, restaurant_coords], color='#5D4037', weight=4, 
                    opacity=0.7, dash_array='10').add_to(m)
else:
    print(f"Restaurant '{restaurant_name}' is not on the preferred route. It is {distance:.2f} meters away from the nearest point.")
    
    # Still draw the connection
    folium.PolyLine([closest_point, restaurant_coords], color='#5D4037', weight=3, 
                    opacity=0.5, dash_array='5').add_to(m)

# Add markers for turning points on the best route
for tp in turning_points:
    folium.CircleMarker(tp, radius=4, color='red', fill=True, fill_color='red', tooltip='Turning Point').add_to(m)

# Add markers for source and destination
folium.Marker([source_location['lat'], source_location['lng']], 
              popup='Starting Point',
              tooltip='Source', 
              icon=folium.Icon(color='green')).add_to(m)

folium.Marker([destination_location['lat'], destination_location['lng']], 
              popup='End Point',
              tooltip='Destination', 
              icon=folium.Icon(color='orange')).add_to(m)

# Add closest point to the map
folium.CircleMarker(closest_point, radius=5, color='yellow', fill=True, 
                    fill_color='yellow', tooltip='Closest point on route to restaurant').add_to(m)

# Save map to file
map_filename = "traffic_map.html"
m.save(map_filename)
print(f"Map saved as {map_filename}. Open this file in a browser to view the routes.")

# Save to Excel
route_data = pd.DataFrame(best_route_coords, columns=["Latitude", "Longitude"])
turning_data = pd.DataFrame(turning_points, columns=["Latitude", "Longitude"])

# Get additional restaurant details for Excel
restaurant_type = ""
for place_result in restaurant_result:
    if 'types' in place_result:
        types = place_result.get('types', [])
        # Filter out generic types
        relevant_types = [t for t in types if t not in ['point_of_interest', 'establishment']]
        if relevant_types:
            restaurant_type = ', '.join(relevant_types).replace('_', ' ')
            break

# Add restaurant analysis to Excel including restaurant name and additional details
restaurant_analysis = pd.DataFrame({
    "Restaurant Name": [restaurant_name],
    "Restaurant Address": [restaurant_address],
    "Restaurant Type": [restaurant_type],
    "Restaurant Latitude": [restaurant_coords[0]],
    "Restaurant Longitude": [restaurant_coords[1]],
    "Closest Point Latitude": [closest_point[0]],
    "Closest Point Longitude": [closest_point[1]],
    "Distance (meters)": [distance],
    "Is On Preferred Route": [on_route]
})

# Extract route statistics for comparison
route_stats = []
for i, route in enumerate(directions_result):
    route_stats.append({
        "Route Type": "Preferred Route" if i == best_route_index else f"Alternative Route {i+1}",
        "Distance": route['legs'][0]['distance']['text'],
        "Duration": route['legs'][0]['duration_in_traffic']['text'],
        "Duration (seconds)": route['legs'][0]['duration_in_traffic']['value']
    })
stats_df = pd.DataFrame(route_stats)

with pd.ExcelWriter("route_analysis.xlsx") as writer:
    route_data.to_excel(writer, sheet_name="Preferred Route Coordinates", index=False)
    turning_data.to_excel(writer, sheet_name="Turning Points", index=False)
    restaurant_analysis.to_excel(writer, sheet_name="Restaurant Analysis", index=False)
    stats_df.to_excel(writer, sheet_name="Route Comparison", index=False)

print("Route analysis saved in 'route_analysis.xlsx'")