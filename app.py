from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Dashboard Keuangan Mess",
    page_icon=":material/account_balance_wallet:",
    layout="wide",
)

DATA_FILE = Path(__file__).parent / "data" / "Uang Mess.xlsx"
MONTHS = {
    "januari": 1,
    "februari": 2,
    "maret": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}
MONTH_LABELS = {number: name.title() for name, number in MONTHS.items()}

st.markdown(
    """
    <style>
    :root {
        --cream: #fbf7ee;
        --paper: #fffaf2;
        --ink: #2d2118;
        --muted: #7d6d5f;
        --forest: #183f33;
        --forest-soft: #e7f0eb;
        --terracotta: #b86b3f;
        --gold: #d8a44b;
        --line: #eadfce;
    }
    .stApp { background: radial-gradient(circle at top left, #fff4dc 0, var(--cream) 34%, #f4f7f5 100%); color: var(--ink); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #183f33 0%, #102b24 100%); }
    [data-testid="stSidebar"] * { color: white; }
    div[data-testid="stMetric"] {
        background: rgba(255, 250, 242, .95);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 12px 30px rgba(77, 48, 24, .08);
    }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .landing-card {
        background: rgba(255, 250, 242, .92);
        border: 1px solid var(--line);
        border-radius: 24px;
        padding: clamp(18px, 2.8vw, 32px);
        box-shadow: 0 24px 70px rgba(79, 53, 26, .12);
    }
    .landing-hero { padding: 8px 0 0; }
    .eyebrow {
        color: var(--terracotta);
        font-weight: 800;
        letter-spacing: .14em;
        text-transform: uppercase;
        font-size: .72rem;
        margin-bottom: .55rem;
    }
    .hero-title {
        color: var(--forest);
        font-size: clamp(2rem, 4.2vw, 3.45rem);
        line-height: .98;
        letter-spacing: -0.06em;
        font-weight: 900;
        margin-bottom: .75rem;
    }
    .hero-copy {
        color: var(--muted);
        font-size: 1rem;
        line-height: 1.55;
        max-width: 620px;
    }
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        margin-top: 18px;
    }
    .feature-pill {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 10px 12px;
        color: var(--forest);
        font-weight: 760;
        font-size: .93rem;
    }
    .login-panel {
        background: linear-gradient(180deg, #ffffff 0%, #fff8ea 100%);
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 18px 20px;
        box-shadow: 0 16px 40px rgba(78, 50, 21, .1);
    }
    .login-panel h3 {
        color: var(--forest);
        margin-top: 0;
        margin-bottom: 4px;
        font-size: 1.25rem;
    }
    .login-panel p {
        color: var(--muted);
        line-height: 1.45;
        margin-bottom: 0;
    }
    @media (max-width: 760px) {
        .feature-grid { grid-template-columns: 1fr; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def rupiah(value):
    return f"Rp{float(value):,.0f}".replace(",", ".")


def get_secret(key, default=""):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def login_gate():
    if st.session_state.get("authenticated"):
        return

    configured_username = str(get_secret("AUTH_USERNAME", "")).strip()
    configured_password = str(get_secret("AUTH_PASSWORD", "")).strip()

    left, right = st.columns([1.2, 0.8], gap="large")
    with left:
        st.markdown(
            """
            <div class="landing-hero">
            <div class="eyebrow">KasMess Private Dashboard</div>
            <div class="hero-title">Keuangan mess yang rapi, hangat, dan terpercaya.</div>
            <div class="hero-copy">
                Pantau iuran penghuni, pengeluaran operasional, dan surplus kas mess
                dari workbook riil. Akses dibatasi agar data penghuni tetap berada
                di tangan pengelola yang berwenang.
            </div>
            <div class="feature-grid">
                <div class="feature-pill">Ringkasan kas</div>
                <div class="feature-pill">Status iuran</div>
                <div class="feature-pill">Laporan CSV</div>
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="login-panel">
                <h3>Masuk Dashboard</h3>
                <p>Gunakan akses bendahara yang disimpan di Streamlit Secrets.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            username = st.text_input("Username", value=configured_username or "")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Masuk", type="primary", use_container_width=True)

        if not configured_password:
            st.warning(
                "Akses belum dikonfigurasi. Tambahkan `AUTH_USERNAME` dan "
                "`AUTH_PASSWORD` pada Streamlit Secrets."
            )
        elif submitted:
            username_ok = not configured_username or username.strip() == configured_username
            password_ok = password == configured_password
            if username_ok and password_ok:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Username atau password belum sesuai.")

    st.stop()


def parse_money(value, values_in_thousands=False):
    if pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, str):
        cleaned = value.strip().replace("Rp", "").replace(" ", "")
        if not cleaned:
            return 0.0
        try:
            return float(cleaned.replace(",", ""))
        except ValueError:
            return 0.0
    number = float(value)
    if values_in_thousands and number != 0 and abs(number) < 10_000:
        return number * 1_000
    return number


def parse_period_label(value, fallback_year):
    text = str(value or "").strip().lower()
    year_match = re.search(r"20\d{2}", text)
    year = int(year_match.group()) if year_match else fallback_year
    month = next((number for name, number in MONTHS.items() if name in text), None)
    return year, month


def expense_category(description):
    text = str(description).lower()
    rules = [
        ("Honor", ["honor"]),
        ("Listrik & Token", ["listrik", "token"]),
        ("Internet", ["wifi"]),
        ("Konsumsi", ["galon", "gas", "kopi", "gula", "bakar"]),
        ("Kebersihan", ["sampah", "bebersih", "tisu", "spons"]),
        ("Perbaikan & Perlengkapan", ["perbaikan", "keran", "lampu", "pintu", "ventilasi", "cctv", "terminal", "serok", "tv", "net voli", "perlengkapan", "belanja"]),
        ("Biaya Admin", ["cost tf", "admin"]),
    ]
    for category, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return category
    return "Lainnya"


@st.cache_data(show_spinner=False)
def load_data(path, modified_time):
    del modified_time
    income_raw = pd.read_excel(path, sheet_name="Pemasukan", header=None)
    expense_raw = pd.read_excel(path, sheet_name="Pengeluaran", header=None)

    residents = []
    for row_index in range(3, len(income_raw)):
        name = income_raw.iat[row_index, 1] if income_raw.shape[1] > 1 else None
        if pd.isna(name) or str(name).strip().lower() == "iuran lebih":
            continue
        fee = parse_money(income_raw.iat[row_index, 3], values_in_thousands=True)
        residents.append(
            {
                "row_index": row_index,
                "Nomor": income_raw.iat[row_index, 0],
                "Nama": str(name).strip(),
                "Tipe Kamar": str(income_raw.iat[row_index, 2]).strip(),
                "Iuran": fee,
            }
        )
    residents = pd.DataFrame(residents)

    income_records = []
    current_year = 2022
    for column in range(income_raw.shape[1]):
        top_value = income_raw.iat[0, column]
        header_value = str(income_raw.iat[1, column]).strip().lower()
        parsed_year, parsed_month = parse_period_label(top_value, current_year)
        if parsed_year:
            current_year = parsed_year
        if header_value != "jumlah bayar" or not parsed_month:
            continue

        period = pd.Timestamp(year=current_year, month=parsed_month, day=1)
        total = parse_money(income_raw.iat[2, column])
        for resident in residents.to_dict("records"):
            payment = parse_money(
                income_raw.iat[resident["row_index"], column],
                values_in_thousands=True,
            )
            date_column = column + 1
            while date_column < income_raw.shape[1]:
                field = str(income_raw.iat[1, date_column]).strip().lower()
                if field == "tanggal bayar":
                    break
                if field == "jumlah bayar":
                    date_column = -1
                    break
                date_column += 1
            paid_at = pd.NaT
            if date_column > 0 and date_column < income_raw.shape[1]:
                paid_at = pd.to_datetime(
                    income_raw.iat[resident["row_index"], date_column], errors="coerce"
                )
            income_records.append(
                {
                    "Periode": period,
                    "Nama": resident["Nama"],
                    "Tipe Kamar": resident["Tipe Kamar"],
                    "Iuran": resident["Iuran"],
                    "Jumlah Bayar": payment,
                    "Tanggal Bayar": paid_at,
                    "Total Periode": total,
                }
            )

    expenses = []
    current_period = None
    for _, row in expense_raw.iterrows():
        sequence = row.iloc[0] if len(row) > 0 else None
        description = row.iloc[1] if len(row) > 1 else None
        amount = row.iloc[2] if len(row) > 2 else None
        paid_at = row.iloc[3] if len(row) > 3 else None

        if pd.isna(sequence) and pd.isna(description) and not pd.isna(amount):
            _, month = parse_period_label(amount, 2026)
            if month:
                current_period = pd.Timestamp(year=2026, month=month, day=1)
            continue
        if current_period is None or pd.isna(description) or not str(description).strip():
            continue
        # Biaya transfer dicatat dalam rupiah, sedangkan nominal operasional
        # kecil lainnya dicatat dalam ribuan rupiah pada workbook.
        nominal = parse_money(
            amount,
            values_in_thousands="cost tf" not in str(description).lower(),
        )
        if nominal == 0:
            continue
        expenses.append(
            {
                "Periode": current_period,
                "Tanggal": pd.to_datetime(paid_at, errors="coerce"),
                "Keterangan": str(description).strip(),
                "Kategori": expense_category(description),
                "Nominal": nominal,
            }
        )

    income = pd.DataFrame(income_records)
    expense = pd.DataFrame(expenses)
    residents = residents.drop(columns="row_index")
    return income, expense, residents


login_gate()

if not DATA_FILE.exists():
    st.error("File data `data/Uang Mess.xlsx` tidak ditemukan.")
    st.stop()

income, expenses, residents = load_data(DATA_FILE, DATA_FILE.stat().st_mtime)
available_periods = sorted(
    set(income["Periode"].dropna()).union(expenses["Periode"].dropna()), reverse=True
)

with st.sidebar:
    st.title("KasMess")
    st.caption("Mess Pegawai")
    st.divider()
    page = st.radio(
        "Menu", ["Ringkasan", "Pemasukan", "Pengeluaran", "Iuran Penghuni", "Laporan"]
    )
    st.divider()
    st.caption("Sumber data")
    st.write("**Uang Mess.xlsx**")
    st.caption("Data riil mess, diperbarui 15 Juni 2026")
    st.divider()
    if st.button("Keluar", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

st.title("Dashboard Keuangan Mess")
st.caption("Ringkasan pemasukan iuran dan pengeluaran operasional mess.")

period_options = {
    f"{MONTH_LABELS[period.month]} {period.year}": period for period in available_periods
}
default_label = next(
    (label for label, period in period_options.items() if period == pd.Timestamp(2026, 6, 1)),
    next(iter(period_options)),
)
selected_label = st.selectbox(
    "Periode", list(period_options), index=list(period_options).index(default_label), width=220
)
selected_period = period_options[selected_label]

period_income_rows = income[income["Periode"] == selected_period].copy()
period_expenses = expenses[expenses["Periode"] == selected_period].copy()
period_income = period_income_rows["Jumlah Bayar"].sum()
if not period_income_rows.empty:
    recorded_total = period_income_rows["Total Periode"].max()
    if recorded_total > 0:
        period_income = recorded_total
period_expense = period_expenses["Nominal"].sum()

year_income = (
    income[income["Periode"].dt.year == selected_period.year]
    .groupby("Periode")["Total Periode"]
    .max()
    .sum()
)
year_expense = expenses[expenses["Periode"].dt.year == selected_period.year]["Nominal"].sum()

active_residents = period_income_rows[period_income_rows["Iuran"] > 0].copy()
active_residents["Status"] = active_residents["Jumlah Bayar"].apply(
    lambda amount: "Sudah Bayar" if amount > 0 else "Belum Bayar"
)
paid_count = (active_residents["Status"] == "Sudah Bayar").sum()

if page == "Ringkasan":
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"Surplus {selected_period.year}", rupiah(year_income - year_expense))
    col2.metric("Pemasukan Periode", rupiah(period_income))
    col3.metric("Pengeluaran Periode", rupiah(period_expense))
    col4.metric("Sudah Bayar Iuran", f"{paid_count} / {len(active_residents)} penghuni")

    year_periods = sorted(
        period for period in available_periods if period.year == selected_period.year
    )
    cashflow_rows = []
    for period in year_periods:
        month_income = income[income["Periode"] == period]["Total Periode"].max()
        month_expense = expenses[expenses["Periode"] == period]["Nominal"].sum()
        cashflow_rows.extend(
            [
                {"Bulan": MONTH_LABELS[period.month], "Jenis": "Pemasukan", "Nominal": month_income},
                {"Bulan": MONTH_LABELS[period.month], "Jenis": "Pengeluaran", "Nominal": month_expense},
            ]
        )
    cashflow = pd.DataFrame(cashflow_rows)

    left, right = st.columns([1.6, 1])
    with left:
        st.subheader(f"Arus Kas {selected_period.year}")
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
        category_data = period_expenses.groupby("Kategori", as_index=False)["Nominal"].sum()
        if category_data.empty:
            st.info("Belum ada pengeluaran pada periode ini.")
        else:
            figure = px.pie(
                category_data,
                names="Kategori",
                values="Nominal",
                hole=0.58,
                color_discrete_sequence=["#176b4d", "#d97824", "#6e91aa", "#c6d2cc"],
            )
            figure.update_layout(margin=dict(l=0, r=0, t=15, b=0), legend_title_text="")
            st.plotly_chart(figure, use_container_width=True)

    left, right = st.columns([1.45, 1])
    with left:
        st.subheader("Pengeluaran Terbaru")
        latest = period_expenses.sort_values("Tanggal", ascending=False).copy()
        latest["Tanggal"] = latest["Tanggal"].dt.strftime("%d %b %Y").fillna("-")
        st.dataframe(
            latest[["Tanggal", "Keterangan", "Kategori", "Nominal"]],
            hide_index=True,
            use_container_width=True,
            column_config={"Nominal": st.column_config.NumberColumn(format="Rp %d")},
        )
    with right:
        st.subheader("Status Iuran")
        progress = paid_count / len(active_residents) if len(active_residents) else 0
        st.progress(
            progress,
            text=f"{paid_count} dari {len(active_residents)} penghuni sudah bayar",
        )
        status_preview = active_residents[["Nama", "Tipe Kamar", "Status"]]
        st.dataframe(status_preview, hide_index=True, use_container_width=True)

elif page == "Pemasukan":
    st.subheader(f"Pemasukan Iuran - {selected_label}")
    display = period_income_rows[
        ["Nama", "Tipe Kamar", "Iuran", "Jumlah Bayar", "Tanggal Bayar"]
    ].copy()
    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Iuran": st.column_config.NumberColumn(format="Rp %d"),
            "Jumlah Bayar": st.column_config.NumberColumn(format="Rp %d"),
            "Tanggal Bayar": st.column_config.DateColumn(format="DD MMM YYYY"),
        },
    )

elif page == "Pengeluaran":
    st.subheader(f"Pengeluaran - {selected_label}")
    st.metric("Total Pengeluaran", rupiah(period_expense))
    st.dataframe(
        period_expenses.sort_values("Tanggal", ascending=False),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Periode": None,
            "Tanggal": st.column_config.DateColumn(format="DD MMM YYYY"),
            "Nominal": st.column_config.NumberColumn(format="Rp %d"),
        },
    )

elif page == "Iuran Penghuni":
    st.subheader(f"Status Iuran Penghuni - {selected_label}")
    filter_status = st.segmented_control(
        "Filter Iuran",
        ["Belum Bayar", "Sudah Bayar"],
        default="Belum Bayar",
    )
    status_data = active_residents
    status_data = status_data[status_data["Status"] == filter_status]
    st.dataframe(
        status_data[["Nama", "Tipe Kamar", "Iuran", "Jumlah Bayar", "Status"]],
        hide_index=True,
        use_container_width=True,
        column_config={
            "Iuran": st.column_config.NumberColumn(format="Rp %d"),
            "Jumlah Bayar": st.column_config.NumberColumn(format="Rp %d"),
        },
    )

else:
    st.subheader("Laporan Keuangan")
    report = []
    for period in sorted(available_periods):
        month_income = income[income["Periode"] == period]["Total Periode"].max()
        month_expense = expenses[expenses["Periode"] == period]["Nominal"].sum()
        report.append(
            {
                "Periode": f"{MONTH_LABELS[period.month]} {period.year}",
                "Pemasukan": month_income,
                "Pengeluaran": month_expense,
                "Surplus/Defisit": month_income - month_expense,
            }
        )
    report = pd.DataFrame(report)
    st.dataframe(
        report,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Pemasukan": st.column_config.NumberColumn(format="Rp %d"),
            "Pengeluaran": st.column_config.NumberColumn(format="Rp %d"),
            "Surplus/Defisit": st.column_config.NumberColumn(format="Rp %d"),
        },
    )
    col1, col2 = st.columns(2)
    col1.download_button(
        "Unduh pemasukan CSV",
        income.to_csv(index=False).encode("utf-8"),
        "pemasukan_mess.csv",
        "text/csv",
    )
    col2.download_button(
        "Unduh pengeluaran CSV",
        expenses.to_csv(index=False).encode("utf-8"),
        "pengeluaran_mess.csv",
        "text/csv",
    )
