import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import requests
from datetime import datetime, timezone
import webbrowser
import json
import os
import math 

HISTORY_FILE = "player_history.json"
MARKERS_FILE = "map_markers.json"

def load_json_file(filepath, default_val):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except:
            return default_val
    return default_val

def save_json_file(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f)

# --- GLOBAL STYLES & TYPES ---
# Removed Friend/Foe as "Types" since they are now "Affiliations"
TYPE_STYLES = {
    "Custom Marker": {"icon": "📍"},
    "Player": {"icon": "🧍"},
    "Rally Point": {"icon": "🚩"},
    "Castle": {"icon": "👑"},
    "Fortress": {"icon": "🏯"},
    "Sanctuary": {"icon": "🏛️"},
    "Builder's Guild": {"icon": "🔨"},
    "Armory": {"icon": "🪖"},
    "Scholar's Tower": {"icon": "📜"},
    "Arsenal": {"icon": "💣"},
    "Forager Grove": {"icon": "🍄"},
    "Harvest Alter": {"icon": "🌿"},
    "Drill Camp": {"icon": "🏕️"},
    "Frontier Lodge": {"icon": "🛖"}
}

AFFILIATION_COLORS = {
    "Ally": "blue",
    "Enemy": "red",
    "Neutral": "gray"
}

def display_result(text, color="black", link_url=None):
    result_box.config(state=tk.NORMAL, fg=color)
    result_box.delete(1.0, tk.END)
    result_box.insert(tk.END, text)
    if link_url:
        result_box.insert(tk.END, "\n\nAvatar Link: ")
        result_box.insert(tk.END, "Click here to view profile photo", "hyperlink")
        result_box.tag_config("hyperlink", foreground="blue", underline=True)
        result_box.tag_bind("hyperlink", "<Button-1>", lambda e, url=link_url: webbrowser.open(url))
        result_box.tag_bind("hyperlink", "<Enter>", lambda e: result_box.config(cursor="hand2"))
        result_box.tag_bind("hyperlink", "<Leave>", lambda e: result_box.config(cursor=""))
    result_box.config(state=tk.DISABLED)

# --- API FUNCTIONS ---
def fetch_stats(event=None): 
    raw_input = id_entry.get().strip()
    player_id = raw_input.split(" - ")[0].strip() 
    if not player_id:
        display_result("Please enter an ID!", "red")
        return
    display_result("Loading player info...", "blue")
    root.update()
    try:
        url = "https://kingshot.net/api/player-info"
        response = requests.get(url, params={"playerId": player_id})
        if response.status_code == 200:
            data = response.json()["data"]
            stats_text = f"Name: {data['name']}\nKingdom: {data['kingdom']}\nLevel: {data['level']}"
            
            history_entry = f"{player_id} - {data['name']}"
            history = load_json_file(HISTORY_FILE, [])
            if history_entry in history: history.remove(history_entry)
            history.insert(0, history_entry)
            history = history[:10]
            save_json_file(HISTORY_FILE, history)
            id_entry['values'] = history
            id_entry.set(history_entry)

            photo_url = data.get('profilePhoto')
            display_result(stats_text, "black", link_url=photo_url)
        else:
            display_result("Player not found.", "red")
    except requests.exceptions.RequestException:
        display_result("Connection failed.", "red")

def fetch_gift_codes(event=None):
    display_result("Checking for free loot...", "blue")
    root.update()
    try:
        url = "https://kingshot.net/api/gift-codes"
        response = requests.get(url)
        if response.status_code == 200:
            codes = response.json()["data"]["giftCodes"]
            if not codes:
                display_result("No active gift codes right now.", "black")
                return
            codes_text = "Active Gift Codes:\n\n"
            for item in codes:
                code_text = item['code']
                expires_at = item.get('expiresAt')
                if expires_at:
                    date_only = expires_at.split('T')[0]
                    codes_text += f"🎁 {code_text} (Expires: {date_only})\n"
                else:
                    codes_text += f"🎁 {code_text} (Permanent)\n"
            display_result(codes_text, "green")
        else:
            display_result("Failed to get codes.", "red")
    except requests.exceptions.RequestException:
        display_result("Connection failed.", "red")

def fetch_kingdom_info(event=None):
    kingdom_id = kd_entry.get().strip()
    if not kingdom_id:
        display_result("Please enter a Kingdom Number!", "red")
        return
    display_result("Looking up server...", "blue")
    root.update()
    try:
        url = "https://kingshot.net/api/kingdom-tracker"
        response = requests.get(url, params={"kingdomId": kingdom_id})
        if response.status_code == 200:
            servers = response.json()["data"]["servers"]
            if not servers:
                display_result(f"Kingdom {kingdom_id} not found.", "black")
                return
            kd_data = servers[0]
            open_time_str = kd_data['openTime']
            open_date = datetime.strptime(open_time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - open_date).days
            date_only = open_time_str.split('T')[0]
            kd_text = (f"Kingdom {kingdom_id} Info:\nOpened: {date_only} ({age_days} days ago)\nExclusive: {'Yes' if kd_data['isExclusive'] else 'No'}")
            display_result(kd_text, "black")
        else:
            display_result("Failed to retrieve data.", "red")
    except requests.exceptions.RequestException:
        display_result("Connection failed.", "red")

def fetch_new_servers(event=None):
    display_result("Finding servers opened in the last 7 days...", "blue")
    root.update()
    try:
        url = "https://kingshot.net/api/kingdom-tracker"
        response = requests.get(url, params={"recent": 7, "limit": 10})
        if response.status_code == 200:
            servers = response.json()["data"]["servers"]
            if not servers:
                display_result("No new servers opened in the last 7 days.", "black")
                return
            out_text = "Newest Servers (Last 7 Days):\n\n"
            for s in servers:
                date_only = s['openTime'].split('T')[0]
                langs_list = s.get('languages') or []
                langs = ", ".join(langs_list) if langs_list else "Unknown"
                out_text += f"👑 KD {s['kingdomId']} | Opened: {date_only} | Lang: {langs}\n"
            display_result(out_text, "black")
    except requests.exceptions.RequestException:
        display_result("Connection failed.", "red")

def fetch_kvk_history(event=None):
    kingdom_id = kd_entry.get().strip()
    if not kingdom_id:
        display_result("Please enter a Kingdom Number!", "red")
        return
    display_result("Looking up attacking and defending records...", "blue")
    root.update()
    try:
        url = "https://kingshot.net/api/kvk/matches"
        att_res = requests.get(url, params={"kingdom_a": kingdom_id, "limit": 1})
        def_res = requests.get(url, params={"kingdom_b": kingdom_id, "limit": 1})
        out_text = f"War Records for Kingdom {kingdom_id}:\n\n"
        if att_res.status_code == 200 and att_res.json()["data"]:
            match = att_res.json()["data"][0]
            prep = "Won" if str(match['prep_winner']) == kingdom_id else "Lost"
            castle = "Won" if str(match['castle_winner']) == kingdom_id else "Lost"
            out_text += f"⚔️ LATEST ATTACK (vs KD {match['kingdom_b']})\nSeason: {match.get('kvk_title', 'Unknown')}\nPrep Phase: {prep} | Castle Phase: {castle}\n\n"
        else:
            out_text += "⚔️ LATEST ATTACK: No records found.\n\n"
        if def_res.status_code == 200 and def_res.json()["data"]:
            match = def_res.json()["data"][0]
            prep = "Won" if str(match['prep_winner']) == kingdom_id else "Lost"
            castle = "Won" if str(match['castle_winner']) == kingdom_id else "Lost"
            out_text += f"🛡️ LATEST DEFENSE (vs KD {match['kingdom_a']})\nSeason: {match.get('kvk_title', 'Unknown')}\nPrep Phase: {prep} | Castle Phase: {castle}\n"
        else:
            out_text += "🛡️ LATEST DEFENSE: No records found.\n"
        display_result(out_text.strip(), "black")
    except requests.exceptions.RequestException:
        display_result("Connection failed.", "red")

def check_health():
    display_result("Pinging KingShot servers...", "blue")
    root.update()
    try:
        url = "https://kingshot.net/api/health"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()["checks"]
            out = f"API Status: ONLINE 🟢\nDatabase: {data['database'].upper()}\nServer: {data['server'].upper()}"
            display_result(out, "green")
        else:
            display_result("API Status: OFFLINE 🔴\nThe game's data servers might be down.", "red")
    except requests.exceptions.RequestException:
        display_result("Connection failed. Check your internet.", "red")

# --- TACTICAL MAP LOGIC (Tab 2) ---
map_zoom = 0.5 
map_offset_x = 50
map_offset_y = 50
drag_data = {"x": 0, "y": 0}
markers = load_json_file(MARKERS_FILE, {})
target_tile = {"x": None, "y": None}
selected_marker_id = None

ruler_mode = False
ruler_clicks = []
min_x, max_x, min_y, max_y = 0, 1200, 0, 1200

def toggle_ruler():
    global ruler_mode, ruler_clicks
    ruler_mode = not ruler_mode
    ruler_clicks = []
    if ruler_mode:
        ruler_btn.config(bg="orange", text="📏 Ruler Active (Click 2 points)")
        map_canvas.config(cursor="target")
    else:
        ruler_btn.config(bg="SystemButtonFace", text="📏 Distance Ruler")
        map_canvas.config(cursor="crosshair")
        ruler_label.config(text="")
    draw_map()

def update_minimap():
    minimap_canvas.delete("all")
    minimap_canvas.create_rectangle(0, 0, 120, 120, fill="#C4E0B4", outline="#2F551E")
    for mk_id, data in markers.items():
        # Check BOTH filters (Type and Affiliation)
        m_type = data.get('type', 'Custom Marker')
        m_affil = data.get('affiliation', 'Neutral')
        
        if type_vars.get(m_type, tk.BooleanVar(value=True)).get() and affil_vars.get(m_affil, tk.BooleanVar(value=True)).get():
            mx = data['x'] / 10
            my = (1200 - data['y']) / 10
            minimap_canvas.create_oval(mx-1, my-1, mx+1, my+1, fill=AFFILIATION_COLORS[m_affil], outline="")
    vx1 = max(0, min_x / 10)
    vy1 = max(0, (1200 - max_y) / 10)
    vx2 = min(120, max_x / 10)
    vy2 = min(120, (1200 - min_y) / 10)
    minimap_canvas.create_rectangle(vx1, vy1, vx2, vy2, outline="white", width=2)

def draw_map():
    global min_x, max_x, min_y, max_y
    map_canvas.delete("all")
    
    cw = map_canvas.winfo_width()
    ch = map_canvas.winfo_height()
    if cw < 10: cw = 500
    if ch < 10: ch = 500
    
    x1, y1 = map_offset_x, map_offset_y
    x2, y2 = map_offset_x + (1200 * map_zoom), map_offset_y + (1200 * map_zoom)
    
    map_canvas.create_rectangle(x1, y1, x2, y2, fill="#C4E0B4", outline="#2F551E", width=3)
    
    min_x = max(0, int(-map_offset_x / map_zoom))
    max_x = min(1200, int((cw - map_offset_x) / map_zoom) + 1)
    
    min_y = max(0, int(1200 - ((ch - map_offset_y) / map_zoom)) - 1)
    max_y = min(1200, int(1200 - (-map_offset_y / map_zoom)) + 1)

    if map_zoom >= 8.0: step = 1     
    elif map_zoom >= 1.5: step = 10    
    else: step = 100   
        
    for i in range(0, 1201, step):
        if min_x <= i <= max_x:
            vx = map_offset_x + (i * map_zoom)
            if i % 100 == 0:
                map_canvas.create_line(vx, y1, vx, y2, fill="#7BAA6B", width=2)
            elif i % 10 == 0:
                map_canvas.create_line(vx, y1, vx, y2, fill="#A3C993", dash=(4, 4))
            else:
                map_canvas.create_line(vx, y1, vx, y2, fill="#CDE6C3", dash=(1, 3))
                
        if min_y <= i <= max_y:
            hy = map_offset_y + ((1200 - i) * map_zoom)
            if i % 100 == 0:
                map_canvas.create_line(x1, hy, x2, hy, fill="#7BAA6B", width=2)
            elif i % 10 == 0:
                map_canvas.create_line(x1, hy, x2, hy, fill="#A3C993", dash=(4, 4))
            else:
                map_canvas.create_line(x1, hy, x2, hy, fill="#CDE6C3", dash=(1, 3))

    for mk_id, data in markers.items():
        m_type = data.get('type', 'Custom Marker')
        m_affil = data.get('affiliation', 'Neutral')
        
        # --- NEW FILTER CHECK: Skip if Type OR Affiliation is unchecked ---
        if not type_vars.get(m_type, tk.BooleanVar(value=True)).get(): continue
        if not affil_vars.get(m_affil, tk.BooleanVar(value=True)).get(): continue

        rad = data.get('radius', 0)
        if rad > 0:
            rx1 = map_offset_x + ((data['x'] - rad) * map_zoom)
            ry1 = map_offset_y + ((1200 - (data['y'] + rad)) * map_zoom)
            rx2 = map_offset_x + ((data['x'] + rad) * map_zoom)
            ry2 = map_offset_y + ((1200 - (data['y'] - rad)) * map_zoom)
            map_canvas.create_oval(rx1, ry1, rx2, ry2, outline=AFFILIATION_COLORS[m_affil], width=max(1, int(2*map_zoom)), dash=(4,4))

    if target_tile["x"] is not None and target_tile["y"] is not None:
        tx, ty = target_tile["x"], target_tile["y"]
        hx1 = map_offset_x + (tx * map_zoom)
        hy1 = map_offset_y + ((1200 - ty) * map_zoom)
        hx2 = map_offset_x + ((tx + 1) * map_zoom)
        hy2 = map_offset_y + ((1200 - (ty + 1)) * map_zoom)
        map_canvas.create_rectangle(hx1, hy1, hx2, hy2, outline="yellow", width=3)
        map_canvas.create_rectangle(hx1-1, hy1-1, hx2+1, hy2+1, outline="red", width=1)

    if ruler_mode and len(ruler_clicks) == 2:
        px1 = map_offset_x + (ruler_clicks[0][0] * map_zoom)
        py1 = map_offset_y + ((1200 - ruler_clicks[0][1]) * map_zoom)
        px2 = map_offset_x + (ruler_clicks[1][0] * map_zoom)
        py2 = map_offset_y + ((1200 - ruler_clicks[1][1]) * map_zoom)
        map_canvas.create_line(px1, py1, px2, py2, fill="orange", width=3, dash=(5,2))
        map_canvas.create_oval(px1-4, py1-4, px1+4, py1+4, fill="orange")
        map_canvas.create_oval(px2-4, py2-4, px2+4, py2+4, fill="orange")

    map_canvas.create_text(x1 + 10, y2 - 10, text="(0,0)", anchor="sw", fill="#2F551E", font=("Arial", 10, "bold"))
    map_canvas.create_text(x2 - 10, y1 + 10, text="(1199,1199)", anchor="ne", fill="#2F551E", font=("Arial", 10, "bold"))

    for mk_id, data in markers.items():
        m_type = data.get('type', 'Custom Marker')
        m_affil = data.get('affiliation', 'Neutral')
        
        if not type_vars.get(m_type, tk.BooleanVar(value=True)).get(): continue
        if not affil_vars.get(m_affil, tk.BooleanVar(value=True)).get(): continue
        
        mx = map_offset_x + (data['x'] * map_zoom)
        my = map_offset_y + ((1200 - data['y']) * map_zoom)
        
        style = TYPE_STYLES.get(m_type, TYPE_STYLES["Custom Marker"])
        font_size = max(10, int(14 * map_zoom))
        font_size = min(font_size, 36) 
        
        map_canvas.create_text(mx, my, text=style["icon"], font=("Arial", font_size))
        
        if mk_id == selected_marker_id:
            map_canvas.create_oval(mx-15, my-15, mx+15, my+15, outline="white", width=2)
            
        map_canvas.create_text(mx, my + (font_size), text=data['name'], fill=AFFILIATION_COLORS[m_affil], font=("Arial", max(8, font_size-4), "bold"))
        
    update_minimap()

def set_affiliation(new_affil):
    global selected_marker_id
    if selected_marker_id and selected_marker_id in markers:
        markers[selected_marker_id]['affiliation'] = new_affil
        save_json_file(MARKERS_FILE, markers)
        # Update sidebar text
        sel_affil_lbl.config(text=f"Affiliation: {new_affil}", fg=AFFILIATION_COLORS[new_affil])
        draw_map()

def start_pan(event):
    global ruler_clicks, selected_marker_id
    map_x = int((event.x - map_offset_x) / map_zoom)
    map_y = int(1200 - ((event.y - map_offset_y) / map_zoom))
    
    clicked_marker_data = None
    clicked_id = None
    for mk_id, data in markers.items():
        m_type = data.get('type', 'Custom Marker')
        m_affil = data.get('affiliation', 'Neutral')
        if not type_vars.get(m_type, tk.BooleanVar(value=True)).get(): continue
        if not affil_vars.get(m_affil, tk.BooleanVar(value=True)).get(): continue
        
        mx = map_offset_x + (data['x'] * map_zoom)
        my = map_offset_y + ((1200 - data['y']) * map_zoom)
        if abs(event.x - mx) < 25 and abs(event.y - my) < 25:
            clicked_marker_data = data
            clicked_id = mk_id
            break

    if ruler_mode:
        if len(ruler_clicks) == 2: ruler_clicks = [] 
        if clicked_marker_data:
            ruler_clicks.append((clicked_marker_data['x'], clicked_marker_data['y']))
        else:
            ruler_clicks.append((map_x, map_y))
        
        if len(ruler_clicks) == 2:
            dist = math.hypot(ruler_clicks[1][0] - ruler_clicks[0][0], ruler_clicks[1][1] - ruler_clicks[0][1])
            ruler_label.config(text=f"Distance: {int(dist)} tiles")
        draw_map()
        return

    drag_data["x"] = event.x
    drag_data["y"] = event.y
            
    selected_marker_id = clicked_id
    
    if selected_marker_id:
        data = markers[selected_marker_id]
        m_affil = data.get('affiliation', 'Neutral')
        
        sel_name_lbl.config(text=f"Name: {data['name']}")
        sel_type_lbl.config(text=f"Type: {data.get('type', 'Custom Marker')}")
        sel_affil_lbl.config(text=f"Affiliation: {m_affil}", fg=AFFILIATION_COLORS[m_affil])
        sel_coord_lbl.config(text=f"Coords: ({data['x']}, {data['y']})")
        sel_rad_lbl.config(text=f"Radius: {data.get('radius', 0)}" if data.get('radius', 0) > 0 else "Radius: None")
        
        btn_copy.config(state=tk.NORMAL)
        btn_delete.config(state=tk.NORMAL)
        btn_ally.config(state=tk.NORMAL)
        btn_enemy.config(state=tk.NORMAL)
        btn_neutral.config(state=tk.NORMAL)
        
        map_instructions.config(
            text=f"📌 SELECTED: {data['name']} | Coords: ({data['x']}, {data['y']})", 
            fg="blue", font=("Arial", 10, "bold")
        )
    else:
        sel_name_lbl.config(text="Select a marker...")
        sel_type_lbl.config(text="")
        sel_affil_lbl.config(text="")
        sel_coord_lbl.config(text="")
        sel_rad_lbl.config(text="")
        btn_copy.config(state=tk.DISABLED)
        btn_delete.config(state=tk.DISABLED)
        btn_ally.config(state=tk.DISABLED)
        btn_enemy.config(state=tk.DISABLED)
        btn_neutral.config(state=tk.DISABLED)
        
        map_instructions.config(
            text="Left-Click & Drag to Pan | Mouse Wheel to Zoom | Right-Click to Add Marker", 
            fg="black", font=("Arial", 9, "italic")
        )
        
    draw_map()

def do_pan(event):
    if ruler_mode: return 
    global map_offset_x, map_offset_y
    dx = event.x - drag_data["x"]
    dy = event.y - drag_data["y"]
    map_offset_x += dx
    map_offset_y += dy
    drag_data["x"] = event.x
    drag_data["y"] = event.y
    draw_map()

def do_zoom(event):
    global map_zoom, map_offset_x, map_offset_y
    old_zoom = map_zoom
    scale_factor = 1.1 if event.delta > 0 else 0.9
    map_zoom *= scale_factor
    map_zoom = max(0.1, min(map_zoom, 25.0)) 
    actual_scale = map_zoom / old_zoom
    
    map_offset_x = event.x - (event.x - map_offset_x) * actual_scale
    map_offset_y = event.y - (event.y - map_offset_y) * actual_scale
    draw_map()

def right_click_add_marker(event):
    if ruler_mode: return
    map_x = int((event.x - map_offset_x) / map_zoom)
    map_y = int(1200 - ((event.y - map_offset_y) / map_zoom))

    if not (0 <= map_x <= 1199 and 0 <= map_y <= 1199): return

    popup = tk.Toplevel(root)
    popup.title("New Marker")
    popup.geometry("250x260") 
    
    tk.Label(popup, text=f"Location: ({map_x}, {map_y})", font=("Arial", 10, "bold")).pack(pady=5)
    
    tk.Label(popup, text="Name:").pack()
    name_entry = tk.Entry(popup)
    name_entry.pack()
    name_entry.focus() 
    
    tk.Label(popup, text="Type:").pack()
    type_box = ttk.Combobox(popup, values=list(TYPE_STYLES.keys()), state="readonly")
    type_box.set("Custom Marker")
    type_box.pack()

    tk.Label(popup, text="Affiliation:").pack()
    affil_box = ttk.Combobox(popup, values=list(AFFILIATION_COLORS.keys()), state="readonly")
    affil_box.set("Enemy")
    affil_box.pack()

    tk.Label(popup, text="Danger Radius (Tiles, 0 for none):").pack()
    rad_entry = tk.Entry(popup)
    rad_entry.insert(0, "0")
    rad_entry.pack()

    def save_new_marker(e=None): 
        m_name = name_entry.get().strip()
        try: m_rad = int(rad_entry.get())
        except ValueError: m_rad = 0
            
        if m_name:
            marker_key = f"{map_x}_{map_y}"
            markers[marker_key] = {
                "name": m_name, 
                "type": type_box.get(), 
                "affiliation": affil_box.get(),
                "x": map_x, 
                "y": map_y,
                "radius": m_rad
            }
            save_json_file(MARKERS_FILE, markers)
            draw_map()
        popup.destroy()

    tk.Button(popup, text="Save Marker", command=save_new_marker).pack(pady=10)
    popup.bind('<Return>', save_new_marker) 

def copy_coords():
    if selected_marker_id and selected_marker_id in markers:
        data = markers[selected_marker_id]
        coord_string = f"({data['x']}, {data['y']})"
        root.clipboard_clear()
        root.clipboard_append(coord_string)
        messagebox.showinfo("Copied!", f"Coordinates {coord_string} copied to clipboard!")

def delete_marker():
    global selected_marker_id
    if selected_marker_id and selected_marker_id in markers:
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this marker?"):
            del markers[selected_marker_id]
            save_json_file(MARKERS_FILE, markers)
            selected_marker_id = None
            
            sel_name_lbl.config(text="Select a marker...")
            sel_type_lbl.config(text="")
            sel_affil_lbl.config(text="")
            sel_coord_lbl.config(text="")
            sel_rad_lbl.config(text="")
            btn_copy.config(state=tk.DISABLED)
            btn_delete.config(state=tk.DISABLED)
            btn_ally.config(state=tk.DISABLED)
            btn_enemy.config(state=tk.DISABLED)
            btn_neutral.config(state=tk.DISABLED)
            draw_map()

def goto_coordinate(event=None):
    global map_offset_x, map_offset_y, map_zoom
    try:
        target_x = int(search_x_entry.get())
        target_y = int(search_y_entry.get())
    except ValueError:
        return 
    target_x = max(0, min(1199, target_x))
    target_y = max(0, min(1199, target_y))
    target_tile["x"] = target_x
    target_tile["y"] = target_y
    cw = map_canvas.winfo_width()
    ch = map_canvas.winfo_height()
    if cw < 10: cw = 500
    if ch < 10: ch = 500
    map_zoom = 12.0 
    map_offset_x = (cw / 2) - (target_x * map_zoom)
    map_offset_y = (ch / 2) - ((1200 - target_y) * map_zoom)
    draw_map()

# --- VISUAL WINDOW SETUP ---
root = tk.Tk()
root.title("StarKist's Kinghot Utility App")
root.geometry("850x700") 

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

tab1_tools = tk.Frame(notebook)
tab2_map = tk.Frame(notebook)

notebook.add(tab1_tools, text="🔧 API Tools")
notebook.add(tab2_map, text="🗺️ Tactical Map")

# ==========================================
# TAB 1: ALL THE OLD TOOLS
# ==========================================
t1_center = tk.Frame(tab1_tools)
t1_center.pack(pady=10)
tk.Button(t1_center, text="📡 Check Server Health", command=check_health, font=("Arial", 9)).pack(pady=(10,0))
tk.Frame(t1_center, height=2, bd=1, relief="sunken", width=450).pack(pady=10)
tk.Label(t1_center, text="Player Lookup", font=("Arial", 10, "bold")).pack()
saved_history = load_json_file(HISTORY_FILE, [])
id_entry = ttk.Combobox(t1_center, font=("Arial", 12), justify="center", values=saved_history)
id_entry.pack(pady=5)
if saved_history: id_entry.set(saved_history[0])
else: id_entry.insert(0, "262432539")
id_entry.bind('<Return>', fetch_stats) 
tk.Button(t1_center, text="Get Player Stats & Avatar", command=fetch_stats).pack()
tk.Frame(t1_center, height=2, bd=1, relief="sunken", width=450).pack(pady=10)
tk.Label(t1_center, text="Kingdom & War Tools", font=("Arial", 10, "bold")).pack()
kd_entry = tk.Entry(t1_center, font=("Arial", 12), justify="center")
kd_entry.pack(pady=5)
kd_entry.insert(0, "23")
kd_entry.bind('<Return>', fetch_kingdom_info) 
btn_frame1 = tk.Frame(t1_center)
btn_frame1.pack()
tk.Button(btn_frame1, text="Get Kingdom Age", command=fetch_kingdom_info).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame1, text="Latest KvK Record", command=fetch_kvk_history).pack(side=tk.LEFT, padx=5)
tk.Button(t1_center, text="Find Brand New Servers", command=fetch_new_servers).pack(pady=5)
tk.Frame(t1_center, height=2, bd=1, relief="sunken", width=450).pack(pady=10)
tk.Label(t1_center, text="Free Loot", font=("Arial", 10, "bold")).pack()
tk.Button(t1_center, text="Get Active Gift Codes", command=fetch_gift_codes, bg="gold").pack(pady=5)
result_box = scrolledtext.ScrolledText(t1_center, width=50, height=10, font=("Arial", 11), wrap=tk.WORD, state=tk.DISABLED)
result_box.pack(pady=15)
display_result("Welcome! Pick a tool above.", "gray")

# ==========================================
# TAB 2: THE TACTICAL MAP
# ==========================================
search_frame = tk.Frame(tab2_map, bg="#E0E0E0")
search_frame.pack(fill=tk.X, pady=0)
tk.Label(search_frame, text="Search X:", bg="#E0E0E0", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5, pady=5)
search_x_entry = tk.Entry(search_frame, width=6)
search_x_entry.pack(side=tk.LEFT, padx=2)
tk.Label(search_frame, text="Search Y:", bg="#E0E0E0", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)
search_y_entry = tk.Entry(search_frame, width=6)
search_y_entry.pack(side=tk.LEFT, padx=2)
search_x_entry.bind('<Return>', goto_coordinate)
search_y_entry.bind('<Return>', goto_coordinate)
tk.Button(search_frame, text="Go To Coord", command=goto_coordinate, bg="#4CAF50", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=15)

map_body = tk.PanedWindow(tab2_map, orient=tk.HORIZONTAL)
map_body.pack(fill=tk.BOTH, expand=True)

# --- THE SIDEBAR ---
# Made it slightly wider (240px) to comfortably fit the new buttons
sidebar = tk.Frame(map_body, width=240, bg="#f0f0f0", relief=tk.RAISED, bd=2)
sidebar.pack_propagate(False) 

# Canvas for inner scrolling of sidebar
sidebar_canvas = tk.Canvas(sidebar, bg="#f0f0f0", highlightthickness=0)
sidebar_scrollbar = ttk.Scrollbar(sidebar, orient="vertical", command=sidebar_canvas.yview)
scrollable_sidebar = tk.Frame(sidebar_canvas, bg="#f0f0f0")

scrollable_sidebar.bind(
    "<Configure>",
    lambda e: sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all"))
)
sidebar_canvas.create_window((0, 0), window=scrollable_sidebar, anchor="nw")
sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)
sidebar_canvas.pack(side="left", fill="both", expand=True)
sidebar_scrollbar.pack(side="right", fill="y")

tk.Label(scrollable_sidebar, text="MINI-MAP", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(pady=(10,2))
minimap_canvas = tk.Canvas(scrollable_sidebar, width=120, height=120, bg="#C4E0B4")
minimap_canvas.pack()

tk.Frame(scrollable_sidebar, height=2, bd=1, relief="sunken", width=200).pack(pady=10)

# Filters: Affiliation AND Type
tk.Label(scrollable_sidebar, text="AFFILIATION FILTERS", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(pady=2)
affil_vars = {}
for m_affil in AFFILIATION_COLORS.keys():
    var = tk.BooleanVar(value=True)
    affil_vars[m_affil] = var
    cb = tk.Checkbutton(scrollable_sidebar, text=m_affil, variable=var, command=draw_map, bg="#f0f0f0")
    cb.pack(anchor="w", padx=15)

tk.Label(scrollable_sidebar, text="TYPE FILTERS", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(pady=(10, 2))
type_vars = {}
for m_type, style in TYPE_STYLES.items():
    var = tk.BooleanVar(value=True)
    type_vars[m_type] = var
    cb = tk.Checkbutton(scrollable_sidebar, text=f"{style['icon']} {m_type}", variable=var, command=draw_map, bg="#f0f0f0")
    cb.pack(anchor="w", padx=15)

tk.Frame(scrollable_sidebar, height=2, bd=1, relief="sunken", width=200).pack(pady=10)

tk.Label(scrollable_sidebar, text="TACTICAL RULER", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(pady=2)
ruler_btn = tk.Button(scrollable_sidebar, text="📏 Distance Ruler", command=toggle_ruler)
ruler_btn.pack(pady=2)
ruler_label = tk.Label(scrollable_sidebar, text="", bg="#f0f0f0", fg="blue", font=("Arial", 9, "bold"))
ruler_label.pack()

tk.Frame(scrollable_sidebar, height=2, bd=1, relief="sunken", width=200).pack(pady=10)

tk.Label(scrollable_sidebar, text="SELECTED MARKER", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(pady=2)
sel_name_lbl = tk.Label(scrollable_sidebar, text="Select a marker...", bg="#f0f0f0", font=("Arial", 9))
sel_name_lbl.pack(anchor="w", padx=10)
sel_type_lbl = tk.Label(scrollable_sidebar, text="", bg="#f0f0f0", font=("Arial", 9))
sel_type_lbl.pack(anchor="w", padx=10)
sel_affil_lbl = tk.Label(scrollable_sidebar, text="", bg="#f0f0f0", font=("Arial", 9, "bold"))
sel_affil_lbl.pack(anchor="w", padx=10)
sel_coord_lbl = tk.Label(scrollable_sidebar, text="", bg="#f0f0f0", font=("Arial", 9))
sel_coord_lbl.pack(anchor="w", padx=10)
sel_rad_lbl = tk.Label(scrollable_sidebar, text="", bg="#f0f0f0", font=("Arial", 9))
sel_rad_lbl.pack(anchor="w", padx=10)

# Affiliation Change Buttons
affil_btn_frame = tk.Frame(scrollable_sidebar, bg="#f0f0f0")
affil_btn_frame.pack(pady=5)
btn_ally = tk.Button(affil_btn_frame, text="🟢 Ally", state=tk.DISABLED, command=lambda: set_affiliation("Ally"))
btn_ally.pack(side=tk.LEFT, padx=2)
btn_enemy = tk.Button(affil_btn_frame, text="🔴 Enemy", state=tk.DISABLED, command=lambda: set_affiliation("Enemy"))
btn_enemy.pack(side=tk.LEFT, padx=2)
btn_neutral = tk.Button(affil_btn_frame, text="⚪ Neutral", state=tk.DISABLED, command=lambda: set_affiliation("Neutral"))
btn_neutral.pack(side=tk.LEFT, padx=2)

# Action Buttons
action_frame = tk.Frame(scrollable_sidebar, bg="#f0f0f0")
action_frame.pack(pady=5)
btn_copy = tk.Button(action_frame, text="📋 Copy", state=tk.DISABLED, command=copy_coords)
btn_copy.pack(side=tk.LEFT, padx=5)
btn_delete = tk.Button(action_frame, text="🗑️ Delete", state=tk.DISABLED, bg="#ffcccc", command=delete_marker)
btn_delete.pack(side=tk.LEFT, padx=5)

map_canvas = tk.Canvas(map_body, bg="#1E1E1E", cursor="crosshair")
map_body.add(map_canvas, stretch="always") 
map_body.add(sidebar, stretch="never")     

root.update() 
map_canvas.bind("<ButtonPress-1>", start_pan)      
map_canvas.bind("<B1-Motion>", do_pan)             
map_canvas.bind("<MouseWheel>", do_zoom)           
map_canvas.bind("<Button-3>", right_click_add_marker) 

# Ensure mouse scrolling works over the sidebar too
def _on_mousewheel(event):
    sidebar_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
sidebar_canvas.bind_all("<MouseWheel>", _on_mousewheel)

draw_map()
root.mainloop()