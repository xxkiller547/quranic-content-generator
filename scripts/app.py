from textual.app import App,ComposeResult
from textual.widgets import (
    Header,
    Label,
    Input,
    Button,
    Footer
)

from textual.containers import Center,Horizontal,Vertical
from pathlib import Path
#========================================================================================

BASE_DIR = Path(__file__).parent.parent.resolve()

#========================================================================================

class GeneratorApp(App):
    TITLE = "Quran Content Generator"
    CSS_PATH = str(BASE_DIR / "scripts" / "styles.tcss")

    def compose(self)->ComposeResult:
        yield Header(show_clock=True)

        with Center(id="form"):

            yield Label("please enter the name of the reciter: ",classes="field-label")
            yield Input(placeholder="eg: El-Minshawy")

            yield Label("please enter the name of the surah:",classes="field-label")
            yield Input(placeholder="eg: Surah el-mulk")

            yield Label("please enter the name of the image:",classes="field-label")
            yield Input(placeholder="eg: Mountains.jpg")

            yield Button("Generate!",id="generate")

        yield Footer()
        pass

#========================================================================================

if __name__ == "__main__":
    app = GeneratorApp()
    app.run()