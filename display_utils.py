from rich.layout import Layout
from rich.panel import Panel

class SynthiaNovaLayout:
    def __init__(self, initialSynthiaText: str = None, initialSystemText: str = None):
        self.synthiaText = initialSynthiaText or ''
        self.systemText = initialSystemText or ''
        self.layout = Layout()
        self.layout.split_column(
            Layout(name = 'system'),
            Layout(name = 'synthia')
        )
        self.layout['system'].size = 3

    def getLayout(self):
        return self.layout
    
    def setSystemPanelSize(self, size: int):
        self.layout['system'].size = size

    def getSynthiaText(self):
        return self.synthiaText
    
    def getSystemText(self):
        return self.systemText

    def update(self, *, synthiaText: str = None, systemText: str = None):
        self.systemText = systemText if systemText is not None else self.systemText
        self.synthiaText = synthiaText if synthiaText is not None else self.synthiaText

        self.layout['system'].visible = True
        self.layout['system'].update(Panel(self.systemText, title = 'System'))

        if self.synthiaText:
            self.layout['synthia'].visible = True
            self.layout['synthia'].update(Panel(self.synthiaText, title = 'Synthia Nova'))
        else:
            self.layout['synthia'].visible = False

SYNTHIA_PANEL = SynthiaNovaLayout()