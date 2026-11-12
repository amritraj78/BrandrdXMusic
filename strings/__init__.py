import os
from typing import List

try:
    import yaml
except ImportError:
    yaml = None

languages = {}
languages_present = {}


def get_string(lang: str):
    return languages.get(lang, languages.get("en", {}))


if yaml is not None and os.path.exists("./strings/langs/"):
    for filename in os.listdir(r"./strings/langs/"):
        if "en" not in languages:
            languages["en"] = yaml.safe_load(
                open(r"./strings/langs/en.yml", encoding="utf8")
            )
            languages_present["en"] = languages["en"]["name"]
        if filename.endswith(".yml"):
            language_name = filename[:-4]
            if language_name == "en":
                continue
            languages[language_name] = yaml.safe_load(
                open(r"./strings/langs/" + filename, encoding="utf8")
            )
            languages_present[language_name] = languages[language_name]["name"]
        for item in languages["en"]:
            if item not in languages[language_name]:
                languages[language_name][item] = languages["en"][item]
        try:
            languages_present[language_name] = languages[language_name]["name"]
        except:
            print("There is some issue with the language file inside bot.")
            exit()
