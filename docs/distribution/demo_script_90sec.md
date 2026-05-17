# Script de demo — 90 secondes

**Format** : screen recording avec voix off. Pas de musique. Pas d'effets visuels. Vitesse normale.

---

## Beat 1 — Le problème (0:00–0:15)

**VO** : "Faire tourner Claude Code en permanence, depuis n'importe où, sans se battre avec SSH ou des serveurs — c'est exactement ce que Maestro règle."

**Écran** : Slide ou fond sobre avec le texte : *"Claude Code. Votre cloud. Votre navigateur."*

---

## Beat 2 — Le paiement (0:15–0:30)

**VO** : "On commence sur maestro.run. Un paiement unique de $99 via Stripe. Pas d'abonnement, pas de surprise mensuelle."

**Écran** : Page d'accueil maestro.run → clic "Get started" → Stripe Checkout ($99, one-time) → confirmation de paiement → redirect vers l'onboarding.

---

## Beat 3 — Le provisionnement (0:30–0:55)

**VO** : "Vous entrez votre clé API DigitalOcean. Maestro déploie un Droplet Ubuntu en arrière-plan — cloud-init installe Claude Code, configure le tunnel cloudflared, démarre le terminal web. Ça prend environ trois à cinq minutes."

**Écran** : Page d'onboarding — champ clé DO → clic "Provision" → barre de progression avec statuts en temps réel ("Creating Droplet… Installing Claude Code… Starting terminal…") → message "Your environment is ready."

---

## Beat 4 — L'authentification OAuth (0:55–1:15)

**VO** : "Le terminal s'ouvre dans le navigateur. Vous lancez l'auth OAuth Claude — exactement la même procédure que sur une machine locale, sauf que cette fois elle s'exécute sur votre propre VPS DigitalOcean."

**Écran** : Terminal web xterm.js s'ouvre → `claude auth login` → URL OAuth Anthropic → navigateur ouvre la page d'auth → autorisation → retour au terminal confirmant la connexion.

---

## Beat 5 — En production (1:15–1:30)

**VO** : "Copiez le snippet MCP dans claude.ai — et c'est prêt. Votre agent Claude Code est en ligne, il tourne sur votre compte DigitalOcean, accessible depuis n'importe quel onglet. Fermez le laptop — il continue."

**Écran** : Dashboard Maestro → copier le snippet MCP → claude.ai → coller le connecteur → lancer une tâche courte (ex : "Résume ce fichier README") → réponse de l'agent → fermer l'onglet → rouvrir → agent toujours actif, contexte intact.

---

*Notes de production : enregistrer en 1080p minimum. Désactiver les notifications système avant de commencer. Masquer les extensions navigateur. Couper entre 1:25 et 1:32 selon le rythme réel de provisionnement.*
