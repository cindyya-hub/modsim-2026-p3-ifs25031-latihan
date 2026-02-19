import random
import math

class SimulasiPiketITDel:
    def __init__(self, total_ompreng=180, total_petugas=7, target_menit=45):
        self.total_ompreng = total_ompreng
        self.total_petugas = total_petugas
        self.target_menit = target_menit
        self.target_detik = target_menit * 60
        
        # Konfigurasi Waktu (Optimized Values based on previous analysis)
        # Menggunakan distribusi normal sekitar rata-rata target untuk realisme
        self.waktu_isi_rata = 30  # detik (Target optimal)
        self.waktu_isi_std = 5    # variasi +/- 5 detik
        
        self.waktu_angkut_rata = 20 # detik per trip
        self.waktu_angkut_std = 5
        
        self.kapasitas_angkut = 7   # Maksimal ompreng per trip
        
        # Formasi Awal (3 Lauk, 1 Angkut, 3 Nasi)
        self.petugas_lauk_awal = 3
        self.petugas_angkut_awal = 1
        self.petugas_nasi_awal = 3
        
    def _generate_time(self, rata, std):
        """Menghasilkan waktu acak berdasarkan distribusi normal (dibatasi minimal 10 detik)"""
        waktu = int(random.gauss(rata, std))
        return max(10, waktu)

    def run_trial(self, trial_id):
        # State Antrean
        # ompreng_lauk_done: Ompreng yang sudah isi lauk, menunggu angkut
        # ompreng_di_meja: Ompreng yang sudah di meja, menunggu isi nasi
        ompreng_lauk_done = [] 
        ompreng_di_meja = []
        ompreng_selesai = 0
        
        # State Petugas (Menyimpan waktu selesai tugas saat ini)
        # Jika waktu <= current_time, petugas siap kerja
        petugas_lauk = [0] * self.petugas_lauk_awal
        petugas_angkut = [0] * self.petugas_angkut_awal
        petugas_nasi = [0] * self.petugas_nasi_awal
        
        # Sisa ompreng yang belum mulai proses lauk
        sisa_lauk = self.total_ompreng
        
        current_time = 0
        log_interval = 300 # Catat log setiap 5 menit
        
        # Untuk fitur alih daya dinamis
        lauk_selesai_permanen = False
        
        while ompreng_selesai < self.total_ompreng:
            # 1. Cek Batas Waktu (Safety Break)
            if current_time > self.target_detik + 600: # Stop jika lewat 10 menit dari target
                break
            
            # 2. Alih Daya Dinamis (Dynamic Reallocation)
            # Jika ompreng lauk habis dan petugas lauk menganggur, pindahkan ke tim nasi
            if sisa_lauk == 0 and len(ompreng_lauk_done) == 0:
                if not lauk_selesai_permanen:
                    # Pindahkan semua petugas lauk ke nasi
                    petugas_nasi.extend(petugas_lauk)
                    petugas_lauk = []
                    lauk_selesai_permanen = True
            
            # 3. Proses Tim Lauk
            for i in range(len(petugas_lauk)):
                if petugas_lauk[i] <= current_time and sisa_lauk > 0:
                    # Mulai tugas baru
                    durasi = self._generate_time(self.waktu_isi_rata, self.waktu_isi_std)
                    petugas_lauk[i] = current_time + durasi
                    sisa_lauk -= 1
                    # Ompreng akan siap di waktu selesai
                    # Kita simpan sebagai event selesai lauk
                    # Untuk simplifikasi simulasi loop, kita masukkan ke list selesai_lauk
                    # Tapi karena kita loop per detik, kita butuh antrian event.
                    # Agar lebih mudah: Kita gunakan pendekatan 'task completion' di bawah.
                    pass 
            
            # *Revisi Logika Loop agar lebih akurat tanpa event queue kompleks*
            # Kita akan cek penyelesaian tugas di setiap detik
            pass 

            # --- REVISI LOGIKA SIMULASI (LEBIH ROBUST) ---
            # Kita tidak update state di atas, tapi kita cek penyelesaian di bawah
            
            # A. Selesaikan Tugas Lauk
            for i in range(len(petugas_lauk)):
                if petugas_lauk[i] == current_time: # Tugas selesai tepat di detik ini
                    ompreng_lauk_done.append(current_time)
            
            # B. Selesaikan Tugas Angkut (Batch)
            # Petugas angkut mengambil maksimal 7 dari ompreng_lauk_done
            for i in range(len(petugas_angkut)):
                if petugas_angkut[i] <= current_time:
                    if len(ompreng_lauk_done) > 0:
                        # Ambil batch
                        batch_size = min(self.kapasitas_angkut, len(ompreng_lauk_done))
                        # Hapus dari antrean lauk done
                        for _ in range(batch_size):
                            ompreng_lauk_done.pop(0)
                        
                        # Kirim ke meja
                        durasi = self._generate_time(self.waktu_angkut_rata, self.waktu_angkut_std)
                        petugas_angkut[i] = current_time + durasi
                        # Ompreng akan tiba di meja pada waktu selesai
                        # Kita simpan dalam list 'tiba_di_meja' nanti
                        # Agar simpel, kita anggap selesai angkut = siap nasi
                        # Tapi perlu simpan jumlah ompreng yang tiba
                        # Kita gunakan list ompreng_di_meja sebagai counter saja
                        for _ in range(batch_size):
                            ompreng_di_meja.append(current_time + durasi) # Waktu siap nasi
                    else:
                        # Jika tidak ada kerja, tunggu 1 detik lalu cek lagi
                        petugas_angkut[i] = current_time + 1

            # C. Selesaikan Tugas Nasi
            for i in range(len(petugas_nasi)):
                if petugas_nasi[i] <= current_time:
                    # Cek ada ompreng yang sudah siap nasi (waktu tiba <= current_time)
                    siap_nasi = [t for t in ompreng_di_meja if t <= current_time]
                    if len(siap_nasi) > 0:
                        # Ambil 1 ompreng
                        ompreng_di_meja.remove(siap_nasi[0])
                        
                        durasi = self._generate_time(self.waktu_isi_rata, self.waktu_isi_std)
                        petugas_nasi[i] = current_time + durasi
                        ompreng_selesai += 1
                    else:
                        petugas_nasi[i] = current_time + 1 # Tunggu
            
            # D. Update Status Lauk (Memulai tugas)
            # Ini harus dilakukan setelah cek selesai, agar slot kosong terisi
            for i in range(len(petugas_lauk)):
                if petugas_lauk[i] <= current_time and sisa_lauk > 0:
                    durasi = self._generate_time(self.waktu_isi_rata, self.waktu_isi_std)
                    petugas_lauk[i] = current_time + durasi
                    sisa_lauk -= 1
            
            # Log Progress
            if current_time % log_interval == 0:
                print(f"[{trial_id}] Menit {current_time//60:02d}:{current_time%60:02d} | "
                      f"Lauk: {self.total_ompreng - sisa_lauk}/{self.total_ompreng} | "
                      f"Selesai: {ompreng_selesai}/{self.total_ompreng}")
            
            current_time += 1
            
            # Kondisi Berhenti jika macet (safety)
            if current_time > 10000: 
                print("Simulasi terhenti: Timeout")
                break

        return current_time

    def run_simulation(self, trials=5):
        print(f"=== SIMULASI PIKET IT DEL ({self.total_petugas} PETUGAS) ===")
        print(f"Target: {self.target_menit} Menit ({self.target_detik} Detik)")
        print(f"Total Ompreng: {self.total_ompreng}")
        print(f"Strategi: 3 Lauk, 1 Angkut, 3 Nasi (Alih Daya Dinamis)")
        print("-" * 50)
        
        hasil = []
        for i in range(trials):
            print(f"\n--- Trial {i+1} ---")
            waktu_selesai_detik = self.run_trial(i+1)
            menit = waktu_selesai_detik // 60
            detik = waktu_selesai_detik % 60
            status = "BERHASIL" if waktu_selesai_detik <= self.target_detik else "GAGAL"
            
            print(f"Trial {i+1} Selesai: {menit} menit {detik} detik [{status}]")
            hasil.append(waktu_selesai_detik)
        
        print("-" * 50)
        avg_detik = sum(hasil) / len(hasil)
        print(f"Rata-rata Waktu: {avg_detik//60} menit {avg_detik%60:.0f} detik")
        print(f"Target: {self.target_menit} menit")
        if avg_detik <= self.target_detik:
            print("KESIMPULAN: Sistem OPTIMAL dan memenuhi target 45 menit.")
        else:
            print("KESIMPULAN: Sistem perlu perbaikan lagi.")

# Menjalankan Simulasi
if __name__ == "__main__":
    # Set seed agar hasil bisa direproduksi (opsional)
    random.seed(42) 
    
    sim = SimulasiPiketITDel()
    sim.run_simulation(trials=5)