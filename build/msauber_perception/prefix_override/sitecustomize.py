import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/andreas/dev_ws/msauber_stack/install/msauber_perception'
