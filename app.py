"""
=============================================================================
Aplikasi Asisten Monitoring Rental Mobil dan Motor
Framework: Streamlit
Pengolahan Data: Pandas
Visualisasi: Matplotlib & Seaborn
Database: SQLite3
=============================================================================
"""

import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, date

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN STREAMLIT & STYLING MODERN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Kings Rental Mobil Bumiayu",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling untuk tampilan modern, bersih, dan elegan
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1f2937, #111827);
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #64748b;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .info-box {
        background-color: #f0fdf4;
        border-left: 5px solid #22c55e;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

DB_NAME = "rental_monitoring.db"

# -----------------------------------------------------------------------------
# 2. MODUL DATABASE (SQLite Connection, Inisialisasi, & Migrasi Otomatis)
# -----------------------------------------------------------------------------

def get_connection():
    """Mengembalikan objek koneksi database SQLite."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """
    Fungsi inisialisasi struktur tabel database SQLite:
    1. tabel_armada     : ID_Kendaraan, Jenis (Mobil/Motor), Nama_Kendaraan, Plat, Biaya_Sewa, Status (Ready/Keluar)
    2. tabel_sewa       : ID_Sewa, ID_Kendaraan, Nama, Waktu_Mulai, Waktu_Selesai, Status_Sewa, Total_Biaya
    3. tabel_kas        : ID_Transaksi, Tipe (Masuk/Keluar), Kategori, Nominal, Tanggal
    4. tabel_pengaturan : Menyimpan status seeding agar jika data contoh dihapus tidak muncul kembali otomatis.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Tabel Pengaturan (Flag Seeding)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tabel_pengaturan (
            Kunci TEXT PRIMARY KEY,
            Nilai TEXT
        );
    """)

    # 1. Tabel Armada
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tabel_armada (
            ID_Kendaraan INTEGER PRIMARY KEY AUTOINCREMENT,
            Jenis TEXT NOT NULL CHECK(Jenis IN ('Mobil', 'Motor')),
            Nama_Kendaraan TEXT NOT NULL DEFAULT '-',
            Plat TEXT UNIQUE NOT NULL,
            Biaya_Sewa REAL NOT NULL DEFAULT 0,
            Status TEXT NOT NULL DEFAULT 'Ready' CHECK(Status IN ('Ready', 'Keluar'))
        );
    """)

    # Migrasi otomatis jika tabel_armada belum memiliki kolom Nama_Kendaraan atau Biaya_Sewa
    cursor.execute("PRAGMA table_info(tabel_armada)")
    armada_cols = [row[1] for row in cursor.fetchall()]
    if 'Nama_Kendaraan' not in armada_cols:
        cursor.execute("ALTER TABLE tabel_armada ADD COLUMN Nama_Kendaraan TEXT DEFAULT '-'")
    if 'Biaya_Sewa' not in armada_cols:
        cursor.execute("ALTER TABLE tabel_armada ADD COLUMN Biaya_Sewa REAL DEFAULT 0")

    # 2. Tabel Sewa
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tabel_sewa (
            ID_Sewa INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_Kendaraan INTEGER NOT NULL,
            Nama TEXT NOT NULL,
            Waktu_Mulai TEXT NOT NULL,
            Waktu_Selesai TEXT,
            Status_Sewa TEXT NOT NULL DEFAULT 'Berjalan' CHECK(Status_Sewa IN ('Berjalan', 'Selesai')),
            Total_Biaya REAL DEFAULT 0,
            FOREIGN KEY (ID_Kendaraan) REFERENCES tabel_armada(ID_Kendaraan)
        );
    """)

    # Migrasi otomatis jika tabel_sewa belum memiliki kolom Total_Biaya
    cursor.execute("PRAGMA table_info(tabel_sewa)")
    sewa_cols = [row[1] for row in cursor.fetchall()]
    if 'Total_Biaya' not in sewa_cols:
        cursor.execute("ALTER TABLE tabel_sewa ADD COLUMN Total_Biaya REAL DEFAULT 0")

    # 3. Tabel Kas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tabel_kas (
            ID_Transaksi INTEGER PRIMARY KEY AUTOINCREMENT,
            Tipe TEXT NOT NULL CHECK(Tipe IN ('Masuk', 'Keluar')),
            Kategori TEXT NOT NULL,
            Nominal REAL NOT NULL,
            Tanggal TEXT NOT NULL
        );
    """)

    # Cek status seeding: hanya isi data contoh jika database benar-benar baru
    cursor.execute("SELECT Nilai FROM tabel_pengaturan WHERE Kunci = 'is_seeded'")
    seeded_status = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM tabel_armada")
    armada_count = cursor.fetchone()[0]

    if seeded_status is None and armada_count == 0:
        armada_awal = [
            ('Mobil', 'Toyota Avanza 1.3 G', 'B 1234 ABC', 350000, 'Ready'),
            ('Mobil', 'Mitsubishi Xpander Ultimate', 'B 5678 DEF', 450000, 'Keluar'),
            ('Mobil', 'Honda Brio RS', 'D 9101 GHI', 300000, 'Ready'),
            ('Mobil', 'Toyota Innova Reborn', 'B 2345 JKL', 550000, 'Ready'),
            ('Motor', 'Honda Vario 160', 'B 6789 MNO', 90000, 'Ready'),
            ('Motor', 'Yamaha NMAX 155', 'B 3456 PQR', 120000, 'Keluar'),
            ('Motor', 'Honda Beat Street', 'F 7890 STU', 75000, 'Ready'),
            ('Motor', 'Yamaha Aerox 155', 'D 4321 VWX', 110000, 'Ready')
        ]
        cursor.executemany(
            "INSERT INTO tabel_armada (Jenis, Nama_Kendaraan, Plat, Biaya_Sewa, Status) VALUES (?, ?, ?, ?, ?)",
            armada_awal
        )

        sewa_awal = [
            (2, 'Ahmad Fauzi', '2026-10-15 09:00', '2026-10-19 18:00', 'Berjalan', 1800000),
            (6, 'Rian Hidayat', '2026-10-17 14:00', '2026-10-20 12:00', 'Berjalan', 360000),
            (1, 'Siti Nurhaliza', '2026-09-05 10:00', '2026-09-07 10:00', 'Selesai', 700000),
            (5, 'Budi Santoso', '2026-09-12 08:00', '2026-09-14 08:00', 'Selesai', 180000)
        ]
        cursor.executemany(
            "INSERT INTO tabel_sewa (ID_Kendaraan, Nama, Waktu_Mulai, Waktu_Selesai, Status_Sewa, Total_Biaya) VALUES (?, ?, ?, ?, ?, ?)",
            sewa_awal
        )

        kas_awal = [
            ('Masuk', 'Sewa Kendaraan', 1200000, '2026-07-10'),
            ('Keluar', 'Servis & Oli Mobil', 450000, '2026-07-15'),
            ('Masuk', 'Sewa Kendaraan', 2500000, '2026-08-05'),
            ('Keluar', 'Gaji & Operasional', 1000000, '2026-08-28'),
            ('Masuk', 'Sewa Kendaraan', 3200000, '2026-09-02'),
            ('Keluar', 'Cuci & Salon Mobil', 250000, '2026-09-15'),
            ('Masuk', 'Sewa Kendaraan', 2800000, '2026-10-01'),
            ('Masuk', 'Sewa Kendaraan', 850000, '2026-10-15'),
            ('Keluar', 'Bahan Bakar & Tol', 300000, '2026-10-16')
        ]
        cursor.executemany(
            "INSERT INTO tabel_kas (Tipe, Kategori, Nominal, Tanggal) VALUES (?, ?, ?, ?)",
            kas_awal
        )

        cursor.execute("INSERT OR REPLACE INTO tabel_pengaturan (Kunci, Nilai) VALUES ('is_seeded', '1')")

    conn.commit()
    conn.close()

# -----------------------------------------------------------------------------
# FUNGSI DATA ACCESS & TRANSAKSI (PANDAS & SQLITE)
# -----------------------------------------------------------------------------

def load_armada():
    """Mengambil seluruh data armada ke dalam Pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM tabel_armada ORDER BY ID_Kendaraan ASC", conn)
    conn.close()
    return df

def load_sewa_aktif():
    """Mengambil data sewa dengan Status_Sewa = 'Berjalan' beserta informasi armada."""
    conn = get_connection()
    query = """
        SELECT 
            s.ID_Sewa,
            s.ID_Kendaraan,
            a.Jenis,
            a.Nama_Kendaraan,
            a.Plat,
            a.Biaya_Sewa,
            s.Nama,
            s.Waktu_Mulai,
            s.Waktu_Selesai,
            s.Status_Sewa,
            s.Total_Biaya
        FROM tabel_sewa s
        JOIN tabel_armada a ON s.ID_Kendaraan = a.ID_Kendaraan
        WHERE s.Status_Sewa = 'Berjalan'
        ORDER BY s.ID_Sewa DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def load_riwayat_sewa():
    """Mengambil riwayat semua transaksi sewa."""
    conn = get_connection()
    query = """
        SELECT 
            s.ID_Sewa,
            s.Nama,
            a.Jenis,
            a.Nama_Kendaraan,
            a.Plat,
            s.Waktu_Mulai,
            s.Waktu_Selesai,
            s.Status_Sewa,
            s.Total_Biaya
        FROM tabel_sewa s
        JOIN tabel_armada a ON s.ID_Kendaraan = a.ID_Kendaraan
        ORDER BY s.ID_Sewa DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def load_kas():
    """Mengambil seluruh data transaksi kas ke dalam Pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM tabel_kas ORDER BY Tanggal DESC, ID_Transaksi DESC", conn)
    conn.close()
    return df

def tambah_armada_baru(jenis, nama_kendaraan, plat, biaya_sewa):
    """Menambahkan kendaraan baru (jenis, nama/tipe mobil, nomor plat, biaya sewa) ke tabel_armada."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        plat_clean = plat.strip().upper()
        nama_clean = nama_kendaraan.strip()
        cursor.execute("""
            INSERT INTO tabel_armada (Jenis, Nama_Kendaraan, Plat, Biaya_Sewa, Status)
            VALUES (?, ?, ?, ?, 'Ready')
        """, (jenis, nama_clean, plat_clean, float(biaya_sewa)))
        conn.commit()
        return True, f"Armada baru [{jenis} - {nama_clean} ({plat_clean})] berhasil ditambahkan dengan status 'Ready'!"
    except sqlite3.IntegrityError:
        return False, f"Nomor plat '{plat.strip().upper()}' sudah terdaftar dalam sistem."
    except Exception as e:
        return False, f"Gagal menambahkan armada: {str(e)}"
    finally:
        conn.close()

def update_armada(id_kendaraan, jenis, nama_kendaraan, plat, biaya_sewa, status):
    """Memperbarui informasi kendaraan armada yang sudah ada."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE tabel_armada
            SET Jenis = ?, Nama_Kendaraan = ?, Plat = ?, Biaya_Sewa = ?, Status = ?
            WHERE ID_Kendaraan = ?
        """, (jenis, nama_kendaraan.strip(), plat.strip().upper(), float(biaya_sewa), status, id_kendaraan))
        conn.commit()
        return True, f"Data armada '{nama_kendaraan}' ({plat.strip().upper()}) berhasil diperbarui!"
    except sqlite3.IntegrityError:
        return False, f"Nomor plat '{plat.strip().upper()}' sudah digunakan oleh kendaraan lain."
    except Exception as e:
        return False, f"Gagal memperbarui armada: {str(e)}"
    finally:
        conn.close()

def hapus_armada(id_kendaraan):
    """Menghapus kendaraan dari tabel_armada."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Status, Nama_Kendaraan, Plat FROM tabel_armada WHERE ID_Kendaraan = ?", (id_kendaraan,))
        row = cursor.fetchone()
        if not row:
            return False, "Armada tidak ditemukan."
        if row['Status'] == 'Keluar':
            return False, f"Kendaraan '{row['Nama_Kendaraan']}' ({row['Plat']}) tidak dapat dihapus karena saat ini statusnya sedang KELUAR (disewa)."
        
        # Hapus riwayat sewa terkait kendaraan ini
        cursor.execute("DELETE FROM tabel_sewa WHERE ID_Kendaraan = ?", (id_kendaraan,))
        cursor.execute("DELETE FROM tabel_armada WHERE ID_Kendaraan = ?", (id_kendaraan,))
        conn.commit()
        return True, f"Armada '{row['Nama_Kendaraan']}' ({row['Plat']}) berhasil dihapus."
    except Exception as e:
        return False, f"Gagal menghapus armada: {str(e)}"
    finally:
        conn.close()

def kosongkan_semua_armada():
    """Mengosongkan semua data armada agar pengguna bisa mengisinya dari nol."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM tabel_sewa")
        cursor.execute("DELETE FROM tabel_armada")
        cursor.execute("INSERT OR REPLACE INTO tabel_pengaturan (Kunci, Nilai) VALUES ('is_seeded', '1')")
        conn.commit()
        return True, "Semua data armada bawaan berhasil dibersihkan! Tabel kini kosong dan siap diisi armada Anda sendiri."
    except Exception as e:
        return False, f"Gagal mengosongkan data armada: {str(e)}"
    finally:
        conn.close()

def proses_penyewaan_baru(id_kendaraan, nama, waktu_mulai, waktu_selesai, total_biaya=0, catat_kas=True):
    """
    Mencatat penyewaan baru:
    1. Insert data ke tabel_sewa
    2. Otomatis UPDATE status di tabel_armada menjadi 'Keluar'
    3. Jika catat_kas=True dan nominal > 0, otomatis mencatat kas masuk ke tabel_kas
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO tabel_sewa (ID_Kendaraan, Nama, Waktu_Mulai, Waktu_Selesai, Status_Sewa, Total_Biaya)
            VALUES (?, ?, ?, ?, 'Berjalan', ?)
        """, (id_kendaraan, nama, waktu_mulai, waktu_selesai, total_biaya))

        cursor.execute("""
            UPDATE tabel_armada
            SET Status = 'Keluar'
            WHERE ID_Kendaraan = ?
        """, (id_kendaraan,))

        if catat_kas and total_biaya > 0:
            tanggal_hari_ini = date.today().strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO tabel_kas (Tipe, Kategori, Nominal, Tanggal)
                VALUES ('Masuk', 'Sewa Kendaraan', ?, ?)
            """, (total_biaya, tanggal_hari_ini))

        conn.commit()
        return True, "Penyewaan berhasil dicatat dan status armada kini 'Keluar'!"
    except Exception as e:
        conn.rollback()
        return False, f"Terjadi kesalahan saat menyimpan sewa: {str(e)}"
    finally:
        conn.close()

def proses_pengembalian_kendaraan(id_sewa, id_kendaraan, waktu_kembali):
    """
    Memproses pengembalian kendaraan:
    1. Update Status_Sewa di tabel_sewa menjadi 'Selesai' dan perbarui Waktu_Selesai
    2. Update status kendaraan di tabel_armada kembali menjadi 'Ready'
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE tabel_sewa
            SET Status_Sewa = 'Selesai', Waktu_Selesai = ?
            WHERE ID_Sewa = ?
        """, (waktu_kembali, id_sewa))

        cursor.execute("""
            UPDATE tabel_armada
            SET Status = 'Ready'
            WHERE ID_Kendaraan = ?
        """, (id_kendaraan,))

        conn.commit()
        return True, "Kendaraan berhasil dikembalikan! Status armada kembali 'Ready'."
    except Exception as e:
        conn.rollback()
        return False, f"Terjadi kesalahan pengembalian: {str(e)}"
    finally:
        conn.close()

def tambah_transaksi_kas(tipe, kategori, nominal, tanggal):
    """Menambahkan pencatatan kas masuk atau kas keluar."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO tabel_kas (Tipe, Kategori, Nominal, Tanggal)
            VALUES (?, ?, ?, ?)
        """, (tipe, kategori, nominal, tanggal))
        conn.commit()
        return True, f"Transaksi kas {tipe.lower()} berhasil disimpan!"
    except Exception as e:
        conn.rollback()
        return False, f"Gagal mencatat transaksi kas: {str(e)}"
    finally:
        conn.close()

def format_rupiah(nominal):
    """Format angka ke format Rupiah (Rp)."""
    if pd.isna(nominal) or nominal is None:
        return "Rp 0"
    return f"Rp {float(nominal):,.0f}".replace(",", ".")

# -----------------------------------------------------------------------------
# 3. MODUL TAMPILAN HALAMAN (VIEW STREAMLIT)
# -----------------------------------------------------------------------------

def render_dashboard_armada():
    """Halaman 1: Dashboard Armada, Pengisian Mandiri, dan Manajemen Armada."""
    st.markdown('<div class="main-title">📊 Dashboard Monitoring Armada</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Kelola dan pantau ketersediaan armada rental mobil dan motor secara mandiri.</div>', unsafe_allow_html=True)

    df_armada = load_armada()

    # Perhitungan Metrik menggunakan Pandas
    total_kendaraan = len(df_armada)
    total_ready = len(df_armada[df_armada['Status'] == 'Ready']) if not df_armada.empty else 0
    total_keluar = len(df_armada[df_armada['Status'] == 'Keluar']) if not df_armada.empty else 0
    persen_ready = (total_ready / total_kendaraan * 100) if total_kendaraan > 0 else 0

    mobil_ready = len(df_armada[(df_armada['Jenis'] == 'Mobil') & (df_armada['Status'] == 'Ready')]) if not df_armada.empty else 0
    motor_ready = len(df_armada[(df_armada['Jenis'] == 'Motor') & (df_armada['Status'] == 'Ready')]) if not df_armada.empty else 0

    # Tampilan Metrik Angka Besar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Armada", value=f"{total_kendaraan} Unit")
    with col2:
        st.metric(label="🟢 Armada READY", value=f"{total_ready} Unit", delta=f"{persen_ready:.1f}% Tersedia" if total_kendaraan > 0 else "0%")
    with col3:
        st.metric(label="🔴 Armada KELUAR", value=f"{total_keluar} Unit", delta=f"-{100-persen_ready:.1f}% Disewa" if total_kendaraan > 0 else "0%", delta_color="inverse")
    with col4:
        st.metric(label="🚗 Mobil / 🛵 Motor Ready", value=f"{mobil_ready} Mobil / {motor_ready} Motor")

    st.markdown("---")

    # TAB INTERAKTIF: TABEL DATA, FORM INPUT SENDIRI, EDIT & HAPUS
    tab_tabel, tab_input_mandiri, tab_edit_hapus, tab_reset = st.tabs([
        "📋 Tabel Data Armada",
        "➕ Tambah Armada Sendiri",
        "✏️ Edit / Hapus Armada",
        "🗑️ Kosongkan / Reset Data"
    ])

    # -----------------------------------
    # TAB 1: TABEL DATA ARMADA & FILTER
    # -----------------------------------
    with tab_tabel:
        if df_armada.empty:
            st.warning("⚠️ Tabel data armada saat ini masih kosong.")
            st.info("👉 Silakan buka tab **'➕ Tambah Armada Sendiri'** di atas untuk mulai memasukkan unit mobil/motor rental Anda.")
        else:
            col_filter1, col_filter2, col_search = st.columns([1, 1, 2])
            with col_filter1:
                filter_jenis = st.selectbox("Filter Kategori", ["Semua", "Mobil", "Motor"], key="filter_kat_dash")
            with col_filter2:
                filter_status = st.selectbox("Filter Status", ["Semua", "Ready", "Keluar"], key="filter_stat_dash")
            with col_search:
                cari_kata = st.text_input("Cari Jenis/Tipe Kendaraan atau Plat", placeholder="Contoh: Avanza / B 1234", key="search_dash")

            # Eksekusi Filter dengan Pandas
            df_filtered = df_armada.copy()
            if filter_jenis != "Semua":
                df_filtered = df_filtered[df_filtered['Jenis'] == filter_jenis]
            if filter_status != "Semua":
                df_filtered = df_filtered[df_filtered['Status'] == filter_status]
            if cari_kata:
                df_filtered = df_filtered[
                    df_filtered['Plat'].str.contains(cari_kata, case=False, na=False) |
                    df_filtered['Nama_Kendaraan'].str.contains(cari_kata, case=False, na=False)
                ]

            col_table, col_chart = st.columns([3, 2])

            with col_table:
                st.subheader("📋 Tabel Data Armada")
                df_display = df_filtered[['ID_Kendaraan', 'Jenis', 'Nama_Kendaraan', 'Plat', 'Status', 'Biaya_Sewa']].copy()
                df_display['Tarif / Hari'] = df_display['Biaya_Sewa'].apply(format_rupiah)
                df_display = df_display.drop(columns=['Biaya_Sewa']).rename(
                    columns={
                        'ID_Kendaraan': 'ID',
                        'Jenis': 'Kategori',
                        'Nama_Kendaraan': 'Jenis / Tipe Mobil & Motor',
                        'Plat': 'Nomor Plat',
                        'Status': 'Status Armada'
                    }
                )
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                st.caption(f"Menampilkan {len(df_filtered)} dari total {total_kendaraan} kendaraan.")

            with col_chart:
                st.subheader("📊 Distribusi Status Armada")
                fig, ax = plt.subplots(figsize=(5, 3.5))
                counts = [total_ready, total_keluar]
                labels = ['Ready', 'Keluar']
                colors = ['#10b981', '#ef4444']
                
                bars = ax.bar(labels, counts, color=colors, width=0.5, edgecolor='#374151')
                ax.set_ylabel('Jumlah Unit')
                ax.set_ylim(0, max(counts) + 2 if max(counts) > 0 else 5)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom', fontweight='bold')
                
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

    # -----------------------------------
    # TAB 2: FORM TAMBAH ARMADA SENDIRI
    # -----------------------------------
    with tab_input_mandiri:
        st.subheader("➕ Formulir Tambah Armada Sendiri")
        st.markdown("Isikan data mobil atau motor rental Anda di bawah ini:")

        with st.form("form_tambah_mandiri", clear_on_submit=True):
            col_k1, col_k2 = st.columns(2)
            with col_k1:
                kategori_baru = st.radio("1. Kategori Armada:", ["Mobil", "Motor"], horizontal=True)
                nama_baru = st.text_input(
                    "2. Jenis / Model Mobil atau Motor:",
                    placeholder="Contoh: Toyota Avanza 1.3 / Honda Brio / Yamaha NMAX",
                    help="Tuliskan merk dan tipe kendaraan Anda"
                )
            with col_k2:
                plat_baru = st.text_input(
                    "3. Nomor Plat Kendaraan:",
                    placeholder="Contoh: B 1234 ABC / D 9876 XYZ",
                    help="Nomor plat harus unik dan belum pernah didaftarkan"
                )
                tarif_baru = st.number_input(
                    "4. Tarif Biaya Sewa per Hari (Rp):",
                    min_value=10000,
                    value=350000 if kategori_baru == "Mobil" else 100000,
                    step=25000,
                    help="Tarif sewa standar harian untuk kendaraan ini"
                )

            st.caption("ℹ️ Kendaraan baru yang disimpan akan otomatis aktif dengan status **'Ready'**.")
            submitted_baru = st.form_submit_button("💾 Simpan Armada ke Database", use_container_width=True)

            if submitted_baru:
                if not nama_baru.strip():
                    st.error("Jenis/Tipe mobil atau motor wajib diisi!")
                elif not plat_baru.strip():
                    st.error("Nomor plat kendaraan tidak boleh kosong!")
                else:
                    sukses, pesan = tambah_armada_baru(kategori_baru, nama_baru, plat_baru, tarif_baru)
                    if sukses:
                        st.success(pesan)
                        st.rerun()
                    else:
                        st.error(pesan)

    # -----------------------------------
    # TAB 3: EDIT ATAU HAPUS ARMADA
    # -----------------------------------
    with tab_edit_hapus:
        st.subheader("✏️ Edit atau Hapus Data Armada")

        if df_armada.empty:
            st.info("Belum ada unit armada yang dapat diedit atau dihapus.")
        else:
            opsi_edit = {
                f"ID {row['ID_Kendaraan']} | [{row['Jenis']}] {row['Nama_Kendaraan']} - {row['Plat']} ({format_rupiah(row['Biaya_Sewa'])})": row['ID_Kendaraan']
                for _, row in df_armada.iterrows()
            }

            pilihan_unit = st.selectbox("Pilih Kendaraan yang Ingin Diperbarui / Dihapus:", list(opsi_edit.keys()))
            id_terpilih = opsi_edit[pilihan_unit]
            data_row = df_armada[df_armada['ID_Kendaraan'] == id_terpilih].iloc[0]

            with st.form(f"form_edit_armada_{id_terpilih}"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    edit_jenis = st.selectbox("Kategori", ["Mobil", "Motor"], index=0 if data_row['Jenis'] == "Mobil" else 1)
                    edit_nama = st.text_input("Jenis / Tipe Mobil & Motor", value=data_row['Nama_Kendaraan'])
                    edit_status = st.selectbox("Status Ketersediaan", ["Ready", "Keluar"], index=0 if data_row['Status'] == "Ready" else 1)

                with col_e2:
                    edit_plat = st.text_input("Nomor Plat", value=data_row['Plat'])
                    edit_tarif = st.number_input("Tarif Biaya Sewa per Hari (Rp)", min_value=10000, value=int(data_row['Biaya_Sewa']), step=25000)

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit_update = st.form_submit_button("💾 Simpan Perubahan", use_container_width=True)
                with col_btn2:
                    st.caption("Untuk menghapus armada ini, gunakan tombol hapus di bawah.")

            if submit_update:
                if not edit_nama.strip() or not edit_plat.strip():
                    st.error("Nama kendaraan dan nomor plat tidak boleh kosong!")
                else:
                    sukses, pesan = update_armada(id_terpilih, edit_jenis, edit_nama, edit_plat, edit_tarif, edit_status)
                    if sukses:
                        st.success(pesan)
                        st.rerun()
                    else:
                        st.error(pesan)

            st.markdown("---")
            col_del1, col_del2 = st.columns([2, 1])
            with col_del1:
                st.write(f"Hapus unit: **{data_row['Nama_Kendaraan']} ({data_row['Plat']})**")
            with col_del2:
                if st.button("🗑️ Hapus Armada Ini", type="secondary", use_container_width=True):
                    sukses_del, pesan_del = hapus_armada(id_terpilih)
                    if sukses_del:
                        st.success(pesan_del)
                        st.rerun()
                    else:
                        st.error(pesan_del)

    # -----------------------------------
    # TAB 4: KOSONGKAN / RESET DATA
    # -----------------------------------
    with tab_reset:
        st.subheader("🗑️ Kosongkan Data Bawaan (Mulai dari Nol)")
        st.warning("""
        **Perhatian:** 
        Fitur ini akan menghapus semua unit kendaraan bawaan/contoh dari database.
        Gunakan opsi ini jika Anda ingin mengosongkan tabel dan mulai mengisi seluruh data armada rental Anda sendiri dari awal secara bersih.
        """)

        konfirmasi = st.checkbox("Saya yakin ingin mengosongkan semua data armada bawaan.")
        if st.button("🚨 Kosongkan Semua Data Armada Sekarang", type="primary", disabled=not konfirmasi):
            sukses_reset, pesan_reset = kosongkan_semua_armada()
            if sukses_reset:
                st.success(pesan_reset)
                st.rerun()
            else:
                st.error(pesan_reset)


def render_halaman_transaksi():
    """Halaman 2: Transaksi Penyewaan Baru & Pengembalian Kendaraan."""
    st.markdown('<div class="main-title">📝 Transaksi Rental & Pengembalian</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Kelola penyewaan kendaraan baru lengkap dengan jenis mobil, plat, dan biaya sewa.</div>', unsafe_allow_html=True)

    tab_sewa, tab_kembali, tab_riwayat = st.tabs(["➕ Input Sewa Baru", "🔄 Proses Pengembalian", "📜 Riwayat Transaksi"])

    # -----------------------------------
    # TAB 1: FORM INPUT SEWA BARU
    # -----------------------------------
    with tab_sewa:
        st.subheader("Form Input Penyewaan Kendaraan")
        st.info("💡 Kendaraan yang disewa otomatis berubah statusnya menjadi **'Keluar'** di tabel armada.")

        df_armada = load_armada()
        kendaraan_ready = df_armada[df_armada['Status'] == 'Ready'] if not df_armada.empty else pd.DataFrame()

        if kendaraan_ready.empty:
            if df_armada.empty:
                st.warning("⚠️ Belum ada kendaraan di database. Silakan isi data armada di menu **'Dashboard Armada'** atau **'Kelola Data Armada'** terlebih dahulu.")
            else:
                st.error("❌ Saat ini tidak ada kendaraan yang berstatus 'Ready'. Semua armada sedang disewa keluar.")
        else:
            opsi_kendaraan = {}
            for _, row in kendaraan_ready.iterrows():
                label = f"[{row['Jenis']}] {row['Nama_Kendaraan']} - {row['Plat']} (Tarif: {format_rupiah(row['Biaya_Sewa'])}/hari)"
                opsi_kendaraan[label] = {
                    'ID_Kendaraan': row['ID_Kendaraan'],
                    'Nama_Kendaraan': row['Nama_Kendaraan'],
                    'Plat': row['Plat'],
                    'Biaya_Sewa': row['Biaya_Sewa']
                }

            with st.form("form_sewa_baru", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    kendaraan_terpilih = st.selectbox("Pilih Kendaraan (Status Ready):", list(opsi_kendaraan.keys()))
                    data_terpilih = opsi_kendaraan[kendaraan_terpilih]
                    
                    nama_penyewa = st.text_input("Nama Lengkap Penyewa", placeholder="Contoh: Budi Santoso")
                    total_biaya = st.number_input(
                        "Total Biaya Sewa (Rp)",
                        min_value=0,
                        value=int(data_terpilih['Biaya_Sewa']) if data_terpilih['Biaya_Sewa'] > 0 else 350000,
                        step=50000,
                        help="Default otomatis mengikuti tarif sewa harian kendaraan yang dipilih. Dapat disesuaikan dengan durasi hari."
                    )

                with col2:
                    tgl_mulai = st.date_input("Tanggal Mulai Sewa", value=date.today())
                    jam_mulai = st.time_input("Jam Mulai Sewa", value=datetime.now().time())
                    tgl_selesai = st.date_input("Perkiraan Tanggal Selesai", value=date.today())
                    jam_selesai = st.time_input("Perkiraan Jam Selesai", value=datetime.now().time())

                catat_ke_kas = st.checkbox("Otomatis catat pembayaran sewa ini ke Kas Pemasukan", value=True)
                submitted = st.form_submit_button("🚀 Konfirmasi & Simpan Penyewaan", use_container_width=True)

                if submitted:
                    if not nama_penyewa.strip():
                        st.error("Nama penyewa wajib diisi!")
                    else:
                        id_kendaraan = data_terpilih['ID_Kendaraan']
                        waktu_mulai_str = f"{tgl_mulai} {jam_mulai.strftime('%H:%M')}"
                        waktu_selesai_str = f"{tgl_selesai} {jam_selesai.strftime('%H:%M')}"

                        sukses, pesan = proses_penyewaan_baru(
                            id_kendaraan,
                            nama_penyewa.strip(),
                            waktu_mulai_str,
                            waktu_selesai_str,
                            total_biaya,
                            catat_ke_kas
                        )
                        if sukses:
                            st.success(pesan)
                            st.rerun()
                        else:
                            st.error(pesan)

    # -----------------------------------
    # TAB 2: PENGEMBALIAN KENDARAAN
    # -----------------------------------
    with tab_kembali:
        st.subheader("Pengembalian Kendaraan (Status Sewa: Berjalan)")
        st.info("💡 Menekan tombol pengembalian akan mengubah Status Sewa menjadi **'Selesai'** dan status armada kembali menjadi **'Ready'**.")

        df_aktif = load_sewa_aktif()

        if df_aktif.empty:
            st.success("✅ Saat ini tidak ada kendaraan yang sedang disewa keluar. Semua armada berada di garasi (Ready)!")
        else:
            st.write(f"Terdapat **{len(df_aktif)} transaksi sewa aktif**:")
            df_display_aktif = df_aktif[['ID_Sewa', 'Nama', 'Jenis', 'Nama_Kendaraan', 'Plat', 'Total_Biaya', 'Waktu_Mulai', 'Waktu_Selesai', 'Status_Sewa']].copy()
            df_display_aktif['Total_Biaya'] = df_display_aktif['Total_Biaya'].apply(format_rupiah)
            df_display_aktif = df_display_aktif.rename(
                columns={
                    'ID_Sewa': 'ID Sewa',
                    'Nama': 'Penyewa',
                    'Jenis': 'Kategori',
                    'Nama_Kendaraan': 'Jenis/Tipe Kendaraan',
                    'Plat': 'No Plat',
                    'Total_Biaya': 'Biaya Sewa',
                    'Waktu_Mulai': 'Mulai Sewa',
                    'Waktu_Selesai': 'Est. Selesai',
                    'Status_Sewa': 'Status'
                }
            )
            st.dataframe(df_display_aktif, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("#### Form Konfirmasi Pengembalian")

            opsi_pengembalian = {
                f"ID Sewa: {row['ID_Sewa']} | {row['Nama']} - {row['Nama_Kendaraan']} [{row['Plat']}]": (row['ID_Sewa'], row['ID_Kendaraan'])
                for _, row in df_aktif.iterrows()
            }

            col_kembali1, col_kembali2 = st.columns([2, 1])
            with col_kembali1:
                sewa_pilihan = st.selectbox("Pilih Transaksi yang Ingin Dikembalikan:", list(opsi_pengembalian.keys()))
            with col_kembali2:
                waktu_kembali_aktual = st.text_input("Waktu Kembali Aktual", value=datetime.now().strftime("%Y-%m-%d %H:%M"))

            if st.button("🔄 Proses Pengembalian (Ubah ke Ready)", type="primary", use_container_width=True):
                id_sewa_selected, id_kendaraan_selected = opsi_pengembalian[sewa_pilihan]
                sukses, pesan = proses_pengembalian_kendaraan(id_sewa_selected, id_kendaraan_selected, waktu_kembali_aktual)
                if sukses:
                    st.success(pesan)
                    st.rerun()
                else:
                    st.error(pesan)

    # -----------------------------------
    # TAB 3: RIWAYAT SEWA
    # -----------------------------------
    with tab_riwayat:
        st.subheader("📜 Riwayat Keseluruhan Transaksi Sewa")
        df_riwayat = load_riwayat_sewa()
        if df_riwayat.empty:
            st.info("Belum ada riwayat transaksi sewa.")
        else:
            cari_nama = st.text_input("Cari Riwayat berdasarkan Nama Penyewa / Tipe / Plat", placeholder="Ketik kata kunci...")
            if cari_nama:
                df_riwayat = df_riwayat[
                    df_riwayat['Nama'].str.contains(cari_nama, case=False, na=False) |
                    df_riwayat['Nama_Kendaraan'].str.contains(cari_nama, case=False, na=False) |
                    df_riwayat['Plat'].str.contains(cari_nama, case=False, na=False)
                ]
            
            df_riwayat_tampil = df_riwayat.copy()
            df_riwayat_tampil['Total_Biaya'] = df_riwayat_tampil['Total_Biaya'].apply(format_rupiah)
            df_riwayat_tampil = df_riwayat_tampil.rename(columns={
                'ID_Sewa': 'ID',
                'Nama': 'Penyewa',
                'Jenis': 'Kategori',
                'Nama_Kendaraan': 'Jenis/Tipe Kendaraan',
                'Plat': 'No Plat',
                'Total_Biaya': 'Biaya Sewa',
                'Waktu_Mulai': 'Mulai',
                'Waktu_Selesai': 'Selesai',
                'Status_Sewa': 'Status'
            })
            st.dataframe(df_riwayat_tampil, use_container_width=True, hide_index=True)


def render_halaman_keuangan():
    """Halaman 3: Form Input Kas & Visualisasi Tren Arus Kas Bulanan."""
    st.markdown('<div class="main-title">💰 Keuangan & Arus Kas Rental</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Monitor arus kas pemasukan dan pengeluaran operasional serta tren keuangan bulanan.</div>', unsafe_allow_html=True)

    df_kas = load_kas()

    if not df_kas.empty:
        total_masuk = df_kas[df_kas['Tipe'] == 'Masuk']['Nominal'].sum()
        total_keluar = df_kas[df_kas['Tipe'] == 'Keluar']['Nominal'].sum()
        saldo_bersih = total_masuk - total_keluar
    else:
        total_masuk = 0
        total_keluar = 0
        saldo_bersih = 0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label="Total Pemasukan (Kas Masuk)", value=format_rupiah(total_masuk))
    with m2:
        st.metric(label="Total Pengeluaran (Kas Keluar)", value=format_rupiah(total_keluar))
    with m3:
        st.metric(label="Saldo Bersih (Net Cash Flow)", value=format_rupiah(saldo_bersih))

    st.markdown("---")

    col_input, col_chart = st.columns([1, 2])

    with col_input:
        st.subheader("➕ Catat Kas Baru")
        with st.form("form_kas", clear_on_submit=True):
            tipe = st.radio("Tipe Transaksi", ["Masuk", "Keluar"], horizontal=True)

            kategori_pilihan = {
                "Masuk": ["Sewa Kendaraan", "Denda Keterlambatan", "Layanan Sopir", "Pendapatan Lain-lain"],
                "Keluar": ["Servis & Sparepart", "Bahan Bakar & Tol", "Gaji & Komisi", "Cuci Kendaraan", "Pajak & Asuransi", "Operasional Kantor", "Lain-lain"]
            }

            kategori = st.selectbox("Kategori Transaksi", kategori_pilihan[tipe])
            nominal = st.number_input("Nominal Transaksi (Rp)", min_value=1000, value=150000, step=10000)
            tanggal_trx = st.date_input("Tanggal Transaksi", value=date.today())

            submit_kas = st.form_submit_button("💾 Simpan Transaksi Kas", use_container_width=True)

            if submit_kas:
                tanggal_str = tanggal_trx.strftime('%Y-%m-%d')
                sukses, pesan = tambah_transaksi_kas(tipe, kategori, nominal, tanggal_str)
                if sukses:
                    st.success(pesan)
                    st.rerun()
                else:
                    st.error(pesan)

    with col_chart:
        st.subheader("📈 Tren Arus Kas Bulanan (Pemasukan vs Pengeluaran)")

        if df_kas.empty:
            st.info("Belum ada data kas untuk divisualisasikan.")
        else:
            df_chart = df_kas.copy()
            df_chart['Tanggal'] = pd.to_datetime(df_chart['Tanggal'])
            df_chart['Bulan'] = df_chart['Tanggal'].dt.to_period('M').astype(str)

            pivot_kas = df_chart.pivot_table(
                index='Bulan',
                columns='Tipe',
                values='Nominal',
                aggfunc='sum',
                fill_value=0
            )

            if 'Masuk' not in pivot_kas.columns:
                pivot_kas['Masuk'] = 0
            if 'Keluar' not in pivot_kas.columns:
                pivot_kas['Keluar'] = 0

            pivot_kas['Net'] = pivot_kas['Masuk'] - pivot_kas['Keluar']
            pivot_kas = pivot_kas.sort_index()

            sns.set_theme(style="whitegrid")
            fig, ax = plt.subplots(figsize=(8, 4.2))

            x_indices = range(len(pivot_kas))
            bar_width = 0.35

            ax.bar([i - bar_width/2 for i in x_indices], pivot_kas['Masuk'] / 1e6,
                   width=bar_width, label='Pemasukan (Masuk)', color='#10b981', alpha=0.9)
            ax.bar([i + bar_width/2 for i in x_indices], pivot_kas['Keluar'] / 1e6,
                   width=bar_width, label='Pengeluaran (Keluar)', color='#ef4444', alpha=0.9)

            ax.plot(list(x_indices), pivot_kas['Net'] / 1e6, color='#3b82f6', marker='o',
                    linewidth=2.5, label='Net Cash Flow')

            ax.set_title('Perbandingan Pemasukan, Pengeluaran & Net (Juta Rp)', fontsize=12, fontweight='bold', pad=12)
            ax.set_xlabel('Periode Bulan', fontsize=10)
            ax.set_ylabel('Nominal (Juta Rupiah)', fontsize=10)
            ax.set_xticks(list(x_indices))
            ax.set_xticklabels(pivot_kas.index, rotation=30, ha='right')
            ax.legend(loc='upper left', frameon=True)
            ax.grid(axis='y', linestyle='--', alpha=0.7)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    st.markdown("---")
    st.subheader("📑 Riwayat Lengkap Buku Kas")
    
    col_k1, col_k2 = st.columns([1, 3])
    with col_k1:
        filter_tipe_kas = st.selectbox("Filter Tipe Kas", ["Semua", "Masuk", "Keluar"])
    
    df_kas_tampil = df_kas.copy()
    if filter_tipe_kas != "Semua":
        df_kas_tampil = df_kas_tampil[df_kas_tampil['Tipe'] == filter_tipe_kas]

    df_kas_tampil['Nominal'] = df_kas_tampil['Nominal'].apply(format_rupiah)
    df_kas_tampil = df_kas_tampil.rename(columns={
        'ID_Transaksi': 'ID',
        'Tipe': 'Tipe Kas',
        'Kategori': 'Kategori',
        'Nominal': 'Jumlah (Rp)',
        'Tanggal': 'Tanggal Trx'
    })

    st.dataframe(df_kas_tampil, use_container_width=True, hide_index=True)


def render_kelola_armada():
    """Halaman 4: Manajemen Lengkap Data Armada (Tambah, Edit, Hapus)."""
    st.markdown('<div class="main-title">⚙️ Manajemen Data Armada</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Kelola data armada rental mobil & motor secara fleksibel.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("➕ Tambah Unit Baru")
        with st.form("form_tambah_armada_page", clear_on_submit=True):
            jenis = st.radio("Kategori", ["Mobil", "Motor"], horizontal=True, key="mgt_jenis")
            nama_kendaraan = st.text_input(
                "Jenis / Tipe Mobil atau Motor",
                placeholder="Contoh: Toyota Avanza / Honda Brio / NMAX",
                key="mgt_nama"
            )
            plat = st.text_input(
                "Nomor Plat Kendaraan",
                placeholder="Contoh: B 1234 XYZ",
                key="mgt_plat"
            )
            biaya_sewa = st.number_input(
                "Tarif Biaya Sewa per Hari (Rp)",
                min_value=10000,
                value=350000 if jenis == "Mobil" else 100000,
                step=25000,
                key="mgt_tarif"
            )

            submit_armada = st.form_submit_button("➕ Simpan Armada Baru", use_container_width=True)

            if submit_armada:
                if not nama_kendaraan.strip():
                    st.error("Jenis/Tipe mobil atau motor wajib diisi!")
                elif not plat.strip():
                    st.error("Nomor plat kendaraan tidak boleh kosong!")
                else:
                    sukses, pesan = tambah_armada_baru(jenis, nama_kendaraan, plat, biaya_sewa)
                    if sukses:
                        st.success(pesan)
                        st.rerun()
                    else:
                        st.error(pesan)

    with col2:
        st.subheader("📋 Daftar Armada Terdaftar")
        df_armada = load_armada()
        if not df_armada.empty:
            df_tampil = df_armada[['ID_Kendaraan', 'Jenis', 'Nama_Kendaraan', 'Plat', 'Biaya_Sewa', 'Status']].copy()
            df_tampil['Biaya_Sewa'] = df_tampil['Biaya_Sewa'].apply(format_rupiah)
            df_tampil = df_tampil.rename(columns={
                'ID_Kendaraan': 'ID',
                'Jenis': 'Kategori',
                'Nama_Kendaraan': 'Jenis/Tipe Kendaraan',
                'Plat': 'Nomor Plat',
                'Biaya_Sewa': 'Tarif / Hari',
                'Status': 'Status'
            })
            st.dataframe(df_tampil, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada unit armada terdaftar.")


# -----------------------------------------------------------------------------
# 4. KONTROL UTAMA & NAVIGASI APLIKASI
# -----------------------------------------------------------------------------

def main():
    # Inisialisasi Database SQLite di awal eksekusi
    init_database()

    # Sidebar Navigasi
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/car-rental.png", width=70)
        st.title("👑 Kings Rental Mobil Bumiayu")
        st.caption("Sistem Monitoring & Kas Rental Kendaraan")
        st.markdown("---")

        menu = st.radio(
            "Pilih Halaman Menu:",
            [
                "📊 Dashboard Armada",
                "📝 Transaksi Sewa & Kembali",
                "💰 Keuangan & Arus Kas",
                "⚙️ Kelola Data Armada"
            ],
            index=0
        )

        st.markdown("---")
        st.markdown("""
        **Fitur Armada Mandiri:**
        - ➕ Tambah Armada Sendiri
        - ✏️ Edit Jenis, Plat & Biaya
        - 🗑️ Hapus & Kosongkan Data Contoh
        """)

    # Routing Halaman berdasarkan Menu
    if menu == "📊 Dashboard Armada":
        render_dashboard_armada()
    elif menu == "📝 Transaksi Sewa & Kembali":
        render_halaman_transaksi()
    elif menu == "💰 Keuangan & Arus Kas":
        render_halaman_keuangan()
    elif menu == "⚙️ Kelola Data Armada":
        render_kelola_armada()


if __name__ == "__main__":
    main()
