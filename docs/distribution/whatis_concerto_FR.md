---
title: "Concerto — votre agent Claude Code, toujours disponible"
geometry: margin=2cm
fontsize: 11pt
---

# Concerto

**Claude Code sur votre cloud — depuis n'importe quel navigateur.**

Un agent actif en permanence, accessible depuis n'importe quel onglet, n'importe quel appareil — sans toucher un terminal.

---

## Comment ça marche

1. **Choisissez votre plan** — Hébergé (39$/mois, infra gérée) ou BYOC (99$ une fois, déploiement sur votre compte DigitalOcean).
2. **Provisionnement automatique** — Concerto déploie un serveur Ubuntu 24.04 (2 vCPU / 4 Go RAM), installe Claude Code, configure le tunnel cloudflared et ouvre un terminal web. 3 à 5 minutes.
3. **Connexion** — OAuth Claude dans le navigateur, copie du snippet MCP dans claude.ai. Votre agent est en ligne.

---

## Pour qui

- **Les abonnés Claude Max** qui veulent un agent actif en permanence, sans gérer l'infrastructure
- **Les développeurs multi-appareils** qui ne veulent pas se battre avec SSH à chaque fois
- **Les opérateurs** qui confient des tâches longues à Claude Code et ont besoin d'un environnement stable

---

## Prix

| | **Hébergé** ★ | **BYOC** |
|---|---|---|
| Prix | 39$/mois | 99$ une fois |
| Infrastructure | Gérée par Concerto | Votre compte DigitalOcean |
| Coût compute | Inclus | ~24$/mois facturé par DigitalOcean |
| Données | Vos fichiers, environnement isolé | Votre VPS, votre compte |

Aucun frais caché. Concerto n'a pas d'accès persistant à votre environnement après le provisionnement.

---

**concerto.run**
