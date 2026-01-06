# main.py

from backend.brain import Assistant
import sys

def main():
    assistant = Assistant()
    print("Assistant bancaire - version ULTRA. Tape 'help' pour les commandes, 'exit' pour quitter.")
    try:
        assistant.start_console()
    except KeyboardInterrupt:
        print("\nInterrompu. Sauvegarde et sortie.")
        assistant.save_user()
        sys.exit(0)

if __name__ == "__main__":
    main()
