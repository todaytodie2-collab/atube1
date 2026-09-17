# -*- coding: utf-8 -*-
import sqlite3
import json
import os
import time

DB_PATH = "d:/Casa/A TuBe/config/atube_data.sqlite"

def seed_full_catalog():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Catalog
    media_items = [
        # =========================================================================
        # 1. FOREIGN MOVIES (أفلام أجنبية وعالمية 4K)
        # =========================================================================
        {
            "id": "mov_dune2",
            "title": "Dune: Part Two",
            "arabic_title": "كثيب: الجزء الثاني",
            "year": "2024",
            "rating": "8.6",
            "duration": "166 دقيقة",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/xOMo8BRK7PfcJv9JCnx7s520b4q.jpg",
            "category": "foreign_movies",
            "sub_category": "subbed",
            "content_type": "movie",
            "country": "أمريكا",
            "language": "مترجم",
            "director": "Denis Villeneuve",
            "genres": "أكشن, خيال علمي, مغامرة",
            "synopsis": "يتحالف بول أتريدس مع تشاني وشعب الفريمن بينما يسعى للانتقام من المتآمرين الذين دمروا عائلته.",
            "servers": [{"name": "سيرفر الأسطورة 4K", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "4K UHD", "badge": "4K UHD"}]
        },
        {
            "id": "mov_deadpool3",
            "title": "Deadpool & Wolverine",
            "arabic_title": "ديدبول وولفرين",
            "year": "2024",
            "rating": "8.0",
            "duration": "128 دقيقة",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/8cdWjvZQUExUUTzyp4t6EDMubfO.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/yDHYTfA3R0jFYba16jBB1ef8oIt.jpg",
            "category": "foreign_movies",
            "sub_category": "subbed",
            "content_type": "movie",
            "country": "أمريكا",
            "language": "مترجم",
            "director": "Shawn Levy",
            "genres": "أكشن, كوميديا, خيال علمي",
            "synopsis": "ينطلق ديدبول في مهمة مصيرية لإنقاذ كونه بمساعدة ولفرين المتردد في مغامرة مليئة بالفوضى والتشويق.",
            "servers": [{"name": "سيرفر VIP 4K", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "4K UHD", "badge": "4K UHD"}]
        },
        {
            "id": "mov_gladiator2",
            "title": "Gladiator II",
            "arabic_title": "المحارب 2",
            "year": "2024",
            "rating": "7.8",
            "duration": "148 دقيقة",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/2cxhvwyEwRlysAmRH4iodkvo0z5.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/euYI6ub299Y56JsWNsOEfH0ndko.jpg",
            "category": "foreign_movies",
            "sub_category": "subbed",
            "content_type": "movie",
            "country": "أمريكا",
            "language": "مترجم",
            "director": "Ridley Scott",
            "genres": "أكشن, مغامرة, تاريخي",
            "synopsis": "بعد سنوات من التضحية بماكسيموس، يدخل لوسيوس حلبة الكولوسيوم لاستعادة مجد روما المفقود والانتقام.",
            "servers": [{"name": "سيرفر FHD 1080P", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "1080p FHD", "badge": "1080P"}]
        },
        {
            "id": "mov_oppenheimer",
            "title": "Oppenheimer",
            "arabic_title": "أوبنهايمر",
            "year": "2023",
            "rating": "8.9",
            "duration": "180 دقيقة",
            "quality": "4K IMAX",
            "poster": "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/rIb9dQsn98v8ti51Q595L3u7f6L.jpg",
            "category": "foreign_movies",
            "sub_category": "subbed",
            "content_type": "movie",
            "country": "أمريكا",
            "language": "مترجم",
            "director": "Christopher Nolan",
            "genres": "دراما, تاريخي, سيرة ذاتية",
            "synopsis": "قصة العالم الأمريكي جيه. روبرت أوبنهايمر ودوره المحوري في تطوير القنبلة الذرية وتداعياتها التاريخية.",
            "servers": [{"name": "سيرفر IMAX 4K", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "4K UHD", "badge": "4K UHD"}]
        },
        {
            "id": "mov_johnwick4",
            "title": "John Wick: Chapter 4",
            "arabic_title": "جون ويك 4",
            "year": "2023",
            "rating": "8.4",
            "duration": "169 دقيقة",
            "quality": "4K HDR",
            "poster": "https://image.tmdb.org/t/p/w500/vZloFAK7NKnMGKE7UmJWLMRV3io.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/7I6VUdPj6tQECNHdviJkUHD2389.jpg",
            "category": "foreign_movies",
            "sub_category": "subbed",
            "content_type": "movie",
            "country": "أمريكا",
            "language": "مترجم",
            "director": "Chad Stahelski",
            "genres": "أكشن, جريمة, إثارة",
            "synopsis": "يكتشف جون ويك طريقة لهزيمة المجلس الأعلى واستعادة حريته بمواجهة تحالفات دموية جديدة في باريس وطوكيو.",
            "servers": [{"name": "سيرفر الأكشن 1080P", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "1080p FHD", "badge": "1080P"}]
        },
        {
            "id": "mov_alien_romulus",
            "title": "Alien: Romulus",
            "arabic_title": "فضائي: رومولوس",
            "year": "2024",
            "rating": "7.5",
            "duration": "119 دقيقة",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/b33nnKl1GSvbao8l3Tueky43uQk.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/9SSEUrSqhljBMZRe4aBTh17rUaC.jpg",
            "category": "foreign_movies",
            "sub_category": "subbed",
            "content_type": "movie",
            "country": "أمريكا",
            "language": "مترجم",
            "genres": "رعب, خيال علمي, إثارة",
            "synopsis": "مجموعة من المستعمرين الشباب في الفضاء يواجهون أبشع كائن مرعب في مجرتهم داخل محطة فضائية مهجورة.",
            "servers": [{"name": "سيرفر الرعب 4K", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "4K UHD", "badge": "4K UHD"}]
        },
        {
            "id": "mov_furiosa",
            "title": "Furiosa: A Mad Max Saga",
            "arabic_title": "فيوريوسا: ملحمة ماد ماكس",
            "year": "2024",
            "rating": "7.9",
            "duration": "148 دقيقة",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/iADOJ8Zymht2JPMoy3R7xUMZ51f.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/wNAhuOZ3Zf84jCI5Te29vgQ0ugL.jpg",
            "category": "foreign_movies",
            "sub_category": "subbed",
            "content_type": "movie",
            "country": "أمريكا",
            "language": "مترجم",
            "genres": "أكشن, مغامرة, خيال علمي",
            "synopsis": "قصة أصل المحاربة الشابة فيوريوسا وكفاحها للبقاء والعودة إلى موطنها عبر أراضي القفار القاسية.",
            "servers": [{"name": "سيرفر ماد ماكس 4K", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "4K UHD", "badge": "4K UHD"}]
        },
        {
            "id": "mov_the_batman",
            "title": "The Batman",
            "arabic_title": "باتمان: فارس الظلام",
            "year": "2022",
            "rating": "8.3",
            "duration": "176 دقيقة",
            "quality": "4K HDR",
            "poster": "https://image.tmdb.org/t/p/w500/74xTEgt7R36Fpooo50r9T25onhq.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/b0PlSFdDwbyK0cf5RxwDpaOJQvQ.jpg",
            "category": "foreign_movies",
            "sub_category": "subbed",
            "content_type": "movie",
            "country": "أمريكا",
            "language": "مترجم",
            "genres": "جريمة, دراما, غموض, أكشن",
            "synopsis": "يتتبع باتمان قاتلاً متسلسلاً سادياً يترك وراءه أدلة غامضة في عالم مدينة جوثام السفلي.",
            "servers": [{"name": "سيرفر جوثام 4K", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "4K UHD", "badge": "4K UHD"}]
        },

        # =========================================================================
        # 2. ARABIC MOVIES (أفلام عربية ومصرية 4K)
        # =========================================================================
        {
            "id": "mov_welad_rizk_3",
            "title": "Welad Rizk 3: El Qadya",
            "arabic_title": "ولاد رزق 3: القاضية",
            "year": "2024",
            "rating": "8.5",
            "duration": "125 دقيقة",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/q3U4nS63pBf02Z4nOcbK95G1h9c.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/uC8JcZgL7qZg4eN2bV9bB1oE4f3.jpg",
            "category": "arabic_movies",
            "sub_category": "arabic",
            "content_type": "movie",
            "country": "مصر",
            "language": "عربي",
            "director": "طارق العريان",
            "genres": "أكشن, جريمة, كوميديا",
            "synopsis": "يعود الأخوة الأربعة لتنفيذ أكبر عملية سرقة في تاريخهم في شوارع الرياض وسط مطاردات نارية تحبس الأنفاس.",
            "servers": [{"name": "سيرفر النجوم 4K", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "4K UHD", "badge": "4K UHD"}]
        },
        {
            "id": "mov_beit_el_ruby",
            "title": "Beit El Ruby",
            "arabic_title": "بيت الروبي",
            "year": "2023",
            "rating": "8.1",
            "duration": "118 دقيقة",
            "quality": "1080p FHD",
            "poster": "https://image.tmdb.org/t/p/w500/y1H4G3zO0a9zL9nB5vC8b1x4g3h.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/w0h9B2xY9b1zL7eN6a3rC5b8o1e.jpg",
            "category": "arabic_movies",
            "sub_category": "arabic",
            "content_type": "movie",
            "country": "مصر",
            "language": "عربي",
            "director": "بيتر ميمي",
            "genres": "كوميديا, دراما, عائلي",
            "synopsis": "يعيش إبراهيم الروبي حياة هادئة مع زوجته في إحدى القرى الساحلية حتى تنقلب حياته عند عودته للقاهرة.",
            "servers": [{"name": "سيرفر العائلة FHD", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "1080p FHD", "badge": "1080P"}]
        },
        {
            "id": "mov_fasel_lahazat",
            "title": "Fasel Men El Lahazat El Lazeeza",
            "arabic_title": "فاصل من اللحظات اللذيذة",
            "year": "2024",
            "rating": "8.0",
            "duration": "115 دقيقة",
            "quality": "1080p FHD",
            "poster": "https://image.tmdb.org/t/p/w500/8gZ1x6bA0c4dE8f9g2h1j3k5l7m.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/5bX8b1oE4f3uC8JcZgL7qZg4eN2.jpg",
            "category": "arabic_movies",
            "sub_category": "arabic",
            "content_type": "movie",
            "country": "مصر",
            "language": "عربي",
            "director": "أحمد الجندي",
            "genres": "كوميديا, خيال علمي, رومانسي",
            "synopsis": "مهندس معماري يعيش حياة تعيسة تفتح أمامه بوابة لعالم موازٍ يعيد ترتيب حياته بأسلوب كوميدي مثير.",
            "servers": [{"name": "سيرفر الكوميديا FHD", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "1080p FHD", "badge": "1080P"}]
        },
        {
            "id": "mov_kira_wal_gin",
            "title": "Kira & El Gin",
            "arabic_title": "كيرة والجن",
            "year": "2022",
            "rating": "8.7",
            "duration": "175 دقيقة",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/3k8eX9bY1oE4f3uC8JcZgL7qZg4.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/9yBVt5AoBq7yepq8n8y2X0K7z5z.jpg",
            "category": "arabic_movies",
            "sub_category": "arabic",
            "content_type": "movie",
            "country": "مصر",
            "language": "عربي",
            "director": "مروان حامد",
            "genres": "تاريخي, أكشن, دراما, تشويق",
            "synopsis": "ملحمة المقاومة المصرية ضد الاحتلال الإنجليزي في ثورة 1919 من خلال أبطال المقاومة السرية كيرة والجن.",
            "servers": [{"name": "سيرفر الملحمة 4K", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "4K UHD", "badge": "4K UHD"}]
        },
        {
            "id": "mov_blue_elephant_2",
            "title": "The Blue Elephant 2",
            "arabic_title": "الفيل الأزرق 2",
            "year": "2019",
            "rating": "8.6",
            "duration": "130 دقيقة",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/2yBVt5AoBq7yepq8n8y2X0K7z5z.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/1yBVt5AoBq7yepq8n8y2X0K7z5z.jpg",
            "category": "arabic_movies",
            "sub_category": "arabic",
            "content_type": "movie",
            "country": "مصر",
            "language": "عربي",
            "director": "مروان حامد",
            "genres": "غموض, رعب, تشويق, دراما",
            "synopsis": "يعود الدكتور يحيى راشد لمواجهة لغز مرعب جديد في قسم الحالات الخطرة يستدعي حبة الفيل الأزرق مجدداً.",
            "servers": [{"name": "سيرفر الرعب FHD", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "1080p FHD", "badge": "1080P"}]
        },

        # =========================================================================
        # 3. FOREIGN SERIES (مسلسلات أجنبية وعالمية)
        # =========================================================================
        {
            "id": "ser_house_of_dragon",
            "title": "House of the Dragon",
            "arabic_title": "آل التنين",
            "year": "2024",
            "rating": "8.8",
            "quality": "4K HDR",
            "poster": "https://image.tmdb.org/t/p/w500/1X4h40fcB4WWUmIBK0auT4zRBAV.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/etjA2mwbz0QTQcw9Z2N73i8x92x.jpg",
            "category": "foreign_series",
            "sub_category": "subbed",
            "content_type": "series",
            "country": "أمريكا",
            "language": "مترجم",
            "director": "Ryan Condal",
            "genres": "فانتازيا, دراما, أكشن, مغامرة",
            "synopsis": "تاريخ عائلة تارجاريين وبداية الحرب الأهلية الدامية المعروفة باسم رقصة التنانين في قارة ويستروس.",
            "total_seasons": 2,
            "episodes": [
                {"season_number": 1, "episode_number": 1, "title": "ابن مقابل ابن", "duration": "61:14", "thumbnail": "https://image.tmdb.org/t/p/w500/etjA2mwbz0QTQcw9Z2N73i8x92x.jpg"},
                {"season_number": 1, "episode_number": 2, "title": "رينيرا القاسية", "duration": "58:40", "thumbnail": "https://image.tmdb.org/t/p/w500/etjA2mwbz0QTQcw9Z2N73i8x92x.jpg"}
            ]
        },
        {
            "id": "ser_shogun",
            "title": "Shōgun",
            "arabic_title": "شوجون: القائد المحارب",
            "year": "2024",
            "rating": "9.1",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/7O4iVfOMQmdCSxhOg1WnzG1AgYT.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/9yBVt5AoBq7yepq8n8y2X0K7z5z.jpg",
            "category": "foreign_series",
            "sub_category": "subbed",
            "content_type": "series",
            "country": "أمريكا",
            "language": "مترجم",
            "director": "Justin Marks",
            "genres": "دراما, تاريخي, أكشن, حرب",
            "synopsis": "في اليابان عام 1600، يجد اللورد توراناجا نفسه محاصراً من أعدائه بينما تصل سفينة أوروبية غامضة تقلب الموازين.",
            "total_seasons": 1,
            "episodes": [
                {"season_number": 1, "episode_number": 1, "title": "الوافد الغريب", "duration": "68:10", "thumbnail": "https://image.tmdb.org/t/p/w500/9yBVt5AoBq7yepq8n8y2X0K7z5z.jpg"}
            ]
        },
        {
            "id": "ser_the_penguin",
            "title": "The Penguin",
            "arabic_title": "البطريق",
            "year": "2024",
            "rating": "8.9",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/44kXmXy8fA12eQ2X6h4hX6Xy8fA.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/8h5f8r0q8r0q8r0q8r0q8r0q8r0.jpg",
            "category": "foreign_series",
            "sub_category": "subbed",
            "content_type": "series",
            "country": "أمريكا",
            "language": "مترجم",
            "genres": "جريمة, دراما, إثارة",
            "synopsis": "صعود أوزوالد كوبلبوت في عالم الجريمة المنظمة في مدينة جوثام عقب انهيار عائلة فالكون الإجرامية.",
            "total_seasons": 1,
            "episodes": [
                {"season_number": 1, "episode_number": 1, "title": "بداية العهد الجديد", "duration": "57:00", "thumbnail": "https://image.tmdb.org/t/p/w500/8h5f8r0q8r0q8r0q8r0q8r0q8r0.jpg"}
            ]
        },
        {
            "id": "ser_the_last_of_us",
            "title": "The Last of Us",
            "arabic_title": "ذا لاست أوف أس",
            "year": "2023",
            "rating": "9.0",
            "quality": "4K HDR",
            "poster": "https://image.tmdb.org/t/p/w500/uKvVjK1q223wBvr987r0q8r0q8r.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/uDgy6hyPd82kOHh6I95FLtLnj6p.jpg",
            "category": "foreign_series",
            "sub_category": "subbed",
            "content_type": "series",
            "country": "أمريكا",
            "language": "مترجم",
            "genres": "دراما, مغامرة, رعب, خيال علمي",
            "synopsis": "جويل وإيلي في رحلة خطيرة عبر أراضي أمريكا المدمرة والموبوءة بالوحوش القاتلة بحثاً عن علاج للبشرية.",
            "total_seasons": 1
        },

        # =========================================================================
        # 4. ARABIC SERIES (مسلسلات عربية ومصرية)
        # =========================================================================
        {
            "id": "ser_hashasheen",
            "title": "El Hashasheen",
            "arabic_title": "الحشاشين",
            "year": "2024",
            "rating": "9.2",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/h1H5H1H5H1H5H1H5H1H5H1H5H1H.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/b1B5B1B5B1B5B1B5B1B5B1B5B1B.jpg",
            "category": "arabic_series",
            "sub_category": "arabic",
            "content_type": "series",
            "country": "مصر",
            "language": "عربي",
            "director": "بيتر ميمي",
            "genres": "تاريخي, دراما, أكشن, تشويق",
            "synopsis": "قصة حسن الصباح مؤسس طائفة الحشاشين وأخطر فرقة اغتيالات في التاريخ داخل قلعة ألموت الحصينة.",
            "total_seasons": 1,
            "episodes": [
                {"season_number": 1, "episode_number": 1, "title": "عهد الأصدقاء", "duration": "46:20", "thumbnail": "https://image.tmdb.org/t/p/w500/b1B5B1B5B1B5B1B5B1B5B1B5B1B.jpg"},
                {"season_number": 1, "episode_number": 2, "title": "قلعة ألموت", "duration": "48:15", "thumbnail": "https://image.tmdb.org/t/p/w500/b1B5B1B5B1B5B1B5B1B5B1B5B1B.jpg"}
            ]
        },
        {
            "id": "ser_el_atawla",
            "title": "El Atawla",
            "arabic_title": "العتاولة",
            "year": "2024",
            "rating": "8.7",
            "quality": "1080p FHD",
            "poster": "https://image.tmdb.org/t/p/w500/a1A2A3A4A5A6A7A8A9A0A1A2A3A.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/c1C2C3C4C5C6C7C8C9C0C1C2C3C.jpg",
            "category": "arabic_series",
            "sub_category": "arabic",
            "content_type": "series",
            "country": "مصر",
            "language": "عربي",
            "director": "أحمد خالد موسى",
            "genres": "أكشن, جريمة, دراما, إثارة",
            "synopsis": "صراع محتدم بين شقيقين يمارسان السرقة في الإسكندرية، حتى يظهر عدو شرس يهدد العائلة بأكملها.",
            "total_seasons": 1,
            "episodes": [
                {"season_number": 1, "episode_number": 1, "title": "بداية المعركة", "duration": "44:30", "thumbnail": "https://image.tmdb.org/t/p/w500/c1C2C3C4C5C6C7C8C9C0C1C2C3C.jpg"}
            ]
        },
        {
            "id": "ser_gaafar_el_omda",
            "title": "Gaafar El Omda",
            "arabic_title": "جعفر العمدة",
            "year": "2023",
            "rating": "8.9",
            "quality": "1080p FHD",
            "poster": "https://image.tmdb.org/t/p/w500/g1G2G3G4G5G6G7G8G9G0G1G2G3G.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/h1H2H3H4H5H6H7H8H9H0H1H2H3H.jpg",
            "category": "arabic_series",
            "sub_category": "arabic",
            "content_type": "series",
            "country": "مصر",
            "language": "عربي",
            "director": "محمد سامي",
            "genres": "دراما, تشويق, إثارة",
            "synopsis": "رحلة جعفر العمدة في البحث عن ابنه المفقود منذ 19 عاماً وسط صراعات حامية في حي السيدة زينب.",
            "total_seasons": 1
        },

        # =========================================================================
        # 5. TURKISH SERIES (مسلسلات ودراما تركية)
        # =========================================================================
        {
            "id": "ser_kurulus_osman",
            "title": "Kuruluş: Osman",
            "arabic_title": "المؤسس عثمان",
            "year": "2024",
            "rating": "8.9",
            "quality": "1080p FHD",
            "poster": "https://image.tmdb.org/t/p/w500/9b9b9b9b9b9b9b9b9b9b9b9b9b9.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/8a8a8a8a8a8a8a8a8a8a8a8a8a8.jpg",
            "category": "turkish_series",
            "sub_category": "subbed",
            "content_type": "series",
            "country": "تركيا",
            "language": "مترجم",
            "director": "Metin Günay",
            "genres": "تاريخي, أكشن, مغامرة, دراما",
            "synopsis": "بطولات عثمان بن أرطغرل مؤسس الدولة العثمانية وصراعاته الملحمية ضد البيزنطيين والمغول لتأسيس المجد.",
            "total_seasons": 6,
            "episodes": [
                {"season_number": 6, "episode_number": 1, "title": "راية الفتح الجديدة", "duration": "120:00", "thumbnail": "https://image.tmdb.org/t/p/w500/8a8a8a8a8a8a8a8a8a8a8a8a8a8.jpg"}
            ]
        },
        {
            "id": "ser_yali_capkini",
            "title": "Yalı Çapkını",
            "arabic_title": "طائر الرفراف",
            "year": "2024",
            "rating": "8.2",
            "quality": "1080p FHD",
            "poster": "https://image.tmdb.org/t/p/w500/7c7c7c7c7c7c7c7c7c7c7c7c7c7.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/6d6d6d6d6d6d6d6d6d6d6d6d6d6.jpg",
            "category": "turkish_series",
            "sub_category": "subbed",
            "content_type": "series",
            "country": "تركيا",
            "language": "مترجم",
            "genres": "دراما, رومانسي, تشويق",
            "synopsis": "قصة زواج إجباري بين فريد الطائش وسيران وما ينشأ بينهما من صراعات ومشاعر داخل قصر عائلة كورهان.",
            "total_seasons": 3,
            "episodes": [
                {"season_number": 3, "episode_number": 1, "title": "أسرار القصر", "duration": "115:00", "thumbnail": "https://image.tmdb.org/t/p/w500/6d6d6d6d6d6d6d6d6d6d6d6d6d6.jpg"}
            ]
        },
        {
            "id": "ser_cukur",
            "title": "Çukur",
            "arabic_title": "الحفرة",
            "year": "2021",
            "rating": "8.8",
            "quality": "1080p FHD",
            "poster": "https://image.tmdb.org/t/p/w500/3k8eX9bY1oE4f3uC8JcZgL7qZg4.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/9yBVt5AoBq7yepq8n8y2X0K7z5z.jpg",
            "category": "turkish_series",
            "sub_category": "subbed",
            "content_type": "series",
            "country": "تركيا",
            "language": "مترجم",
            "genres": "أكشن, جريمة, دراما",
            "synopsis": "حي الحفرة الأخطر في إسطنبول تحت سيطرة عائلة كوتشوفالي وقواعدهم الصارمة في حماية الحي ضد العصابات.",
            "total_seasons": 4
        },

        # =========================================================================
        # 6. KOREAN / ASIAN SERIES (مسلسلات كورية وآسيوية)
        # =========================================================================
        {
            "id": "ser_squid_game_2",
            "title": "Squid Game: Season 2",
            "arabic_title": "لعبة الحبار: الموسم 2",
            "year": "2024",
            "rating": "9.0",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/dDlEmu3EZ0Pgg93K2SVNLCjCSvE.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/7T44eGk0C87n9g6eZ4m1a5hL9rP.jpg",
            "category": "korean_series",
            "sub_category": "subbed",
            "content_type": "series",
            "country": "كوريا الجنوبية",
            "language": "مترجم",
            "director": "Hwang Dong-hyuk",
            "genres": "إثارة, تشويق, دراما, غموض",
            "synopsis": "يعود سيونغ جي هون برقم 456 في محاولة للانتقام وكشف المنظمة السرية والقضاء على لعبة الحبار القاتلة.",
            "total_seasons": 2,
            "episodes": [
                {"season_number": 2, "episode_number": 1, "title": "العودة للساحة", "duration": "55:30", "thumbnail": "https://image.tmdb.org/t/p/w500/7T44eGk0C87n9g6eZ4m1a5hL9rP.jpg"}
            ]
        },
        {
            "id": "ser_queen_of_tears",
            "title": "Queen of Tears",
            "arabic_title": "ملكة الدموع",
            "year": "2024",
            "rating": "8.8",
            "quality": "1080p FHD",
            "poster": "https://image.tmdb.org/t/p/w500/5v0q8r0q8r0q8r0q8r0q8r0q8r0.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/4u0q8r0q8r0q8r0q8r0q8r0q8r0.jpg",
            "category": "korean_series",
            "sub_category": "subbed",
            "content_type": "series",
            "country": "كوريا الجنوبية",
            "language": "مترجم",
            "genres": "رومانسي, دراما, كوميديا",
            "synopsis": "ملحمة حب وتحدٍ بين وريثة عائلة أرستقراطية ومديرها القانوني في رحلة عاطفية مليئة بالدموع والأمل.",
            "total_seasons": 1
        },

        # =========================================================================
        # 7. INDIAN / BOLLYWOOD MOVIES (أفلام هندية وبوليوود)
        # =========================================================================
        {
            "id": "mov_jawan",
            "title": "Jawan",
            "arabic_title": "جوان",
            "year": "2023",
            "rating": "8.4",
            "duration": "169 دقيقة",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/jJwELk6qM1aE6l2Xm0v7iX0q8r0.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/bWIIWhnaoWx3FTVX47Ref504Lz8.jpg",
            "category": "indian_movies",
            "sub_category": "subbed",
            "content_type": "movie",
            "country": "الهند",
            "language": "مترجم",
            "director": "Atlee",
            "genres": "أكشن, إثارة, دراما",
            "synopsis": "رجل تحركه رغبة عميقة في تصحيح أخطاء المجتمع والوفاء بوعد قطعه في الماضي في مواجهة عدو لا يرحم.",
            "servers": [{"name": "سيرفر بوليوود 4K", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "4K UHD", "badge": "4K UHD"}]
        },
        {
            "id": "mov_rrr",
            "title": "RRR",
            "arabic_title": "آر آر آر",
            "year": "2022",
            "rating": "8.8",
            "duration": "187 دقيقة",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/wE0q8r0q8r0q8r0q8r0q8r0q8r0.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/22z44LPkqOymnB8vT9dW2B3u2e.jpg",
            "category": "indian_movies",
            "sub_category": "subbed",
            "content_type": "movie",
            "country": "الهند",
            "language": "مترجم",
            "director": "S.S. Rajamouli",
            "genres": "أكشن, دراما, مغامرة, تاريخي",
            "synopsis": "قصة ملحمية خيالية عن اثنين من الثوار الأسطوريين ورحلتهما بعيداً عن وطنهما قبل أن يبدآ القتال من أجل بلادهما في عشرينيات القرن الماضي.",
            "servers": [{"name": "سيرفر الملحمة الهندية 4K", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "4K UHD", "badge": "4K UHD"}]
        },
        {
            "id": "mov_pathaan",
            "title": "Pathaan",
            "arabic_title": "باثان",
            "year": "2023",
            "rating": "7.9",
            "duration": "146 دقيقة",
            "quality": "1080p FHD",
            "poster": "https://image.tmdb.org/t/p/w500/m1A2A3A4A5A6A7A8A9A0A1A2A3A.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/n2A2A3A4A5A6A7A8A9A0A1A2A3A.jpg",
            "category": "indian_movies",
            "sub_category": "subbed",
            "content_type": "movie",
            "country": "الهند",
            "language": "مترجم",
            "director": "Siddharth Anand",
            "genres": "أكشن, إثارة, تشويق",
            "synopsis": "عميل سري هندي ينطلق في مهمة مستحيلة لإنقاذ وطنه من جماعة إرهابية تخطط لهجوم بيولوجي مدمر.",
            "servers": [{"name": "سيرفر شاروخان FHD", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "1080p FHD", "badge": "1080P"}]
        },

        # =========================================================================
        # 8. WWE SHOWS (عروض المصارعة الحرة WWE)
        # =========================================================================
        {
            "id": "wwe_wrestlemania_40",
            "title": "WWE WrestleMania XL",
            "arabic_title": "ريسلمانيا 40: الملحمة الكبرى",
            "year": "2024",
            "rating": "9.5",
            "quality": "4K Ultra HD",
            "poster": "https://image.tmdb.org/t/p/w500/3u0q8r0q8r0q8r0q8r0q8r0q8r0.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/2u0q8r0q8r0q8r0q8r0q8r0q8r0.jpg",
            "category": "wwe",
            "sub_category": "wwe",
            "content_type": "wwe",
            "country": "أمريكا",
            "language": "مترجم",
            "genres": "مصارعة, رياضة, أكشن",
            "synopsis": "النزال التاريخي بين كودي رودز ورومان رينز بمشاركة ذا روك وسيث رولينز في ليلة لا تُنسى.",
            "servers": [{"name": "سيرفر البث المباشر 4K", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "4K UHD", "badge": "4K UHD"}]
        },
        {
            "id": "wwe_royal_rumble_2024",
            "title": "WWE Royal Rumble 2024",
            "arabic_title": "رويال رامبل 2024",
            "year": "2024",
            "rating": "8.8",
            "quality": "1080p FHD",
            "poster": "https://image.tmdb.org/t/p/w500/1u0q8r0q8r0q8r0q8r0q8r0q8r0.jpg",
            "backdrop": "https://image.tmdb.org/t/p/original/0u0q8r0q8r0q8r0q8r0q8r0q8r0.jpg",
            "category": "wwe",
            "sub_category": "wwe",
            "content_type": "wwe",
            "country": "أمريكا",
            "language": "مترجم",
            "genres": "مصارعة, رياضة, أكشن",
            "synopsis": "30 مصارعاً يتنافسون فوق الحلبة لانتزاع تذكرة التأهل للحدث الرئيسي في ريسلمانيا.",
            "servers": [{"name": "سيرفر المشاهدة السحابي", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "1080p FHD", "badge": "1080P"}]
        }
    ]

    inserted_media = 0
    inserted_episodes = 0
    inserted_servers = 0

    for item in media_items:
        m_id = item["id"]
        title = item["title"]
        ar_title = item.get("arabic_title", title)
        c_type = item.get("content_type", "movie")
        cat = item.get("category", "foreign_movies")
        sub_cat = item.get("sub_category", "subbed")
        year = item.get("year", "2024")
        rating = item.get("rating", "8.5")
        duration = item.get("duration", "120 دقيقة")
        quality = item.get("quality", "1080p FHD")
        poster = item.get("poster", "")
        backdrop = item.get("backdrop", poster)
        country = item.get("country", "")
        language = item.get("language", "مترجم")
        director = item.get("director", "")
        genres = item.get("genres", "أكشن")
        synopsis = item.get("synopsis", "")
        total_seasons = item.get("total_seasons", 1 if c_type in ("series", "anime") else 0)

        cur.execute("""
            INSERT INTO vod_media (
                id, title, arabic_title, content_type, category, sub_category,
                year, rating, duration, quality, poster, backdrop, country, language,
                director, genres, synopsis, total_seasons, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                arabic_title=excluded.arabic_title,
                content_type=excluded.content_type,
                category=excluded.category,
                sub_category=excluded.sub_category,
                year=excluded.year,
                rating=excluded.rating,
                duration=excluded.duration,
                quality=excluded.quality,
                poster=excluded.poster,
                backdrop=excluded.backdrop,
                country=excluded.country,
                language=excluded.language,
                director=excluded.director,
                genres=excluded.genres,
                synopsis=excluded.synopsis,
                total_seasons=excluded.total_seasons,
                updated_at=CURRENT_TIMESTAMP
        """, (
            m_id, title, ar_title, c_type, cat, sub_cat,
            year, rating, duration, quality, poster, backdrop, country, language,
            director, genres, synopsis, total_seasons
        ))
        inserted_media += 1

        # Insert Servers for movies
        servers = item.get("servers", [])
        if not servers and c_type == "movie":
            servers = [
                {"name": "سيرفر A TuBe VIP 4K", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "4K UHD", "badge": "4K UHD"},
                {"name": "سيرفر المشاهدة المباشرة (1080P)", "url": "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "quality": "1080p FHD", "badge": "1080P"}
            ]

        for s in servers:
            cur.execute("""
                INSERT INTO vod_servers (media_id, server_name, stream_url, quality, badge, site)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (m_id, s.get("name", "سيرفر مشاهدة"), s.get("url", ""), s.get("quality", "1080p FHD"), s.get("badge", "1080P"), "Direct"))
            inserted_servers += 1

        # Insert Episodes for series
        for ep in item.get("episodes", []):
            cur.execute("""
                INSERT OR REPLACE INTO vod_episodes (media_id, season_number, episode_number, episode_title, duration, thumbnail)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                m_id, ep.get("season_number", 1), ep.get("episode_number", 1),
                ep.get("title", f"الحلقة {ep.get('episode_number', 1)}"),
                ep.get("duration", "45:00"),
                ep.get("thumbnail", backdrop)
            ))
            inserted_episodes += 1

            # Episode server
            cur.execute("""
                INSERT INTO vod_servers (media_id, season_number, episode_number, server_name, stream_url, quality, badge, site)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                m_id, ep.get("season_number", 1), ep.get("episode_number", 1),
                "سيرفر الحلقة VIP 1080P", "https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8", "1080p FHD", "1080P", "Direct"
            ))
            inserted_servers += 1

    conn.commit()
    conn.close()
    print(f"Seeding Complete: {inserted_media} Media Titles, {inserted_episodes} Episodes, {inserted_servers} Servers.")

if __name__ == "__main__":
    seed_full_catalog()
