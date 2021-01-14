import pygame
import speech_recognition as sr
from threading import Thread
from queue import Queue
from palabras import glosario

# iniciar el pygame
pygame.init()

# creando la pantalla
screen = pygame.display.set_mode((800, 600))

# titulo e icono
pygame.display.set_caption("Prototipo")
icon = pygame.image.load("Captura.png")
pygame.display.set_icon(icon)

# Reconocimiento de voz
r = sr.Recognizer()
user_commands = Queue()

# escucha, transcribe, y posiciona en cola para 
# procesamiento los commandos de voz del usuario.
def fetch_user_commands():
    with sr.Microphone() as source:
        while True:
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source)
            try:
                command = r.recognize_google(audio, language="es-HN")
                user_commands.put(command)
            except sr.UnknownValueError:
                print('Lo siento no entendi eso')
            except sr.RequestError:
                print('Perdon, mi sistema esta caido')

# clase que contiene las imagenes para una todas las palabras.
class PicDictionary(pygame.sprite.Sprite):
    def __init__(self, glossary):
        super(PicDictionary, self).__init__()
        # es necesario tener una imagen para usar por defecto
        assert "default" in glossary, "'default' image is missing."
        # copiar todas las palabras del glosario
        self.glossary = dict.fromkeys(glossary)
        # por cada palabra cargar la lista de imagenes a memoria
        for word, paths in glossary.items():
            self.glossary[word] = []
            for path in paths:
                # si va lento es por culpa del cachimbo de imagenes que se cargan aqui.
                self.glossary[word].append(pygame.image.load(path))
        # renderizar la animacion por defecto.
        self.load_new_word("default")
        self.queue = Queue()
        self.completed = False

    def load_new_word(self, word):
        # cargamos las imagenes necesarias para decir la palabra
        # del glosario
        self.images = self.glossary[word]
        # empezamos mostrando la primer imagen de la animacion
        self.index = 0
        self.image = self.images[self.index]

    def load_next_frame(self):
        # magia
        index = int(self.index) % len(self.images)
        self.image = self.images[index]
        # chequeamos si la imagen que tenemos es el ultimo marco 
        # de la animacion, en cuyo caso la animacion termino
        self.completed = index == (len(self.images) - 1)
        print(f"completed: {self.completed}")

    def update(self, surface, word, speed):
        # chequeamos si la palabra esta en glosario y 
        if word in self.glossary and word != "default":
            # de ser asi ponemos la palabra en la fila
            self.queue.put(word)
        # chequeamos si la animacion _no_ ha terminado
        if not self.completed:
            # incrementamos el indice
            self.index += speed
            # y vemos si tenemos que cambiar de marco o no.
            self.load_next_frame()
        else:
            # vamos a cargar una nueva palabra <=> una nueva animacion
            self.completed = False
            # si la fila de espera esta vacia,
            if self.queue.empty():
                # cargamos la animacion por defecto
                self.load_new_word("default")
            else:
                # de _no_ esta vacia cargamos la siguiente palabra
                self.load_new_word(self.queue.get())
        # mostramos el marco que corresponde.
        return surface.blit(self.image, (0, 0))

# loop que se encarga de actualizar la interfaz grafica.
def game_loop():
    global screen, glosario
    corriendo = True
    command = "default"
    clock = pygame.time.Clock()
    picdic = PicDictionary(glosario)

    while corriendo:
        # maximo de 24 marcos por segundo.
        clock.tick(24)
        # Maneja eventos relacionados con pygame, e.g. botones presionados, etc.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                corriendo = False
        # extrae palabras en la file, para ser procesadas.
        if not user_commands.empty():
            command = user_commands.get()
        # primer parametro es la pantalla donde se va a dibujar la imagen
        # segundo es la palabra que dijo el usuario
        # tercero es para controlar la velocidad de la animacion
        portion = picdic.update(screen, command.lower(), 0.25)
        pygame.display.update(portion)
        # hay que resetear el commando
        command = "default"

# crear thread donde capturamos commandos del usuario
t = Thread(target=fetch_user_commands, daemon=True)
t.start()

# iniciar interfaz grafica
game_loop()
pygame.display.quit()
