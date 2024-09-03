import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch
import streamlit as st
import requests
import os
from matplotlib import font_manager as fm
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from io import BytesIO
from matplotlib.colors import to_rgba
import pandas as pd
import matplotlib
import matplotlib.gridspec as gridspec
import io
import base64
from matplotlib.transforms import Bbox

matplotlib.rcParams["figure.dpi"] = 300

st.set_page_config(
    page_title="Süper Lig - Oyuncu Şut Haritası",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
        /* Sidebar içindeki tüm text input elementlerini hedef alma */
        input[id^="text_input"] {
            background-color: #242C3A !important;  /* Arka plan rengi */
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    html, body, [class*="cache"], [class*="st-"]  {
        font-family: 'Poppins', sans-serif;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
        /* Bilgisayarlar için */
        @media (min-width: 1024px) {
            .block-container {
                width: 1000px;
                max-width: 1000px;
                padding-top: 40px;
            }
        }

        /* Tabletler için (genellikle 768px - 1024px arası ekran genişliği) */
        @media (min-width: 768px) and (max-width: 1023px) {
            .block-container.st-emotion-cache-13ln4jf.ea3mdgi5 {
                width: 700px;
                max-width: 700px;
            }
        }

        /* Telefonlar için (genellikle 768px ve altı ekran genişliği) */
        @media (max-width: 767px) {
            .block-container.st-emotion-cache-13ln4jf.ea3mdgi5 {
                width: 100%;
                max-width: 100%;
                padding-left: 10px;
                padding-right: 10px;
            }
        }
        .stDownloadButton {
            padding-top: 40px;
            display: flex;
            justify-content: center;
            text-align: center;
        }
        .stDownloadButton button {
            background-color: rgba(51, 51, 51, 0.17);
            color: gray;  /* Text color */
            border: 0.5px solid gray;  /* Thin gray border */
            transition: background-color 0.5s ease;
        }
        .stDownloadButton button:hover {
            background-color: rgba(51, 51, 51, 0.65);
            border: 1px solid gray;  /* Thin gray border */
        }
        .stDownloadButton button:active {
            background-color: rgba(51, 51, 51, 0.17);
            color: gray;  /* Text color */
            border: 0.5px solid gray;  /* Thin gray border */
            transition: background-color 0.5s ease;
        }
    </style>
    """,
    unsafe_allow_html=True
)

current_dir = os.path.dirname(os.path.abspath(__file__))

# Poppins fontunu yükleme
font_path = os.path.join(current_dir, 'fonts', 'Poppins-Regular.ttf')
prop = fm.FontProperties(fname=font_path)

bold_font_path = os.path.join(current_dir, 'fonts', 'Poppins-SemiBold.ttf')
bold_prop = fm.FontProperties(fname=bold_font_path)

fig = plt.figure(figsize=(15, 9))

gs = gridspec.GridSpec(1, 2, width_ratios=[5, 1])

# Sol taraftaki şut haritası alanı
ax_shotmap = plt.subplot(gs[0])

# Sağ taraftaki oyuncu bilgisi alanı
ax_info = plt.subplot(gs[1])

pitch = VerticalPitch(corner_arcs=True, half=True, pitch_type='uefa', pitch_color='#0e1117', line_color='#818f86', goal_type='box')

pitch.draw(ax=ax_shotmap)
fig.patch.set_facecolor('#0e1117')

ax_info.axis('off')
ax_shotmap.axis('off')

#fig.subplots_adjust()

primary_text_color = '#818f86'
pitch_color = '#0e1117'

# API'den veri çekme
url = "https://www.fotmob.com/api/leagueseasondeepstats?id=71&season=23864&type=players&stat=total_scoring_att&slug=super-lig"
response = requests.get(url)
data = response.json()

# Gerekli bilgileri işleme
oyuncular = [
    {
        "player_id": player["id"],
        "team_id": player["teamId"],
        "player_name": player["name"]
    }
    for player in data["statsData"]
]

# Sidebar'da oyuncu seçimi
oyuncu_ismi_listesi = [oyuncu["player_name"] for oyuncu in oyuncular]
secilen_oyuncu_ismi = st.sidebar.selectbox("Oyuncu Seçin", oyuncu_ismi_listesi)

# Seçilen oyuncunun player_id ve team_id bilgilerini alma
secilen_oyuncu = next(oyuncu for oyuncu in oyuncular if oyuncu["player_name"] == secilen_oyuncu_ismi)
player_id = secilen_oyuncu["player_id"]
team_id = secilen_oyuncu["team_id"]
player_name = secilen_oyuncu["player_name"]
league_id = 71
league_string = "Süper Lig"
season_string = "2024-2025"

def get_team_data(team_id):
    team_data_url = f"https://www.fotmob.com/api/teams?id={team_id}"
    team_data_response = requests.get(team_data_url)
    team_data = team_data_response.json()
    return team_data

team_data = get_team_data(team_id)
team_name = team_data["details"]["name"]

league_season_string = f"{team_name} | {league_string} - {season_string}"

def get_entry_id_for_selected_player(player_id):
    """
    Seçilen oyuncunun 2024/2025 Süper Lig sezonuna ait entryId bilgisini döner.
    """
    # Seçilen oyuncunun sezon bilgilerini API'den çekme
    player_data_url = f"https://www.fotmob.com/api/playerData?id={player_id}"
    player_data_response = requests.get(player_data_url)
    player_data = player_data_response.json()

    # 2024/2025 Süper Lig sezonuna ait entryId'yi bulma
    entry_id = None
    for season in player_data.get("statSeasons", []):
        if season["seasonName"] == "2024/2025":
            for tournament in season["tournaments"]:
                if tournament["name"] == "Super Lig" and tournament["tournamentId"] == 71:
                    entry_id = tournament["entryId"]
                    break
    return entry_id

# Seçilen oyuncunun 2024/2025 Süper Lig sezonu entryId'sini alma
entry_id = get_entry_id_for_selected_player(player_id)
    
def get_shotmap_data(player_id, entry_id):
    """
    Seçilen oyuncunun şut haritası verilerini API'den çeker.
    """
    shotmap_url = f"https://www.fotmob.com/api/playerStats?playerId={player_id}&seasonId={entry_id}"
    shotmap_response = requests.get(shotmap_url)
    shotmap_data = shotmap_response.json()
    shotmap = shotmap_data.get("shotmap", [])
    if shotmap is not None: 
        return shotmap
    else:
        return None

def get_player_shooting_stats(player_id, season_id):
    """
    Seçilen oyuncunun sezon performansındaki 'Shooting' istatistiklerini API'den çeker.
    """
    url = f"https://www.fotmob.com/api/playerStats?playerId={player_id}&seasonId={season_id}"
    response = requests.get(url)
    data = response.json()
    
    # Stats section içerisindeki 'Shooting' başlığı altındaki verileri al
    stats_section = data.get("statsSection", {}).get("items", [])
    
    if not stats_section:
        print("İstatistikler bölümü mevcut değil veya boş.")
        return None
    
    shooting_stats = None
    for section in stats_section:
        if section.get("title") == "Shooting":
            shooting_stats = section.get("items", [])
            break
    
    if shooting_stats is None:
        print("Shooting istatistikleri bulunamadı.")
    
    return shooting_stats

def get_player_match_played_stats(player_id, season_id):
    """
    Seçilen oyuncunun sezon performansındaki 'Matches', 'Started', 'Minutes' istatistiklerini API'den çeker.
    """
    url = f"https://www.fotmob.com/api/playerStats?playerId={player_id}&seasonId={season_id}"
    response = requests.get(url)
    data = response.json()

    # Stats section içerisindeki verileri al
    stats_section = data.get("topStatCard", {}).get("items", [])

    match_stats = {
        "Matches": None,
        "Started": None,
        "Minutes": None
    }

    for stat in stats_section:
        if stat.get("title") in match_stats:
            match_stats[stat["title"]] = stat.get("statValue")

    return match_stats

shotmap_data = get_shotmap_data(player_id, entry_id)
player_shooting_stats = get_player_shooting_stats(player_id, entry_id)
player_match_stats = get_player_match_played_stats(player_id, entry_id)

matches_played = player_match_stats["Matches"]
started_in_11 = player_match_stats["Started"]
minutes_played = player_match_stats["Minutes"]

if shotmap_data is not None:
    # 'Goals' başlığını arayarak gol sayısını çekme
    goal_stat = next((item for item in player_shooting_stats if item["title"] == "Goals"), None)
    goal_count = goal_stat["statValue"] if goal_stat else '-'

    # 'Shots' başlığını arayarak şut sayısını çekme
    shots_stat = next((item for item in player_shooting_stats if item["title"] == "Shots"), None)
    shots_count = shots_stat["statValue"] if shots_stat else '-'

    # 'Shots on target' başlığını arayarak isabetli şut sayısını çekme
    shotsontarget_stat = next((item for item in player_shooting_stats if item["title"] == "Shots on target"), None)
    shotsontarget_count = shotsontarget_stat["statValue"] if shotsontarget_stat else '-'

    # 'xG' başlığını arayarak beklentili gol sayısını çekme
    xG_stat = next((item for item in player_shooting_stats if item["title"] == "xG"), None)
    xG_count = xG_stat["statValue"] if xG_stat else '-'

    # 'xG excl. penalty' başlığını arayarak penaltı hariç beklentili gol sayısını çekme
    xGnP_stat = next((item for item in player_shooting_stats if item["title"] == "xG excl. penalty"), None)
    xGnP_count = xGnP_stat["statValue"] if xGnP_stat else '-'

    # 'xGOT' başlığını arayarak isabetli beklentili gol sayısını çekme
    xGOT_stat = next((item for item in player_shooting_stats if item["title"] == "xGOT"), None)
    xGOT_count = xGOT_stat["statValue"] if xGOT_stat else '-'
    
    goal_color = '#f5cb36'
    attemptSaved_color = '#3066d9'
    miss_color = 'red'
        
    # Seçilen oyuncunun şut haritasını çiz
    for shot in shotmap_data:
        if shot['expectedGoals'] is not None:
            if shot['eventType'] == 'Goal':
                shot_color = goal_color
                pitch.lines(shot['x'], shot['y'], 105, shot['goalCrossedY'], ax=ax_shotmap, color=to_rgba(shot_color, alpha=0.5), lw=1)
                pitch.scatter(shot['x'], shot['y'], ax=ax_shotmap, c=shot_color, s=round(shot['expectedGoals'], 2)*800, edgecolors='black', marker='*', alpha=0.8, lw=0.5)
            if shot['eventType'] == 'AttemptSaved':
                shot_color = attemptSaved_color
                if (shot['isBlocked'] == True) & (shot['expectedGoalsOnTarget'] == 0):
                    pitch.lines(shot['x'], shot['y'], shot['blockedX'], shot['blockedY'], ax=ax_shotmap, color=to_rgba(shot_color, alpha=0.5), lw=1)
                elif (shot['isBlocked'] == False) & (shot['expectedGoalsOnTarget'] > 0):
                    pitch.lines(shot['x'], shot['y'], shot['blockedX'], shot['blockedY'], ax=ax_shotmap, color=to_rgba(shot_color, alpha=0.5), lw=1)
                else:
                    pitch.lines(shot['x'], shot['y'], 105, shot['goalCrossedY'], ax=ax_shotmap, color=to_rgba(shot_color, alpha=0.25), lw=1)
                pitch.scatter(shot['x'], shot['y'], ax=ax_shotmap, c=shot_color, s=round(shot['expectedGoals'], 2)*800, edgecolors='black', marker='o', alpha=0.8, lw=1.5)
            if shot['eventType'] == 'Miss':
                shot_color = miss_color
                pitch.lines(shot['x'], shot['y'], 105, shot['goalCrossedY'], ax=ax_shotmap, color=to_rgba(shot_color, alpha=0.25), lw=1)
                pitch.scatter(shot['x'], shot['y'], ax=ax_shotmap, c=shot_color, s=round(shot['expectedGoals'], 2)*800, edgecolors='black', marker='x', alpha=0.8, lw=1.5)
            else:
                shot_color = 'gray'
                
    ax_shotmap.text(0.937, 0.08, '@bariscanyeksin\nVeri: FotMob', transform=ax_shotmap.transAxes,
            fontsize=9, fontproperties=prop, ha='right', va='bottom', color=primary_text_color, weight='normal', alpha=0.5)

    pitch.scatter(58.1,66,ax=ax_shotmap,c=goal_color, s=100, edgecolors='black', marker='*', alpha=0.5, lw=0.5)
    pitch.scatter(56.2,66,ax=ax_shotmap,c=attemptSaved_color, s=100, edgecolors='black', marker='o', alpha=0.5, lw=1.5)
    pitch.scatter(54.2,66,ax=ax_shotmap,c=miss_color, s=50, edgecolors='black', marker='x', alpha=0.5, lw=1.5)

    ax_shotmap.text(0.1, 0.147, 'Gol', transform=ax_shotmap.transAxes,
            fontsize=9, fontproperties=prop, ha='left', va='bottom', color=primary_text_color, weight='normal', alpha=0.5)
    ax_shotmap.text(0.1, 0.1155, 'Kurtarış/Blok', transform=ax_shotmap.transAxes,
            fontsize=9, fontproperties=prop, ha='left', va='bottom', color=primary_text_color, weight='normal', alpha=0.5)
    ax_shotmap.text(0.1, 0.083, 'İsabetsiz', transform=ax_shotmap.transAxes,
            fontsize=9, fontproperties=prop, ha='left', va='bottom', color=primary_text_color, weight='normal', alpha=0.5)
                
    # Oyuncu görselini URL'den çekme
    url = f'https://images.fotmob.com/image_resources/playerimages/{player_id}.png'
    response = requests.get(url)
    img = mpimg.imread(BytesIO(response.content))

    # Görseli ekleme
    imagebox = OffsetImage(img, zoom=0.3)
    ab = AnnotationBbox(imagebox, (0.05, 1.1), frameon=False, xycoords='axes fraction', box_alignment=(0, 1))
    ax_shotmap.add_artist(ab)
    
    url_teamlogo = f'https://images.fotmob.com/image_resources/logo/teamlogo/{team_id}.png'
    response_teamlogo = requests.get(url_teamlogo)
    img_teamlogo = mpimg.imread(BytesIO(response_teamlogo.content))

    # Görseli ekleme
    imagebox_teamlogo = OffsetImage(img_teamlogo, zoom=0.4, alpha=0.5)
    ab_teamlogo = AnnotationBbox(imagebox_teamlogo, (-0.2, 0.9), frameon=False, xycoords='axes fraction', box_alignment=(0, 1))
    ax_info.add_artist(ab_teamlogo)

    # Oyuncu ismini ekleme
    #ax_info.text(0.1, 0.75, player_name, transform=ax_info.transAxes, fontsize=14, fontproperties=bold_prop, verticalalignment='top', horizontalalignment='center', color='white', weight='bold')

    back_box = dict(boxstyle='round, pad=0.4', facecolor='wheat', alpha=0.5)
    back_box_2 = dict(boxstyle='round, pad=0.4', facecolor='#facd5c', alpha=0.5)

    ax_info.text(0.08, 0.67, "Gol", size=12, ha="right", fontproperties=prop, color=primary_text_color)
    ax_info.text(0.08, 0.60, "Toplam Şut", size=12, ha="right", fontproperties=prop, color=primary_text_color)
    ax_info.text(0.08, 0.53, "İsabetli Şut", size=12, ha="right", fontproperties=prop, color=primary_text_color)
    ax_info.text(0.08, 0.46, "Gol Beklentisi (xG)", size=12, ha="right", fontproperties=prop, color=primary_text_color)
    ax_info.text(0.08, 0.39, "Penaltısız xG", size=12, ha="right", fontproperties=prop, color=primary_text_color)
    ax_info.text(0.08, 0.32, "İsabetli Şutta xG", size=12, ha="right", fontproperties=prop, color=primary_text_color)

    ax_info.text(0.32, 0.671, str(goal_count), size=12, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
    ax_info.text(0.32, 0.601, str(shots_count), size=12, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
    ax_info.text(0.32, 0.531, str(shotsontarget_count), size=12, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
    ax_info.text(0.32, 0.461, str(xG_count), size=12, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
    ax_info.text(0.32, 0.391, str(xGnP_count), size=12, ha="center", fontproperties=prop, bbox=back_box_2, color='black')
    ax_info.text(0.32, 0.321, str(xGOT_count), size=12, ha="center", fontproperties=prop, bbox=back_box_2, color='black')

    #ax_info.text(0.1, 0.22, f"{str(matches_played)} maç", size=12, ha="center", fontproperties=prop, color=primary_text_color)
    #ax_info.text(0.1, 0.17, f"{str(started_in_11)} ilk 11", size=12, ha="center", fontproperties=prop, color=primary_text_color)
    #ax_info.text(0.1, 0.12, f"{str(minutes_played)} dakika", size=12, ha="center", fontproperties=prop, color=primary_text_color)
    
    ax_shotmap.text(0.148, 1.055, str(player_name), transform=ax_shotmap.transAxes, size=21, ha="left", fontproperties=bold_prop, weight='bold', color='white')
    ax_shotmap.text(0.148, 1.015, str(league_season_string), transform=ax_shotmap.transAxes, size=12, ha="left", fontproperties=prop, weight='normal', color='white')
    
    # Örnek oyuncu bilgileri
    data = [["Maç", matches_played],
            ["İlk 11", started_in_11],
            ["Dakika", minutes_played]]
    
    bbox = Bbox([[-0.25, 0.1], [0.45, 0.225]])  # Sol alt köşe (0.05, 0.1), sağ üst köşe (0.3, 0.3)
    
    # Tabloyu dikdörtgenin içine yerleştirme
    table = ax_info.table(cellText=data, cellLoc='center', 
                        bbox=bbox,  # Tabloyu dikdörtgenin sınırlayıcı kutusuna yerleştir
                        zorder=10,  # Tabloyu dikdörtgenin üzerine yerleştir
                        cellColours=[['lightgray', 'white']]*3)

    # Yazı tipi ve renk ayarları
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2)
            
    # İlk sütunu özelleştirme
    for i in range(len(data)):
        cell = table[i, 0]  # İlk sütundaki hücreler
        cell.set_facecolor(to_rgba(primary_text_color, alpha=0.15))  # Veri hücreleri arka plan rengi
        cell.set_edgecolor(primary_text_color)  # Hücre kenar rengi
        cell.set_text_props(color=primary_text_color, fontproperties=prop, fontweight='normal')  # Yazı rengi ve kalınlığı

    # İkinci sütunu özelleştirme
    for i in range(len(data)):
        cell = table[i, 1]  # İkinci sütundaki hücreler
        cell.set_facecolor(pitch_color)  # Veri hücreleri arka plan rengi
        cell.set_edgecolor(primary_text_color)  # Hücre kenar rengi
        cell.set_text_props(color=primary_text_color, fontproperties=prop, fontweight='bold')  # Yazı rengi ve kalınlığı

    ax_shotmap.axis('off')
    # Görseli göster
    st.pyplot(fig)
    
    player_name_replaced = player_name.replace(" ", "_")
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi = 300, bbox_inches = "tight")
    buf.seek(0)
    file_name = f"{player_name_replaced}_{league_string}_{season_string}_Şut_Haritası.png"
    
    st.download_button(
        label="Grafiği İndir",
        data=buf,
        file_name=file_name,
        mime="image/png"
    )
else:
    st.write('Oyuncu verisi bulunamadı.')
    
# Function to convert image to base64
def img_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Signature section
st.sidebar.markdown("---")  # Add a horizontal line to separate your signature from the content

# Load and encode icons
twitter_icon_base64 = img_to_base64("icons/twitter.png")
github_icon_base64 = img_to_base64("icons/github.png")
twitter_icon_white_base64 = img_to_base64("icons/twitter_white.png")  # White version of Twitter icon
github_icon_white_base64 = img_to_base64("icons/github_white.png")  # White version of GitHub icon

# Display the icons with links at the bottom of the sidebar
st.sidebar.markdown(
    f"""
    <style>
    .sidebar {{
        width: auto;
        text-align:center;
    }}
    .sidebar-content {{
        display: flex;
        flex-direction: column;
        height: 100%;
        margin-top: 10px;
        text-align:center;
    }}
    .icon-container {{
        display: flex;
        justify-content: center;
        margin-top: auto;
        padding-bottom: 20px;
        gap: 30px;  /* Space between icons */
    }}
    .icon-container img {{
        transition: filter 0.5s cubic-bezier(0.4, 0, 0.2, 1);  /* Smooth and natural easing */
    }}
    .icon-container a:hover img {{
        filter: brightness(0) invert(1);  /* Inverts color to white */
    }}
    </style>
    <div class="sidebar-content">
        <!-- Other sidebar content like selectbox goes here -->
        <div class="icon-container">
            <a href="https://x.com/bariscanyeksin" target="_blank">
                <img src="data:image/png;base64,{twitter_icon_base64}" alt="Twitter" width="30">
            </a>
            <a href="https://github.com/bariscanyeksin" target="_blank">
                <img src="data:image/png;base64,{github_icon_base64}" alt="GitHub" width="30">
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
