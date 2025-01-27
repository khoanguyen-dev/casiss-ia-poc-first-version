from googletrans import Translator

translator = Translator()
text = "Tfdfsd"
translated = translator.translate(text, src='auto', dest='fr')
print(translated.text)  # Output: Bonjour tout le monde