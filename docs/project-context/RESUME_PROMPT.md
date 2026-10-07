# Prompt para retomar EngCalc en una sesión nueva

Pegar tal cual en una sesión nueva de Claude Code abierta en la carpeta
`C:\Users\elias\engcalc` (cualquier cuenta):

```
Retomamos EngCalc (repo eliaszamora/engcalc-colab, carpeta C:\Users\elias\engcalc). Antes de
nada lee AGENTS.md y docs/project-context/CURRENT.md: empieza por el bloque "Where things stand
today" y su párrafo "Handoff 2026-10-07", luego la sección "How to resume in a new
conversation" y NEXT.md. Verifica contra GitHub el SHA de main, la versión y que no haya PRs
abiertos. Estado al cerrar la sesión anterior: la 0.46.1 está publicada y probada en mi Colab;
eigenvals(K, G) con G singular quedó en la rama fix/chapter-10-findings con su arnés de
auditoría en tools/eigen_audit/. El siguiente paso propuesto es una 0.46.2 corta con los
hallazgos menores de la auditoría (solve con rango y límites en pulgadas, la unidad de una
razón mm/m en max/min, dos mensajes que muestran nombres internos). Las decisiones te las dejo
a ti y tienes mi autorización para fusionar y publicar, siguiendo el procedimiento de
publicación de CURRENT.md (auditoría independiente incluida) y probando al final en mi Colab
con la extensión de Claude en Chrome. Respóndeme en español. Antes de empezar, dime en pocas
líneas qué leíste y qué vas a hacer.
```
