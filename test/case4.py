class Tubes:
    def __init__(self):
        self.banyak = 5
        self.waktu_tidur = False
    
    def isAlive(self):
        return (self.banyak < 3 and self.waktu_tidur)