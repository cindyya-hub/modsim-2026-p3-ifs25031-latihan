import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import random
import numpy as np
from datetime import datetime, timedelta

class SimulasiPiketITDel:
    def __init__(self, total_ompreng=180, total_petugas=7, target_menit=45, 
                 waktu_isi_rata=30, waktu_angkut_rata=20, kapasitas_angkut=7,
                 seed=None):
        self.total_ompreng = total_ompreng
        self.total_petugas = total_petugas
        self.target_menit = target_menit
        self.target_detik = target_menit * 60
        
        self.waktu_isi_rata = waktu_isi_rata
        self.waktu_isi_std = 5
        
        self.waktu_angkut_rata = waktu_angkut_rata
        self.waktu_angkut_std = 5
        
        self.kapasitas_angkut = kapasitas_angkut
        
        self.petugas_lauk_awal = 3
        self.petugas_angkut_awal = 1
        self.petugas_nasi_awal = 3
        
        if seed is not None:
            random.seed(seed)
        
        # Untuk tracking data visualisasi
        self.progress_data = []
        self.event_log = []
        
    def _generate_time(self, rata, std):
        waktu = int(random.gauss(rata, std))
        return max(10, waktu)

    def run_trial(self, trial_id, track_progress=True):
        # Reset tracking data
        if track_progress:
            self.progress_data = []
            self.event_log = []
        
        # State Antrean
        ompreng_lauk_done = [] 
        ompreng_di_meja = []
        ompreng_selesai = 0
        
        # State Petugas
        petugas_lauk = [0] * self.petugas_lauk_awal
        petugas_angkut = [0] * self.petugas_angkut_awal
        petugas_nasi = [0] * self.petugas_nasi_awal
        
        sisa_lauk = self.total_ompreng
        
        current_time = 0
        log_interval = 60  # Catat setiap menit
        
        lauk_selesai_permanen = False
        max_time = self.target_detik + 600
        
        # Tracking utilization
        lauk_busy_time = 0
        angkut_busy_time = 0
        nasi_busy_time = 0
        
        while ompreng_selesai < self.total_ompreng:
            if current_time > max_time:
                break
            
            # Track busy time
            if track_progress and current_time > 0:
                lauk_busy_time += sum(1 for t in petugas_lauk if t > current_time)
                angkut_busy_time += sum(1 for t in petugas_angkut if t > current_time)
                nasi_busy_time += sum(1 for t in petugas_nasi if t > current_time)
            
            # Alih Daya Dinamis
            if sisa_lauk == 0 and len(ompreng_lauk_done) == 0:
                if not lauk_selesai_permanen:
                    petugas_nasi.extend(petugas_lauk)
                    petugas_lauk = []
                    lauk_selesai_permanen = True
            
            # A. Selesaikan Tugas Lauk
            for i in range(len(petugas_lauk)):
                if petugas_lauk[i] == current_time:
                    ompreng_lauk_done.append(current_time)
                    if track_progress:
                        self.event_log.append({
                            'time': current_time,
                            'event': 'lauk_done',
                            'trial': trial_id
                        })
            
            # B. Selesaikan Tugas Angkut
            for i in range(len(petugas_angkut)):
                if petugas_angkut[i] <= current_time:
                    if len(ompreng_lauk_done) > 0:
                        batch_size = min(self.kapasitas_angkut, len(ompreng_lauk_done))
                        for _ in range(batch_size):
                            ompreng_lauk_done.pop(0)
                        
                        durasi = self._generate_time(self.waktu_angkut_rata, self.waktu_angkut_std)
                        petugas_angkut[i] = current_time + durasi
                        
                        for _ in range(batch_size):
                            ompreng_di_meja.append(current_time + durasi)
                        if track_progress:
                            self.event_log.append({
                                'time': current_time,
                                'event': 'angkut_start',
                                'batch': batch_size,
                                'trial': trial_id
                            })
                    else:
                        petugas_angkut[i] = current_time + 1

            # C. Selesaikan Tugas Nasi
            for i in range(len(petugas_nasi)):
                if petugas_nasi[i] <= current_time:
                    siap_nasi = [t for t in ompreng_di_meja if t <= current_time]
                    if len(siap_nasi) > 0:
                        ompreng_di_meja.remove(siap_nasi[0])
                        
                        durasi = self._generate_time(self.waktu_isi_rata, self.waktu_isi_std)
                        petugas_nasi[i] = current_time + durasi
                        ompreng_selesai += 1
                        if track_progress:
                            self.event_log.append({
                                'time': current_time,
                                'event': 'nasi_done',
                                'trial': trial_id
                            })
                    else:
                        petugas_nasi[i] = current_time + 1
            
            # D. Update Status Lauk
            for i in range(len(petugas_lauk)):
                if petugas_lauk[i] <= current_time and sisa_lauk > 0:
                    durasi = self._generate_time(self.waktu_isi_rata, self.waktu_isi_std)
                    petugas_lauk[i] = current_time + durasi
                    sisa_lauk -= 1
                    if track_progress:
                        self.event_log.append({
                            'time': current_time,
                            'event': 'lauk_start',
                            'trial': trial_id
                        })
            
            # Log Progress
            if track_progress and current_time % log_interval == 0:
                self.progress_data.append({
                    'time': current_time,
                    'trial': trial_id,
                    'lauk_done': self.total_ompreng - sisa_lauk,
                    'nasi_done': ompreng_selesai,
                    'in_progress': len(ompreng_lauk_done) + len(ompreng_di_meja)
                })
            
            current_time += 1
            
            if current_time > 10000: 
                break

        # Final log
        if track_progress:
            self.progress_data.append({
                'time': current_time,
                'trial': trial_id,
                'lauk_done': self.total_ompreng,
                'nasi_done': ompreng_selesai,
                'in_progress': 0
            })
        
        # Calculate utilization
        total_possible_time = current_time * len(petugas_lauk) if petugas_lauk else current_time * 3
        utilization = {
            'lauk': (lauk_busy_time / (current_time * 3)) * 100 if current_time > 0 else 0,
            'angkut': (angkut_busy_time / (current_time * 1)) * 100 if current_time > 0 else 0,
            'nasi': (nasi_busy_time / (current_time * 3)) * 100 if current_time > 0 else 0
        }
        
        return current_time, utilization

    def run_simulation(self, trials=5):
        hasil = []
        utilizations = []
        all_progress = []
        
        for i in range(trials):
            waktu_selesai, util = self.run_trial(i+1)
            hasil.append(waktu_selesai)
            utilizations.append(util)
            all_progress.extend(self.progress_data)
        
        avg_detik = sum(hasil) / len(hasil)
        
        return {
            'times': hasil,
            'avg_time': avg_detik,
            'utilizations': utilizations,
            'progress': all_progress,
            'events': self.event_log
        }

# Streamlit App
st.set_page_config(
    page_title="Simulasi Piket IT Del",
    page_icon="🍱",
    layout="wide"
)

st.title("🍱 Simulasi Sistem Piket IT Del")
st.markdown("---")

# Sidebar untuk parameter
st.sidebar.header("⚙️ Parameter Simulasi")

total_ompreng = st.sidebar.number_input("Total Ompreng", min_value=60, max_value=300, value=180, step=10)
total_petugas = st.sidebar.number_input("Total Petugas", min_value=3, max_value=15, value=7, step=1)
target_menit = st.sidebar.number_input("Target Waktu (menit)", min_value=30, max_value=90, value=45, step=5)

st.sidebar.subheader("Waktu Kerja")
waktu_isi_rata = st.sidebar.slider("Rata-rata Waktu Isi (detik)", 20, 60, 30, 5)
waktu_angkut_rata = st.sidebar.slider("Rata-rata Waktu Angkut (detik)", 10, 60, 20, 5)
kapasitas_angkut = st.sidebar.slider("Kapasitas Angkut (ompreng/trip)", 3, 10, 7, 1)

num_trials = st.sidebar.slider("Jumlah Trial", 1, 20, 5, 1)
random_seed = st.sidebar.number_input("Random Seed (opsional)", min_value=0, max_value=1000, value=42, step=1)

# Tombol simulasi
if st.sidebar.button("🚀 Jalankan Simulasi", type="primary"):
    with st.spinner("Menjalankan simulasi..."):
        sim = SimulasiPiketITDel(
            total_ompreng=total_ompreng,
            total_petugas=total_petugas,
            target_menit=target_menit,
            waktu_isi_rata=waktu_isi_rata,
            waktu_angkut_rata=waktu_angkut_rata,
            kapasitas_angkut=kapasitas_angkut,
            seed=random_seed if random_seed > 0 else None
        )
        
        results = sim.run_simulation(trials=num_trials)
        
        # Konversi ke DataFrame
        df_times = pd.DataFrame({
            'Trial': range(1, len(results['times']) + 1),
            'Waktu (menit)': [t/60 for t in results['times']],
            'Status': ['✅ Berhasil' if t <= target_menit*60 else '❌ Gagal' for t in results['times']]
        })
        
        df_progress = pd.DataFrame(results['progress'])
        
        # Utilization average
        avg_util = {
            'lauk': np.mean([u['lauk'] for u in results['utilizations']]),
            'angkut': np.mean([u['angkut'] for u in results['utilizations']]),
            'nasi': np.mean([u['nasi'] for u in results['utilizations']])
        }
        
        # Tampilkan hasil
        st.success(f"✅ Simulasi Selesai!")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        avg_minutes = results['avg_time'] / 60
        success_rate = (df_times['Status'] == '✅ Berhasil').sum() / len(df_times) * 100
        
        with col1:
            st.metric("Rata-rata Waktu", f"{avg_minutes:.1f} menit", 
                     delta=f"{'✅' if avg_minutes <= target_menit else '⚠️'} Target: {target_menit} menit")
        with col2:
            st.metric("Waktu Tercepat", f"{min(results['times'])/60:.1f} menit")
        with col3:
            st.metric("Waktu Terlama", f"{max(results['times'])/60:.1f} menit")
        with col4:
            st.metric("Tingkat Keberhasilan", f"{success_rate:.0f}%")
        
        st.markdown("---")
        
        # Tab untuk visualisasi
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Progress Chart", "📈 Distribusi Waktu", "⚡ Utilization", "📋 Detail Data"])
        
        with tab1:
            st.subheader("Progress Pengerjaan per Waktu")
            
            # Line chart progress
            fig_progress = go.Figure()
            
            for trial in df_progress['trial'].unique():
                trial_data = df_progress[df_progress['trial'] == trial]
                fig_progress.add_trace(go.Scatter(
                    x=[t/60 for t in trial_data['time']],
                    y=trial_data['nasi_done'],
                    mode='lines',
                    name=f'Trial {trial}',
                    line=dict(width=2)
                ))
            
            # Target line
            fig_progress.add_hline(
                y=total_ompreng, 
                line_dash="dash", 
                line_color="red",
                annotation_text="Target: Semua Ompreng",
                annotation_position="top right"
            )
            
            fig_progress.add_vline(
                x=target_menit, 
                line_dash="dash", 
                line_color="green",
                annotation_text=f"Target Waktu: {target_menit} menit",
                annotation_position="top right"
            )
            
            fig_progress.update_layout(
                title="Jumlah Ompreng Selesai vs Waktu",
                xaxis_title="Waktu (menit)",
                yaxis_title="Ompreng Selesai",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig_progress, use_container_width=True)
            
            # Area chart untuk stage
            if not df_progress.empty:
                fig_stage = go.Figure()
                
                trial_1 = df_progress[df_progress['trial'] == 1]
                
                fig_stage.add_trace(go.Scatter(
                    x=[t/60 for t in trial_1['time']],
                    y=trial_1['lauk_done'],
                    mode='lines',
                    name='Lauk Selesai',
                    stackgroup='one',
                    line=dict(width=0.5)
                ))
                
                fig_stage.add_trace(go.Scatter(
                    x=[t/60 for t in trial_1['time']],
                    y=trial_1['nasi_done'],
                    mode='lines',
                    name='Nasi Selesai (Final)',
                    stackgroup='one',
                    line=dict(width=2, color='green')
                ))
                
                fig_stage.update_layout(
                    title="Stack Progress: Lauk → Nasi",
                    xaxis_title="Waktu (menit)",
                    yaxis_title="Jumlah Ompreng",
                    height=400
                )
                
                st.plotly_chart(fig_stage, use_container_width=True)
        
        with tab2:
            st.subheader("Distribusi Waktu Penyelesaian")
            
            # Histogram
            fig_hist = px.histogram(
                df_times, 
                x="Waktu (menit)",
                color="Status",
                nbins=10,
                title="Distribusi Waktu Penyelesaian per Trial",
                labels={"Waktu (menit)": "Waktu (menit)", "count": "Frekuensi"},
                color_discrete_map={'✅ Berhasil': 'green', '❌ Gagal': 'red'}
            )
            
            fig_hist.add_vline(
                x=target_menit,
                line_dash="dash",
                line_color="orange",
                annotation_text=f"Target: {target_menit} menit"
            )
            
            fig_hist.update_layout(height=400)
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # Box plot
            col1, col2 = st.columns(2)
            
            with col1:
                fig_box = px.box(
                    df_times, 
                    y="Waktu (menit)",
                    title="Box Plot Waktu Penyelesaian",
                    points="all"
                )
                fig_box.add_hline(
                    y=target_menit,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Target"
                )
                fig_box.update_layout(height=400)
                st.plotly_chart(fig_box, use_container_width=True)
            
            with col2:
                # Gauge chart untuk success rate
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=success_rate,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Tingkat Keberhasilan", 'font': {'size': 24}},
                    delta={'reference': 100, 'increasing': {'color': "RebeccaPurple"}},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "gray"},
                            {'range': [80, 100], 'color': "lightgreen"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': target_menit
                        }
                    }
                ))
                fig_gauge.update_layout(height=400)
                st.plotly_chart(fig_gauge, use_container_width=True)
        
        with tab3:
            st.subheader("Utilization Petugas")
            
            # Bar chart utilization
            util_df = pd.DataFrame({
                'Tim': ['Isi Lauk', 'Angkut', 'Isi Nasi'],
                'Utilization (%)': [avg_util['lauk'], avg_util['angkut'], avg_util['nasi']]
            })
            
            fig_util = px.bar(
                util_df,
                x='Tim',
                y='Utilization (%)',
                color='Utilization (%)',
                color_continuous_scale='RdYlGn',
                title="Rata-rata Utilization Petugas per Tim",
                text=util_df['Utilization (%)'].apply(lambda x: f"{x:.1f}%")
            )
            
            fig_util.update_traces(textposition='outside')
            fig_util.update_layout(height=400)
            st.plotly_chart(fig_util, use_container_width=True)
            
            # Pie chart
            col1, col2 = st.columns(2)
            
            with col1:
                fig_pie = px.pie(
                    values=[avg_util['lauk'], avg_util['angkut'], avg_util['nasi']],
                    names=['Isi Lauk', 'Angkut', 'Isi Nasi'],
                    title="Distribusi Utilization"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.markdown("### 💡 Insight Utilization")
                if avg_util['angkut'] < 50:
                    st.warning("⚠️ Tim Angkut underutilized. Pertimbangkan mengurangi 1 petugas angkut.")
                if avg_util['lauk'] > 90 or avg_util['nasi'] > 90:
                    st.error("🔴 Tim Lauk/Nasi overload. Tambah petugas atau percepat proses.")
                if avg_util['angkut'] > 80:
                    st.info("ℹ️ Tim Angkut bekerja optimal. Pertahankan kapasitas 7 ompreng/trip.")
        
        with tab4:
            st.subheader("Detail Data per Trial")
            
            # Tabel hasil
            st.dataframe(df_times, use_container_width=True)
            
            # Download button
            csv = df_times.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data (CSV)",
                data=csv,
                file_name='hasil_simulasi_piket.csv',
                mime='text/csv'
            )
            
            # Kesimpulan
            st.markdown("### 📝 Kesimpulan")
            if avg_minutes <= target_menit:
                st.success(f"""
                **✅ SISTEM OPTIMAL**
                
                Dengan konfigurasi saat ini:
                - {total_petugas} petugas
                - {kapasitas_angkut} ompreng per trip
                - {waktu_isi_rata} detik waktu isi rata-rata
                
                Sistem dapat menyelesaikan {total_ompreng} ompreng dalam **{avg_minutes:.1f} menit** 
                (target: {target_menit} menit).
                """)
            else:
                st.error(f"""
                **⚠️ SISTEM PERLU OPTIMASI**
                
                Rata-rata waktu penyelesaian: **{avg_minutes:.1f} menit**
                Target: **{target_menit} menit**
                Keterlambatan: **{avg_minutes - target_menit:.1f} menit**
                
                **Rekomendasi:**
                1. Tambah jumlah petugas
                2. Percepat waktu isi/angkut
                3. Tingkatkan kapasitas angkut
                """)

else:
    st.info("👈 Klik tombol 'Jalankan Simulasi' di sidebar untuk memulai")
    
    # Contoh visualisasi default
    st.markdown("### 📖 Cara Menggunakan:")
    st.markdown("""
    1. Atur parameter di sidebar (jumlah ompreng, petugas, target waktu, dll)
    2. Klik tombol **Jalankan Simulasi**
    3. Lihat hasil di 4 tab:
       - **Progress Chart**: Visualisasi progress pengerjaan
       - **Distribusi Waktu**: Histogram dan box plot waktu penyelesaian
       - **Utilization**: Efisiensi kerja setiap tim
       - **Detail Data**: Tabel hasil simulasi
    
    ### 🎯 Parameter Default:
    - Total Ompreng: 180 (60 meja × 3 mahasiswa)
    - Total Petugas: 7 orang
    - Formasi: 3 Isi Lauk, 1 Angkut, 3 Isi Nasi
    - Target: 45 menit
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Simulasi Piket IT Del | Built with Streamlit & Plotly</p>
</div>
""", unsafe_allow_html=True)