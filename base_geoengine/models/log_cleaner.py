import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning, module="importmagic.util")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="importmagic")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="spark_parser")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="mpld3")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="cerberus")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="nose")
warnings.simplefilter("ignore", category=DeprecationWarning)
