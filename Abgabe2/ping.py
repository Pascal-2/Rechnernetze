from icmplib import ping, multiping, Host
import matplotlib.pyplot as plt

# ipPhilippe = "172.20.140.57"
urlGoetheFrankfurt = "https://www.uni-frankfurt.de"
urlUniWestAust = "https://www.uwa.edu.au"
urlUniTexas = "https://www.utexas.edu"
urlFinnishNews = "https://www.esaimaa.fi"

hosts = [urlGoetheFrankfurt, urlUniWestAust , urlUniTexas, urlFinnishNews]

from icmplib import ping
from urllib.parse import urlparse

def get_hostname_from_url(url):
    parsed_url = urlparse(url)
    return parsed_url.hostname

def record_response_times(urls, count=100, timeout=2):
    results = {}
    for url in urls:
        hostname = get_hostname_from_url(url)
        try:
            host = ping(hostname, count=count, timeout=timeout, privileged=False)
            results[url] = {
                'average_rtt': host.avg_rtt,
                'min_rtt': host.min_rtt,
                'max_rtt': host.max_rtt,
                'packet_loss': host.packet_loss,
                'is_alive': host.is_alive
            }
        except Exception as e:
            results[url] = {'error': str(e)}
    return results

# Example usage
urls = hosts

response_times = record_response_times(urls)
for url, data in response_times.items():
    print(f"{url} -> {data}")

plt.plot(["Frankfurt", "Perth", "Austin", "Lappeenranta"], [y["average_rtt"] for x,y in response_times.items()])
plt.show()