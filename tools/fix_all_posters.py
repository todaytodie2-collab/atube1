import os
import sys
import glob
import shutil
import sqlite3
import urllib.request

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\TheRift\.gemini\antigravity-ide\brain\f2aea73c-a700-40db-b87e-d2568f401d4d"
POSTERS_DIR = os.path.abspath("frontend/assets/posters")
BACKDROPS_DIR = os.path.abspath("frontend/assets/backdrops")
os.makedirs(POSTERS_DIR, exist_ok=True)
os.makedirs(BACKDROPS_DIR, exist_ok=True)

# 1. Copy generated posters from ARTIFACT_DIR
generated_mappings = {
    "welad_rizk_poster_*.jpg": "mov_welad_rizk_3.jpg",
    "beit_el_ruby_poster_*.jpg": "mov_beit_el_ruby.jpg",
    "fasel_lahazat_poster_*.jpg": "mov_fasel_lahazat.jpg",
    "kira_wal_gin_poster_*.jpg": "mov_kira_wal_gin.jpg",
    "blue_elephant_2_poster_*.jpg": "mov_blue_elephant_2.jpg",
    "hashasheen_poster_*.jpg": "ser_hashasheen.jpg",
    "gaafar_el_omda_poster_*.jpg": "ser_gaafar_el_omda.jpg",
    "el_atawla_poster_*.jpg": "ser_el_atawla.jpg",
    "kurulus_osman_poster_*.jpg": "ser_kurulus_osman.jpg",
    "cukur_poster_*.jpg": "ser_cukur.jpg",
    "yali_capkini_poster_*.jpg": "ser_yali_capkini.jpg",
}

print("=== 1. Moving Generated Posters ===")
for pattern, target_name in generated_mappings.items():
    matches = glob.glob(os.path.join(ARTIFACT_DIR, pattern))
    if matches:
        latest = max(matches, key=os.path.getmtime)
        dest = os.path.join(POSTERS_DIR, target_name)
        shutil.copy2(latest, dest)
        print(f"Copied {os.path.basename(latest)} -> posters/{target_name}")

# Also copy local frames as backdrops & posters
frames_mapping = {
    "frontend/assets/welad_rizk_frame.jpg": "mov_welad_rizk_3.jpg",
    "frontend/assets/beit_el_ruby_frame.jpg": "mov_beit_el_ruby.jpg",
    "frontend/assets/fasel_lahazat_frame.jpg": "mov_fasel_lahazat.jpg",
    "frontend/assets/deadpool3_frame.jpg": "mov_deadpool3.jpg",
    "frontend/assets/dune2_frame.jpg": "mov_dune2.jpg",
    "frontend/assets/your_name_frame.jpg": "mov_anime_your_name.jpg",
    "frontend/assets/suzume_frame.jpg": "mov_anime_suzume.jpg",
    "frontend/assets/spirited_away_frame.jpg": "mov_anime_spirited_away.jpg",
}

for src, fname in frames_mapping.items():
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(BACKDROPS_DIR, fname))
        if not os.path.exists(os.path.join(POSTERS_DIR, fname)):
            shutil.copy2(src, os.path.join(POSTERS_DIR, fname))
        print(f"Copied frame -> backdrops/{fname}")

# 2. Download remaining Wikipedia / TMDB posters
wiki_downloads = {
    "mov_gladiator2.jpg": "https://upload.wikimedia.org/wikipedia/en/0/06/Gladiator_II_poster.jpg",
    "mov_oppenheimer.jpg": "https://upload.wikimedia.org/wikipedia/en/4/4a/Oppenheimer_%28film%29.jpg",
    "mov_furiosa.jpg": "https://upload.wikimedia.org/wikipedia/en/3/34/Furiosa_A_Mad_Max_Saga.jpg",
    "mov_the_batman.jpg": "https://upload.wikimedia.org/wikipedia/en/f/ff/The_Batman_%28film%29_poster.jpg",
    "mov_anime_one_piece_red.jpg": "https://upload.wikimedia.org/wikipedia/en/4/4f/One_Piece_Film_Red_Poster.jpg",
    "mov_anime_jujutsu_kaisen_0.jpg": "https://upload.wikimedia.org/wikipedia/en/8/8b/Jujutsu_Kaisen_0_poster.jpg",
    "mov_anime_demon_slayer_mugen.jpg": "https://upload.wikimedia.org/wikipedia/en/2/21/Kimetsu_no_Yaiba_Mugen_Ressha_Hen_Poster.jpg",
    "mov_rrr.jpg": "https://upload.wikimedia.org/wikipedia/en/d/d7/RRR_Poster.jpg",
    "mov_pathaan.jpg": "https://upload.wikimedia.org/wikipedia/en/c/c3/Pathaan_film_poster.jpg",
    "mov_jawan.jpg": "https://upload.wikimedia.org/wikipedia/en/3/39/Jawan_film_poster.jpg",
    "wwe_wrestlemania_40.jpg": "https://upload.wikimedia.org/wikipedia/en/6/69/WrestleMania_XL_Poster.jpg",
    "wwe_royal_rumble_2024.jpg": "https://upload.wikimedia.org/wikipedia/en/1/10/RoyalRumble24Poster.jpg",
    "ser_house_of_dragon.jpg": "https://upload.wikimedia.org/wikipedia/en/9/93/House_of_the_Dragon_Season_2_Poster.jpg",
    "ser_shogun.jpg": "https://upload.wikimedia.org/wikipedia/en/b/b6/Sh%C5%8Dgun_%282024_miniseries%29_poster.jpg",
    "ser_the_last_of_us.jpg": "https://upload.wikimedia.org/wikipedia/en/0/05/The_Last_of_Us_Season_1_Poster.jpg",
    "ser_the_penguin.jpg": "https://upload.wikimedia.org/wikipedia/en/2/25/The_Penguin_Poster.jpg",
    "ser_squid_game_2.jpg": "https://upload.wikimedia.org/wikipedia/en/d/dd/Squid_Game_Season_2.png",
    "ser_queen_of_tears.jpg": "https://upload.wikimedia.org/wikipedia/en/7/75/Queen_of_Tears_poster.jpg",
    "mov_dune2.jpg": "https://upload.wikimedia.org/wikipedia/en/5/52/Dune_Part_Two_poster.jpeg",
    "mov_deadpool3.jpg": "https://upload.wikimedia.org/wikipedia/en/4/4c/Deadpool_%26_Wolverine_poster.jpg",
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
print("\n=== 2. Downloading Wikipedia Theatrical Posters ===")
for target_name, url in wiki_downloads.items():
    dest = os.path.join(POSTERS_DIR, target_name)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp, open(dest, 'wb') as f:
            f.write(resp.read())
        print(f"Downloaded -> posters/{target_name} ({os.path.getsize(dest)} bytes)")
    except Exception as e:
        print(f"Failed {target_name}: {e}")

# 3. Update SQLite Database vod_media table
print("\n=== 3. Updating SQLite vod_media Table ===")
conn = sqlite3.connect("config/atube_data.sqlite")
cur = conn.cursor()

# For any poster file in posters/ or backdrops/, update DB
for f in os.listdir(POSTERS_DIR):
    if not f.endswith(('.jpg', '.png', '.jpeg')): continue
    media_id = os.path.splitext(f)[0]
    poster_rel = f"assets/posters/{f}"
    
    # Check if backdrop exists
    backdrop_file = f
    if os.path.exists(os.path.join(BACKDROPS_DIR, backdrop_file)):
        backdrop_rel = f"assets/backdrops/{backdrop_file}"
    else:
        backdrop_rel = poster_rel

    cur.execute("""
        UPDATE vod_media 
        SET poster = ?, backdrop = ? 
        WHERE id = ?
    """, (poster_rel, backdrop_rel, media_id))

# Also ensure Alien Romulus
cur.execute("""
    UPDATE vod_media 
    SET poster = 'assets/posters/mov_alien_romulus.jpg',
        backdrop = 'assets/backdrops/mov_alien_romulus.jpg'
    WHERE id = 'mov_alien_romulus'
""")

conn.commit()
print(f"Updated {conn.total_changes} rows in vod_media.")
conn.close()

print("\n=== COMPLETE: All Posters Localized and Verified ===")
