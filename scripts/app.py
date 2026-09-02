from textual.app import App,ComposeResult
from textual.screen import ModalScreen
from textual import on,work
from textual.widgets import (
    Header,
    Label,
    Input,
    Button,
    Footer
)
from textual.containers import Center,Horizontal,Vertical,VerticalScroll
from compose_surah_page import compose_surah_page
import requests
from pathlib import Path
from moviepy import ImageClip, AudioFileClip
from time import sleep

#========================================================================================

BASE_DIR = Path(__file__).parent.parent.resolve()
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "outputs"
ASSETS_DIR = BASE_DIR / "assets"


#========================================================================================
class Generator:

    def __init__(self,BASE_DIR:Path,TEMP_DIR:Path,OUTPUT_DIR:Path,ASSETS_DIR:Path)-> None:
        self.base_dir = BASE_DIR
        self.temp_dir = TEMP_DIR
        self.output_dir = OUTPUT_DIR
        self.assets = ASSETS_DIR
    
    def GenerateBackgroundImage(self,surah_number,image_name,text_color = "#e5b86a"):
        images = [str(image) for image in ASSETS_DIR.iterdir() if image.is_file()]

        if str( ASSETS_DIR / image_name) not in images:
            return False
        image_path = Path(str( ASSETS_DIR / image_name))

        output_path = self.temp_dir/ f"{surah_number:03d}_{image_name}"
        compose_surah_page(image_path,surah_number, Path(str(ASSETS_DIR / "svgs" )),output_path,color=text_color)
        return str(output_path)

    def FetchSurahAudio(self,reciter_name,surah_number):
        """from the Mp3quran.com"""
        reciters_data_url = "https://www.mp3quran.net/api/v3/reciters"
        params = {"language":"eng"}

        try:
            reciters_data = requests.get(reciters_data_url,params=params,timeout=10)
        except requests.RequestException:
            return False
        
        if reciters_data.status_code != 200:
            return False
        
        reciters_data = reciters_data.json()
        reciters_list = reciters_data["reciters"]

        reciter_to_server = {}

        for reciter in reciters_list:
            if not reciter["moshaf"]:
                reciter_to_server[reciter["name"]] = None
                continue
            server = next(
                (m["server"] for m in reciter["moshaf"] if m["rewaya_id"] == 1),
                None
            )
            reciter_to_server[reciter["name"]] = server

        if reciter_name not in reciter_to_server.keys():
            return False
        try:
            audio = requests.get(f"{reciter_to_server[reciter_name]}{surah_number:03d}.mp3") if reciter_to_server[reciter_name] is not None else None
        except requests.RequestException:
            return False
        if audio == None:
            return False

        if audio.status_code != 200:
            return False

        with open(self.temp_dir / f"{str(surah_number)}.mp3","wb") as audio_file:
            audio_file.write(audio.content)
            return str(self.temp_dir / f"{str(surah_number)}.mp3")

    def clear_temp(self):
        for f in self.temp_dir.iterdir():
            if f.is_file():
                f.unlink()

    def make_full_video(self, img_path, audio_path, output_path):

        audio_clip = AudioFileClip(str(audio_path))
        image_clip = ImageClip(str(img_path)).with_duration(audio_clip.duration)
        video_clip = image_clip.with_audio(audio_clip)
    
        video_clip.write_videofile(
            str(output_path),
            codec="libx264",
            audio_codec="aac",
            fps=1,
            preset="ultrafast",   # skips most encoder search work — big CPU win for a static frame
            threads=2,            # cap core usage instead of maxing every core
            audio_bitrate="128k", # avoids re-encoding at unnecessarily high quality
            logger=None,
        )

        audio_clip.close()
        video_clip.close()
        return output_path

class RecitersPopupScreen(ModalScreen):
    def __init__(self):
        super().__init__()
        self.reciters = []
        
    def compose(self)-> ComposeResult:
        with VerticalScroll(id="reciters-popup"):
            yield Label("[green]Loading reciters.....[/green]",id="status-label")

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss()
    
    def FetchReciters(self) -> list:
        """from the Mp3quran.com"""
        reciters_data_url = "https://www.mp3quran.net/api/v3/reciters"
        params = {"language":"eng"}

        try:
            reciters_data = requests.get(reciters_data_url,params=params,timeout=10)
        except requests.RequestException:
            return ["[red]We couldnt fetch reciters![/red]"]
        
        if reciters_data.status_code != 200:
            return ["[red]We couldnt fetch reciters![/red]"]
        
        reciters_data = reciters_data.json()
        reciters_data_list = reciters_data["reciters"]

        reciters_names_list = sorted([reciter["name"] for reciter in reciters_data_list])
        reciters_names_list.insert(0,"Available Reciters (ESC for escape)")
        
        return reciters_names_list
    
    @work(thread=True)
    def LoadReciters(self):
        reciters = self.FetchReciters()
        self.app.call_from_thread(self.ShowReciters,reciters)


    def ShowReciters(self,reciters):
        status_label = self.query_one("#status-label")
        status_label.update(reciters[0])

        if len(reciters) == 1:
            return
        
        container = self.query_one("#reciters-popup")

        for reciter in reciters[1::]:
            container.mount(Label(reciter))
        pass
    def on_mount(self):
        self.LoadReciters()

class GeneratorApp(App):

    BINDINGS = [("f1", "show_reciters", "Reciters"),]
    TITLE = "Quran Content Generator"
    CSS_PATH = str(BASE_DIR / "scripts" / "styles.tcss")

    def __init__(self):
        super().__init__()
        self.generator = Generator(BASE_DIR=BASE_DIR,TEMP_DIR=TEMP_DIR,OUTPUT_DIR=OUTPUT_DIR,ASSETS_DIR=ASSETS_DIR)
        self.reciter = None
        self.surah_number = None
        self.image_name = "base.png"

    def compose(self)->ComposeResult:
        yield Header(show_clock=True)

        with Center(id="form"):

            yield Label("please enter the name of the reciter: ",classes="field-label")
            yield Input(placeholder="eg: Mishari Rashid al-Afasy",id = "reciter_input")

            yield Label("please enter the number of the surah:",classes="field-label")
            yield Input(placeholder="eg: 114 for surah Al-nas",id="surah_number_input")

            yield Label("please enter the name of the image(or leave blank for base):",classes="field-label")
            yield Input(placeholder="eg: Mountains.jpg",id="image_input")

            yield Button("Generate!",id="generate")

            yield Label("Nothing generating yet",id="progress-displayer") #TODO attach the error handeling and the failures and connect it to this 
        yield Footer()

    @on(Button.Pressed,"#generate")
    def Generate(self):
        progress_label = self.query_one("#progress-displayer")

        if not self.surah_number and self.reciter:
            progress_label.update("[yellow]Please fill the the surah number input and reciter input atleast![/yellow]")
            sleep(1.5)
            progress_label.update("Nothing to generate!")
            return
        if not self.reciter:
            progress_label.update("[yellow]Please fill the reiter name input![/yellow]")
            sleep(1.5)
            progress_label.update("Nothing to generate!")
            return
        if not self.surah_number:
            progress_label.update("[yellow]Please fill the surah number input![/yellow]")
            sleep(1.5)
            progress_label.update("Nothing to generate!")
            return

        try:
            surah_number_validatator = int(self.surah_number)
            if not (1 <= surah_number_validatator <= 114):
                progress_label.update("[yellow]Please enter a valid surah number![/yellow]")
                sleep(1.5)
                progress_label.update("Nothing to generate!")
                return
        except:
            progress_label.update("[yellow]Please enter a valid surah number![/yellow]")
            sleep(1.5)
            progress_label.update("Nothing to generate!")
            return

        progress_label.update(f"[green] Generating the background image ({self.image_name})...[/green]")
        self.StartGeneratorWorker()



    @work(thread=True)
    def StartGeneratorWorker(self):
        progress_label = self.query_one("#progress-displayer")

        image_output_path = self.generator.GenerateBackgroundImage(surah_number=self.surah_number,image_name=self.image_name)
        if not image_output_path:
            self.call_from_thread(progress_label.update,f"[red]failed to generate image! stopping...[/red]")
            sleep(1.5)
            self.call_from_thread(progress_label.update,"Nothing generating yet")
            self.generator.clear_temp()
            return

        self.call_from_thread(progress_label.update,"[green]Fetching audio...[/green]")
        audio_output_path = self.generator.FetchSurahAudio(reciter_name=self.reciter,surah_number=self.surah_number)
        if not audio_output_path:
            self.call_from_thread(progress_label.update,f"[red]failed to fetch audio! stopping...[/red]")
            sleep(1.5)
            self.call_from_thread(progress_label.update,"Nothing generating yet")
            self.generator.clear_temp()
            return

        self.call_from_thread(progress_label.update,"[green]Combining full video...[/green]")
        video_output_path = self.generator.output_dir / f"{self.surah_number}.mp4"
        self.generator.make_full_video(img_path=image_output_path,audio_path=audio_output_path,output_path=video_output_path)
        self.generator.clear_temp()
        self.call_from_thread(progress_label.update,"[green]We are Done![/green]")
        sleep(1.5)
        pass

    @on(Input.Submitted,"#reciter_input")
    def SetReciter(self,event: Input.Blurred):
        self.reciter = event.value
        self.set_focus(None)
        pass

    @on(Input.Submitted,"#surah_number_input")
    def SetSurah(self,event:Input.Blurred):
        self.surah_number = int(event.value) if event.value.strip().isdigit() else None
        self.set_focus(None)
        pass

    @on(Input.Submitted,"#image_input")
    def SetImage(self,event:Input.Blurred):
        self.image_name = event.value
        self.set_focus(None)
        pass

    def action_show_reciters(self):
        self.push_screen(RecitersPopupScreen())
#========================================================================================

if __name__ == "__main__":
    app = GeneratorApp()
    app.run()
    pass