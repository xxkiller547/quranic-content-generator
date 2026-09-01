from textual.app import App,ComposeResult
from textual import on
from textual.widgets import (
    Header,
    Label,
    Input,
    Button,
    Footer
)
from textual.containers import Center,Horizontal,Vertical
from compose_surah_page import compose_surah_page
import requests
from pathlib import Path
from moviepy import ImageClip, AudioFileClip

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

class GeneratorApp(App):

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

            yield Label("please enter the name of the image(or leave blank for bas):",classes="field-label")
            yield Input(placeholder="eg: Mountains.jpg",id="image_input")

            yield Button("Generate!",id="generate")

        yield Footer()

    @on(Button.Pressed,"#generate")
    def Generate(self):
        image_output_path = self.generator.GenerateBackgroundImage(surah_number=self.surah_number,image_name=self.image_name)
        audio_output_path = self.generator.FetchSurahAudio(reciter_name=self.reciter,surah_number=self.surah_number)
        video_output_path = self.generator.output_dir / f"{self.surah_number}.mp4"
        self.generator.make_full_video(img_path=image_output_path,audio_path=audio_output_path,output_path=video_output_path)
        pass

    @on(Input.Submitted,"#reciter_input")
    def SetReciter(self,event: Input.Changed):
        self.reciter = event.value
        pass

    @on(Input.Submitted,"#surah_number_input")
    def SetSurah(self,event:Input.Changed):
        self.surah_number = int(event.value)
        pass

    @on(Input.Submitted,"#image_input")
    def SetImage(self,event:Input.Changed):
        self.image_name = event.value
        pass
#========================================================================================

if __name__ == "__main__":
    app = GeneratorApp()
    app.run()
    pass
