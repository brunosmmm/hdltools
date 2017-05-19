"""Top-level module drawing builder."""

from ..hdl import (HDLModule)
from pylatex import (TikZ, TikZNode, TikZDraw,
                        TikZUserPath, TikZOptions,
                        TikZCoordinate,
                        Document)


class TopLevelDrawing(object):
    """Top-level drawing."""

    def __init__(self, module):
        """Initialize.

        Args
        ----
        module: HDLModule
            A module
        """
        if not isinstance(module, HDLModule):
            raise TypeError('only HDLModule type allowed')

        self.module = module

    def _build_drawing(self):
        doc = Document()
        with doc.create(TikZ()) as tikz_pic:

            # create a node
            node_options = {'align': 'center',
                            'inner sep': '20pt',
                            'label': '{{270:{}}}'.format(self.module.name)}
            box = TikZNode(handle='module',
                           options=TikZOptions('draw',
                                               'rounded corners',
                                               **node_options))

            tikz_pic.append(box)
            for port in self.module.ports:
                if port.direction == 'in':
                    tikz_pic.append(TikZNode(text=port.name,
                                             options=TikZOptions(anchor='west'),
                                             at=TikZCoordinate(-1, 1)))
                    break

        doc.generate_tex('test')
        return doc

    def get_tikzpicture(self):
        return self._build_drawing()

    def dumps(self):
        return self._build_drawing().dumps()
