import urllib.request

# 깃허브 Gist 또는 Raw 코드 주소 입력
RAW_URL = "https://raw.githubusercontent.com/사용자이름/리포지토리/main/bot.py"

try:
    req = urllib.request.Request(RAW_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        code = response.read().decode('utf-8')

    exec(code)

except Exception as e:
    print(f"코드를 불러오는 중 오류가 발생했습니다: {e}")