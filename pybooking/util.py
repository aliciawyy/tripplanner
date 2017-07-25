from os import path


OUTPUT_DIR = path.join(path.dirname(__file__), "..", "output")


class APIKeys(object):
    geocode = "AIzaSyBmkF_p89N8DjBO77oJ-QOUFebB3rQwG30"
    place = "AIzaSyDqUsNug8hrxQyTyk14y1euWlq5SFZGtRs"
    distance = "AIzaSyDqUsNug8hrxQyTyk14y1euWlq5SFZGtRs"


def get_coordinates(info):
    xy = info['geometry']['location']
    return xy['lat'], xy["lng"]


def get_dump_filename(city, interest, ext="json"):
    return path.join(OUTPUT_DIR, "{}_{}.{}".format(city, interest, ext))
