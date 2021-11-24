# Tes matriks dua dimensi
N = int(input("Masukkan nilai N: "))

mat = [[]]

for i in range(N):
    for j in range(N):
        mat[i][j] = int(input("Masukkan elemen pada baris ke-" + str(i+1) + " kolom ke-" + str(j+1) + ": "))

for i in range(N):
    baris = input()
    baris = baris.split(" ")
    for j in range(N):
        baris[j] = int(baris[j])
    mat[i] = baris

isdiagonal = True
isskalar = True
i = 0
j = 0
while i < N and isdiagonal:
    skalar = mat[0][0]
    j = 0
    while j < N and isdiagonal:
        if(i != j and mat[i][j] != 0):
            isdiagonal = False
            isskalar = False
        if(i == j and mat[i][j] != skalar):
            isskalar = False
        j += 1
    i += 1

if(isskalar):
    print("Matriks merupakan matriks skalar.")
elif(isdiagonal):
    print("Matriks merupakan matriks diagonal.")
else:
    print("Matriks merupakan matriks sembarang.")
