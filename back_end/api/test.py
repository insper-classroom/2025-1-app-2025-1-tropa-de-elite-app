# test_import.py
import app

print("Atributos visíveis no módulo app.py:")
for nome in dir(app):
    if not nome.startswith("_"):
        print("  ", nome)
