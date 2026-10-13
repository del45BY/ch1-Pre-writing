# Catatan Perubahan (CHANGELOG)

Aturan: setiap perubahan ditulis di sini (terbaru di atas): tanggal, apa yang berubah, dan alasannya.
Setiap kali tampilan template berubah, naikkan `TEMPLATE_VERSION` di `worksheet_engine/config.py`.

## [1.1] - 2026-10-13
### Ditambahkan
- Template G (Counting / Berhitung): hitung 1-5 gambar dan lingkari angkanya (kata angka EN/ID). Opsional, tidak masuk set bawaan.
- `PANDUAN_TAMBAH_TEMPLATE.md`: panduan menambah template baru.
### Diuji
- Template A-E untuk baris 001 identik piksel-demi-piksel dengan `samples/baseline_chicken_egg_preview.png`.

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
