from apps import (
    dashboard,
    sekretaris,
    bendahara,
    hr,
    asisten,
    akademik_praktikum,
    hardware_software,
    manajemen_praktikum,
)

# Tab yang tersedia per role
PAGE_TABS_BY_ROLE = {
    "koordinator": {
        "📊 Dashboard": dashboard,
        "🧑‍🔧 Aktivitas Asisten": asisten
    },
    "sekretaris": {
        "📁 Manajemen Dokumen": sekretaris,
        "🧑‍🔧 Aktivitas Asisten": asisten
    },
    "bendahara": {
        "💰 Manajemen Keuangan": bendahara,
        "🧑‍🔧 Aktivitas Asisten": asisten
    },
    "hr": {
        "👥 Human Resource": hr,
        "🧑‍🔧 Aktivitas Asisten": asisten
    },
    "akademik": {
        "📖 Divisi Akademik Praktikum": akademik_praktikum,
        "🧑‍🔧 Aktivitas Asisten": asisten
    },
    "hardware": {
        "🛠️ Divisi Hardware & Software": hardware_software,
        "🧑‍🔧 Aktivitas Asisten": asisten
    },
    "manajemen_praktikum": {
        "📚 Divisi Manajemen Praktikum": manajemen_praktikum,
        "🧑‍🔧 Aktivitas Asisten": asisten
    },
        "asisten": {
        "🧑‍🔧 Aktivitas Asisten": asisten
    }
}
