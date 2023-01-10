import re


class Utils:
    def __init__(self, log):
        self.log = log

    def find_earliest_year(publishers):
        pattern = r"\(\d{4}\)|\(\d{4}-\d{4}\)"
        years = []
        for publisher in publishers:
            publisher = publisher.text_content().strip()
            match = re.search(pattern, publisher)
            if not match:
                continue
            match = match.group().strip("()")
            if '-' in match:
                years += [int(year) for year in match.split("-")]
            else:
                years.append(int(match))
        return str(min(years)) if len(years) > 0 else None
