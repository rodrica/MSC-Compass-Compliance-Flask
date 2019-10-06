
import abc
from contextlib import ContextDecorator


class ClosableInstance(ContextDecorator, abc.ABC):
    '''
        Instance that can be used with the `with` statement

        i.e.:
            with Instance(..) as i:
                # do stuff
    '''

    @abc.abstractmethod
    def __init__(
        self,
        tenant_id: str,
        instance_name: str
    ):
        pass

    def __enter__(self):
        return self.get()

    def __exit__(self, *exc):
        return self.close()

    @abc.abstractmethod
    def get(self):
        pass

    @abc.abstractmethod
    def close(self):
        return True
