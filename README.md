# 👑 Kings Rental Mobil Bumiayu

Aplikasi manajemen dan pemantauan armada rental kendaraan berbasis Python, menggunakan framework **Streamlit**, manipulasi data dengan **Pandas**, dan database relasional **SQLite3**, serta visualisasi grafik interaktif dengan **Matplotlib** dan **Seaborn**.

---

## 📋 Fitur Utama

1. **📊 Dashboard Armada**:
   - Menampilkan metrik utama jumlah kendaraan berstatus **Ready** vs **Keluar**.
   - Menampilkan detail Jenis/Tipe Mobil atau Motor, Nomor Plat, dan Tarif Sewa/Hari.
   - Filter interaktif berdasarkan kategori armada, status ketersediaan, serta pencarian nama tipe atau plat nomor.
   - Grafik distribusi ketersediaan unit.

2. **📝 Transaksi Sewa & Pengembalian**:
   - **Form Input Sewa Baru**: Dropdown otomatis menampilkan jenis kendaraan yang **Ready** beserta plat nomor dan tarif hariannya.
   - **Kalkulasi Biaya Sewa**: Biaya otomatis terisi dari tarif standar armada dan dapat disesuaikan.
   - **Update Otomatis**: Saat kendaraan disewa, status armada di `tabel_armada` langsung otomatis berubah menjadi **'Keluar'**.
   - **Integrasi Kas**: Tersedia opsi otomatis mencatat nominal sewa ke buku kas masuk.
   - **Fitur Pengembalian**: Memilih sewa aktif yang berjalan, mencatat waktu kembali aktual, dan mengembalikan status armada menjadi **'Ready'**.
   - **Riwayat Transaksi**: Log lengkap riwayat penyewaan sebelumnya beserta total biaya sewa.

3. **💰 Keuangan & Arus Kas**:
   - Ringkasan KPI keuangan: Total Pemasukan, Total Pengeluaran, dan Saldo Bersih (*Net Cash Flow*).
   - Form pencatatan kas masuk dan kas keluar dengan berbagai kategori operasional (servis, bahan bakar, cuci, dll).
   - **Visualisasi Tren Bulanan**: Grafik perbandingan Pemasukan vs Pengeluaran per bulan dengan garis tren arus kas bersih (*Net Cash Flow*) menggunakan Matplotlib & Seaborn.
   - Buku kas lengkap dengan filter tipe transaksi.

4. **⚙️ Manajemen Data Armada**:
   - Menambahkan unit armada baru: **Jenis Mobil/Motor**, **Tipe / Model Kendaraan**, **Nomor Plat**, dan **Tarif Biaya Sewa per Hari (Rp)**.

---

## 🗄️ Struktur Database (SQLite)

Database disimpan secara lokal dalam file `rental_monitoring.db`:

```sql
-- 1. Tabel Armada
CREATE TABLE tabel_armada (
    ID_Kendaraan INTEGER PRIMARY KEY AUTOINCREMENT,
    Jenis TEXT NOT NULL CHECK(Jenis IN ('Mobil', 'Motor')),
    Nama_Kendaraan TEXT NOT NULL DEFAULT '-',
    Plat TEXT UNIQUE NOT NULL,
    Biaya_Sewa REAL NOT NULL DEFAULT 0,
    Status TEXT NOT NULL DEFAULT 'Ready' CHECK(Status IN ('Ready', 'Keluar'))
);

-- 2. Tabel Sewa
CREATE TABLE tabel_sewa (
    ID_Sewa INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_Kendaraan INTEGER NOT NULL,
    Nama TEXT NOT NULL,
    Waktu_Mulai TEXT NOT NULL,
    Waktu_Selesai TEXT,
    Status_Sewa TEXT NOT NULL DEFAULT 'Berjalan' CHECK(Status_Sewa IN ('Berjalan', 'Selesai')),
    Total_Biaya REAL DEFAULT 0,
    FOREIGN KEY (ID_Kendaraan) REFERENCES tabel_armada(ID_Kendaraan)
);

-- 3. Tabel Kas
CREATE TABLE tabel_kas (
    ID_Transaksi INTEGER PRIMARY KEY AUTOINCREMENT,
    Tipe TEXT NOT NULL CHECK(Tipe IN ('Masuk', 'Keluar')),
    Kategori TEXT NOT NULL,
    Nominal REAL NOT NULL,
    Tanggal TEXT NOT NULL
);
```

---

## 🚀 Cara Menjalankan Aplikasi

Jika perintah `streamlit` tidak dikenali langsung di PowerShell/CMD (karena folder script Python belum ada di PATH Windows), gunakan perintah modul Python atau file batch yang sudah disediakan:

### Opsi 1: Menggunakan File Batch (Paling Praktis)
Cukup klik ganda (double-click) file:
```
run.bat
```
atau di terminal:
```powershell
.\run.bat
```

### Opsi 2: Perintah Python Module
```powershell
python -m streamlit run app.py
```

Aplikasi akan otomatis terbuka di browser pada alamat:
`http://localhost:8501`
