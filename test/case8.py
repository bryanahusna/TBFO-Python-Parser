# Deskripsi: Membuat kubus sesedikit mungkin dari potongan-potongan lego 1x1x1

# KAMUS
# n, i : int
# kubus : int

#ALGORITMA
n = int(input("Masukkan banyak potongan lego: "))

# Mencari bilangan dengan pangkat 3 terkecil yang lebih besar atau sama dengan n
i = 1
while(i**3 < n):
    i += 1

kubus = 0      # Jumlah kubus
while(n > 0):
    if(n - i**3 < 0):   # Kalau i pangkat tiga lebih besar daripada n, i dikurangi 1
        i -= 1
    else:               # kalau tidak jumlah kubus tambah 1, potongan lego dikurangi i pangkat tiga
        kubus += 1
        n -= i**3
print("Tuan Kil dapat membuat " + str(kubus) + " kubus.")