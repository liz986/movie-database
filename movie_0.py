import requests

from tabulate import tabulate # type: ignore

def main():

    title_query = input("Search for a title: ")
    movies = {"Type":[], "Title":[], "Year":[], "Rating":[]}
    try:
        response = requests.get(f"https://api.imdbapi.dev/search/titles?query={title_query}")
        content = response.json()

        for movie in content['titles']:
            movies["Type"].append(movie['type'])
            movies["Title"].append(movie['primaryTitle'])
            movies["Year"].append(movie['startYear'])
            movies["Rating"].append(movie['rating']['aggregateRating'])

    except KeyError:
        pass

    print(tabulate(movies, headers="keys", tablefmt="grid"))
    
if __name__ == '__main__':
    main()
