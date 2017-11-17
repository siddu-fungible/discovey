
def bsort(l):
    for i in range(len(l) - 1):
        for j in range(i + 1, len(l)):
            if l[i] > l[j]:
                temp = l[j]
                l[j] = l[i]
                l[i] = temp
    return l


print bsort([5, 4, 3, 1, 67, 1, 33, 8])