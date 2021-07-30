
import pick_plaz_robot

class OutOfSaveSpaceException(Exception):
    pass

class SaveRobot(pick_plaz_robot.Robot):
    """ Wrapper for Robot that checks for illegal operations"""
    
    def __init__(self, comport):
        super().__init__(comport)

        self.x_bounds = (0,800)
        self.y_bounds = (0,800)

    @staticmethod
    def __check_range(x, start_stop):
        """ Return True if the value is outside of the given bounds"""
        if x is None:
            return False
        elif x < start_stop[0] or x > start_stop[1]:
            return True
        else:
            return False 

    def drive(self, x=None, y=None, z=None, e=None, a=None, b=None, c=None, f=None):

        if self.__check_range(x, self.x_bounds):
            raise OutOfSaveSpaceException(f"Attempting to drive x={x} which is outside of save bounds {self.x_bounds}")

        if self.__check_range(y, self.y_bounds):
            raise OutOfSaveSpaceException(f"Attempting to drive y={y} which is outside of save bounds {self.y_bounds}")

        return super().drive(x=x, y=y, z=z, e=e, b=b, c=c, f=f)