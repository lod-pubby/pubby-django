import gzip
import json
import logging

from django.conf import settings

__all__ = ['fetch_gnd_id']

"""
GND-ID module
2021, By Benjamin Schnabel
schnabel@hdm-stuttgart.de

This script fetches a GND ID from the file ep_GND_ids.json.gz.

"""

def fetch_gnd_id(entity):
    """
    Method to find the GND-ID.
    @param entity: String
    @return: GND_ID as a String
    """

    # access the file on the server
    try:
        # unpack the gnd gz file
        with gzip.open(settings.GND_FILE, mode="rb") as fout:
            content = fout.read()
            dictionary = json.loads(content)

            # search the json
            for key in dictionary.keys():
                if key[-7:] == entity[-7:]:
                    return(dictionary.get(key))
    except FileNotFoundError as e:
        logging.error(e)
        return None
