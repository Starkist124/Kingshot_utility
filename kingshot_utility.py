import streamlit as st
import requests
from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# --- 1. SECURITY GATEKEEPER ---
st.set_page_config(page_title="KingShot War Room", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🛡️ KingShot War Room Login")
    pwd = st.text_input("Enter Alliance Password:", type="password")
    if st.button("Login"):
        if pwd == st.secrets["passwords"]["alliance_pass"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password. Access denied.")
    st.stop() # Stops the rest of the app from loading!

# --- GLOBAL VARIABLES ---
TYPE_STYLES = {
    "Custom Marker": "📍", "Player": "🧍", "Rally Point": "🚩",
    "Castle": "👑", "Fortress": "🏯", "Sanctuary": "🏛️",
    "Builder's Guild": "🔨", "Armory": "🪖", "Scholar's Tower": "📜",
    "Arsenal": "💣", "Forager Grove": "🍄", "Harvest Alter": "🌿",
    "Drill Camp": "🏕️", "Frontier Lodge": "🛖"
}

AFFILIATION_COLORS = {
    "Ally": "blue", "Enemy": "red", "Neutral": "gray"
}

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Read the sheet. ttl=0 means it always fetches the newest live data!
        df = conn.read(ttl=0)
        return df.dropna(how="all") # Clean up empty rows
    except Exception as e:
        st.error(f"Could not connect to Google Sheets: {e}")
        return pd.DataFrame(columns=["Name", "Type", "Affiliation", "X", "Y", "Radius"])

# --- UI LAYOUT ---
st.title("🗺️ KingShot Ultimate War Room")
tab1, tab2 = st.tabs(["🔧 API Tools", "🗺️ Tactical Map"])

# ==========================================
# TAB 1: API TOOLS
# ==========================================
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Player Lookup")
        
        # Initialize an empty history list in the session state
        if "search_history" not in st.session_state:
            st.session_state.search_history = []
            
        # Create a dropdown that displays recent searches
        selected_history = st.selectbox("Recent Searches", st.session_state.search_history) if st.session_state.search_history else ""
        
        # Text input defaults to whatever they pick from the dropdown
        player_id = st.text_input("Enter Player ID (e.g., 262432539)", value=selected_history)
        
        if st.button("Get Player Stats"):
            raw_id = player_id.split(" - ")[0].strip()
            if raw_id:
                # Add to history if it's a new ID, and limit history to 10 items
                if player_id not in st.session_state.search_history:
                    st.session_state.search_history.insert(0, player_id)
                    st.session_state.search_history = st.session_state.search_history[:10]
                
                res = requests.get("https://kingshot.net/api/player-info", params={"playerId": raw_id})
                if res.status_code == 200:
                    data = res.json()["data"]
                    st.success(f"**Name:** {data['name']} | **Kingdom:** {data['kingdom']} | **Level:** {data['level']}")
                    if data.get('profilePhoto'):
                        st.image(data['profilePhoto'], width=150)
                else:
                    st.error("Player not found.")
                    
        st.divider()
        st.subheader("Free Loot")
        if st.button("Get Active Gift Codes", type="primary"):
            res = requests.get("https://kingshot.net/api/gift-codes")
            if res.status_code == 200:
                for item in res.json()["data"]["giftCodes"]:
                    date_only = item.get('expiresAt', 'Permanent').split('T')[0]
                    st.info(f"🎁 **{item['code']}** (Expires: {date_only})")

    with col2:
        st.subheader("Kingdom Tools")
        kd_id = st.text_input("Enter Kingdom ID", value="23")
        
        if st.button("Get Kingdom Age"):
            res = requests.get("https://kingshot.net/api/kingdom-tracker", params={"kingdomId": kd_id})
            if res.status_code == 200 and res.json()["data"]["servers"]:
                kd_data = res.json()["data"]["servers"][0]
                open_date = datetime.strptime(kd_data['openTime'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                age_days = (datetime.now(timezone.utc) - open_date).days
                st.info(f"Kingdom {kd_id} is **{age_days} days old**.")
                
        if st.button("Latest KvK Record"):
            att_res = requests.get("https://kingshot.net/api/kvk/matches", params={"kingdom_a": kd_id, "limit": 1})
            if att_res.status_code == 200 and att_res.json()["data"]:
                match = att_res.json()["data"][0]
                st.warning(f"⚔️ **Latest Attack** vs KD {match['kingdom_b']} | Season: {match.get('kvk_title', 'Unknown')}")


# ==========================================
# TAB 2: TACTICAL MAP
# ==========================================

# Initialize Map View State (For the Search Feature)
if "map_x_range" not in st.session_state:
    st.session_state.map_x_range = [0, 1200]
if "map_y_range" not in st.session_state:
    st.session_state.map_y_range = [0, 1200]

with tab2:
    df = load_data()
    
    map_col, sidebar_col = st.columns([3, 1]) # Map takes 75% of screen, sidebar 25%
    
    with sidebar_col:
        st.header("🎛️ Map Controls")
        
        # 1. Search Feature (RESTORED)
        st.subheader("🔍 Find Coordinate")
        col_sx, col_sy = st.columns(2)
        search_x = col_sx.number_input("Search X", min_value=0, max_value=1200, value=600, key="sx")
        search_y = col_sy.number_input("Search Y", min_value=0, max_value=1200, value=600, key="sy")
        
        col_go, col_reset = st.columns(2)
        if col_go.button("Go To Coord", use_container_width=True):
            # Zooms into a 100x100 tile view around the target
            st.session_state.map_x_range = [max(0, search_x - 50), min(1200, search_x + 50)]
            st.session_state.map_y_range = [max(0, search_y - 50), min(1200, search_y + 50)]
            st.rerun()
            
        if col_reset.button("Reset View", use_container_width=True):
            # Pops the map back out to the full 1200x1200 grid
            st.session_state.map_x_range = [0, 1200]
            st.session_state.map_y_range = [0, 1200]
            st.rerun()

        # 2. Add New Marker Form
        with st.expander("➕ Add New Marker", expanded=False):
            with st.form("add_marker_form", clear_on_submit=True):
                new_name = st.text_input("Marker Name")
                col_ax, col_ay = st.columns(2)
                new_x = col_ax.number_input("X Coord", min_value=0, max_value=1199, value=600, key="ax")
                new_y = col_ay.number_input("Y Coord", min_value=0, max_value=1199, value=600, key="ay")
                new_type = st.selectbox("Type", list(TYPE_STYLES.keys()))
                new_affil = st.selectbox("Affiliation", list(AFFILIATION_COLORS.keys()))
                new_rad = st.number_input("Danger Radius", min_value=0, value=0)
                
                if st.form_submit_button("Save to Database"):
                    if new_name:
                        new_row = pd.DataFrame([{
                            "Name": new_name, "Type": new_type, "Affiliation": new_affil, 
                            "X": new_x, "Y": new_y, "Radius": new_rad
                        }])
                        updated_df = pd.concat([df, new_row], ignore_index=True)
                        conn.update(worksheet="Sheet1", data=updated_df)
                        st.success("Saved!")
                        st.rerun() 

        # 3. Filters
        st.subheader("👁️ Filters")
        show_allies = st.checkbox("Show Allies 🟢", value=True)
        show_enemies = st.checkbox("Show Enemies 🔴", value=True)
        show_neutral = st.checkbox("Show Neutral ⚪", value=True)

    with map_col:
        # Filter the dataframe based on checkboxes
        filtered_df = df.copy()
        allowed_affils = []
        if show_allies: allowed_affils.append("Ally")
        if show_enemies: allowed_affils.append("Enemy")
        if show_neutral: allowed_affils.append("Neutral")
        
        if not filtered_df.empty:
            filtered_df = filtered_df[filtered_df["Affiliation"].isin(allowed_affils)]

        # Draw the Plotly Map
        fig = go.Figure()

        if not filtered_df.empty:
            colors = filtered_df["Affiliation"].map(AFFILIATION_COLORS)
            hover_text = filtered_df.apply(lambda row: f"<b>{row['Name']}</b><br>Type: {row['Type']}<br>Coords: ({row['X']}, {row['Y']})", axis=1)

            # Draw the Target Square if they searched for a coordinate!
            if st.session_state.map_x_range != [0, 1200]:
                fig.add_shape(type="rect",
                    x0=search_x-1, y0=search_y-1, x1=search_x+1, y1=search_y+1,
                    line=dict(color="yellow", width=3), fillcolor="rgba(255, 255, 0, 0.2)"
                )

            fig.add_trace(go.Scatter(
                x=filtered_df["X"],
                y=filtered_df["Y"],
                mode="markers+text",
                marker=dict(size=12, color=colors, line=dict(width=2, color='white')),
                text=filtered_df["Type"].map(TYPE_STYLES), 
                textposition="top center",
                textfont=dict(size=16),
                hoverinfo="text",
                hovertext=hover_text
            ))

        # Format the Map Canvas
        fig.update_layout(
            plot_bgcolor="#C4E0B4",
            paper_bgcolor="#1E1E1E",
            dragmode="pan",
            xaxis=dict(
                range=st.session_state.map_x_range, # Driven by the Search button!
                showgrid=True, gridcolor="#A3C993", dtick=100, side="bottom"
            ),
            yaxis=dict(
                range=st.session_state.map_y_range, # Driven by the Search button!
                showgrid=True, gridcolor="#A3C993", dtick=100,
                scaleanchor="x", scaleratio=1 # This forces the grid to be perfectly square
            ),
            margin=dict(l=10, r=10, t=40, b=10),
            title=dict(text="Live Tactical Map", font=dict(color="#E0E0E0")),
            showlegend=False
        )

        # Turn off scroll zoom to stop the stutter, and bring back a cleaned-up menu bar!
        st.plotly_chart(
            fig, 
            use_container_width=True, 
            config={
                'scrollZoom': False, 
                'displayModeBar': True, 
                'displaylogo': False, # Hides the Plotly logo
                'modeBarButtonsToRemove': [
                    'lasso2d', 'select2d', 'autoScale2d', 
                    'hoverClosestCartesian', 'hoverCompareCartesian', 
                    'toggleSpikelines'
                ] # Hides all the useless data-science tools!
            } 
        )
