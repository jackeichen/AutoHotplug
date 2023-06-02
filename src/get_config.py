import yaml
from src.script_path import config_file_path

_Loader = yaml.Loader
try:
    _Loader = yaml.FullLoader
except:
    pass

def get_config():
    content = None
    with open(config_file_path, 'r') as f:
        content = yaml.load(f.read(), Loader=_Loader)
    return content
