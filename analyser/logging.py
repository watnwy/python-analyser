import logging


class PrivateEndpointsFilter(logging.Filter):
    def filter(self, record):
        return record.getMessage().find("/_/") == -1
