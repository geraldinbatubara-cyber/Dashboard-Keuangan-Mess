from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Dashboard Keuangan Mess",
    page_icon=":material/account_balance_wallet:",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background: #f4f7f5; }
    [data-testid="stSidebar"] { background: #173c31; }
    [data-testid="stSidebar"] * { color: white; }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e9e5;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 8px 24px rgba(20, 70, 50, .06);
    }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

DEFAULT_TRANSACTIONS = [
    {"Tanggal": "2026-06-01", "Keterangan": "Saldo awal", "Kategori": "Saldo Awal", "Jenis": "Pemasukan", "Nominal": 9_020_000},
    {"Tanggal": "2026-06-03", "Keterangan": "Iuran kamar A-01", "Kategori": "Iuran", "Jenis": "Pemasukan", "Nominal": 500_000},
    {"Tanggal": "2026-06-04", "Keterangan": "Tagihan air", "Kategori": "Utilitas", "Jenis": "Pengeluaran", "Nominal": 720_000},
    {"Tanggal": "2026-06-05", "Keterangan": "Perbaikan pompa air", "Kategori": "Perbaikan", "Jenis": "Pengeluaran", "Nominal": 850_000},
    {"Tanggal": "2026-06-08", "Keterangan": "Iuran kamar B-05", "Kategori": "Iuran", "Jenis": "Pemasukan", "Nominal": 500_000},
    {"Tanggal": "2026-06-10", "Keterangan": "Perlengkapan kebersihan", "Kategori": "Kebersihan", "Jenis": "Pengeluaran", "Nominal": 475_000},
    {"Tanggal": "2026-06-12", "Keterangan": "Token listrik mess", "Kategori": "Utilitas", "Jenis": "Pengeluaran", "Nominal": 1_250_000},
    {"Tanggal": "2026-06-14", "Keterangan": "Iuran kamar A-03", "Kategori": "Iuran", "Jenis": "Pemasukan", "Nominal": 500_000},
]

RESIDENTS = pd.DataFrame(
    [
        {"Nama": "Andi Rinaldi", "Kamar": "A-01", "Status": "Lunas", "Nominal": 500_000},
        {"Nama": "Dewi Sartika", "Kamar": "A-02", "Status": "Lunas", "Nominal": 500_000},
        {"Nama": "Riko Saputra", "Kamar": "A-03", "Status": "Lunas", "Nominal": 500_000},
        {"Nama": "Budi Pratama", "Kamar": "B-02", "Status": "Belum", "Nominal": 0},
        {"Nama": "Maya Ningsih", "Kamar": "B-04", "Status": "Belum", "Nominal": 0},
        {"Nama": "Fajar Nugraha", "Kamar": "B-05", "Status": "Lunas", "Nominal": 500_000},
    ]
)

if "transactions" not in st.session_state:
    st.session_state.transactions = DEFAULT_TRANSACTIONS.copy()


def rupiah(value):
    return f"Rp{value:,.0f}".replace(",", ".")


with st.sidebar:
    st.title("KasMess")
    st.caption("Mess Pegawai")
    st.divider()
    page = st.radio(
        "Menu", ["Ringkasan", "Transaksi", "Iuran Penghuni", "Laporan"]
    )
    st.divider()
    st.caption("Pengelola aktif")
    st.write("**Bendahara Mess**")

transactions = pd.DataFrame(st.session_state.transactions)
transactions["Tanggal"] = pd.to_datetime(transactions["Tanggal"])

st.title("Dashboard Keuangan Mess")
st.caption("Pantau kas, iuran, dan pengeluaran mess pegawai dalam satu tempat.")

if page == "Ringkasan":
    st.selectbox("Periode", ["Juni 2026", "Mei 2026", "April 2026"], width=220)
    income = transactions.loc[transactions["Jenis"] == "Pemasukan", "Nominal"].sum()
    expense = transactions.loc[transactions["Jenis"] == "Pengeluaran", "Nominal"].sum()
    paid = (RESIDENTS["Status"] == "Lunas").sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Kas", rupiah(income - expense), "8,4% dari bulan lalu")
    col2.metric("Total Pemasukan", rupiah(income))
    col3.metric("Total Pengeluaran", rupiah(expense), "3,1%", delta_color="inverse")
    col4.metric("Iuran Terkumpul", f"{paid} / {len(RESIDENTS)} penghuni")

    left, right = st.columns([1.6, 1])
    cashflow = pd.DataFrame(
        {
            "Bulan": ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun"] * 2,
            "Jenis": ["Pemasukan"] * 6 + ["Pengeluaran"] * 6,
            "Nominal": [6_200_000, 6_900_000, 7_400_000, 6_600_000, 8_200_000, income]
            + [4_400_000, 4_800_000, 5_200_000, 4_300_000, 5_700_000, expense],
        }
    )
    with left:
        st.subheader("Arus Kas 6 Bulan")
        figure = px.bar(
            cashflow,
            x="Bulan",
            y="Nominal",
            color="Jenis",
            barmode="group",
            color_discrete_map={"Pemasukan": "#2b8a65", "Pengeluaran": "#efad68"},
        )
        figure.update_layout(margin=dict(l=0, r=0, t=15, b=0), legend_title_text="")
        st.plotly_chart(figure, use_container_width=True)

    with right:
        st.subheader("Komposisi Pengeluaran")
        expenses = (
            transactions[transactions["Jenis"] == "Pengeluaran"]
            .groupby("Kategori", as_index=False)["Nominal"]
            .sum()
        )
        figure = px.pie(
            expenses,
            names="Kategori",
            values="Nominal",
            hole=0.58,
            color_discrete_sequence=["#176b4d", "#d97824", "#6e91aa", "#c6d2cc"],
        )
        figure.update_layout(margin=dict(l=0, r=0, t=15, b=0), legend_title_text="")
        st.plotly_chart(figure, use_container_width=True)

    left, right = st.columns([1.45, 1])
    with left:
        st.subheader("Transaksi Terbaru")
        latest = transactions.sort_values("Tanggal", ascending=False).head(6).copy()
        latest["Tanggal"] = latest["Tanggal"].dt.strftime("%d %b %Y")
        latest["Nominal"] = latest.apply(
            lambda row: ("+ " if row["Jenis"] == "Pemasukan" else "- ")
            + rupiah(row["Nominal"]),
            axis=1,
        )
        st.dataframe(
            latest[["Tanggal", "Keterangan", "Kategori", "Nominal"]],
            hide_index=True,
            use_container_width=True,
        )
    with right:
        st.subheader("Status Iuran")
        st.progress(paid / len(RESIDENTS), text=f"{paid} dari {len(RESIDENTS)} penghuni sudah membayar")
        st.dataframe(
            RESIDENTS[["Nama", "Kamar", "Status"]],
            hide_index=True,
            use_container_width=True,
        )

elif page == "Transaksi":
    st.subheader("Catat Transaksi")
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        tx_type = col1.selectbox("Jenis", ["Pemasukan", "Pengeluaran"])
        tx_date = col2.date_input("Tanggal", value=date.today())
        description = st.text_input("Keterangan")
        col1, col2 = st.columns(2)
        category = col1.selectbox(
            "Kategori",
            ["Iuran", "Utilitas", "Kebersihan", "Konsumsi", "Perbaikan", "Lainnya"],
        )
        amount = col2.number_input("Nominal", min_value=0, step=50_000)
        submitted = st.form_submit_button("Simpan Transaksi", type="primary")
        if submitted and description and amount > 0:
            st.session_state.transactions.append(
                {
                    "Tanggal": str(tx_date),
                    "Keterangan": description,
                    "Kategori": category,
                    "Jenis": tx_type,
                    "Nominal": amount,
                }
            )
            st.success("Transaksi berhasil ditambahkan.")
            st.rerun()

    st.subheader("Daftar Transaksi")
    st.dataframe(
        transactions.sort_values("Tanggal", ascending=False),
        hide_index=True,
        use_container_width=True,
    )

elif page == "Iuran Penghuni":
    st.subheader("Status Iuran Penghuni")
    st.dataframe(RESIDENTS, hide_index=True, use_container_width=True)

else:
    st.subheader("Laporan Keuangan")
    report = transactions.copy()
    report["Bulan"] = report["Tanggal"].dt.to_period("M").astype(str)
    summary = report.pivot_table(
        index="Bulan", columns="Jenis", values="Nominal", aggfunc="sum", fill_value=0
    ).reset_index()
    st.dataframe(summary, hide_index=True, use_container_width=True)
    st.download_button(
        "Unduh transaksi CSV",
        transactions.to_csv(index=False).encode("utf-8"),
        "transaksi_mess.csv",
        "text/csv",
    )
