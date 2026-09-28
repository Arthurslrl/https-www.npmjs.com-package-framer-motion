# Instructions pour Claude

## Création de sites web / interfaces (UI)

Pour **toute** demande de création, refonte ou modification d'un site web, d'une page,
d'une landing page, d'une app ou d'un composant UI — même si le prompt ne le précise pas :

1. **Lire tous les skills UI installés** (dans `.claude/skills/`) avant d'écrire du code :
   - `design-taste-frontend` (et `design-taste-frontend-v1` pour comparaison)
   - `high-end-visual-design`
   - `minimalist-ui`
   - `industrial-brutalist-ui`
   - `gpt-taste`
   - `stitch-design-taste`
   - `redesign-existing-projects` (si un site existe déjà)
   - `brandkit` (si la demande touche à l'identité visuelle / au logo)
   - `imagegen-frontend-web`, `imagegen-frontend-mobile`, `image-to-code` (pour leurs principes de composition)
   - `full-output-enforcement` (toujours : code complet, sans placeholders)
   - `web-design-guidelines`
2. **Consulter la bibliothèque `design-md/`** : si la demande évoque une marque ou un style
   (ex. « style Stripe », « comme Linear »), lire le `design-md/<nom>/DESIGN.md` correspondant.
   Si un `DESIGN.md` existe à la racine du projet, il fait autorité.
3. **Synthétiser, ne pas empiler** : les skills de style se contredisent (minimaliste vs
   brutaliste, etc.). Choisir **une direction visuelle principale** adaptée à la demande,
   reprendre les bonnes pratiques communes des autres, et indiquer brièvement dans la
   réponse quelle direction a été retenue et pourquoi.
4. **Vérifier à la fin** avec `web-design-guidelines` (accessibilité, UX) et corriger les
   problèmes trouvés avant de livrer.

Si l'utilisateur nomme explicitement un skill ou un style dans son prompt, celui-ci prime
sur le choix automatique.
