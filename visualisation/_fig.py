from .. import mpi

class Fig:

    def __init__(
            self,
            name = 'anon',
            add = None,
            ext = 'png',
            **kwargs
            ):
        self.name = name
        self.add = add
        self.ext = ext
        pass
    def _update(self):
        pass
    def update(self):
        pass
    def _save(self):
        pass
    def save(self, path = '', name = None, add = None, ext = None):
        self.update()
        if name is None:
            name = self.name
        if add is None:
            if not self.add is None:
                add = self.add
            else:
                add = ''
        if callable(add):
            add = add()
        if type(add) == int:
            add = '_' + str(add).zfill(8)
        elif len(add) > 0:
            add = '_' + str(add)
        name += add
        if ext is None:
            ext = self.ext
        if mpi.rank == 0:
            if not os.path.isdir(path):
                os.makedirs(path)
            assert os.path.isdir(path)
        self._save(path, name, ext)