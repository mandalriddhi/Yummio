import googlemaps
from datetime import datetime
import folium
from googlemaps.convert import decode_polyline
import time
import re
import pandas as pd
from math import radians, sin, cos, sqrt, atan2

# Initialize Google Maps client with your API key
gmaps = googlemaps.Client(key='AIzaSyBRBeH0AcfEEg-hzaaORkDAcuaFfObTzMA')  # Replace with your actual API key

# Get user input for source and destination
source = input("Enter the source address: ")
destination = input("Enter the destination address: ")

# Geocode the source and destination addresses
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
    departure_time=datetime.now(),
    traffic_model='best_guess',
    alternatives=True
)

# Initialize map at source location
m = folium.Map(location=[source_location['lat'], source_location['lng']], zoom_start=12)

# Define traffic-based colors
def get_traffic_color(traffic_value):
    if traffic_value < 10:
        return "green"
    elif traffic_value < 20:
        return "yellow"
    return "red"

best_route_index = 0
min_duration = float('inf')

# Iterate through route options
for i, route in enumerate(directions_result):
    leg = route['legs'][0]
    duration = leg['duration_in_traffic']['value']
    route_color = get_traffic_color(duration // 60)
    
    if duration < min_duration:
        min_duration = duration
        best_route_index = i
    
    polyline = route['overview_polyline']['points']
    decoded_points = decode_polyline(polyline)
    coordinates = [(point['lat'], point['lng']) for point in decoded_points]
    
    folium.PolyLine(coordinates, color=route_color, weight=5, opacity=0.7).add_to(m)
    midpoint = coordinates[len(coordinates) // 2]
    folium.Marker(midpoint, icon=folium.DivIcon(html=f'<div style="font-size: 12px; color: black; background: white; padding: 3px;">{leg["duration_in_traffic"]["text"]}</div>')).add_to(m)

# Highlight best route
best_route = directions_result[best_route_index]
best_polyline = best_route['overview_polyline']['points']
decoded_best_points = decode_polyline(best_polyline)
best_coordinates = [(point['lat'], point['lng']) for point in decoded_best_points]
folium.PolyLine(best_coordinates, color='purple', weight=6, opacity=1, dash_array='5, 5').add_to(m)

# Add markers for source and destination
folium.Marker([source_location['lat'], source_location['lng']], tooltip='Source', icon=folium.Icon(color='blue')).add_to(m)
folium.Marker([destination_location['lat'], destination_location['lng']], tooltip='Destination', icon=folium.Icon(color='red')).add_to(m)

# --------- IMPROVED RESTAURANT SEARCH FUNCTIONALITY -----------

# Extract detailed steps from the best route
best_route_steps = best_route['legs'][0]['steps']
restaurant_list = []
seen_place_ids = set()  # To avoid duplicates using place_id

# Function to extract road names from HTML instructions
def extract_road_names(instruction):
    clean_text = re.sub('<[^<]+?>', ' ', instruction).strip()
    patterns = [
        r"onto ([^<]+?)(?: toward| for| \.)",
        r"on ([^<]+?)(?: toward| for| \.)",
        r"Continue on ([^<]+?)(?: toward| for| \.)",
        r"Take ([^<]+?)(?: toward| for| \.)"
    ]
    for pattern in patterns:
        match = re.search(pattern, clean_text)
        if match:
            return match.group(1).strip()
    words = clean_text.split()
    for i in range(len(words)-1):
        if words[i].lower() in ['on', 'onto'] and i+1 < len(words):
            potential_road = words[i+1]
            if len(potential_road) > 2 and potential_road[0].isupper():
                return potential_road
    return None

# Function to calculate distance between two points using Haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in meters
    R = 6371000  
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance  # Distance in meters

# Function to find minimum distance from a point to a polyline
def distance_to_route(point, route_coordinates):
    min_distance = float('inf')
    closest_point = None
    closest_segment_index = 0
    
    # Check distance to each segment of the route
    for i in range(len(route_coordinates) - 1):
        segment_start = route_coordinates[i]
        segment_end = route_coordinates[i + 1]
        
        # Calculate distance to this segment
        distance = calculate_distance(point[0], point[1], segment_start[0], segment_start[1])
        
        if distance < min_distance:
            min_distance = distance
            closest_point = segment_start
            closest_segment_index = i
    
    return min_distance, closest_point, closest_segment_index

# Process each step to extract coordinates
road_segments = []
for step in best_route_steps:
    road_name = extract_road_names(step['html_instructions']) if 'html_instructions' in step else None
    points = decode_polyline(step['polyline']['points'])
    coords = [(point['lat'], point['lng']) for point in points]
    
    distance = step.get('distance', {}).get('value', 0)  # in meters
    num_points = max(1, int(distance / 200))  # Search every 200 meters
    step_size = max(1, len(coords) // num_points)
    
    for i in range(0, len(coords), step_size):
        road_segments.append({
            'coords': coords[i],
            'road_name': road_name
        })

print(f"Identified {len(road_segments)} search points along the route.")

# Function to fetch all pages of results for a given location
def fetch_all_nearby_restaurants(location, radius=250):
    restaurants = []
    next_token = None
    
    while True:
        try:
            results = gmaps.places_nearby(
                location=location,
                radius=radius,
                type='restaurant',
                page_token=next_token if next_token else None
            )
            
            for place in results.get('results', []):
                if place.get('place_id') not in seen_place_ids:
                    seen_place_ids.add(place['place_id'])
                    restaurants.append(place)
            
            next_token = results.get('next_page_token')
            if not next_token:
                break  # No more pages
            
            time.sleep(2)  # Wait for next_page_token to become valid (Google API requirement)
            
        except Exception as e:
            print(f"Error fetching nearby restaurants: {str(e)}")
            break
    
    return restaurants

# Search for restaurants at each segment point
for i, segment in enumerate(road_segments):
    print(f"Searching location {i+1}/{len(road_segments)}...")
    
    nearby_restaurants = fetch_all_nearby_restaurants(segment['coords'], radius=250)
    
    for place in nearby_restaurants:
        road_name = segment['road_name'] if segment['road_name'] else "Unnamed Road"
        
        # Calculate distance from restaurant to the route
        restaurant_coords = (place['geometry']['location']['lat'], place['geometry']['location']['lng'])
        distance_to_main_road, closest_point, _ = distance_to_route(restaurant_coords, best_coordinates)
        
        restaurant_list.append({
            'name': place['name'],
            'address': place.get('vicinity', 'Address not available'),
            'rating': place.get('rating', 'Not rated'),
            'road': road_name,
            'location': place['geometry']['location'],
            'place_id': place['place_id'],
            'distance_to_road': distance_to_main_road  # Add distance to main road
        })
        
        # Format distance for display
        distance_text = f"{int(distance_to_main_road)} meters from road"
        
        folium.Marker(
            location=[place['geometry']['location']['lat'], place['geometry']['location']['lng']],
            popup=f"""<b>{place['name']}</b><br>
                   Rating: {place.get('rating', 'Not rated')}<br>
                   Road: {road_name}<br>
                   Distance: {distance_text}<br>
                   {place.get('vicinity', 'Address not available')}""",
            tooltip=place['name'],
            icon=folium.Icon(color='darkpurple', icon='cutlery', prefix='fa')
        ).add_to(m)
    
    time.sleep(0.2)  # Short pause between segment searches

# Additional text-based search for named roads
road_names = set(segment['road_name'] for segment in road_segments if segment['road_name'])
print(f"Searching for additional restaurants on {len(road_names)} named roads...")

for road_name in road_names:
    try:
        # Fetch all pages for text-based search
        next_token = None
        while True:
            results = gmaps.places(
                query=f"restaurants on {road_name} between {source} and {destination}",
                location=source_location,
                radius=5000,
                page_token=next_token if next_token else None
            )
            
            for place in results.get('results', []):
                if place.get('place_id') not in seen_place_ids:
                    seen_place_ids.add(place['place_id'])
                    
                    # Calculate distance from restaurant to the route
                    restaurant_coords = (place['geometry']['location']['lat'], place['geometry']['location']['lng'])
                    distance_to_main_road, closest_point, _ = distance_to_route(restaurant_coords, best_coordinates)
                    
                    # Format distance for display
                    distance_text = f"{int(distance_to_main_road)} meters from road"
                    
                    restaurant_list.append({
                        'name': place['name'],
                        'address': place.get('vicinity', place.get('formatted_address', 'Address not available')),
                        'rating': place.get('rating', 'Not rated'),
                        'road': road_name,
                        'location': place['geometry']['location'],
                        'place_id': place['place_id'],
                        'distance_to_road': distance_to_main_road  # Add distance to main road
                    })
                    
                    folium.Marker(
                        location=[place['geometry']['location']['lat'], place['geometry']['location']['lng']],
                        popup=f"""<b>{place['name']}</b><br>
                               Rating: {place.get('rating', 'Not rated')}<br>
                               Road: {road_name}<br>
                               Distance: {distance_text}<br>
                               {place.get('vicinity', place.get('formatted_address', 'Address not available'))}""",
                        tooltip=place['name'],
                        icon=folium.Icon(color='darkpurple', icon='cutlery', prefix='fa')
                    ).add_to(m)
            
            next_token = results.get('next_page_token')
            if not next_token:
                break
            
            time.sleep(2)  # Wait for next_page_token
            
    except Exception as e:
        print(f"Error searching for restaurants on {road_name}: {str(e)}")
        continue

# Save map to file
map_filename = "traffic_map.html"
m.save(map_filename)

# Create DataFrame for Excel export
excel_data = []
for restaurant in restaurant_list:
    excel_data.append({
        'Name': restaurant['name'],
        'Rating': restaurant['rating'],
        'Road': restaurant['road'],
        'Address': restaurant['address'],
        'Distance_to_Road_meters': restaurant['distance_to_road'],
        'Latitude': restaurant['location']['lat'],
        'Longitude': restaurant['location']['lng'],
        'Place_ID': restaurant['place_id']
    })

# Create DataFrame and export to Excel
if excel_data:
    df = pd.DataFrame(excel_data)
    excel_file = "restaurants_along_route.xlsx"
    df.to_excel(excel_file, index=False)
    print(f"\nExported all restaurant data to {excel_file}")
else:
    print("\nNo restaurants found to export.")

# Print grouped restaurant list
print("\nRestaurants along the preferred route (grouped by road):")
print("=======================================================")

restaurants_by_road = {}
for restaurant in restaurant_list:
    road = restaurant['road']
    if road not in restaurants_by_road:
        restaurants_by_road[road] = []
    restaurants_by_road[road].append(restaurant)

for road, restaurants in restaurants_by_road.items():
    print(f"\n{road}:")
    print("-" * len(road) + "--")
    for i, restaurant in enumerate(restaurants, 1):
        print(f"  {i}. {restaurant['name']}")
        print(f"     Rating: {restaurant['rating']}")
        print(f"     Distance from road: {int(restaurant['distance_to_road'])} meters")
        print(f"     Address: {restaurant['address']}")

print(f"\nTotal restaurants found: {len(restaurant_list)}")
print(f"Map saved as {map_filename}. Open this file in a browser to view the routes and restaurants.")
print(f"Restaurant data exported to {excel_file}")