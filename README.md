# Dashboard Keuangan Mess

Dashboard berbasis Python dan Streamlit untuk mengelola pemasukan, pengeluaran,
iuran penghuni, saldo kas, dan laporan keuangan mess pegawai.

## Menjalankan aplikasi

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deployment Streamlit Community Cloud

1. Hubungkan akun GitHub ke Streamlit Community Cloud.
2. Pilih repository `geraldinbatubara-cyber/Dashboard-Keuangan-Mess`.
3. Pilih branch `main` dan entry point `app.py`.
4. Tambahkan secrets berikut pada menu **Advanced settings > Secrets**:

```toml
AUTH_USERNAME = "bendahara"
AUTH_PASSWORD = "ganti-dengan-password-kuat"
```

5. Klik **Deploy**.
