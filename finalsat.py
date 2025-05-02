import streamlit as st
import requests
from skyfield.api import load, EarthSatellite
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

# Streamlit config
st.set_page_config(layout="wide")
st.title("🌍 Live Satellite Tracker")
st.markdown("Track the ISS, NOAA 15, TIANMU-1 14, METEOR satellites")
st.markdown("Design by Mr Zay Bhone Aung")

# Input location
col1, col2 = st.columns(2)
with col1:
    my_lat = st.number_input("Your Latitude", value=16.8409)
with col2:
    my_lon = st.number_input("Your Longitude", value=96.1735)

# Reusable function to get TLE for a named satellite
@st.cache_data(ttl=3600)
def get_tle(name, url):
    lines = requests.get(url).text.strip().split("\n")
    for i in range(0, len(lines), 3):
        if name in lines[i]:
            return lines[i], lines[i+1], lines[i+2]
    raise ValueError(f"{name} not found")

# List all satellite names in a given TLE file
def list_satellite_names(url):
    lines = requests.get(url).text.strip().split("\n")
    names = [lines[i] for i in range(0, len(lines), 3)]
    return names

# Satellite data extraction
def get_satellite_data(satellite, ts):
    time_now = ts.now()
    geocentric = satellite.at(time_now)
    subpoint = geocentric.subpoint()
    lat = subpoint.latitude.degrees
    lon = subpoint.longitude.degrees
    alt = subpoint.elevation.km
    velocity = geocentric.velocity.km_per_s
    speed = np.linalg.norm(velocity)

    times = ts.utc(time_now.utc_datetime().year,
                   time_now.utc_datetime().month,
                   time_now.utc_datetime().day,
                   np.linspace(0, 24, 100))
    positions = [satellite.at(t).subpoint() for t in times]
    lats = [pos.latitude.degrees for pos in positions]
    lons = [pos.longitude.degrees for pos in positions]

    return lat, lon, alt, speed, lats, lons

# Main app
def main():
    ts = load.timescale()

    name_iss, tle1_iss, tle2_iss = get_tle("ISS (ZARYA)", "https://celestrak.org/NORAD/elements/stations.txt")
    name_noaa, tle1_noaa, tle2_noaa = get_tle("NOAA 15", "https://celestrak.org/NORAD/elements/weather.txt")
    name_tianmu, tle1_tianmu, tle2_tianmu = get_tle("TIANMU-1 14", "https://celestrak.org/NORAD/elements/weather.txt")
    name_meteor, tle1_meteor, tle2_meteor = get_tle("METEOR", "https://celestrak.org/NORAD/elements/weather.txt")  # relaxed name

    sat_iss = EarthSatellite(tle1_iss, tle2_iss, name_iss, ts)
    sat_noaa = EarthSatellite(tle1_noaa, tle2_noaa, name_noaa, ts)
    sat_tianmu = EarthSatellite(tle1_tianmu, tle2_tianmu, name_tianmu, ts)
    sat_meteor = EarthSatellite(tle1_meteor, tle2_meteor, name_meteor, ts)

    satellites = [
        {"sat": sat_iss, "color": "yellow"},
        {"sat": sat_noaa, "color": "red"},
        {"sat": sat_tianmu, "color": "magenta"},
        {"sat": sat_meteor, "color": "lime"}
    ]

    fig, ax = plt.subplots(figsize=(12, 6))
    m = Basemap(projection='cyl', resolution='c')
    m.drawcoastlines()
    m.drawcountries()
    m.drawmapboundary(fill_color='midnightblue')
    m.fillcontinents(color='forestgreen', lake_color='darkgreen')
    m.drawparallels(np.arange(-90., 91., 30.))
    m.drawmeridians(np.arange(-180., 181., 60.))

    x_my, y_my = m(my_lon, my_lat)
    ax.scatter(x_my, y_my, color='white', marker='^', s=100, label="Your Location")

    # Plot satellite paths first
    for item in satellites:
        sat = item["sat"]
        color = item["color"]
        lat, lon, alt, speed, path_lats, path_lons = get_satellite_data(sat, ts)
        path_x, path_y = m(path_lons, path_lats)
        ax.plot(path_x, path_y, linestyle='--', color=color)

    # Now plot satellite positions on top of paths
    for item in satellites:
        sat = item["sat"]
        color = item["color"]
        lat, lon, alt, speed, _, _ = get_satellite_data(sat, ts)
        x, y = m(lon, lat)
        ax.scatter(x, y, color=color, edgecolor='black', s=100, zorder=5, label=sat.name)
        st.markdown(f"**{sat.name}** — Lat: `{lat:.2f}°`, Lon: `{lon:.2f}°`, Alt: `{alt:.1f} km`, Speed: `{speed:.2f} km/s`")


    ax.legend(loc='lower left', fontsize=9)
    st.pyplot(fig)

# Reload button
if st.button("🔁 Reload Satellite Data"):
    st.rerun()

# Run the main function
main()
