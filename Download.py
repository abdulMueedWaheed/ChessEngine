import requests

url = "http://images.chesscomfiles.com/chess-themes/sounds/_MP3_/default/game-end.mp3"
output_file = "game-end.mp3"

response = requests.get(url)
if response.status_code == 200:
    with open(output_file, "wb") as file:
        file.write(response.content)
    print(f"File downloaded successfully as {output_file}")
else:
    print(f"Failed to download file. HTTP status code: {response.status_code}")
