import googlemaps
import polyline
import pandas as pd
from datetime import datetime

# Initialize Google Maps client with your API key
gmaps = googlemaps.Client(key='AIzaSyBRBeH0AcfEEg-hzaaORkDAcuaFfObTzMA')

# Get user input for country, city, and source/destination
country = input("Enter your current country: ")
city = input("Enter your current city: ")
source = input(f"Enter the source address in {city}, {country}: ")
destination = input(f"Enter the destination address in {city}, {country}: ")

# Geocode the source and destination addresses to get their coordinates
source_location = gmaps.geocode(source)[0]['geometry']['location']
destination_location = gmaps.geocode(destination)[0]['geometry']['location']

# Get real-time traffic-based directions
directions_result = gmaps.directions(
    origin=source,
    destination=destination,
    mode="driving",
    departure_time=datetime.now(),  # Real-time traffic data
    traffic_model='best_guess'
)

# Extract and display the best route based on traffic
if directions_result:
    best_route = directions_result[0]
    leg = best_route['legs'][0]
    print(f"\nShortest path based on current traffic:\n")
    print(f"From: {leg['start_address']}")
    print(f"To: {leg['end_address']}")
    print(f"Estimated duration (with traffic): {leg['duration_in_traffic']['text']}")
    print(f"Distance: {leg['distance']['text']}\n")

    # Print step-by-step directions
    print("Directions:")
    for step in leg['steps']:
        instruction = step['html_instructions']
        # Remove HTML tags for clean output
        clean_instruction = ''.join(c for c in instruction if c.isalnum() or c.isspace())
        print(f"- {clean_instruction} ({step['distance']['text']})")
    
    # Extract and store all coordinates along the route
    all_coordinates = []
    turning_points = []
    print("\nMain Coordinates (Turning Points) along the route:")
    print("Latitude\tLongitude")
    
    for step in leg['steps']:
        decoded_points = polyline.decode(step['polyline']['points'])
        all_coordinates.extend(decoded_points)
        
        # Store turning points (start of each step)
        if decoded_points:
            turning_points.append(decoded_points[0])
    
    # Print only turning points in terminal
    for lat, lng in turning_points:
        print(f"{float(lat):.6f}\t{float(lng):.6f}")
    
    # Save all coordinates to an Excel file
    df = pd.DataFrame(all_coordinates, columns=['Latitude', 'Longitude'])
    df.to_excel("route_coordinates.xlsx", index=False)
    print("\nAll route coordinates saved to route_coordinates.xlsx")
else:
    print("No route found. Please check your addresses and try again.")