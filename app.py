import pandas as pd
import requests
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Tyre Monitoring Dashboard", page_icon="🛞", layout="wide"
)

# URL CSV Google Sheets Anda
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSecE07RLrZyfUlzIKsR-OtX2Ne70t1041dEdedWjA-FneiHc0aBqE5ajjugMKavNCmpnEdlP1SegHn/pub?output=csv"


@st.cache_data(ttl=600)
def load_data(url):
  try:
    df = pd.read_csv(url)
    # Bersihkan nama kolom dari spasi berlebih jika ada
    df.columns = df.columns.str.strip()
    return df
  except Exception as e:
    st.error(f"Gagal memuat data dari CSV: {e}")
    return pd.DataFrame()


df = load_data(CSV_URL)

if df.empty:
  st.warning(
      "Data kosong atau gagal dimuat. Periksa kembali link publikasi CSV Anda."
  )
  st.stop()

# Sidebar Navigasi untuk 6 Dashboard
st.sidebar.title("🛞 Tyre Monitoring System")
menu = st.sidebar.selectbox(
    "Pilih Dashboard",
    (
        "1. Achievement Program Tyre",
        "2. Tyre Pressure Inspection",
        "3. Rolling Tyre",
        "4. Backlog Tyre",
        "5. Repair Tyre",
        "6. Observasi Area Kerja Tyre",
    ),
)


# Fungsi Helper untuk Filter Bulan & Tanggal Umum
def filter_bulan_tanggal(
    data, col_bulan, col_tanggal, selected_bulan, selected_tanggal
):
  filtered = data.copy()
  if selected_bulan and selected_bulan != "SEMUA BULAN / YEAR TO DATE":
    if col_bulan in filtered.columns:
      filtered = filtered[filtered[col_bulan].astype(str) == str(selected_bulan)]

  if (
      selected_tanggal
      and selected_tanggal != "SEMUA TANGGAL"
      and col_tanggal
  ):
    if col_tanggal in filtered.columns:
      filtered = filtered[
          filtered[col_tanggal].astype(str) == str(selected_tanggal)
      ]
  return filtered


# ==========================================
# 1. ACHIEVEMENT PROGRAM TYRE
# ==========================================
if menu == "1. Achievement Program Tyre":
  st.title("📊 1. Achievement Program Tyre")
  st.markdown("Ringkasan pencapaian dari seluruh program tyre.")

  # Filter Bulan
  st.sidebar.subheader("Filter Utama")
  # Mengambil list bulan unik dari kolom B (asumsi kolom B adalah bulan di sheet terkait atau general)
  # Di sini kita sediakan opsi universal atau ambil dari salah satu kolom bulan (misal kolom B)
  list_bulan = (
      ["SEMUA BULAN / YEAR TO DATE"] + list(df.iloc[:, 1].dropna().unique())
      if df.shape[1] > 1
      else ["SEMUA BULAN / YEAR TO DATE"]
  )
  pilih_bulan = st.sidebar.selectbox(
      "Pilih Bulan", list_bulan, key="ach_bulan"
  )

  st.info(
      "Menampilkan rekapitulasi pencapaian Plan vs Actual vs Achievement per"
      " section."
  )

  # Menyiapkan ringkasan data dari section-section terkait
  # Sesuai permintaan: Tyre Pressure, Rolling, Repair, Observasi Area Kerja, Backlog
  col_tab1, col_tab2 = st.tabs(["Tabel Ringkasan", "Visualisasi Data"])

  with col_tab1:
    st.subheader("Ringkasan Pencapaian Program")

    # Fungsi pembantu untuk membuat rekap per section
    def get_summary(sec_col, plan_col, act_col, ach_col, nama_program):
      if all(
          c in df.columns
          for c in [sec_col, plan_col, act_col, ach_col]
      ):
        temp = df[[sec_col, plan_col, act_col, ach_col]].dropna(
            subset=[sec_col]
        )
        temp.columns = ["Section", "Plan", "Actual", "Achievement"]
        temp["Program"] = nama_program
        return temp
      return pd.DataFrame()

    # Indeks kolom berdasarkan abjad (A=0, B=1, dst):
    # Tyre Pressure: A (Section), B (Bulan), C (Tanggal), E (Plan), F (Actual), G (Achievement) -> index 0, 4, 5, 6
    # Rolling Tyre: J (Section), K (Bulan), L (Tanggal), N (Plan), O (Actual), P (Achievement) -> index 9, 13, 14, 15
    # Backlog Tyre: S (Bulan), T (Tanggal), V (Plan), W (Actual), X (Achievement) -> index 21, 22, 23 (Tanpa section, atau 'All')
    # Repair Tyre: AA (Section), AB (Bulan), AC (Tanggal), AE (Plan), AF (Actual), AG (Achievement) -> index 26, 30, 31, 32
    # Observasi Area: AJ (Location/Section), AK (Bulan), AL (Tanggal), AN (Plan), AO (Actual), AP (Achievement) -> index 35, 39, 40, 41

    try:
      summary_list = []
      if df.shape[1] > 6:
        t1 = df.iloc[:, [0, 4, 5, 6]].copy()
        t1.columns = ["Section", "Plan", "Actual", "Achievement"]
        t1["Program"] = "Tyre Pressure Inspection"
        summary_list.append(t1)

      if df.shape[1] > 15:
        t2 = df.iloc[:, [9, 13, 14, 15]].copy()
        t2.columns = ["Section", "Plan", "Actual", "Achievement"]
        t2["Program"] = "Rolling Tyre"
        summary_list.append(t2)

      if df.shape[1] > 23:
        t3 = df.iloc[:, [21, 22, 23]].copy()
        t3.columns = ["Plan", "Actual", "Achievement"]
        t3["Section"] = "GENERAL / ALL"
        t3["Program"] = "Backlog Tyre"
        summary_list.append(t3)

      if df.shape[1] > 32:
        t4 = df.iloc[:, [26, 30, 31, 32]].copy()
        t4.columns = ["Section", "Plan", "Actual", "Achievement"]
        t4["Program"] = "Repair Tyre"
        summary_list.append(t4)

      if df.shape[1] > 41:
        t5 = df.iloc[:, [35, 39, 40, 41]].copy()
        t5.columns = ["Section", "Plan", "Actual", "Achievement"]
        t5["Program"] = "Observasi Area Kerja Tyre"
        summary_list.append(t5)

      if summary_list:
        final_summary = pd.concat(summary_list, ignore_index=True)
        st.dataframe(final_summary, use_container_width=True)
      else:
        st.warning("Struktur kolom tidak mencukupi untuk ringkasan otomatis.")
    except Exception as ex:
      st.error(f"Terjadi kesalahan saat memproses ringkasan: {ex}")

  with col_tab2:
    st.subheader("Grafik Pencapaian Keseluruhan")
    st.info(
      "Pastikan kolom Plan, Actual, dan Achievement bertipe angka agar grafik"
      " dapat dirender dengan baik."
    )


# ==========================================
# 2. TYRE PRESSURE INSPECTION
# ==========================================
elif menu == "2. Tyre Pressure Inspection":
  st.title("🔍 2. Tyre Pressure Inspection")

  # Filter Kolom A (Section), B (Bulan), C (Tanggal) -> Indeks 0, 1, 2
  col_A = df.columns[0] if len(df.columns) > 0 else None
  col_B = df.columns[1] if len(df.columns) > 1 else None
  col_C = df.columns[2] if len(df.columns) > 2 else None

  st.sidebar.subheader("Filter Tyre Pressure")
  sec_list = (
      ["ALL SECTION"] + list(df[col_A].dropna().unique()) if col_A else []
  )
  bulan_list = (
      ["SEMUA BULAN / YEAR TO DATE"] + list(df[col_B].dropna().unique())
      if col_B
      else []
  )
  tanggal_list = (
      ["SEMUA TANGGAL"] + list(df[col_C].dropna().unique()) if col_C else []
  )

  p_sec = st.sidebar.selectbox("Pilih Section (Kolom A)", sec_list)
  p_bulan = st.sidebar.selectbox("Pilih Bulan (Kolom B)", bulan_list)
  p_tgl = st.sidebar.selectbox("Pilih Tanggal (Kolom C)", tanggal_list)

  filtered_df = df.copy()
  if p_sec != "ALL SECTION" and col_A:
    filtered_df = filtered_df[filtered_df[col_A] == p_sec]
  if p_bulan != "SEMUA BULAN / YEAR TO DATE" and col_B:
    filtered_df = filtered_df[filtered_df[col_B].astype(str) == str(p_bulan)]
  if p_tgl != "SEMUA TANGGAL" and col_C:
    filtered_df = filtered_df[filtered_df[col_C].astype(str) == str(p_tgl)]

  # Menampilkan Plan (E -> Indeks 4), Actual (F -> Indeks 5), Achievement (G -> Indeks 6)
  target_cols = []
  col_names_map = {}
  if len(df.columns) > 4:
    target_cols.append(df.columns[4])
    col_names_map[df.columns[4]] = "Plan (Kolom E)"
  if len(df.columns) > 5:
    target_cols.append(df.columns[5])
    col_names_map[df.columns[5]] = "Actual (Kolom F)"
  if len(df.columns) > 6:
    target_cols.append(df.columns[6])
    col_names_map[df.columns[6]] = "Achievement (Kolom G)"

  display_cols = (
      [col_A, col_B, col_C] + target_cols
      if all([col_A, col_B, col_C])
      else target_cols
  )
  valid_display_cols = [c for c in display_cols if c in filtered_df.columns]

  st.subheader("Data Inspection")
  st.dataframe(
      filtered_df[valid_display_cols].rename(columns=col_names_map),
      use_container_width=True,
  )


# ==========================================
# 3. ROLLING TYRE
# ==========================================
elif menu == "3. Rolling Tyre":
  st.title("🔄 3. Rolling Tyre")

  # Filter Kolom J (Section), K (Bulan), L (Tanggal) -> Indeks 9, 10, 11
  col_J = df.columns[9] if len(df.columns) > 9 else None
  col_K = df.columns[10] if len(df.columns) > 10 else None
  col_L = df.columns[11] if len(df.columns) > 11 else None

  st.sidebar.subheader("Filter Rolling Tyre")
  sec_list = (
      ["ALL SECTION"] + list(df[col_J].dropna().unique()) if col_J else []
  )
  bulan_list = (
      ["SEMUA BULAN / YEAR TO DATE"] + list(df[col_K].dropna().unique())
      if col_K
      else []
  )
  tanggal_list = (
      ["SEMUA TANGGAL"] + list(df[col_L].dropna().unique()) if col_L else []
  )

  r_sec = st.sidebar.selectbox("Pilih Section (Kolom J)", sec_list)
  r_bulan = st.sidebar.selectbox("Pilih Bulan (Kolom K)", bulan_list)
  r_tgl = st.sidebar.selectbox("Pilih Tanggal (Kolom L)", tanggal_list)

  filtered_df = df.copy()
  if r_sec != "ALL SECTION" and col_J:
    filtered_df = filtered_df[filtered_df[col_J] == r_sec]
  if r_bulan != "SEMUA BULAN / YEAR TO DATE" and col_K:
    filtered_df = filtered_df[filtered_df[col_K].astype(str) == str(r_bulan)]
  if r_tgl != "SEMUA TANGGAL" and col_L:
    filtered_df = filtered_df[filtered_df[col_L].astype(str) == str(r_tgl)]

  # Menampilkan Plan (N -> Indeks 13), Actual (O -> Indeks 14), Achievement (P -> Indeks 15)
  target_cols = []
  col_names_map = {}
  if len(df.columns) > 13:
    target_cols.append(df.columns[13])
    col_names_map[df.columns[13]] = "Plan (Kolom N)"
  if len(df.columns) > 14:
    target_cols.append(df.columns[14])
    col_names_map[df.columns[14]] = "Actual (Kolom O)"
  if len(df.columns) > 15:
    target_cols.append(df.columns[15])
    col_names_map[df.columns[15]] = "Achievement (Kolom P)"

  display_cols = (
      [col_J, col_K, col_L] + target_cols
      if all([col_J, col_K, col_L])
      else target_cols
  )
  valid_display_cols = [c for c in display_cols if c in filtered_df.columns]

  st.subheader("Data Rolling Tyre")
  st.dataframe(
      filtered_df[valid_display_cols].rename(columns=col_names_map),
      use_container_width=True,
  )


# ==========================================
# 4. BACKLOG TYRE
# ==========================================
elif menu == "4. Backlog Tyre":
  st.title("⏳ 4. Backlog Tyre")

  # Filter Kolom S (Bulan), T (Tanggal) -> Indeks 18, 19
  col_S = df.columns[18] if len(df.columns) > 18 else None
  col_T = df.columns[19] if len(df.columns) > 19 else None

  st.sidebar.subheader("Filter Backlog Tyre")
  bulan_list = (
      ["SEMUA BULAN / YEAR TO DATE"] + list(df[col_S].dropna().unique())
      if col_S
      else []
  )
  tanggal_list = (
      ["SEMUA TANGGAL"] + list(df[col_T].dropna().unique()) if col_T else []
  )

  b_bulan = st.sidebar.selectbox("Pilih Bulan (Kolom S)", bulan_list)
  b_tgl = st.sidebar.selectbox("Pilih Tanggal (Kolom T)", tanggal_list)

  filtered_df = df.copy()
  if b_bulan != "SEMUA BULAN / YEAR TO DATE" and col_S:
    filtered_df = filtered_df[filtered_df[col_S].astype(str) == str(b_bulan)]
  if b_tgl != "SEMUA TANGGAL" and col_T:
    filtered_df = filtered_df[filtered_df[col_T].astype(str) == str(b_tgl)]

  # Menampilkan Plan (V -> Indeks 21), Actual (W -> Indeks 22), Achievement (X -> Indeks 23)
  target_cols = []
  col_names_map = {}
  if len(df.columns) > 21:
    target_cols.append(df.columns[21])
    col_names_map[df.columns[21]] = "Plan (Kolom V)"
  if len(df.columns) > 22:
    target_cols.append(df.columns[22])
    col_names_map[df.columns[22]] = "Actual (Kolom W)"
  if len(df.columns) > 23:
    target_cols.append(df.columns[23])
    col_names_map[df.columns[23]] = "Achievement (Kolom X)"

  display_cols = (
      [col_S, col_T] + target_cols if all([col_S, col_T]) else target_cols
  )
  valid_display_cols = [c for c in display_cols if c in filtered_df.columns]

  st.subheader("Data Backlog Tyre")
  st.dataframe(
      filtered_df[valid_display_cols].rename(columns=col_names_map),
      use_container_width=True,
  )


# ==========================================
# 5. REPAIR TYRE
# ==========================================
elif menu == "5. Repair Tyre":
  st.title("🔧 5. Repair Tyre")

  # Filter Kolom AA (Section), AB (Bulan), AC (Tanggal) -> Indeks 26, 27, 28
  col_AA = df.columns[26] if len(df.columns) > 26 else None
  col_AB = df.columns[27] if len(df.columns) > 27 else None
  col_AC = df.columns[28] if len(df.columns) > 28 else None

  st.sidebar.subheader("Filter Repair Tyre")
  sec_list = (
      ["ALL SECTION"] + list(df[col_AA].dropna().unique()) if col_AA else []
  )
  bulan_list = (
      ["SEMUA BULAN / YEAR TO DATE"] + list(df[col_AB].dropna().unique())
      if col_AB
      else []
  )
  tanggal_list = (
      ["SEMUA TANGGAL"] + list(df[col_AC].dropna().unique()) if col_AC else []
  )

  rep_sec = st.sidebar.selectbox("Pilih Section (Kolom AA)", sec_list)
  rep_bulan = st.sidebar.selectbox("Pilih Bulan (Kolom AB)", bulan_list)
  rep_tgl = st.sidebar.selectbox("Pilih Tanggal (Kolom AC)", tanggal_list)

  filtered_df = df.copy()
  if rep_sec != "ALL SECTION" and col_AA:
    filtered_df = filtered_df[filtered_df[col_AA] == rep_sec]
  if rep_bulan != "SEMUA BULAN / YEAR TO DATE" and col_AB:
    filtered_df = filtered_df[filtered_df[col_AB].astype(str) == str(rep_bulan)]
  if rep_tgl != "SEMUA TANGGAL" and col_AC:
    filtered_df = filtered_df[filtered_df[col_AC].astype(str) == str(rep_tgl)]

  # Menampilkan Plan (AE -> Indeks 30), Actual (AF -> Indeks 31), Achievement (AG -> Indeks 32)
  target_cols = []
  col_names_map = {}
  if len(df.columns) > 30:
    target_cols.append(df.columns[30])
    col_names_map[df.columns[30]] = "Plan (Kolom AE)"
  if len(df.columns) > 31:
    target_cols.append(df.columns[31])
    col_names_map[df.columns[31]] = "Actual (Kolom AF)"
  if len(df.columns) > 32:
    target_cols.append(df.columns[32])
    col_names_map[df.columns[32]] = "Achievement (Kolom AG)"

  display_cols = (
      [col_AA, col_AB, col_AC] + target_cols
      if all([col_AA, col_AB, col_AC])
      else target_cols
  )
  valid_display_cols = [c for c in display_cols if c in filtered_df.columns]

  st.subheader("Data Repair Tyre")
  st.dataframe(
      filtered_df[valid_display_cols].rename(columns=col_names_map),
      use_container_width=True,
  )


# ==========================================
# 6. OBSERVASI AREA KERJA TYRE
# ==========================================
elif menu == "6. Observasi Area Kerja Tyre":
  st.title("📋 6. Observasi Area Kerja Tyre")

  # Filter Kolom AJ (Location), AK (Bulan), AL (Tanggal) -> Indeks 35, 36, 37
  col_AJ = df.columns[35] if len(df.columns) > 35 else None
  col_AK = df.columns[36] if len(df.columns) > 36 else None
  col_AL = df.columns[37] if len(df.columns) > 37 else None

  st.sidebar.subheader("Filter Observasi Area")
  loc_list = (
      ["ALL LOCATION"] + list(df[col_AJ].dropna().unique()) if col_AJ else []
  )
  bulan_list = (
      ["SEMUA BULAN / YEAR TO DATE"] + list(df[col_AK].dropna().unique())
      if col_AK
      else []
  )
  tanggal_list = (
      ["SEMUA TANGGAL"] + list(df[col_AL].dropna().unique()) if col_AL else []
  )

  obs_loc = st.sidebar.selectbox("Pilih Location (Kolom AJ)", loc_list)
  obs_bulan = st.sidebar.selectbox("Pilih Bulan (Kolom AK)", bulan_list)
  obs_tgl = st.sidebar.selectbox("Pilih Tanggal (Kolom AL)", tanggal_list)

  filtered_df = df.copy()
  if obs_loc != "ALL LOCATION" and col_AJ:
    filtered_df = filtered_df[filtered_df[col_AJ] == obs_loc]
  if obs_bulan != "SEMUA BULAN / YEAR TO DATE" and col_AK:
    filtered_df = filtered_df[filtered_df[col_AK].astype(str) == str(obs_bulan)]
  if obs_tgl != "SEMUA TANGGAL" & col_AL:
    filtered_df = filtered_df[filtered_df[col_AL].astype(str) == str(obs_tgl)]

  # Menampilkan Plan (AN -> Indeks 39), Actual (AO -> Indeks 40), Achievement (AP -> Indeks 41)
  target_cols = []
  col_names_map = {}
  if len(df.columns) > 39:
    target_cols.append(df.columns[39])
    col_names_map[df.columns[39]] = "Plan (Kolom AN)"
  if len(df.columns) > 40:
    target_cols.append(df.columns[40])
    col_names_map[df.columns[40]] = "Actual (Kolom AO)"
  if len(df.columns) > 41:
    target_cols.append(df.columns[41])
    col_names_map[df.columns[41]] = "Achievement (Kolom AP)"

  display_cols = (
      [col_AJ, col_AK, col_AL] + target_cols
      if all([col_AJ, col_AK, col_AL])
      else target_cols
  )
  valid_display_cols = [c for c in display_cols if c in filtered_df.columns]

  st.subheader("Data Observasi Area Kerja Tyre")
  st.dataframe(
      filtered_df[valid_display_cols].rename(columns=col_names_map),
      use_container_width=True,
  )
