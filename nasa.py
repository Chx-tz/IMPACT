import requests
import folium
from datetime import datetime, timedelta
import math

# NASA API endpoint (no key required for DEMO_KEY)
NASA_API_KEY = "DEMO_KEY"
NEO_URL = "https://api.nasa.gov/neo/rest/v1/feed"

def fetch_neo_data():
    """Fetch Near Earth Objects from NASA API"""
    today = datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    params = {
        "start_date": today,
        "end_date": end_date,
        "api_key": NASA_API_KEY
    }
    
    try:
        response = requests.get(NEO_URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def calculate_impact_effects(diameter_km, velocity_kmps):
    """Calculate crater size and shockwave radius based on asteroid properties"""
    # Simplified impact calculations
    # Crater diameter (in km) - simplified Collins et al. formula
    crater_diameter = diameter_km * 20 * (velocity_kmps / 17) ** 0.43
    
    # Energy in megatons TNT
    mass = (4/3) * math.pi * (diameter_km * 500) ** 3 * 2500  # assume density 2500 kg/m³
    energy_joules = 0.5 * mass * (velocity_kmps * 1000) ** 2
    energy_megatons = energy_joules / (4.184e15)
    
    # Shockwave radii (km)
    severe_damage = (energy_megatons ** 0.33) * 2.2  # severe structural damage
    moderate_damage = (energy_megatons ** 0.33) * 5.5  # moderate damage
    light_damage = (energy_megatons ** 0.33) * 15  # broken windows
    
    return {
        "crater_diameter": crater_diameter,
        "energy_megatons": energy_megatons,
        "severe_damage_radius": severe_damage,
        "moderate_damage_radius": moderate_damage,
        "light_damage_radius": light_damage
    }

def create_impact_map(neo_data):
    """Create interactive map with NEO impact visualizations"""
    # Center map on a default location (can be changed)
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=5)  # NYC default
    
    if not neo_data or "near_earth_objects" not in neo_data:
        print("No NEO data available")
        return m
    
    # Process NEO data
    all_neos = []
    for date, objects in neo_data["near_earth_objects"].items():
        all_neos.extend(objects)
    
    # Sort by size and take top 10
    all_neos.sort(key=lambda x: x["estimated_diameter"]["kilometers"]["estimated_diameter_max"], reverse=True)
    top_neos = all_neos[:10]
    
    print(f"\nFound {len(all_neos)} Near Earth Objects. Showing top 10 by size:\n")
    
    # Add impact zones for each NEO at different locations
    locations = [
        [40.7128, -74.0060],  # NYC
        [34.0522, -118.2437],  # LA
        [51.5074, -0.1278],  # London
        [35.6762, 139.6503],  # Tokyo
        [48.8566, 2.3522],  # Paris
        [-33.8688, 151.2093],  # Sydney
        [19.4326, -99.1332],  # Mexico City
        [55.7558, 37.6173],  # Moscow
        [28.6139, 77.2090],  # Delhi
        [39.9042, 116.4074]  # Beijing
    ]
    
    for idx, neo in enumerate(top_neos):
        name = neo["name"]
        diameter_km = neo["estimated_diameter"]["kilometers"]["estimated_diameter_max"]
        velocity_kmps = float(neo["close_approach_data"][0]["relative_velocity"]["kilometers_per_second"])
        miss_distance = float(neo["close_approach_data"][0]["miss_distance"]["kilometers"])
        hazardous = neo["is_potentially_hazardous_asteroid"]
        
        # Calculate impact effects
        effects = calculate_impact_effects(diameter_km, velocity_kmps)
        
        # Get location for this NEO
        lat, lon = locations[idx % len(locations)]
        
        # Create popup info
        popup_html = f"""
        <div style="width: 300px;">
            <h4>{name}</h4>
            <b>Diameter:</b> {diameter_km:.3f} km<br>
            <b>Velocity:</b> {velocity_kmps:.2f} km/s<br>
            <b>Miss Distance:</b> {miss_distance:,.0f} km<br>
            <b>Hazardous:</b> {'Yes' if hazardous else 'No'}<br>
            <hr>
            <h5>Hypothetical Impact Effects:</h5>
            <b>Impact Energy:</b> {effects['energy_megatons']:.1f} megatons TNT<br>
            <b>Crater Diameter:</b> {effects['crater_diameter']:.2f} km<br>
            <b>Severe Damage:</b> {effects['severe_damage_radius']:.1f} km radius<br>
            <b>Moderate Damage:</b> {effects['moderate_damage_radius']:.1f} km radius<br>
            <b>Light Damage:</b> {effects['light_damage_radius']:.1f} km radius
        </div>
        """
        
        # Add crater circle (red)
        folium.Circle(
            location=[lat, lon],
            radius=effects['crater_diameter'] * 500,  # convert to meters
            color='darkred',
            fill=True,
            fillColor='red',
            fillOpacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{name} - Crater"
        ).add_to(m)
        
        # Add severe damage zone (orange)
        folium.Circle(
            location=[lat, lon],
            radius=effects['severe_damage_radius'] * 1000,
            color='orangered',
            fill=True,
            fillColor='orange',
            fillOpacity=0.4,
            tooltip="Severe Damage Zone"
        ).add_to(m)
        
        # Add moderate damage zone (yellow)
        folium.Circle(
            location=[lat, lon],
            radius=effects['moderate_damage_radius'] * 1000,
            color='yellow',
            fill=True,
            fillColor='yellow',
            fillOpacity=0.2,
            tooltip="Moderate Damage Zone"
        ).add_to(m)
        
        # Add light damage zone (light blue)
        folium.Circle(
            location=[lat, lon],
            radius=effects['light_damage_radius'] * 1000,
            color='lightblue',
            fill=True,
            fillColor='lightblue',
            fillOpacity=0.1,
            tooltip="Light Damage Zone"
        ).add_to(m)
        
        # Add marker at center
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color='red' if hazardous else 'blue', icon='meteor', prefix='fa'),
            tooltip=f"{name}"
        ).add_to(m)
        
        # Print info
        print(f"{idx+1}. {name}")
        print(f"   Diameter: {diameter_km:.3f} km")
        print(f"   Velocity: {velocity_kmps:.2f} km/s")
        print(f"   Impact Energy: {effects['energy_megatons']:.1f} megatons")
        print(f"   Crater: {effects['crater_diameter']:.2f} km diameter")
        print(f"   Severe damage: {effects['severe_damage_radius']:.1f} km radius")
        print(f"   Hazardous: {'Yes' if hazardous else 'No'}\n")
    
    return m

def main():
    print("Fetching Near Earth Objects from NASA...")
    neo_data = fetch_neo_data()
    
    if neo_data:
        print(f"Total NEO count: {neo_data['element_count']}")
        impact_map = create_impact_map(neo_data)
        
        # Save map
        output_file = "neo_impact_map.html"
        impact_map.save(output_file)
        print(f"\nMap saved as '{output_file}'")
        print("Open this file in a web browser to view the interactive map!")
    else:
        print("Failed to fetch NEO data")

if __name__ == "__main__":
    main()