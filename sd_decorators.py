import pymel.all as pm


def sd_preserve_selection(func):
    def inner(*args, **kwargs):
        sel = list(pm.selected())
        result = func(*args, **kwargs)
        pm.select(sel, replace=True)
        return result
    return inner


def sd_undo_chunk(func):
    def inner(*args, **kwargs):
        print 'its sort of working'
        pm.undoInfo(openChunk=True)
        try:
            return func(*args, **kwargs)
        except RuntimeError as ex:
            print ex
            print 'the process failed'
        finally:
            pm.undoInfo(closeChunk=True)
    return inner


class undo_chunk(object):
    def __enter__(self):
        pm.undoInfo(openChunk=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pm.undoInfo(closeChunk=True)