# Deskripsi: Menentukan faktor-faktor prima suatu bilangan

# KAMUS
# n, i, j : int
# isPrime : bool

#ALGORITMA
n = int(input("Masukkan N: "))

print("Faktor primanya adalah ", end="")
isFirst = True     # isFirst hanya untuk membantu print jawaban
for i in range(2, n+1):     # n+1 agar sampai n, untuk mengecek juga apakah n prima (misal angka 3, 3 sendiri termasuk faktor prima dirinya sendiri)
    if(n % i == 0): # Kalau n habis dibagi i lanjut dicek apakah i prima, kalau tidak tak perlu dicek
        j = 2
        isPrime = True
        while(j < i and isPrime):
            if(i % j == 0):
                isPrime = False
            j += 1
        if(isPrime): 
            if(isFirst):    # Faktor prima pertama dicetak tanpa koma di depan angka
                print(i, end="")
                isFirst = False
            else:
                print(",", i, end="")

print(".")