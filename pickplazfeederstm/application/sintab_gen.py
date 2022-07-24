import math

f = open("sintab.c", "w")

n = 256


print('#include "stdint.h"', file=f)
print("#define SINTAB_LEN %d" % n, file=f)
print("const uint8_t sintab[%d] = {" % n, file=f)
for i in range(n):
    angle = math.pi * 2 * i / n
    sine = (math.sin(angle) + 1) / 2
    value = int(sine**4 * 256)
    print(value)
    print("    %d," % value, file=f)
print("};", file=f)