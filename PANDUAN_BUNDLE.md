# Panduan: Paket Campuran (Bundle) - tiap halaman beda hewan

Biasanya satu produk = satu pasangan (misalnya Chicken & Egg) di semua halaman.
Mode **bundle** membuat satu PDF di mana **tiap halaman memakai pasangan yang berbeda**:

| Halaman | Template | Pasangan |
|---|---|---|
| 1 | A Garis Tegak | Chicken & Egg |
| 2 | B Garis Datar | Bee & Honey |
| 3 | C Garis Miring | Cow & Milk |
| 4 | D Garis Zigzag | Sheep & Wool |
| 5 | E Garis Lengkung | Tree & Apple |

Judul, kata dua bahasa, dan gambar di setiap halaman mengikuti pasangannya sendiri.
Hasilnya ada di `PRODUCTS/Bundles/<NamaPaket>/` (PDF, Preview.png, Cover.png, Thumbnail.png),
ditambah `PRODUCTS/manifest_bundles.csv`.

## Tiga cara membuatnya

### Cara 1. Daftar ID (paling cepat)
```
python -m worksheet_engine.main --db data/worksheet_database.xlsx --out PRODUCTS --bundle Animal_Friends_Pack_1 --ids 001,002,003,004,005
```
Halaman 1 memakai baris 001, halaman 2 baris 002, dan seterusnya. Template berurutan A, B, C ... J.
Jika ID lebih sedikit dari halaman, ID **diulang berputar** (5 ID + 10 template = halaman 6 kembali ke ID pertama).
Batasi halaman dengan `--templates`, misalnya `--templates A,B,C,D,E` untuk 5 halaman saja.

### Cara 2. Pemetaan manual (urutan bebas)
```
python -m worksheet_engine.main --db data/worksheet_database.xlsx --out PRODUCTS --bundle Mini_Pack --pages "A=002,C=004,J=005"
```
Format `TEMPLATE=ID`, dipisah koma. Hanya halaman yang Anda tulis yang dibuat, dalam urutan yang Anda tulis.
Satu ID boleh dipakai di beberapa halaman.

### Cara 3. Lewat Excel (paling cocok untuk banyak paket)
Tambahkan sheet bernama **Bundles** di file database dengan tiga kolom:

| Bundle | Template | ID |
|---|---|---|
| Animal_Friends_Pack_1 | | 001 |
| Animal_Friends_Pack_1 | | 002 |
| Mini_Pack | A | 002 |
| Mini_Pack | C | 004 |

* Satu baris = satu halaman, urut dari atas ke bawah.
* **Template kosong** = otomatis A, B, C ... sesuai urutan baris dalam paket itu.
* **ID** harus ada di sheet Database (format teks, `001`).
* Nama paket (kolom Bundle) menjadi nama folder dan judul sampul. Pakai garis bawah, bukan spasi.

Jalankan semua paket di sheet:
```
python -m worksheet_engine.main --db data/worksheet_database.xlsx --out PRODUCTS --bundles-sheet
```
Hanya satu paket: tambahkan `--bundle Mini_Pack`. Contoh sheet sudah ada di `worksheet_database.xlsx` bawaan.

## Aturan penting
* **Mode bundle hanya membuat paket**, tidak membuat produk tunggal. Jalankan perintah biasa (tanpa `--bundle`) untuk produk tunggal.
* Semua baris yang dipakai harus lolos QC. Jika ada yang gagal, ID tidak ada, atau template salah, paket itu **dilewati** dengan pesan jelas; paket lain tetap jalan.
* Dengan `--strict`, baris berstatus WARN juga membuat paket dilewati.
* Dijalankan ulang tidak membangun ulang paket yang tidak berubah (pakai `--force` untuk memaksa).

## Do & Don't
**Lakukan:**
* Satukan hewan dari tema yang sama dalam satu paket (misalnya "Animal Friends"), supaya mudah dijual.
* Pastikan setiap hewan punya gambar PNG (`assets/images/`), karena cadangan berhuruf kurang layak jual.
* Beri nama paket yang unik dan deskriptif.
* Cek `Preview.png` paket sebelum mengunggah.

**Jangan:**
* Jangan memakai nama paket yang sama untuk isi berbeda (folder akan tertimpa).
* Jangan menaruh spasi atau karakter khusus di nama paket (otomatis dirapikan, tetapi tidak disarankan).
* Jangan memasukkan baris yang masih berstatus WARN kosakata tanpa dicek penutur asli.
* Jangan mengira template yang memakai gambar pengecoh (misalnya I Mengikuti Jalur) hanya memakai hewan paket; pengecohnya diambil dari seluruh database.
