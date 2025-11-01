import requests


def main():
    response = requests.get("https://api.imdbapi.dev/titles")
    content = response.json()
    for movie in content['titles']:
        print(f"* {movie['originalTitle']}")



main()