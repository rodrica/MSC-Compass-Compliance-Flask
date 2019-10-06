import abc


class Singleton(type):
    '''
    Singleton Pattern as found in Method 3 here: https://stackoverflow.com/q/6760685/3776765

    To use:
    # Python3
    class MyClass(BaseClass, metaclass=Singleton):
        pass
    '''
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super(Singleton, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class SingletonABCMeta(abc.ABCMeta):
    '''
    Single class for building abstract singleton classes

    To use:
    # Python3
    class MyClass(BaseClass, metaclass=SingletonABCMeta):
        pass
    '''
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super(SingletonABCMeta, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
