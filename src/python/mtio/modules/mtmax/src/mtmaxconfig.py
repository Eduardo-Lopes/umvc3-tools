import sys
import yaml
import os
import importlib

# general
flipUpAxis = True
scale = 1

# import settings
importWeights = True
importFilePath = ''
importConvertTexturesToDDS = True
importMetadataPath = ''
importNormals = True
importGroups = True
importSkeleton = True
importPrimitives = True
importSaveMrlYml = True

# export settings
exportWeights = True
exportFilePath = ''
exportTexturesToTex = True
exportMetadataPath = ''
exportNormals = True
exportGroups = True
exportSkeleton = True
exportPrimitives = True
exportMrlYml = True
exportRefPath = ''
exportMrlYmlPath = ''

def _getModule():
    if not __name__ in sys.modules:
        importlib.import_module(__name__)
    return sys.modules[__name__]

def _getSavePath():
    return os.path.join(os.path.dirname(__file__), 'config.yml')

def _getVariables():
    mod = _getModule()
    variables = dict([(item, getattr(mod, item)) for item in dir(mod) if \
        not item.startswith('__') and 
        (
        isinstance(getattr(mod, item), int) or 
        isinstance(getattr(mod, item), bool) or
        isinstance(getattr(mod, item), float) or
        isinstance(getattr(mod, item), str)
        )])
    return variables

def save():
    with open(_getSavePath(), 'w') as f:
        yaml.dump(_getVariables(), f)

def load():
    if os.path.exists(_getSavePath()):
        with open(_getSavePath(), 'r') as f:
            temp = yaml.load(f, Loader=yaml.FullLoader)
            if temp != None:
                for key in temp:
                    if hasattr(_getModule(), key):
                        setattr(_getModule(), key, temp[key])

if __name__ == '__main__':
    save()
    load()
