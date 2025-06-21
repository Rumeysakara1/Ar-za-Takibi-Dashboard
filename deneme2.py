import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Bakım ve Arıza Verisi Dashboard")

# ✔ Oturumda grafikleri tutmak için liste
if "eklenen_grafikler" not in st.session_state:
    st.session_state.eklenen_grafikler = []

# ✔ Sidebar: Dosya Yükleme
st.sidebar.header("Veri Yükle ve Filtrele")
uploaded_file = st.sidebar.file_uploader("Excel dosyasını yükleyin", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()
        st.sidebar.success("✅ Excel dosyası yüklendi")

        # ✔ Genel İstatistik Kutusu
        st.markdown("""
    <div style="border: 4px solid #4CAF50; padding: 16px; border-radius: 8px; background-color: #f9f9f9; width: 100%;">
        <div style="display: flex; justify-content: space-around; align-items: center;">
            <div style="text-align: center;">
                <div style="font-weight: 600; font-size: 18px;">Toplam Arıza Sayısı</div>
                <div style="font-size: 32px; color: #2E7D32;">{}</div>
            </div>
            <div style="text-align: center;">
                <div style="font-weight: 600; font-size: 18px;">Üretimi Durduran Arıza Süresi</div>
                <div style="font-size: 32px; color: #2E7D32;">{} dk</div>
            </div>
            <div style="text-align: center;">
                <div style="font-weight: 600; font-size: 18px;">Toplam Arıza Süresi</div>
                <div style="font-size: 32px; color: #2E7D32;">{} dk</div>
            </div>
        </div>
    </div>
""".format(
    len(df),
    int(df['ÜRETİM DURDU'].sum()),
    int(df['ÜRETİM DURDU'].sum() + df['DİĞER ARIZALAR'].sum())
), unsafe_allow_html=True)

        # ✔ Sidebar: Filtreler
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtreler")
        filtered_df = df.copy()
        active_filters = {}

        for col in df.columns:
            unique_vals = df[col].dropna().unique()
            if len(unique_vals) <= 100:
                options = sorted([str(val) for val in unique_vals])
                selected = st.sidebar.multiselect(f"{col} filtresi", options=options)
                if selected:
                    active_filters[col] = selected
                    filtered_df = filtered_df[filtered_df[col].astype(str).isin(selected)]

        # ✔ Grafik Seçimi
        st.sidebar.markdown("---")
        chart_type = st.sidebar.selectbox("Grafik Türü Seçin", ["Seçiniz", "Sütun (Bar)", "Çizgi (Line)", "Daire (Pie)"])

        # ✔ Grafik Ayarları (Grafik türüne bağlı olarak)
        x_axis = y_axis = measure = ratio_type = compare_type = None
        if chart_type in ["Sütun (Bar)", "Çizgi (Line)"]:
            x_axis = st.sidebar.selectbox("X Ekseni", ["ARIZA TÜRÜ", "BÖLÜM ADI", "MAKİNE", "ARIZA SEBEBİ"])
            y_axis = st.sidebar.selectbox("Y Ekseni", ["Arıza Sayısı", "Arıza Süreci (dk)"])
            compare_type = st.sidebar.selectbox("Kıyas", ["Toplam", "Üretim Durdu/Durmadı"])
        elif chart_type == "Daire (Pie)":
            measure = st.sidebar.selectbox("Ölçüt Seçin", ["Arıza Sayısı", "Arıza Süreci (dk)"])
            ratio_type = st.sidebar.selectbox("Oran Tipi", ["Tüme Oran", "Üretim Durdu/Durmadı"])

        generate_chart = st.sidebar.button("Grafik Getir")

        if generate_chart:
            if chart_type == "Seçiniz":
                st.warning("Lütfen grafik türü seçin.")
            elif not active_filters:
                st.warning("Lütfen en az bir filtre seçin.")
            elif filtered_df.empty:
                st.warning("⚠️ Eşleşen kayıt bulunamadı.")
            else:
                st.markdown("### Grafik ve Tablo")

                # ✔ Grafik Veri Hazırlama
                if chart_type in ["Sütun (Bar)", "Çizgi (Line)"]:
                    if y_axis == "Arıza Sayısı":
                        if compare_type == "Toplam":
                            agg_df = filtered_df.groupby(x_axis).size().reset_index(name="Değer")
                            fig = px.bar(agg_df, x=x_axis, y="Değer") if chart_type == "Sütun (Bar)" else px.line(agg_df, x=x_axis, y="Değer")
                        else:
                            df_temp = filtered_df.copy()
                            df_temp["Durum"] = df_temp["ÜRETİM DURDU"].apply(lambda x: "Durdu" if x > 0 else "Durmadı")
                            agg_df = df_temp.groupby([x_axis, "Durum"]).size().reset_index(name="Değer")
                            fig = px.bar(agg_df, x=x_axis, y="Değer", color="Durum", barmode="group") if chart_type == "Sütun (Bar)" else px.line(agg_df, x=x_axis, y="Değer", color="Durum")
                    else:  # Arıza Süreci (dk)
                        df_temp = filtered_df.copy()
                        df_temp["Toplam"] = df_temp["ÜRETİM DURDU"] + df_temp["DİĞER ARIZALAR"]
                        if compare_type == "Toplam":
                            agg_df = df_temp.groupby(x_axis)["Toplam"].sum().reset_index()
                            fig = px.bar(agg_df, x=x_axis, y="Toplam") if chart_type == "Sütun (Bar)" else px.line(agg_df, x=x_axis, y="Toplam")
                        else:
                            df_temp["Durum"] = df_temp["ÜRETİM DURDU"].apply(lambda x: "Durdu" if x > 0 else "Durmadı")
                            agg_df = df_temp.groupby([x_axis, "Durum"])["Toplam"].sum().reset_index()
                            fig = px.bar(agg_df, x=x_axis, y="Toplam", color="Durum", barmode="group") if chart_type == "Sütun (Bar)" else px.line(agg_df, x=x_axis, y="Toplam", color="Durum")

                elif chart_type == "Daire (Pie)":
                    if measure == "Arıza Sayısı":
                        if ratio_type == "Tüme Oran":
                            oran = len(filtered_df) / len(df)
                            fig = px.pie(names=["Seçilenler", "Diğerleri"], values=[oran, 1-oran])
                            agg_df = pd.DataFrame({"Kategori": ["Seçilenler", "Diğerleri"], "Oran": [oran, 1 - oran]})
                        else:
                            durdu = len(filtered_df[filtered_df["ÜRETİM DURDU"] > 0])
                            durmadi = len(filtered_df) - durdu
                            fig = px.pie(names=["Durdu", "Durmadı"], values=[durdu, durmadi])
                            agg_df = pd.DataFrame({"Durum": ["Durdu", "Durmadı"], "Sayı": [durdu, durmadi]})
                    else:
                        total_filtered = filtered_df["ÜRETİM DURDU"] + filtered_df["DİĞER ARIZALAR"]
                        if ratio_type == "Tüme Oran":
                            toplam = df["ÜRETİM DURDU"] + df["DİĞER ARIZALAR"]
                            oran = total_filtered.sum() / toplam.sum()
                            fig = px.pie(names=["Seçilenler", "Diğerleri"], values=[oran, 1 - oran])
                            agg_df = pd.DataFrame({"Kategori": ["Seçilenler", "Diğerleri"], "Oran": [oran, 1 - oran]})
                        else:
                            durdu = filtered_df["ÜRETİM DURDU"].sum()
                            durmadi = filtered_df["DİĞER ARIZALAR"].sum()
                            fig = px.pie(names=["Durdu", "Durmadı"], values=[durdu, durmadi])
                            agg_df = pd.DataFrame({"Durum": ["Durdu", "Durmadı"], "Süre": [durdu, durmadi]})

                # ✔ Grafik ve tablo göster
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(agg_df)

                # ✔ Grafik ekleme butonu
                if st.button("Grafiği Ekle"):
                    st.session_state.eklenen_grafikler.insert(0, (fig, agg_df))
                    st.success("Grafik eklendi ✅")

        # ✔ Eklenen grafiklerin gösterimi
        if st.session_state.eklenen_grafikler:
            st.markdown("## Eklenen Grafikler")
            for i, (f, tdf) in enumerate(st.session_state.eklenen_grafikler):
                st.markdown(f"### Grafik {i+1}")
                st.plotly_chart(f, use_container_width=True)
                st.dataframe(tdf)

    except Exception as e:
        st.sidebar.error(f"Dosya okunurken hata oluştu: {e}")
