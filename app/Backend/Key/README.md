# Gestion de l'usb
L'ensemble du code lié a la gestion de l'usb est ici.
Gestion de la creation des cles securiser et gestion de leur secret

## Flux POSIX actuel

Au démarrage, le backend Linux / POSIX :

1. liste les supports USB avec partition
2. réutilise les montages existants si le support est déjà monté
3. monte temporairement les partitions non montées pour inspection
4. cherche `USBSecurity/USBKey.rin`, puis `USBSecurity/USBKey.json`
5. garde montée la partition de la clé retenue pour le flux de login
6. démonte les partitions montées uniquement pour le check si elles ne contiennent pas de clé valide
7. démonte à la fermeture de l'application uniquement les partitions montées par l'application

Important :

- un support déjà monté avant le lancement de l'application n'est pas démonté par le backend
- la page de login doit s'ouvrir même si la clé existante n'était pas montée au moment du démarrage
