# Panduan: Cara Menambah Template Baru

Contoh yang dipakai: **Template G "Berhitung"** (anak menghitung jumlah gambar, lalu melingkari angkanya).
Kodenya sudah ada di `worksheet_engine/templates.py`. Panduan ini menjelaskan cara membuat yang serupa.

> **Catatan versi 2.0:** template aktif kini A sampai J (pra-menulis) dan ada di `worksheet_engine/templates.py`.
> Template lama dipindah ke `templates_legacy.py` (kunci `LA`..`LI`). Contoh di bawah (Template G "Berhitung") adalah
> template lama, yaitu `draw_g` di `templates_legacy.py`; cara membuat template barunya tetap sama.
> Untuk template berbasis garis atau bentuk, **pakai `tracing.py`**: cukup buat daftar titik `[(x, y), ...]`,
> lalu panggil `trace_path(c, gaya, titik, accent)` dan `marker_start` / `marker_end`.
> Contoh paling sederhana ada di `draw_b` (garis datar) dan `draw_f` (gelombang) pada `templates.py`.
> Jika template baru memakai kunci baru (misalnya `K`), tambahkan ke `TEMPLATES` dan `DEFAULT_SET`.

## Gambaran: template itu apa?

Template = satu fungsi Python yang menggambar **isi** satu halaman. Header (judul, usia) dan footer
(brand, nomor halaman) ditambahkan otomatis oleh mesin, jadi Anda tidak perlu menggambarnya.

Setiap template butuh dua hal:
1. **Fungsi gambar** `draw_x(c, row, pool, rng, accent)`
2. **Pendaftaran** di kamus `TEMPLATES` (nama, warna, tujuan belajar)

| Bagian fungsi | Artinya |
|---|---|
| `c` | "kertas" tempat menggambar |
| `row` | data satu baris Excel (`row.obj_en`, `row.obj_id`, `row.rel_en`, `row.rel_id`) |
| `pool` | daftar pasangan gambar dari baris lain (untuk gambar pengecoh) |
| `rng` | pengacak yang dikunci per ID + template (hasil selalu sama saat dibuat ulang) |
| `accent` | nama warna template, misalnya `"sky"` |

## Langkah demi langkah

### Langkah 1. Tentukan idenya di atas kertas
Tulis: apa yang dilakukan anak, apa yang tampil, dan berapa banyak ruang yang dipakai.
Area isi halaman hanya sekitar **576 pt** tinggi dan **523 pt** lebar. Contoh G: dua blok,
masing-masing berisi instruksi, deretan gambar, dan baris angka 1 sampai 5.

### Langkah 2. Tulis fungsi gambar di `templates.py`
Letakkan di atas baris `TEMPLATES = {`. Mulailah dengan bilah instruksi:

```python
def draw_h(c, row, pool, rng, accent):
    y = instruction(c, row, CONTENT_TOP,
                    "Teks instruksi Inggris.",       # boleh pakai {OBJECT_EN_LOWER}
                    "Teks instruksi Indonesia.",
                    accent, "H")                      # huruf lencana di kiri
    # y = posisi tepat di bawah bilah instruksi; gambar sisanya dari sini ke bawah
    draw_object(c, row.obj_en, 300, y - 150, 100, "color")
```

Alat yang bisa dipakai ulang (tidak perlu menulis dari nol):

| Alat | Fungsi |
|---|---|
| `draw_object(c, nama_en, x, y, ukuran, mode)` | gambar objek. Mode: `"color"`, `"outline"` (mewarnai), `"shadow"` (siluet) |
| `panel(c, x, y, lebar, tinggi, fill=, stroke=)` | kotak bersudut bulat |
| `text_fit(...)` | teks yang otomatis mengecil agar muat |
| `word_pair(...)` | kata Inggris di atas kata Indonesia |
| `dot`, `arrow`, `star`, `scissors_line`, `dotted_text`, `tracing_line` | hiasan dan alat bantu |

**Koordinat:** titik (0,0) ada di **kiri bawah** kertas. Makin ke atas, angka y makin besar.

### Langkah 3. Daftarkan di `TEMPLATES`
```python
"H": dict(name_en="Nama Inggris", name_id="Nama Indonesia", accent="sky", fn=draw_h,
          objective_en="do something with {OBJECT_EN_LOWER}.",
          objective_id="melakukan sesuatu dengan {OBJECT_ID_LOWER}."),
```
`objective_en` dan `objective_id` otomatis ditulis setelah kata "I can" dan "Saya bisa" di header.
Pilihan `accent`: `coral`, `sky`, `sun`, `mint`, `grape`.

### Langkah 4. Uji satu produk
```
python -m worksheet_engine.main --db data/worksheet_database.xlsx --out UJI --only 001 --templates H --force
```
Buka PDF di folder `UJI`. Periksa: teks tidak terpotong, tidak ada tumpang tindih, ruang kosong cukup.
Uji juga baris yang kata-katanya panjang, karena itu paling sering merusak tata letak.

### Langkah 5. Uji bahwa template lama tidak berubah
Buat ulang baris 001 (template A sampai E), lalu bandingkan `Preview.png`-nya dengan
`samples/baseline_chicken_egg_preview.png`. Hasilnya harus identik.

### Langkah 6. Aktifkan
- Untuk dipakai sebagai tambahan: `--templates A,B,C,D,E,H`, atau isi kolom `Templates` di Excel per baris.
- Untuk selalu ikut: tambahkan `"H"` ke `DEFAULT_SET` (baris paling bawah `templates.py`).

### Langkah 7. Catat dan simpan
Tambahkan catatan di `CHANGELOG.md`, lalu:
```
git add -A
git commit -m "Tambah template H: <nama>"
```

## Contoh: bagaimana Template G bekerja

- Jumlah gambar dipilih acak 1 sampai 5 lewat `rng`, jadi **selalu sama** untuk ID yang sama.
- Blok kedua memakai jumlah yang berbeda dari blok pertama.
- Gambar diletakkan berderet dan dipusatkan: `x0 = tengah_halaman - jarak * (jumlah - 1) / 2`.
- Baris angka 1 sampai 5 memuat angka dan kata dalam dua bahasa ("two / dua").
- Instruksi tidak memakai bentuk jamak ("Count the chicken", bukan "chickens"), karena tiap kata punya
  bentuk jamak berbeda (sheep tetap sheep). Ini cara aman untuk database yang terus bertambah.

## Do & Don't

**Lakukan:**
- Pakai placeholder (`{OBJECT_EN_LOWER}`) di semua teks, bukan kata tetap.
- Tulis semua teks dalam dua bahasa.
- Pakai `rng` untuk hal acak, bukan `random` langsung, supaya hasilnya konsisten.
- Biarkan banyak ruang kosong dan objek besar (anak 3 sampai 5 tahun).
- Naikkan `TEMPLATE_VERSION` di `config.py` **hanya jika** tampilan template yang sudah ada berubah.

**Jangan:**
- Jangan menulis kata seperti "chicken" langsung di template.
- Jangan menggambar header atau footer sendiri.
- Jangan memakai instruksi yang butuh kemampuan membaca tanpa petunjuk gambar.
- Jangan menggambar di bawah y = 80 (area footer) atau melewati margin 36 pt di kiri-kanan.
- Jangan mengubah fungsi `draw_a` sampai `draw_f` hanya untuk memperbaiki template baru. Kalau perlu, ubah `components.py` dan ulangi Langkah 5.
- Jangan memakai bentuk jamak bahasa Inggris tanpa mengurus pengecualiannya (sheep, fish, honey).

## Daftar periksa sebelum dijual

- [ ] Diuji pada baris dengan kata pendek dan kata panjang
- [ ] Dicetak di A4 skala 100%, tidak ada yang terpotong
- [ ] Template lama (A sampai E) identik dengan baseline
- [ ] CHANGELOG sudah diperbarui dan sudah di-commit
