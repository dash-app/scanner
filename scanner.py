#!/usr/bin/env python3

from colorama import init, Fore, Back, Style
import util.aeha
import irscanner
import config

# Init colorama
init()

prev = []
while True:
    # previous hexcode [[0x00, 0x00]...]
    r = irscanner.rec(config)
    arr = [r[i:i+2] for i in range(0, len(r), 2)]
    s = util.aeha.format(arr)
    for i in range(0, len(s)):
        for j in range(0, len(s[i])):
            fmt = "0x{:02X} ".format(s[i][j])
            if len(prev) != 0 and len(s) <= len(prev) and len(s[i]) <= len(prev[i]):
                if prev[i][j] < s[i][j]:
                    print(Fore.GREEN + fmt + Fore.RESET, end="")
                    continue
                elif prev[i][j] > s[i][j]:
                    print(Fore.RED + fmt + Fore.RESET, end="")
                    continue
            print(fmt, end="")
        print("")
    prev = s
