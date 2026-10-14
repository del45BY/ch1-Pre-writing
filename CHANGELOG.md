# Catatan Perubahan (CHANGELOG)

Aturan: setiap perubahan ditulis di sini (terbaru di atas): tanggal, apa yang berubah, dan alasannya.
Setiap kali tampilan template berubah, naikkan `TEMPLATE_VERSION` di `worksheet_engine/config.py`.

## [2.1] - 2026-10-14
### Ditambahkan
- Mode bundle: satu PDF dengan tiap halaman memakai baris (hewan dan pasangan) berbeda. Opsi `--bundle`, `--ids`, `--pages`, `--bundles-sheet`; sheet Excel opsional `Bundles` (Bundle | Template | ID).
- Keluaran `PRODUCTS/Bundles/<nama>/` (PDF, Preview, Cover dengan semua gambar paket, Thumbnail) dan `manifest_bundles.csv`.
- `PANDUAN_BUNDLE.md`; contoh sheet Bundles di database bawaan.
### Diuji
- Produk tunggal v2.0 identik dengan baseline; kesalahan (ID/template salah, baris gagal QC) melewati paket dengan pesan jelas.

## [2.0] - 2026-10-14
### Diubah (BESAR)
- Set template bawaan diganti menjadi 10 template pra-menulis: A Garis Tegak, B Garis Datar, C Garis Miring, D Garis Zigzag, E Garis Lengkung, F Garis Gelombang, G Lingkaran & Spiral, H Pola Campuran, I Mengikuti Jalur, J Menebalkan Bentuk Dasar.
- Produk bawaan kini 10 halaman (sebelumnya 5). `Preview.png` memakai kisi 5x2.
- `TEMPLATE_VERSION` dinaikkan ke 2.0 (semua produk akan dibuat ulang).
### Ditambahkan
- `tracing.py`: mesin garis/bentuk (geometri, 5 gaya garis, penanda mulai/selesai, panah petunjuk digambar).
- Setiap template punya lima tingkat kesulitan garis: titik besar, putus-putus, titik kecil, jalur, gambar sendiri.
### Dipindahkan
- Template lama (matching, kosakata, lingkari, gunting-tempel, mewarnai, bayangan, berhitung, garis datar/miring lama) dipindah ke `templates_legacy.py`. Tetap bisa dipakai dengan kunci `LA`..`LI`; hasilnya diuji identik dengan versi 1.x.
### Diubah (tampilan)
- Warna aksen kuning (susah dibaca sebagai teks) tidak lagi dipakai sebagai aksen template.

## [1.3] - 2026-10-13
### Ditambahkan
- Template I (Diagonal Lines / Garis Miring): 4 panel (2x2), garis miring naik dan turun dari objek ke pasangannya (titik besar, putus-putus, jalur, gambar sendiri). Opsional.
### Diubah
- Mesin garis dipisah menjadi bagian bersama untuk H dan I: `trace_line_xy`, `start_finish`, `hint_with_arrows` (garis boleh dengan sudut apa pun).
- Panah di teks petunjuk template H kini digambar (bukan karakter font), agar aman memakai font apa pun. Hanya area kecil petunjuk itu yang berubah; baris garis H identik.
### Diuji
- Template A-E identik dengan baseline.

## [1.2] - 2026-10-13
### Ditambahkan
- Template H (Horizontal Lines / Garis Datar): latihan pra-menulis, menelusuri 5 garis datar dari kiri ke kanan (titik besar, putus-putus, titik kecil, jalur, gambar sendiri), dari objek ke pasangannya. Opsional, tidak masuk set bawaan.
### Diuji
- Template A-E baris 001 tetap identik dengan baseline.

## [1.1] - 2026-10-13
### Ditambahkan
- Template G (Counting / Berhitung): hitung 1-5 gambar dan lingkari angkanya (kata angka EN/ID). Opsional, tidak masuk set bawaan.
- `PANDUAN_TAMBAH_TEMPLATE.md`: panduan menambah template baru.
### Diuji
- Template A-E untuk baris 001 identik piksel-demi-piksel dengan `samples/baseline_legacy_v1_chicken_egg_preview.png` (sekarang di baseline_legacy_v1).

## [1.0] - 2026-10-13
### Ditambahkan
- Mesin lembar kerja dwibahasa (Inggris-Indonesia) untuk usia 3-5 tahun.
- Template A (Animal Matching), B (Vocabulary), C (Find and Circle), D (Cut and Paste), E (Coloring), F (Shadow Matching, opsional).
- Pemeriksaan kualitas (QC) dengan glosarium `data/approved_vocab.csv` (35 kata).
- Perpustakaan gambar vektor bawaan untuk 10 kata: chicken, egg, bee, honey, cow, milk, sheep, wool, tree, apple.
- Dukungan gambar PNG sendiri di `assets/images/` (mode berwarna, garis, siluet).
- Keluaran per baris: PDF, Preview.png, Cover.png, Thumbnail.png; ringkasan `manifest.csv` dan `qc_report.csv`.
- Versi pustaka terkunci di `requirements-lock.txt`.

### Diketahui / belum selesai
- Belum ada halaman kunci jawaban.
- Gambar bawaan baru untuk 10 kata contoh.
- Diuji pada 5 baris; belum diuji pada ribuan baris.
- Gambar PNG hanya diuji dengan gambar sintetis, belum dengan gambar AI asli.
