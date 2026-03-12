from __future__ import annotations

from typing import Final

LOCAL_MARKETING_IMAGE_URL: Final[str] = "/static/images/og-image.png"


HOME_PROOF_POINTS: Final[list[dict[str, str]]] = [
    {
        "title": "Go-live lebih cepat",
        "description": "Sekolah tidak perlu merakit modul satu per satu. CBT Pro langsung siap dipakai untuk simulasi, PTS, PAS, ANBK internal, dan try out.",
    },
    {
        "title": "Biaya tetap terkendali",
        "description": "Bayar sekali untuk lisensi sekolah. Anda hanya fokus pada domain, VPS, dan operasional ujian yang memang dibutuhkan.",
    },
    {
        "title": "Alur kerja sesuai sekolah",
        "description": "Admin, guru, dan siswa mendapat tampilan yang berbeda sehingga pekerjaan lebih fokus dan resiko salah klik berkurang.",
    },
]

LANDING_FEATURE_CARDS: Final[list[dict[str, str]]] = [
    {
        "icon": "ri-stack-line",
        "title": "Bank soal terstruktur",
        "description": "Kelola soal per mapel, tingkat kesulitan, paket, dan kompetensi tanpa spreadsheet yang tercecer.",
    },
    {
        "icon": "ri-shuffle-line",
        "title": "Randomisasi paket",
        "description": "Soal dan pilihan jawaban dapat diacak otomatis untuk menekan peluang kerja sama antarpeserta.",
    },
    {
        "icon": "ri-shield-check-line",
        "title": "Monitoring pengawas",
        "description": "Pantau aktivitas ujian, indikasi pelanggaran, dan status peserta dari dashboard pengawas real-time.",
    },
    {
        "icon": "ri-bar-chart-grouped-line",
        "title": "Nilai dan analitik instan",
        "description": "Skor, rekap hasil, dan performa soal langsung tersedia sesaat setelah ujian selesai.",
    },
    {
        "icon": "ri-smartphone-line",
        "title": "Responsif lintas perangkat",
        "description": "Dapat diakses dari laptop, tablet, maupun smartphone tanpa instalasi aplikasi tambahan.",
    },
    {
        "icon": "ri-award-line",
        "title": "Sertifikat PDF otomatis",
        "description": "Terbitkan sertifikat hasil ujian dari sistem yang sama saat sekolah membutuhkannya.",
    },
]

LANDING_STATS: Final[list[dict[str, str]]] = [
    {"value": "1200+", "label": "pengguna aktif"},
    {"value": "5400+", "label": "bank soal"},
    {"value": "920+", "label": "sesi ujian"},
    {"value": "99%", "label": "uptime rata-rata"},
]

IMPLEMENTATION_STEPS: Final[list[dict[str, str]]] = [
    {
        "number": "01",
        "title": "Konsultasi kebutuhan sekolah",
        "description": "Kami petakan jumlah peserta, alur ujian, dan infrastruktur yang sudah dimiliki sekolah.",
    },
    {
        "number": "02",
        "title": "Setup dan konfigurasi",
        "description": "Tim membantu pemasangan di VPS/domain sekolah sampai halaman login, role, dan identitas lembaga siap dipakai.",
    },
    {
        "number": "03",
        "title": "Simulasi lalu go-live",
        "description": "Sekolah menjalankan uji coba singkat sebelum dipakai untuk ujian sebenarnya agar pelaksanaan lebih tenang.",
    },
]

FEATURE_PAGE_ITEMS: Final[list[dict[str, object]]] = [
    {
        "title": "Bank soal yang rapi untuk banyak guru",
        "description": "Fitur CBT sekolah harus memudahkan tim guru berbagi bank soal, bukan membuat duplikasi file. CBT Pro menata soal berdasarkan mapel, kelas, paket, dan tingkat kesulitan sehingga penyusunan ujian berikutnya jauh lebih cepat.",
        "bullets": [
            "Import dan edit soal dari panel yang sama",
            "Pengelompokan berdasarkan mapel, kelas, dan kompetensi",
            "Pratinjau soal sebelum dipublikasikan ke peserta",
        ],
        "image_url": LOCAL_MARKETING_IMAGE_URL,
        "image_alt": "Guru berdiskusi menyiapkan bank soal digital di ruang kerja sekolah",
    },
    {
        "title": "Randomisasi ujian agar lebih adil",
        "description": "CBT Pro membantu sekolah membuat paket ujian yang tetap setara walaupun urutan soal dan opsi jawaban berbeda untuk setiap peserta. Ini penting saat sesi ujian berlangsung serentak di laboratorium maupun dari rumah.",
        "bullets": [
            "Acak urutan soal dan opsi jawaban per peserta",
            "Dukungan pengaturan sesi dan jadwal ujian",
            "Lebih aman untuk try out, PTS, PAS, dan asesmen internal",
        ],
        "image_url": LOCAL_MARKETING_IMAGE_URL,
        "image_alt": "Siswa menggunakan laptop untuk mengikuti ujian online di kelas",
    },
    {
        "title": "Monitoring pengawas dalam satu dashboard",
        "description": "Guru pengawas tidak perlu berpindah-pindah halaman untuk melihat status peserta. Semua progres ujian, peringatan pelanggaran, dan aktivitas penting dirangkum agar keputusan bisa diambil lebih cepat.",
        "bullets": [
            "Pantau peserta yang aktif, terlambat, atau bermasalah",
            "Catatan pelanggaran lebih mudah ditinjau kembali",
            "Cocok untuk ruang ujian fisik maupun hybrid",
        ],
        "image_url": LOCAL_MARKETING_IMAGE_URL,
        "image_alt": "Pengawas sekolah memonitor aktivitas siswa dari dashboard laptop",
    },
    {
        "title": "Penilaian otomatis dan analitik hasil",
        "description": "Setelah ujian ditutup, guru tidak perlu menunggu rekap manual. Nilai objektif langsung tersedia beserta gambaran performa kelas sehingga tindak lanjut pembelajaran bisa lebih cepat dilakukan.",
        "bullets": [
            "Perhitungan skor otomatis untuk soal objektif",
            "Rekap hasil per siswa dan per ujian",
            "Analitik performa untuk evaluasi butir soal",
        ],
        "image_url": LOCAL_MARKETING_IMAGE_URL,
        "image_alt": "Dashboard analitik hasil ujian digital ditinjau oleh tim sekolah",
    },
    {
        "title": "Workflow multi-role yang mudah dipelajari",
        "description": "Setiap aktor mendapat tampilan yang sesuai. Admin fokus pada akun dan struktur data, guru fokus pada ujian dan soal, siswa fokus mengerjakan. Hasilnya adalah proses implementasi yang lebih cepat dan beban pelatihan yang lebih ringan.",
        "bullets": [
            "Hak akses admin, guru, dan siswa terpisah jelas",
            "Alur kerja lebih aman untuk tim sekolah yang berganti-ganti",
            "Dukungan sertifikat PDF dan fitur lanjutan lain saat dibutuhkan",
        ],
        "image_url": LOCAL_MARKETING_IMAGE_URL,
        "image_alt": "Tim sekolah berkolaborasi menggunakan aplikasi CBT untuk berbagai peran",
    },
]

PRICING_PLAN: Final[dict[str, object]] = {
    "list_price": "999.000",
    "price": "499.000",
    "headline": "CBT Pro lisensi sekolah",
    "description": "Paket ini cocok untuk sekolah, madrasah, bimbel, dan lembaga kursus yang ingin menjalankan sistem CBT milik sendiri tanpa biaya langganan bulanan.",
    "included": [
        "ZIP source code aplikasi CBT Pro",
        "Panduan instalasi lokal dan deployment VPS",
        "Setup awal sampai sistem siap dipakai",
        "Penyesuaian identitas sekolah pada aplikasi",
        "Update minor dan perbaikan bug dasar",
    ],
    "excluded": [
        "Biaya VPS atau server fisik",
        "Biaya domain dan SSL",
        "Layanan email SMTP pihak ketiga",
    ],
}

PRICING_COMPARISON_ROWS: Final[list[dict[str, str]]] = [
    {
        "label": "Model biaya",
        "cbt_pro": "Bayar sekali, pakai selamanya",
        "saas": "Bulanan atau tahunan per sekolah/per peserta",
        "custom": "Biaya awal tinggi lalu tetap ada biaya maintenance",
    },
    {
        "label": "Kontrol data",
        "cbt_pro": "Data ujian ada di server sekolah sendiri",
        "saas": "Umumnya mengikuti infrastruktur vendor",
        "custom": "Penuh, tetapi seluruh kontrol teknis ada di tim Anda",
    },
    {
        "label": "Waktu implementasi",
        "cbt_pro": "Cepat, karena fitur inti sudah siap",
        "saas": "Cepat, tetapi bergantung paket vendor",
        "custom": "Paling lama karena mulai dari spesifikasi dan development",
    },
    {
        "label": "Kustomisasi kebutuhan sekolah",
        "cbt_pro": "Lebih fleksibel dibanding SaaS umum",
        "saas": "Terbatas pada fitur yang disediakan vendor",
        "custom": "Paling fleksibel, tetapi mahal dan lama",
    },
    {
        "label": "Biaya jangka panjang",
        "cbt_pro": "Stabil, fokus pada infrastruktur sendiri",
        "saas": "Naik seiring durasi langganan dan skala penggunaan",
        "custom": "Tinggi karena development lanjutan dan perawatan",
    },
    {
        "label": "Kecocokan untuk ujian sekolah",
        "cbt_pro": "Dirancang untuk alur ujian dan try out sekolah",
        "saas": "Sering generik untuk banyak segmen",
        "custom": "Bisa sangat cocok jika budget dan tim memadai",
    },
]

PRICING_FAQ: Final[list[dict[str, str]]] = [
    {
        "question": "Apakah harga CBT sekolah Rp499.000 sudah termasuk pemasangan?",
        "answer": "Ya. Harga promo saat ini sudah termasuk bantuan setup awal sampai aplikasi siap dipakai di server sekolah.",
    },
    {
        "question": "Apakah ada biaya bulanan setelah membeli?",
        "answer": "Tidak ada biaya langganan dari CBT Pro. Biaya rutin hanya domain, VPS, atau layanan pendukung yang Anda pilih sendiri.",
    },
    {
        "question": "Bolehkah dipasang di server sekolah sendiri?",
        "answer": "Boleh. Justru model ini memberi kontrol lebih penuh terhadap data ujian dan operasional sekolah.",
    },
    {
        "question": "Apakah bisa konsultasi dulu sebelum membeli?",
        "answer": "Bisa. Gunakan halaman kontak atau WhatsApp untuk mendiskusikan jumlah peserta, kebutuhan sesi, dan rekomendasi server.",
    },
]

FAQ_GROUPS: Final[list[dict[str, object]]] = [
    {
        "title": "Umum",
        "items": [
            {
                "question": "Apa itu CBT Pro?",
                "answer": "CBT Pro adalah aplikasi ujian berbasis komputer untuk sekolah dan lembaga pendidikan yang ingin mengelola ujian digital secara mandiri.",
            },
            {
                "question": "Siapa yang cocok menggunakan CBT Pro?",
                "answer": "Sekolah, madrasah, bimbel, kampus kecil, lembaga kursus, dan panitia try out yang membutuhkan sistem ujian online yang rapi dan mudah dikontrol.",
            },
            {
                "question": "Apakah siswa bisa mengakses dari HP?",
                "answer": "Bisa. Antarmuka peserta dirancang responsif untuk smartphone, tablet, dan laptop, selama koneksi internet memadai.",
            },
            {
                "question": "Apakah aplikasi ini hanya untuk ujian akhir?",
                "answer": "Tidak. CBT Pro dapat dipakai untuk simulasi, latihan harian, PTS, PAS, try out, ujian masuk, dan asesmen internal lainnya.",
            },
            {
                "question": "Apakah sekolah harus punya tim IT sendiri?",
                "answer": "Tidak wajib. Untuk tahap awal kami membantu setup, dan setelah itu pengelolaan rutin dapat dilakukan oleh admin sekolah yang terbiasa memakai panel web.",
            },
        ],
    },
    {
        "title": "Harga & Pembelian",
        "items": [
            {
                "question": "Berapa harga CBT sekolah untuk lisensi CBT Pro?",
                "answer": "Harga landing page saat ini adalah Rp499.000 untuk lisensi sekolah, dengan promo yang sudah termasuk bantuan pemasangan awal.",
            },
            {
                "question": "Apa saja yang tidak termasuk dalam pembelian?",
                "answer": "Domain, VPS/server, SSL berbayar bila diperlukan, dan layanan eksternal seperti SMTP premium tetap disiapkan oleh sekolah atau dibeli terpisah.",
            },
            {
                "question": "Apakah ada biaya upgrade atau renewal tahunan?",
                "answer": "Tidak ada renewal lisensi tahunan untuk paket ini. Jika ada permintaan pengembangan khusus di luar paket, itu dibicarakan terpisah.",
            },
            {
                "question": "Bagaimana proses setelah sekolah memutuskan membeli?",
                "answer": "Setelah konfirmasi, sekolah menyiapkan domain/VPS atau akses hosting, lalu tim membantu instalasi, branding awal, dan uji coba singkat sampai siap digunakan.",
            },
        ],
    },
    {
        "title": "Teknis",
        "items": [
            {
                "question": "Berapa spesifikasi server minimal yang disarankan?",
                "answer": "Untuk beban awal yang wajar, VPS 2 vCPU dan 2 GB RAM biasanya cukup. Untuk peserta serentak yang lebih besar, spesifikasi ditingkatkan sesuai simulasi beban.",
            },
            {
                "question": "Apakah data ujian bisa disimpan di server sekolah sendiri?",
                "answer": "Bisa. CBT Pro dirancang agar sekolah dapat menempatkan aplikasi dan database pada infrastruktur milik sendiri.",
            },
            {
                "question": "Apakah mendukung import soal dan pengaturan role pengguna?",
                "answer": "Ya. Sistem sudah memiliki modul manajemen soal, user admin/guru/siswa, pengelompokan kelas, dan pengaturan ujian.",
            },
            {
                "question": "Apakah bisa diintegrasikan dengan backend lain atau Formspree untuk kontak?",
                "answer": "Bisa. Halaman kontak yang kami buat sudah menyiapkan state sukses dan validasi dasar, sehingga dapat disambungkan ke backend internal atau layanan seperti Formspree.",
            },
        ],
    },
]

FAQ_PREVIEW: Final[list[dict[str, str]]] = [
    FAQ_GROUPS[0]["items"][0],
    FAQ_GROUPS[0]["items"][2],
    FAQ_GROUPS[1]["items"][0],
    FAQ_GROUPS[2]["items"][0],
]
