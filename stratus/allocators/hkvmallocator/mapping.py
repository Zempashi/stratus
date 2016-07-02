import re

class Map(object):

    def __init__(self, regex, group_name):
        self.regex = re.compile(regex)
        self.group_name = group_name

    def match(self, vm_name):
        return self.regex.match(vm_name)


class _all_(object):
    pass
