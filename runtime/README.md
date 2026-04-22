# Amadeus Security Hub - Runtime Python

Ce dossier contient le runtime Python utilise par l'application desktop.

## Role

- lancer l'application `pywebview`
- embarquer les dependances Python du projet
- fournir le bridge entre le frontend HTML/JS et le backend Python

## Dependances connues

Le fichier `requirements.txt` contient actuellement :

- `argon2-cffi`
- `cryptography`
- `wmi`
- `pywebview`

## Notes

- le frontend n'est pas un projet web separe : il est charge par `pywebview`
- le point d'entree applicatif du depot est `app/main.py`
