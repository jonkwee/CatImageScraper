import configparser

class Configuration:

    def __init__(self, path_to_config: str) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(path_to_config)

    def convertToList(self, value: str) -> list:
        return list(map(lambda v : v.strip()[1:-1], value[1:-1].split(",")))

    def convertToInt(self, value: str) -> int:
        return int(value)

    def convertToBool(self, value: str) -> bool:
        return value == "True"

    def getProperty(self, section: str, name: str, extract_type: type):
        property_value = self.config.get(section, name)
        if extract_type == list:
            return self.convertToList(property_value)
        elif extract_type == int:
            return self.convertToInt(property_value)
        elif extract_type == str:
            return property_value
        elif extract_type == bool:
            return self.convertToBool(property_value)
