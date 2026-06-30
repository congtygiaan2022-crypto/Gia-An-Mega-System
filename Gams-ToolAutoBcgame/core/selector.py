"""
Selector - Lựa chọn trận đấu và Khớp tên (Fuzzy Matching)
"""
import random
import json
import os
import re
from typing import List, Dict, Optional
from thefuzz import fuzz
from loguru import logger

# Hậu tố phổ biến cần loại bỏ khi so khớp
_STRIP_SUFFIXES = [
    r'\bFC\b', r'\bCF\b', r'\bSC\b', r'\bFK\b', r'\bAC\b', r'\bRC\b',
    r'\bBK\b', r'\bIF\b', r'\bAF\b', r'\bRFC\b', r'\bAFC\b',
    r'\(KSA\)', r'\(URU\)', r'\(ARG\)', r'\(BRA\)', r'\(CHN\)',
    r'\(VIE\)', r'\(VNM\)', r'\(PHB\)', r'\(TBNB\)',
    r'\bF\.C\.\b', r'\bA\.C\.\b',
]

import unicodedata

# Từ điển dịch tên diacritic-stripped
TRANSLATIONS = {
    "viet nam": "vietnam",
    "saudi arabia": "saudi arabia",
    "sa-u-di a-ra-bi-a": "saudi arabia",
    "a rap saudi": "saudi arabia",
    "saudi": "saudi arabia",
    "a rap xe ut": "saudi arabia",
    "campuchia": "cambodia",
    "ma roc": "morocco",
    "bo dao nha": "portugal",
    "tay ban nha": "spain",
    "cong hoa sec": "czech republic",
    "nam phi": "south africa",
    "bac ireland": "northern ireland",
    "han quoc": "south korea",
    "nhat ban": "japan",
    "trung quoc": "china",
    "thai lan": "thailand",
    "singapore": "singapore",
    "malaysia": "malaysia",
    "indonesia": "indonesia",
    "philippines": "philippines",
    "tuyen quoc gia": "national team",
    "doi tuyen": "national team",
    "tuyen": "national",
    "thuy dien": "sweden",
    "y": "italy",
    "bi": "belgium",
    "duc": "germany",
    "phap": "france",
    "anh": "england",
    "ha lan": "netherlands",
    "thuy si": "switzerland",
    "dan mach": "denmark",
    "na uy": "norway",
    "phan lan": "finland",
    "ao": "austria",
    "uc": "australia",
    "my": "usa",
    "hoa ky": "usa",
    "nga": "russia",
    "tho nhi ky": "turkey",
    "hy lap": "greece",
    "croatia": "croatia",
    "ukraina": "ukraine",
    "ucraina": "ukraine",
    "ba lan": "poland",
    "sec": "czech",
    "slovakia": "slovakia",
    "hungary": "hungary",
    "rumani": "romania",
    "bulgaria": "bulgaria",
    "wales": "wales",
    "scotland": "scotland",
    "ireland": "ireland",
    "mexico": "mexico",
    "ai cap": "egypt",
    "maroc": "morocco",
    "algeria": "algeria",
    "nigeria": "nigeria",
    "cameroon": "cameroon",
    "ghana": "ghana",
    "senegal": "senegal",
    
    # Clubs
    "ha noi": "ha noi",
    "hai phong": "hai phong",
    "viettel": "the cong viettel",
    "nam dinh": "nam dinh",
    "hoang anh gia lai": "hoang anh gia lai",
    "hagl": "hoang anh gia lai",
    "mu": "manchester united",
    "m.u": "manchester united",
    "man utd": "manchester united",
    "manchester utd": "manchester united",
    "mc": "manchester city",
    "m.c": "manchester city",
    "man city": "manchester city",
    "munchen": "munich",
    "at. madrid": "atletico madrid",
    "r. madrid": "real madrid",
    "barca": "barcelona",
    "fc barcelona": "barcelona",
    "internazionale": "inter milan",
    "ac milan": "milan",
    "juve": "juventus",
    "psg": "paris saint germain",
    "tottenham": "tottenham hotspur",
    "spurs": "tottenham hotspur",
    "wolves": "wolverhampton",
    "west ham": "west ham united",
    
    # Keywords
    "nu": "women",
    "nam": "men",
    "tre": "youth"
}

def strip_diacritics(text: str) -> str:
    """Loại bỏ dấu tiếng Việt"""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text

def normalize_name(name: str) -> str:
    """Chuẩn hóa tên đội bóng: dịch, loại bỏ dấu tiếng Việt, loại hậu tố, dấu câu, khoảng trắng thừa"""
    s = strip_diacritics(name).lower().strip()
    
    # Dịch các từ/cụm từ (sử dụng khớp từ hoàn chỉnh để tránh double-replacement)
    sorted_keys = sorted(TRANSLATIONS.keys(), key=len, reverse=True)
    for k in sorted_keys:
        v = TRANSLATIONS[k]
        pattern = r'(?<![a-z0-9_])' + re.escape(k) + r'(?![a-z0-9_])'
        s = re.sub(pattern, v, s)
        
    for pat in _STRIP_SUFFIXES:
        s = re.sub(pat, '', s, flags=re.IGNORECASE)
    # Loại dấu câu thừa
    s = re.sub(r'[\(\)\[\]\-_\.]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

class MatchSelector:
    """Xử lý chọn trận ngẫu nhiên và khớp tên đội bóng"""
    
    def __init__(self, dictionary_path: str = "data/name_dictionary.json"):
        if not os.path.isabs(dictionary_path):
            _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dictionary_path = os.path.join(_root, dictionary_path)
        self.dictionary_path = dictionary_path
        self.name_map = self._load_dictionary()

    def _load_dictionary(self) -> Dict:
        """Tải từ điển ánh xạ tên đội bóng"""
        if os.path.exists(self.dictionary_path):
            try:
                with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Lỗi tải từ điển tên: {e}")
        return {}

    def save_dictionary(self):
        """Lưu từ điển ánh xạ tên đội bóng"""
        try:
            os.makedirs(os.path.dirname(self.dictionary_path), exist_ok=True)
            with open(self.dictionary_path, 'w', encoding='utf-8') as f:
                json.dump(self.name_map, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Lỗi lưu từ điển tên: {e}")

    def pick_random_match(self, matches: List[Dict]) -> Optional[Dict]:
        """Chọn ngẫu nhiên 1 trận từ danh sách"""
        if not matches:
            return None
        return random.choice(matches)

    def is_match_similar(self, wap_home: str, wap_away: str, bc_home: str, bc_away: str, threshold: int = 65) -> bool:
        """So khớp tên đội bóng thông minh với nhiều chiến lược"""
        
        # 1. Kiểm tra qua từ điển trước (Nhanh nhất)
        wap_home_mapped = self.name_map.get(wap_home, wap_home)
        wap_away_mapped = self.name_map.get(wap_away, wap_away)
        if wap_home_mapped.lower() == bc_home.lower() and wap_away_mapped.lower() == bc_away.lower():
            return True

        # 2. Chuẩn hóa tên
        n_wh = normalize_name(wap_home)
        n_wa = normalize_name(wap_away)
        n_bh = normalize_name(bc_home)
        n_ba = normalize_name(bc_away)

        # 3. Kiểm tra lệch U-phân khúc (Tuổi)
        def get_age_category(name: str) -> str:
            # Tìm u15, u16, u17, u18, u19, u20, u21, u23, u-21, u-19, etc.
            u_match = re.search(r'\bu-?(\d{2})\b', name)
            if u_match:
                return f"u{u_match.group(1)}"
            if 'youth' in name or 'tre' in name:
                return 'youth'
            if 'reserve' in name:
                return 'reserve'
            return 'senior'

        age_wh = get_age_category(n_wh)
        age_wa = get_age_category(n_wa)
        age_bh = get_age_category(n_bh)
        age_ba = get_age_category(n_ba)

        # Trận đấu phải cùng độ tuổi cho từng cặp
        age_ok = (age_wh == age_bh) and (age_wa == age_ba)
        age_ok_rev = (age_wh == age_ba) and (age_wa == age_bh)

        # 4. Kiểm tra lệch Giới tính
        def is_women(name: str) -> bool:
            return 'women' in name or 'female' in name or 'nu' in name

        w_wh = is_women(n_wh)
        w_wa = is_women(n_wa)
        w_bh = is_women(n_bh)
        w_ba = is_women(n_ba)

        gender_ok = (w_wh == w_bh) and (w_wa == w_ba)
        gender_ok_rev = (w_wh == w_ba) and (w_wa == w_bh)

        def _score_pair(a1, a2, b1, b2):
            """Tính điểm so khớp cho một cặp (wap vs bc)"""
            s1 = fuzz.token_sort_ratio(a1, b1)
            s2 = fuzz.token_sort_ratio(a2, b2)
            
            # Chỉ dùng containment/partial_ratio nếu từ đó đủ dài và không bị trùng lặp từ phân biệt
            # E.g. tránh Manchester United vs Manchester City
            def _is_valid_substring(short_n, long_n):
                if short_n in long_n and len(short_n) >= 4:
                    dist_words = ['united', 'city', 'town', 'rovers', 'wanderers', 'county', 'athletic', 'real', 'inter', 'hotspur', 'sporting', 'union']
                    for w in dist_words:
                        if (w in short_n) != (w in long_n):
                            return False
                    return True
                return False

            c1 = 100 if _is_valid_substring(a1, b1) or _is_valid_substring(b1, a1) else 0
            c2 = 100 if _is_valid_substring(a2, b2) or _is_valid_substring(b2, a2) else 0

            # partial_ratio cũng phải kiểm tra chống trùng lặp
            p1 = fuzz.partial_ratio(a1, b1)
            p2 = fuzz.partial_ratio(a2, b2)
            # Nếu partial_ratio cao nhưng token_sort_ratio quá thấp (ví dụ lệch hẳn 1 từ phân biệt), hạ điểm
            if p1 >= 85 and s1 < 50:
                p1 = s1
            if p2 >= 85 and s2 < 50:
                p2 = s2

            h_score = max(s1, p1, c1)
            a_score = max(s2, p2, c2)
            return h_score, a_score

        # Chiến lược thuận
        h, a = _score_pair(n_wh, n_wa, n_bh, n_ba)
        # Chiến lược đảo ngược
        h_rev, a_rev = _score_pair(n_wh, n_wa, n_ba, n_bh)

        matched = False
        if age_ok and gender_ok and h >= threshold and a >= threshold:
            matched = True
            self.name_map[wap_home] = bc_home
            self.name_map[wap_away] = bc_away
        elif age_ok_rev and gender_ok_rev and h_rev >= threshold and a_rev >= threshold:
            matched = True
            self.name_map[wap_home] = bc_away
            self.name_map[wap_away] = bc_home

        if matched:
            logger.info(f"✅ KHỚP: '{wap_home}' ≈ '{bc_home}' ({h}%) | '{wap_away}' ≈ '{bc_away}' ({a}%)")
            self.save_dictionary()
        
        return matched

    def find_best_match_in_list(self, target_home: str, target_away: str, candidate_matches: List[Dict], threshold: int = 75) -> Optional[Dict]:
        """Tìm trận đấu phù hợp nhất trong danh sách dựa trên tên đội"""
        best_match = None
        highest_avg_score = 0

        if not candidate_matches:
            return None

        for cand in candidate_matches:
            cand_home = cand.get('home_team', '')
            cand_away = cand.get('away_team', '')
            
            # Sử dụng is_match_similar để đảm bảo độ chính xác (tuổi, giới tính, chống trùng lặp)
            if self.is_match_similar(target_home, target_away, cand_home, cand_away, threshold=threshold):
                # Tính điểm trung bình để chọn cái tốt nhất nếu có nhiều ứng cử viên
                s_home = fuzz.token_sort_ratio(normalize_name(target_home), normalize_name(cand_home))
                s_away = fuzz.token_sort_ratio(normalize_name(target_away), normalize_name(cand_away))
                avg = (s_home + s_away) / 2
                
                if avg > highest_avg_score:
                    highest_avg_score = avg
                    best_match = cand
                    
        return best_match
