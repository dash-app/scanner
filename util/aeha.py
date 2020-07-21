#!/usr/bin/python3

# entries
# [[0,0], [1,1] ...]
def format(entries):
    r = []
    offset = -1
    byte = 0
    line_arr = []
    for i in range(len(entries)):
        if len(entries[i]) < 2:
            r.append(line_arr)
            break

        on = int(entries[i][0])
        off = int(entries[i][1])
        if off == 0:
            r.append(line_arr)
            break

        if on > 1500:
            if offset >= 0:
                r.append(line_arr)
                line_arr = []

            offset = 0
            byte = 0
        else:
            if offset < 0:
                byte = 0
            else:
                byte |= (off > on * 2) << offset
            offset = offset + 1

            if (offset & 7) == 0:
                line_arr.append(byte)
                offset = 0
                byte = 0
    return r
