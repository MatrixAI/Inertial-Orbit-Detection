import rotation_mapping
from copy import deepcopy

# this it the first event loop, it will be processing the actual data from the game controller

message_regex = re.compile('^Time.(\d+).X.(\d+).Y.(\d+).Z.(\d+)', re.I)

def analysis_loop():

