COL_DICT = {
    "OGRENCI_NO": "std_id",
    "ADI": "std_name",
    "SOYADI": "std_surname",
    "KIMLIK_NO": "std_tc",
    "OKUDUGU_SINIF": "std_year",
    "OZEL_KOD": "course_code",
    "DERS_ADI": "course_name",
    "DERSI_ALDIGI_BOLUM": "course_dept",
    "DERSI_ALDIGI_SUBESI": "course_section",
    "DERSLIK_ADI": "classroom",
    "DERSI_ALDIGI_GUN": "course_day",
    "DERSI_ALDIGI_SAAT_ARALIGI": "course_session",
    "MAIL": "std_email",
    "OGRETIM_UYESI_ADI": "course_instructor",
    "DERS_TURU": "course_type",
    "TEKRAR_SAYISI": "repeat",
    "FINAL_NOTU": "final",
    "DEVAM_DURUMU": "attendance",
    "DURUMU": "status",
    "BASARI_NOTU": "grade",
}

DEPT_DICT = {
    "Turizm İşletmeciliği": "TMT",
    "Uluslararası İlişkiler": "IRE",
    "İşletme": "BUS",
    "İktisat": "ECO",
    "Uluslararası İşletmecilik ve Ticaret": "IBS",
    "İşletme (UOLP-SUNY-Albany)": "BUSS",
    "İktisat (UOLP-SUNY-Albany)": "ECOS",
    "Uluslararası İlişkiler (UOLP-SUNY- Albany)": "IRES",
}


DEPTID_DICT = {
    1: "ECO",
    2: "BUS",
    3: "IRE",
    4: "IBS",
    5: "TMT",
    6: "BUSS",
    7: "ECOS",
    8: "IRES",
}

DEPTID_LONG_DICT = {
    431: "ECO",
    432: "BUS",
    433: "IRE",
    434: "IBS",
    435: "TMT",
    436: "BUSS",
    437: "ECOS",
    438: "IRES",
}

REQUIRED_COLS = [
    "std_id",
    "std_tc",
    "course_code",
    "course_name",
    "course_dept",
    "course_instructor",
    "course_section",
    "std_name",
    "std_surname",
]

TURKISH_CHAR = {
    ord("Ç"): "C",
    ord("Ğ"): "G",
    ord("İ"): "I",
    ord("Ö"): "O",
    ord("Ş"): "S",
    ord("Ü"): "U",
    ord("ç"): "c",
    ord("ğ"): "g",
    ord("ı"): "i",
    ord("ö"): "o",
    ord("ş"): "s",
    ord("ü"): "u",
}

DEPARTMENT_LIST = [
    ("BUS", "Business Administration", "İşletme"),
    ("BUSS", "Business Administration (Suny)", "İşletme (Suny)"),
    ("ECO", "Economics", "İktisat"),
    ("ECOS", "Economics (Suny)", "İktisat (Suny)"),
    (
        "IBS",
        "International Business and Trade",
        "Uluslararası İşletmecilik ve Ticaret",
    ),
    ("IRE", "International Relations", "Uluslararası İlişkiler"),
    (
        "IRES",
        "International Relations (Suny)",
        "Uluslararası İlişkiler (Suny)",
    ),
    ("TMT", "Tourism Management", "Turizm İşletmeciliği"),
]

CHAIRS = {
    "Z-08": dict(zip("ABCDEF", [8, 8, 7, 7, 8, 8])),
    "Z-10": dict(zip("ABCDEF", [8, 8, 7, 7, 8, 8])),
    "108": dict(zip("ABCDEF", [8, 8, 7, 7, 8, 8])),
    "Z-07": dict(zip("ABCDE", [6, 6, 6, 6, 4])),
    "102": dict(zip("ABCDE", [6, 6, 6, 6, 4])),
    "104": dict(zip("ABCDE", [6, 6, 6, 6, 4])),
    "103/A": dict(zip("ABC", [7, 7, 7])),
    "105/A": dict(zip("ABC", [7, 7, 7])),
    "Z-25/A": dict(zip("ABC", [7, 7, 7])),
    "103/B": dict(zip("ABC", [6, 6, 6])),
    "105/B": dict(zip("ABC", [6, 6, 6])),
    "Z-25/B": dict(zip("ABC", [6, 6, 6])),
    "107": dict(zip("ABCDE", [7, 6, 6, 6, 4])),
    "Z-23": dict(zip("ABCDE", [7, 6, 6, 6, 6])),
    "106": dict(zip("ABCDE", [7, 6, 6, 7, 5])),
    "Z-05": dict(zip("ABCDE", [8, 7, 6, 6, 5])),
    "Z-09": dict(zip("ABCDE", [8, 7, 6, 6, 5])),
    "Z-11": dict(zip("ABCDE", [8, 7, 6, 6, 5])),
    "Z-20": dict(zip("ABCDE", [5, 7, 6, 6, 7])),
    "Z-24": dict(zip("ABCDE", [5, 7, 7, 7, 7])),
    "Z-26": dict(zip("ABCDE", [5, 7, 7, 8, 8])),
}
