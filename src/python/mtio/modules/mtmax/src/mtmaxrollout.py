from pymxs import runtime as rt
import mtmaxconfig
import mtmaxlog
from mtmaxutil import _handleException

class MtRollout:
    @classmethod
    def onEvent( cls, e, *args ):
        try:
            mtmaxlog.debug(f'received event: {e} with args: {args}')
            if hasattr(cls, e):
                getattr(cls, e)(*args)
            else:
                mtmaxlog.debug(f'no event handler for {e}')

            if hasattr( cls, 'updateVisibility'): 
                cls.updateVisibility()
            else:
                mtmaxlog.debug(f'no update visibility handler defined in {cls}')

            mtmaxconfig.save()
        except Exception as e:
            _handleException( e, 'A fatal error occured while processing user input' )
            
    @classmethod
    def getMxsVar( cls ):
        assert( hasattr( rt, cls.__name__ ) )
        return getattr( rt, cls.__name__ )