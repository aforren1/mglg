from glm import mat4
# TODO: not very useful right now, but could be moveable in the future


class Camera(object):
    def __init__(self, view=mat4(), projection=mat4()):
        self.vp = projection * view
