# AGENTS.md — Playbook de review pour pr-reviewer-bot

## Conventions de nommage
- Fonctions/variables Python : snake_case
- Fichiers de test : test_*.py

## Règles de tests
- Toute nouvelle fonction publique doit avoir un test associé
- Pas de PR mergée avec des tests qui échouent

## Toujours
- Signaler les TODO ou FIXME oubliés dans le diff
- Signaler les secrets/clés API en dur dans le code
- Vérifier que les nouvelles routes API gèrent les erreurs

## Jamais
- Ne jamais approuver automatiquement une PR
- Ne jamais commenter sur des fichiers de configuration CI/CD sans certitude élevée
- Ne jamais suggérer de supprimer des tests existants