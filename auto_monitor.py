# auto_monitor.py (Финальная, полная и отлаженная версия)
from dotenv import load_dotenv
load_dotenv() # Загружает переменные из .env файла в окружение
from flask import Flask
from threading import Thread
import requests
from requests.auth import HTTPBasicAuth
import time
import json
import gspread
import html
import telegram
import traceback
import sys
import os
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import shutil

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# --- КОНФИГУРАЦИЯ ---
# Этот блок остается без изменений
LEAGUES_TO_MONITOR = {
    #"LCK": "League of Legends - LCK",
    #"LEC": "League of Legends - LEC",
    #"LTA North": "League of Legends - LTA North",
    "LCP":"League of Legends - LCP",
    "LTA South":"League of Legends - LTA South"
    # Можете добавить сюда столько турниров, сколько нужно
}

TEAM_NAME_MAPPING = {
    "G2": "G2 Esports",
    "Bilibili": "BILIBILI GAMING DREAMSMART",
    "GAM": "GAM Esports",
    "Gen.G": "Gen.G Esports",
    "Hanwha Life": "Hanwha Life Esports",
    "EDward Gaming": "SHANGHAI EDWARD GAMING HYCAN",
    "Weibo": "WeiboGaming Faw Audi",
    "Invictus": "Invictus Gaming",
    "Top Esports": "TOPESPORTS",
    "ThunderTalk": "THUNDERTALKGAMING",
    "Dplus KIA Challengers": "DK Challengers",
    "Nongshim Academy": "NS Challengers",
    "DRX Challengers": "DRX Challengers",
    "KT Rolster Challengers": "kt Challengers",
    "DN Freecs": "DN FREECS",
    "Nongshim Redforce": "NONGSHIM RED FORCE",
    "BNK FearX": "BNK FEARX",
    "KT Rolster": "kt Rolster",
    "BoostGate": "BoostGate Espor",
    "The Forbidden Five": "The Forbidden Five",
    "Bushido Wildcats": "Bushido Wildcats",
    "Papara SuperMassive": "Papara SuperMassive",
    "Ramboot": "Ramboot Club",
    "ZETA": "ZETA Gaming",
    "Veni Vidi Vici": "Veni Vidi Vici",
    "GIANTX Pride": "GIANTX PRIDE",
    "Los Heretics": "Los Heretics",
    "Barca": "Barça Esports",
    "GameWard": "GameWard",
    "BDS Academy": "BDS Academy",
    "Joblife": "Joblife",
    "BK ROG": "BK ROG Esports",
    "Galions": "Galions",
    "Ici Japon Corp": "Ici Japon Corp",
    "Solary": "Solary",
    "Karmine Corp Blue": "Karmine Corp Blue",
    "Gentle Mates": "Gentle Mates",
    "Vitality.Bee":"Vitality.Bee",
    "ULF":"ULF ESPORTS",
    "BBL Dark Passage":"BBL Dark Passage",
    "Dplus KIA":"Dplus KIA",
    "DN Freecs Challengers":"DNF Challengers",
    "Gen.G Global Academy":"Gen.G Global Academy",
    "T1 Academy":"T1 Esports Academy",
    "OKSavingsBank BRION Challengers":"BRO Challengers",
    "BNK FearX Youth":"BNK FEARX Youth",
    "UCAM":"UCAM Esports",
    "Movistar KOI Fenix":"Movistar KOI Fénix",
    "Natus Vincere":"Natus Vincere",
    "Karmine Corp":"Karmine Corp",
    "Heretics":"Team Heretics",
    "Fnatic":"Fnatic",
    "100 Thieves":"100 Thieves",
    "FlyQuest":"FlyQuest",
    "Lyon":"LYON",
    "Liquid":"Team Liquid",
    "BDS":"Team BDS",
    "SK Gaming":"SK Gaming",
    "GIANTX":"GIANTX",
    "Dignitas":"Dignitas",
    "Cloud9":"Cloud9",
    "Vitality":"Team Vitality",
    "BK ROG": "BK ROG Esports",
    "Galions": "Galions",
    "Ici Japon Corp": "Ici Japon Corp",
    "Solary": "Solary",
    "Karmine Corp Blue": "Karmine Corp Blue",
    "Gentle Mates": "Gentle Mates",
    "Vitality.Bee":"Vitality.Bee",
    "ULF":"ULF ESPORTS",
    "BBL Dark Passage":"BBL Dark Passage",
    "Dplus KIA":"Dplus KIA",
    "DN Freecs Challengers":"DNF Challengers",
    "Gen.G Global Academy":"Gen.G Global Academy",
    "T1 Academy":"T1 Esports Academy",
    "OKSavingsBank BRION Challengers":"BRO Challengers",
    "BNK FearX Youth":"BNK FEARX Youth",
    "UCAM":"UCAM Esports",
    "Movistar KOI Fenix":"Movistar KOI Fénix",
    "LUA":"LUA Gaming",
    "Misa":"Misa Esports",
    "Besiktas":"Beşiktaş Esports",
    "DetonatioN FocusMe":"DetonatioN FocusMe",
    "Chiefs":"The Chiefs Esports Club",
    "CTBC Flying Oyster":"CTBC Flying Oyster",
    "TALON":"PSG Talon",
    "paiN":"paiN Gaming",
    "FURIA":"FURIA",
    "Isurus Estral":"Isurus",
    "Fluxo W7M":"Fluxo W7M",
    "Fukuoka SoftBank HAWKS":"Fukuoka SoftBank HAWKS gaming",
    "MGN Vikings":"MGN Vikings Esports",
    "GAM":"GAM Esports",
    "Secret Whales":"Team Secret Whales",
    "Leviatan":"LEVIATÁN",
    "Vivo Keyd Stars":"Vivo Keyd Stars",
    "LOUD":"LOUD",
    "RED Canids":"RED Kalunga",
    "Hanwha Life Challengers":"HLE Challengers"
}
ROLES = ["Top", "Jungle", "Mid", "Bot", "Support"]
SOURCE_SHEET_NAME = "LoL Matches sync"
HISTORY_WORKSHEET_NAME = "Лист2"
AUTO_PREDICTIONS_SHEET_NAME = "Auto Predictions"
COLUMN_INDICES = { "Timestamp": 0, "Team1": 1, "Team2": 2, "Team1Picks": 3, "Team2Picks": 4, "PredictedWinner": 5, "WinnerProb": 6, "Team1Odds": 7, "Team2Odds": 8, "ActualResult": 9, "TimestampResult": 10, "Comment": 11, "BetAmount": 12, "AggressiveBet": 13, "BalancedBet": 14, "ReliableBet": 15, "AggressivePL": 16, "BalancedPL": 17, "ReliablePL": 18, "Month": 19, "SkipReason": 20 }

API_TO_SHEET_CHAMP_MAP = {
    "Kaisa": "Kai'Sa", "KaiSa": "Kai'Sa", "TahmKench":"Tahm Kench", "MonkeyKing": "Wukong", "Leblanc": "LeBlanc",
    "Renata": "Renata Glasc", "XinZhao": "Xin Zhao", "MissFortune": "Miss Fortune", "Chogath": "Cho'Gath",
    "JarvanIV": "Jarvan IV", "LeeSin": "Lee Sin", "TwistedFate": "Twisted Fate", "Khazix": "Kha'Zix",
    "AurelionSol": "Aurelion Sol", "KSante": "K'Sante", "Ksante": "K'Sante", "KhaZix": "Kha'Zix",
    "RenataGlasc": "Renata Glasc", "Renataglasc": "Renata Glasc", "DrMundo": "Dr. Mundo"
}

# --- ПОДКЛЮЧЕНИЯ ---
# Этот блок полностью переписан для безопасной загрузки ключей
try:
    # --- ЗАГРУЗКА СЕКРЕТНЫХ КЛЮЧЕЙ ИЗ ОКРУЖЕНИЯ ---
    # Скрипт будет искать эти переменные в вашем .env файле (локально) или в настройках сервера
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    LOL_ESPORTS_API_KEY = os.environ.get("LOL_ESPORTS_API_KEY")
    ODDS_API_USER = os.environ.get("ODDS_API_USER")
    ODDS_API_PASS = os.environ.get("ODDS_API_PASS")
    TELEGRAM_CHAT_ID = -1002770534718 # ID чата можно оставить, это не секретная информация

    # Проверка, что все переменные успешно загрузились
    if not all([TELEGRAM_TOKEN, LOL_ESPORTS_API_KEY, ODDS_API_USER, ODDS_API_PASS]):
        print("CRITICAL ERROR: Не удалось загрузить одну или несколько переменных окружения.")
        print("Убедитесь, что TELEGRAM_TOKEN, LOL_ESPORTS_API_KEY, ODDS_API_USER, ODDS_API_PASS заданы в .env файле или на сервере.")
        sys.exit(1) # Выход из программы с кодом ошибки

    # Подключение к Google Sheets
    creds = ServiceAccountCredentials.from_json_keyfile_name(resource_path("credentials.json"), ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    sheet_file = client.open(SOURCE_SHEET_NAME)
    history_sheet = sheet_file.worksheet(HISTORY_WORKSHEET_NAME)
    try:
        auto_predictions_sheet = sheet_file.worksheet(AUTO_PREDICTIONS_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        print(f"WARNING: Лист '{AUTO_PREDICTIONS_SHEET_NAME}' не найден. Создание...")
        header = list(COLUMN_INDICES.keys()) + ["MatchID", "GameNumber"]
        auto_predictions_sheet = sheet_file.add_worksheet(title=AUTO_PREDICTIONS_SHEET_NAME, rows="1", cols=len(header))
        auto_predictions_sheet.append_row(header, value_input_option='USER_ENTERED')

    all_auto_preds = auto_predictions_sheet.get_all_values()[1:]
    processed_game_keys = {f"{row[21]}-{row[22]}" for row in all_auto_preds if len(row) > 22}
    print(f"INFO: Загружено {len(processed_game_keys)} уже обработанных ключей игр.")

    # Подключение к Telegram
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

except Exception as e:
    print(f"CRITICAL ERROR: Ошибка при инициализации подключений: {e}")
    traceback.print_exc()
    sys.exit()

# Конфигурация API с использованием загруженных ключей
LOL_ESPORTS_HEADERS = {"x-api-key": LOL_ESPORTS_API_KEY}
ODDS_API_AUTH = HTTPBasicAuth(ODDS_API_USER, ODDS_API_PASS)
ODDS_API_HEADERS = {"Accept": "application/json", "User-Agent": "MyParser/1.0"}


# --- ЛОГИКА РАСЧЕТОВ ---
# Дальше ваш файл остается без изменений...
# --- ЛОГИКА РАСЧЕТОВ ---
def calculate_betting_decisions(team1_prob, team2_prob, team1_odds, team2_odds):
    winner = "Team 1" if team1_prob > team2_prob else "Team 2"
    winner_prob = max(team1_prob, team2_prob)
    winner_odds = team1_odds if winner == "Team 1" else team2_odds
    advantage = abs(team1_prob - team2_prob)
    ev = (winner_prob / 100 * winner_odds) - 1 if winner_odds > 0 else -1
    decisions = {"Aggressive": {"bet": False}, "Balanced": {"bet": False}, "Reliable": {"bet": False}}
    if advantage < 4: return decisions, "Too small advantage, bet skipped"
    decisions["Aggressive"]["bet"] = advantage >= 4 and winner_odds >= 1.2
    decisions["Balanced"]["bet"] = advantage >= 6 and ev > 0.02
    decisions["Reliable"]["bet"] = advantage >= 9 and winner_odds >= 1.5
    skip_reason = "" if any(d["bet"] for d in decisions.values()) else "No strategy met conditions"
    return decisions, skip_reason

def calculate_role_pair_synergy(champion1, role_index1, champion2, role_index2, historical_data):
    pair_wins, pair_games = 0, 0
    blue_pick_col1, blue_pick_col2 = 5 + role_index1, 5 + role_index2
    red_pick_col1, red_pick_col2 = 10 + role_index1, 10 + role_index2
    if role_index1 == role_index2: return 50.0
    for row in historical_data:
        if len(row) <= max(blue_pick_col1, blue_pick_col2, red_pick_col1, red_pick_col2): continue
        blue_team, red_team, winner = row[2], row[3], row[4]
        if row[blue_pick_col1] == champion1 and row[blue_pick_col2] == champion2:
            pair_games += 1;
            if winner == blue_team: pair_wins += 1
        if row[red_pick_col1] == champion1 and row[red_pick_col2] == champion2:
            pair_games += 1;
            if winner == red_team: pair_wins += 1
    return (pair_wins / pair_games * 100) if pair_games > 0 else 50.0




def calculate_base_winrate(champion, role_index, role_data):
    champion_wins, champion_games = 0, 0
    blue_pick_col, red_pick_col = 5 + role_index, 10 + role_index
    for row in role_data:
        if len(row) <= max(blue_pick_col, red_pick_col): continue
        blue_team, red_team, winner = row[2], row[3], row[4]
        if row[blue_pick_col] == champion:
            champion_games += 1
            if winner == blue_team: champion_wins += 1
        if row[red_pick_col] == champion:
            champion_games += 1
            if winner == red_team: champion_wins += 1
    base_winrate = (champion_wins / champion_games * 100) if champion_games > 0 else 50.0
    return base_winrate, champion_games

def calculate_normalized_winrate(champion1, role_index1, champion2, role_index2, role_data):
    base_winrate, _ = calculate_base_winrate(champion1, role_index1, role_data)
    h2h_wins, h2h_games = 0, 0
    blue_pick_col1, red_pick_col1 = 5 + role_index1, 10 + role_index1
    blue_pick_col2, red_pick_col2 = 5 + role_index2, 10 + role_index2
    for row in role_data:
        if len(row) <= max(blue_pick_col1, red_pick_col1, blue_pick_col2, red_pick_col2): continue
        blue_team, red_team, winner = row[2], row[3], row[4]
        if row[blue_pick_col1] == champion1 and row[red_pick_col2] == champion2:
            h2h_games += 1;
            if winner == blue_team: h2h_wins += 1
        elif row[red_pick_col1] == champion1 and row[blue_pick_col2] == champion2:
            h2h_games += 1;
            if winner == red_team: h2h_wins += 1
    h2h_winrate = (h2h_wins / h2h_games * 100) if h2h_games > 0 else base_winrate
    all_wins, all_games = 0, 0
    for row in role_data:
        if len(row) <= max(blue_pick_col1, red_pick_col1, blue_pick_col2, red_pick_col2): continue
        blue_team, red_team, winner = row[2], row[3], row[4]
        if row[blue_pick_col1] == champion1:
            opponent_in_role2 = row[red_pick_col2]
            if opponent_in_role2 and opponent_in_role2 != "TBD":
                all_games += 1;
                if winner == blue_team: all_wins += 1
        elif row[red_pick_col1] == champion1:
            opponent_in_role2 = row[blue_pick_col2]
            if opponent_in_role2 and opponent_in_role2 != "TBD":
                all_games += 1;
                if winner == red_team: all_wins += 1
    all_winrate = (all_wins / all_games * 100) if all_games > 0 else base_winrate
    return (h2h_winrate * 0.5 + all_winrate * 0.5)

def calculate_team_win_probability_with_synergy(team1, team2, team1_picks, team2_picks, historical_data):
    if not historical_data: return 50.0, 50.0, "N/A", 0.0, [50.0] * 5, [50.0] * 5, {}, {}
    team1_norm_winrates, team2_norm_winrates = [], []
    team1_base_winrates_for_tg, team2_base_winrates_for_tg = [], []
    team1_games_played, team2_games_played = {}, {}
    for i, champ1 in enumerate(team1_picks):
        base_win1, champ1_games = calculate_base_winrate(champ1, i, historical_data)
        team1_base_winrates_for_tg.append(base_win1)
        team1_games_played[champ1] = champ1_games
        norm_wins_vs_team2 = [calculate_normalized_winrate(champ1, i, champ2, j, historical_data) for j, champ2 in enumerate(team2_picks)]
        avg_norm_win1 = sum(norm_wins_vs_team2) / len(norm_wins_vs_team2) if norm_wins_vs_team2 else base_win1
        team1_norm_winrates.append(avg_norm_win1)
    for j, champ2 in enumerate(team2_picks):
        base_win2, champ2_games = calculate_base_winrate(champ2, j, historical_data)
        team2_base_winrates_for_tg.append(base_win2)
        team2_games_played[champ2] = champ2_games
        norm_wins_vs_team1 = [calculate_normalized_winrate(champ2, j, champ1, i, historical_data) for i, champ1 in enumerate(team1_picks)]
        avg_norm_win2 = sum(norm_wins_vs_team1) / len(norm_wins_vs_team1) if norm_wins_vs_team1 else base_win2
        team2_norm_winrates.append(avg_norm_win2)
    team1_matchup_score = sum(team1_norm_winrates) / len(team1_norm_winrates) if team1_norm_winrates else 50.0
    team2_matchup_score = sum(team2_norm_winrates) / len(team2_norm_winrates) if team2_norm_winrates else 50.0
    role_pairs = [(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]
    team1_synergy_scores = [calculate_role_pair_synergy(team1_picks[i], i, team1_picks[j], j, historical_data) for i, j in role_pairs]
    avg_team1_synergy = sum(team1_synergy_scores) / len(team1_synergy_scores) if team1_synergy_scores else 50.0
    team2_synergy_scores = [calculate_role_pair_synergy(team2_picks[i], i, team2_picks[j], j, historical_data) for i, j in role_pairs]
    avg_team2_synergy = sum(team2_synergy_scores) / len(team2_synergy_scores) if team2_synergy_scores else 50.0
    team1_combined_score = (team1_matchup_score + avg_team1_synergy) / 2
    team2_combined_score = (team2_matchup_score + avg_team2_synergy) / 2
    total_combined = team1_combined_score + team2_combined_score
    if total_combined == 0: total_combined = 1
    team1_prob = (team1_combined_score / total_combined) * 100
    team2_prob = 100 - team1_prob
    winner = team1 if team1_prob > team2_prob else team2
    winner_prob = max(team1_prob, team2_prob)
    return team1_prob, team2_prob, winner, winner_prob, team1_base_winrates_for_tg, team2_base_winrates_for_tg, team1_games_played, team2_games_played

# --- ФУНКЦИИ МОНИТОРИНГА ---
def get_msi_schedule(target_schedule_name):
    print(f"MONITOR: Запрашиваю расписание для '{target_schedule_name}'..."); 
    url="https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=ru-RU"
    try:
        r=requests.get(url,headers=LOL_ESPORTS_HEADERS, timeout=15); r.raise_for_status()
        events=r.json().get('data',{}).get('schedule',{}).get('events',[])
        # БЫЛО: if e.get('league',{}).get('name')==SCHEDULE_LEAGUE_NAME
        matches=[{"id":e['match']['id'],"team1":e['match']['teams'][0].get('name','TBD'),"team2":e['match']['teams'][1].get('name','TBD')} for e in events if e.get('league',{}).get('name') == target_schedule_name and e.get('match') and len(e['match'].get('teams',[]))>=2]
        print(f"MONITOR: Найдено {len(matches)} матчей в расписании для '{target_schedule_name}'."); return matches
    except Exception as e: print(f"MONITOR ERROR (get_msi_schedule): {e}"); return []

def get_msi_odds(target_odds_name):
    print(f"MONITOR: Запрашиваю кэфы для '{target_odds_name}'..."); 
    api_url="https://www.twilightspire11.xyz/sports-service/sv/odds/events?sp=12"
    odds={};
    try:
        r=requests.get(api_url,auth=ODDS_API_AUTH,headers=ODDS_API_HEADERS,timeout=20); r.raise_for_status()
        es_data=next((s for s in r.json().get('n',[]) if s[0]==12),None)
        if not es_data: return {}
        # БЫЛО: if l[1]==ODDS_LEAGUE_NAME
        msi_l=next((l for l in es_data[2] if l[1] == target_odds_name),None)
        if not msi_l: return {}
        for ev in msi_l[2]:
            if "(Kills)" in ev[1]: continue
            t1,t2=ev[1].strip(),ev[2].strip()
            ct1,ct2=TEAM_NAME_MAPPING.get(t1,t1),TEAM_NAME_MAPPING.get(t2,t2)
            mo,p={},ev[8]
            for mk in sorted([k for k in p.keys() if k.isdigit() and k!='0']):
                try:
                    md=p[mk][2]
                    # --- ГЛАВНОЕ ИСПРАВЛЕНИЕ ЗДЕСЬ ---
                    # md[1] - home, md[0] - away. Храним как (home, away).
                    if md and len(md)>=2: mo[int(mk)]=(float(md[1]),float(md[0]))
                except (IndexError, TypeError, KeyError, ValueError): continue
            if mo: odds[(ct1,ct2)]=mo
        print(f"MONITOR: Найдено {len(odds)} матчей с кэфами на карты."); return odds
    except Exception as e: print(f"MONITOR ERROR (get_msi_odds): {e}"); return {}

def get_match_details(match_id):
    """Возвращает полный объект event от API, содержащий всю информацию о матче."""
    url = f"https://esports-api.lolesports.com/persisted/gw/getEventDetails?hl=ru-RU&id={match_id}"
    try:
        response = requests.get(url, headers=LOL_ESPORTS_HEADERS, timeout=15); response.raise_for_status()
        event_data = response.json().get("data", {}).get("event", {})
        if not event_data:
            print(f"MONITOR ERROR: Не найдены данные 'event' для {match_id}")
            return None
        return event_data
    except Exception as e:
        print(f"MONITOR ERROR (get_match_details) for {match_id}: {e}.")
        return None

def check_and_get_draft(gid):
    """
    Делает ОДНУ попытку получить драфт.
    Возвращает ID команд и их пики.
    """
    url = f"https://feed.lolesports.com/livestats/v1/window/{gid}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            game_metadata = data.get('gameMetadata', {})
            blue_team_meta = game_metadata.get('blueTeamMetadata')
            red_team_meta = game_metadata.get('redTeamMetadata')

            if blue_team_meta and red_team_meta:
                # --- ИЗВЛЕКАЕМ ID КОМАНД НАПРЯМУЮ ---
                blue_team_id = blue_team_meta.get('esportsTeamId')
                red_team_id = red_team_meta.get('esportsTeamId')
                
                blue_participants = blue_team_meta.get('participantMetadata', [])
                red_participants = red_team_meta.get('participantMetadata', [])
                
                blue_api_picks = [p['championId'] for p in blue_participants]
                red_api_picks = [p['championId'] for p in red_participants]
                
                blue_sheet_picks = [API_TO_SHEET_CHAMP_MAP.get(p, p) for p in blue_api_picks]
                red_sheet_picks = [API_TO_SHEET_CHAMP_MAP.get(p, p) for p in red_api_picks]
                
                if blue_team_id and red_team_id and len(blue_sheet_picks) == 5 and len(red_sheet_picks) == 5:
                    print(f"MONITOR: Драфт {gid} успешно получен!")
                    return blue_team_id, blue_sheet_picks, red_team_id, red_sheet_picks
    except requests.exceptions.RequestException as e:
        print(f"MONITOR ERROR (check_draft): {e}.")
    
    return None, None, None, None
def main_loop():
    print(f"\n{'='*25} ЗАПУСК НОВОГО ЦИКЛА МОНИТОРИНГА {'='*25}")
    print(f"Время запуска: {datetime.now():%Y-%m-%d %H:%M:%S}")

    # ИЗМЕНЕНИЕ: Мы возвращаем использование папки cache
    os.makedirs("cache", exist_ok=True)

    found_active_game_to_track_overall = False

    try:
        h_data = history_sheet.get_all_values()[1:]
    except Exception as e:
        print(f"CRITICAL: Не удалось загрузить историю матчей: {e}.")
        return False

    for schedule_name, odds_name in LEAGUES_TO_MONITOR.items():
        print(f"\n{'='*15} ОБРАБОТКА ТУРНИРА: {schedule_name} {'='*15}")

        scheduled_matches = get_msi_schedule(schedule_name)
        if not scheduled_matches:
            continue

        # Запрашиваем ВСЕ актуальные кэфы для лиги один раз за цикл
        all_live_odds_data = get_msi_odds(odds_name)

        for match in scheduled_matches:
            match_id, schedule_t1, schedule_t2 = match['id'], match['team1'].strip(), match['team2'].strip()
            if "TBD" in schedule_t1 or "TBD" in schedule_t2: continue

            # --- НАЧАЛО НОВОЙ ЛОГИКИ УМНОГО КЭШИРОВАНИЯ ---
            cache_path = os.path.join("cache", f"{match_id}.json")
            cached_data = {}
            
            # 1. Загружаем данные из кэша, если они есть
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'r') as f:
                        cached_data = json.load(f)
                except Exception as e:
                    print(f"WARNING: Ошибка чтения кэша {cache_path}: {e}")
                    cached_data = {}

            # 2. Ищем свежие кэфы для этого матча в данных с API
            live_odds_for_match = all_live_odds_data.get((schedule_t1, schedule_t2))
            swapped_odds = cached_data.get("swapped", False) # По умолчанию берем из кэша
            
            if not live_odds_for_match:
                live_odds_for_match = all_live_odds_data.get((schedule_t2, schedule_t1))
                if live_odds_for_match:
                    swapped_odds = True # Если нашли в обратном порядке, флаг в True
            else:
                 swapped_odds = False # Если нашли в прямом порядке, флаг в False

            # 3. Объединяем кэш и свежие данные
            # Сначала берем то, что было в кэше
            final_match_odds = cached_data.get("odds", {})
            # Затем обновляем/дополняем свежими данными из API.
            if live_odds_for_match:
                # Конвертируем ключи из live_odds_for_match в строки для консистентности с JSON
                live_odds_for_match_str_keys = {str(k): v for k, v in live_odds_for_match.items()}
                final_match_odds.update(live_odds_for_match_str_keys)

            # 4. Сохраняем обновленный кэш обратно в файл
            if final_match_odds: # Сохраняем, только если есть хоть какие-то кэфы
                try:
                    with open(cache_path, 'w') as f:
                        json.dump({"odds": final_match_odds, "swapped": swapped_odds}, f, indent=4)
                except Exception as e:
                    print(f"WARNING: Не удалось сохранить обновленный кэш для {match_id}: {e}")
            
            # Если после всех манипуляций кэфов нет, пропускаем матч
            if not final_match_odds:
                continue
            
            # Конвертируем ключи обратно в int для работы в коде
            match_odds_by_map = {int(k): v for k, v in final_match_odds.items()}
            # --- КОНЕЦ НОВОЙ ЛОГИКИ УМНОГО КЭШИРОВАНИЯ ---

            event_data = get_match_details(match_id)
            if not event_data or event_data.get("state") == "completed":
                continue

            print(f"\n{'~'*60}")
            print(f"--- [ШАГ 1] Обработка матча: {schedule_t1} vs {schedule_t2} (ID: {match_id}) ---")
            
            match_data = event_data.get("match", {})
            id_to_name_map = {team['id']: team['name'] for team in match_data.get('teams', [])}

            for i, game_info in enumerate(match_data.get("games", [])):
                gn, gid = i + 1, game_info.get('id')
                gk = f"{match_id}-{gn}"
                
                if gk in processed_game_keys or game_info.get('state') == 'unneeded':
                    continue

                if gn not in match_odds_by_map:
                    continue

                print(f"\n--- [ШАГ 2] Проверка Карты {gn} (GameID: {gid}) ---")
                found_active_game_to_track_overall = True
                
                draft_data = check_and_get_draft(gid)
                if not draft_data[0]:
                    print(f"LOG: Драфт для карты {gn} ({gid}) еще не готов.")
                    continue 

                print(f"--- [ШАГ 3] Найдена и обрабатывается карта: {gn} (GameID: {gid}) ---")
                blue_team_id, blue_picks, red_team_id, red_picks = draft_data
                
                blue_team_name = id_to_name_map.get(blue_team_id, "").strip()
                red_team_name = id_to_name_map.get(red_team_id, "").strip()

                if not blue_team_name or not red_team_name:
                    print(f"CRITICAL: Не удалось найти полное имя для ID '{blue_team_id}' или '{red_team_id}'.")
                    continue
                
                print(f"LOG: Фактическое распределение сторон (по ID из драфта): СИНИЕ='{blue_team_name}', КРАСНЫЕ='{red_team_name}'")
                
                map_odds_pair = match_odds_by_map.get(gn)
                original_home_odds, original_away_odds = map_odds_pair[0], map_odds_pair[1]
                if swapped_odds: home_team_for_odds, away_team_for_odds = schedule_t2, schedule_t1
                else: home_team_for_odds, away_team_for_odds = schedule_t1, schedule_t2
                
                print(f"LOG: Исходные кэфы на Карту {gn}: '{home_team_for_odds}' (Home) = {original_home_odds}, '{away_team_for_odds}' (Away) = {original_away_odds}")

                if blue_team_name == home_team_for_odds: 
                    blue_team_odds, red_team_odds = original_home_odds, original_away_odds
                elif blue_team_name == away_team_for_odds: 
                    blue_team_odds, red_team_odds = original_away_odds, original_home_odds
                else:
                    print(f"CRITICAL: Несоответствие имен при присвоении кэфов! Blue Team: '{blue_team_name}', Home: '{home_team_for_odds}', Away: '{away_team_for_odds}'")
                    continue
                
                t1p, t2p, w, wp, t1_br, t2_br, t1_games, t2_games = calculate_team_win_probability_with_synergy(blue_team_name, red_team_name, blue_picks, red_picks, h_data)
                decs, skip_r_bets = calculate_betting_decisions(t1p, t2p, blue_team_odds, red_team_odds)
                insuff_champs = [f"{ch}({g})" for ch, g in {**t1_games, **t2_games}.items() if g < 10]
                skip_data = bool(insuff_champs)
                skip_reason_data = f"Мало данных (<10): " + ", ".join(insuff_champs) if skip_data else ""
                is_skip = skip_data or not any(d["bet"] for d in decs.values())
                skip_r = skip_reason_data if skip_data else skip_r_bets
                
                bet_amount = 1000.0
                winner_odds = blue_team_odds if w == blue_team_name else red_team_odds
                advantage = abs(t1p - t2p)
                if not is_skip and winner_odds < 1.8 and advantage >= 10: bet_amount = 2000.0

                if schedule_t1 == blue_team_name:
                    final_t1, final_t2, final_p1, final_p2, final_t1o, final_t2o, final_t1p, final_t2p, final_w, final_wp, final_t1_br, final_t2_br = blue_team_name, red_team_name, blue_picks, red_picks, blue_team_odds, red_team_odds, t1p, t2p, w, wp, t1_br, t2_br
                else:
                    final_t1, final_t2, final_p1, final_p2, final_t1o, final_t2o, final_t1p, final_t2p, final_w, final_wp, final_t1_br, final_t2_br = red_team_name, blue_team_name, red_picks, blue_picks, red_team_odds, blue_team_odds, t2p, t1p, w, wp, t2_br, t1_br
                
                ts, cm = datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime("%Y-%m")
                row = [""] * (len(COLUMN_INDICES) + 2)
                row[COLUMN_INDICES["Timestamp"]] = ts
                row[COLUMN_INDICES["Team1"]] = final_t1
                row[COLUMN_INDICES["Team2"]] = final_t2
                row[COLUMN_INDICES["Team1Picks"]] = ",".join(final_p1)
                row[COLUMN_INDICES["Team2Picks"]] = ",".join(final_p2)
                row[COLUMN_INDICES["PredictedWinner"]] = final_w if not is_skip else "N/A (Пропуск)"
                row[COLUMN_INDICES["WinnerProb"]] = f"{final_wp:.2f}" if not is_skip else "N/A"
                row[COLUMN_INDICES["Team1Odds"]] = str(final_t1o)
                row[COLUMN_INDICES["Team2Odds"]] = str(final_t2o)
                row[COLUMN_INDICES["Comment"]] = f"Auto-prediction Map {gn}"
                row[COLUMN_INDICES["BetAmount"]] = str(bet_amount)
                row[COLUMN_INDICES["AggressiveBet"]] = str(decs["Aggressive"]["bet"] and not is_skip)
                row[COLUMN_INDICES["BalancedBet"]] = str(decs["Balanced"]["bet"] and not is_skip)
                row[COLUMN_INDICES["ReliableBet"]] = str(decs["Reliable"]["bet"] and not is_skip)
                row[COLUMN_INDICES["Month"]] = cm
                row[COLUMN_INDICES["SkipReason"]] = skip_r if is_skip else ""
                row[len(COLUMN_INDICES)] = match_id
                row[len(COLUMN_INDICES) + 1] = gn
                auto_predictions_sheet.append_row(row, value_input_option='USER_ENTERED')
                processed_game_keys.add(gk)
                print(f"LOG: Анализ Карты {gn} успешно добавлен в 'Auto Predictions'.")

                st1, st2, sw = html.escape(final_t1), html.escape(final_t2), html.escape(final_w)
                msg = f" {st1} ({final_t1o}) vs {st2} ({final_t2o})\n\n"
                msg += f"Пики {st1}:\n"
                if len(final_p1) == 5 and len(final_t1_br) == 5:
                    for i_msg, champ in enumerate(final_p1): msg += f"  {ROLES[i_msg]}: {html.escape(champ)} ({final_t1_br[i_msg]:.1f}%)\n"
                msg += f"\nПики {st2}:\n"
                if len(final_p2) == 5 and len(final_t2_br) == 5:
                    for i_msg, champ in enumerate(final_p2): msg += f"  {ROLES[i_msg]}: {html.escape(champ)} ({final_t2_br[i_msg]:.1f}%)\n"
                msg += f"\n{'-'*20}\n\n--- Прогноз ---\n"
                msg += f" Прогноз: {st1} {final_t1p:.1f}% | {st2} {final_t2p:.1f}%\n"

                if is_skip:
                    msg += f"❗️<b>Пропуск ставки:</b> {html.escape(skip_r)}\n"
                else:
                    msg += f"Победитель: <b>{sw}</b>\n"
                    bets_s = ",".join([s for s, k in [("A", "Aggressive"), ("B", "Balanced"), ("R", "Reliable")] if decs[k]["bet"]])
                    bet_size_text = "двойная" if bet_amount == 2000.0 else "стандартная"
                    msg += f"Ставки: {bets_s} ({bet_size_text})\n"

                if bot:
                    try:
                        bot.send_message(TELEGRAM_CHAT_ID, msg, parse_mode='HTML')
                    except Exception as e:
                        print(f"CRITICAL: Ошибка отправки в Telegram: {e}")

    print(f"\n{'='*25} ЦИКЛ МОНИТОРИНГА ЗАВЕРШЕН {'='*25}")
    return found_active_game_to_track_overall


def run_monitoring():
    # Блок очистки кэша полностью удален, так как кэш должен быть постоянным.

    # Далее идет ваш основной код, который будет работать в цикле
    SLOW_POLL_INTERVAL = 300  # 5 минут - медленный режим
    FAST_POLL_INTERVAL = 10   # 10 секунд - быстрый режим
    is_tracking_active_game = False

    while True:
        try:
            is_tracking_active_game = main_loop()
        except Exception as e:
            print(f"MONITOR CRITICAL (Global): Произошла критическая ошибка в главном цикле: {e}")
            traceback.print_exc()
            is_tracking_active_game = False

        if is_tracking_active_game:
            current_interval = FAST_POLL_INTERVAL
            print(f"\nMONITOR: Найден активный матч. Переход в быстрый режим.")
        else:
            current_interval = SLOW_POLL_INTERVAL
            print(f"\nMONITOR: Активных матчей нет. Переход в медленный режим.")

        print(f"MONITOR: Пауза на {current_interval} секунд до следующего цикла.")
        time.sleep(current_interval)


if __name__ == "__main__":
    # Создаем мини-веб-сервер
    app = Flask(__name__)

    @app.route('/')
    def health_check():
        # Эта функция будет отвечать на запросы от Render и UptimeRobot
        return "Monitoring service is running.", 200

    # Запускаем основной цикл мониторинга в отдельном фоновом потоке
    monitor_thread = Thread(target=run_monitoring)
    monitor_thread.daemon = True # Позволяет основному процессу завершаться
    monitor_thread.start()

    # Запускаем веб-сервер, который будет держать сервис "живым" для Render
    # Render автоматически предоставит переменную PORT
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)