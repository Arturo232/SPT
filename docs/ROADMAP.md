# Roadmap — Plan de implementación SPT

Estado al 2026-08-15 (tag `v1.7.0`). **Proyecto completo al 100%.**

## Resumen por fases

| Fase | Ítem | Esfuerzo | Estado |
|---|---|---|---|
| 0.1 | `AGENTS.md` | Bajo | ✅ **v1.5.0** |
| 0.2 | CI en GitHub Actions (`pytest` en push/PR) | Bajo | ✅ **v1.5.0** |
| 1.1 | `docs/arquitectura.md` (capas, servicios, errores) | Bajo | ✅ **v1.5.0** |
| 1.2 | `docs/contratos.md` (esquemas de datos) | Bajo | ✅ **v1.5.0** |
| 1.3 | `docs/presentacion.md` | Bajo | ✅ **v1.5.0** |
| 1.4 | `docs/materiales.md` (trazabilidad) | Bajo | ✅ **v1.5.0** |
| 2.1 | Opción "Ejercicios del taller 2026" en el menú | Bajo | ✅ **v1.6.0** |
| 2.2 | Comando `exportar` en la consola (TXT/JSON/CSV/XLSX) | Bajo | ✅ **v1.6.0** |
| 2.3 | Comando `grafica` en la consola (fasores / triángulo) | Bajo | ✅ **v1.6.0** |
| 2.4 | Corregir `pcarga` para leer `V_nominal` del input | Muy bajo | ✅ **v1.6.0** |
| 3.1–3.5 | **GUI con customtkinter** | Alto | ✅ **v1.4.0** |
| 4.1 | Type hints + `mypy` en módulos clave | Medio | ✅ **v1.7.0** |
| 4.2 | `pytest --cov` (pytest-cov) en CI | Bajo | ✅ **v1.7.0** |
| 4.3 | Badges en README (tests, cobertura, versión, mypy) | Bajo | ✅ **v1.7.0** |
| 4.4 | `docs/AI_CONTEXT.md` (documentación para agentes IA) | Bajo | ✅ **v1.7.0** |
| 4.5 | `docs/GUIA_USUARIO.md` (manual completo de usuario) | Bajo | ✅ **v1.7.0** |

## Historial de versiones

| Versión | Contenido |
|---|---|
| **v1.0.0** | Port completo de MATLAB a Python (12 módulos, tests, CLI) |
| **v1.1.0** | Consola de comandos, CircuitoTrifasico, asistente guiado |
| **v1.2.0** | Reporte completo de variables, comandos de consulta |
| **v1.3.0** | Modo monofásico, CircuitoMonofasico, docs/consola.md |
| **v1.4.0** | GUI con customtkinter (sidebar, cards, feedback visual) |
| **v1.5.0** | AGENTS.md, CI, documentación técnica (4 docs) |
| **v1.6.0** | Exportar, gráficas, Taller 2026, corrección pcarga |
| **v1.7.0** | Type hints, pytest-cov, badges, AI_CONTEXT, GUIA_USUARIO |

## Dependencias entre fases

```
Fase 0 (AGENTS + CI)   →  ✅ completada (v1.5.0)
Fase 1 (documentación) →  ✅ completada (v1.5.0)
Fase 2 (UX mejoras)    →  ✅ completada (v1.6.0)
Fase 3 (GUI)           →  ✅ completada (v1.4.0)
Fase 4 (calidad)       →  ✅ completada (v1.7.0)
```

## Notas

- Las pruebas cubren **150+ tests** (100 % pasando en pytest).
- Cobertura medida con `pytest-cov`; chequeo de tipos con `mypy`.
- El proyecto está **completo**; futuras versiones pueden agregar nuevos módulos de SEP.
