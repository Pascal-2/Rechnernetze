with open("sharkfood.txt", "r", encoding="utf-8") as f:
    lines = [l.rstrip() for l in f]

sum = 0
ips = set()
for x in lines:
    sum += int(x.split()[5])
    ips.add(x.split()[2])
print("Übertragene Bytes:", sum)
print("Anzahl Pakete:", len(lines))
print("Menge der ip Adressen:", len(ips))