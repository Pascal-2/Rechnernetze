import matplotlib.pyplot as plt

with open("ping_results.txt", "r", encoding="utf-8") as f:
    text = [l.rstrip() for l in f]

avg_rtt = []
for x in text:
    avg_rtt.append(float(x.split()[3][:-1]))

for x in avg_rtt:
    print(x)


plt.plot(["Frankfurt", "Perth", "Austin", "Lappeenranta"], avg_rtt)
plt.title("Average Round Trip Time")
plt.ylabel("Time (ms)")
plt.show()