arr = [0 for i in range(19)]

json = {
    "0": {"node":1},
    "1": {"node":12},
    "2": {"node":16},
    "3": {"node":17},
    "4": {"node":3},
    "5": {"node":8},
    "6": {"node":5},
    "7": {"node":13},
    "8": {"node":18},
    "9": {"node":2},
    "10": {"node":7},
    "11": {"node":9},
    "12": {"node":11},
    "13": {"node":14},
    "14": {"node":15},
    "15": {"node":4},
    "16": {"node":0},
    "17": {"node":6},
    "18": {"node":10}
}

# arr = []
for i in range(19):
    
    map = json[str(i)]
    node = map["node"]
    arr[i] = node
    
print(arr)
# [1, 12, 16, 17, 3, 8, 5, 13, 18, 2, 7, 9, 11, 14, 15, 4, 0, 6, 10]