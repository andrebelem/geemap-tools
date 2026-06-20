# DEVELOPMENT.md

Plano de refatoração do `geemap-tools` para uma versão bilíngue (PT/EN) e ampliada.
Baseado na análise estrutural do repositório em 2026-06-20. Nenhuma das etapas abaixo
foi implementada ainda — este arquivo é apenas o plano.

## Decisão pendente: estratégia de i18n

Hoje "bilíngue" = docstrings com PT e EN no mesmo texto. Mensagens em runtime
(`raise`, `warnings.warn`, `print`, `tqdm.write`) são só em português em todos os
módulos. Antes da Fase 2, decidir entre:

- **(a) Mensagens só em inglês** + docstrings bilíngues como hoje. Mais simples,
  rápido de aplicar, mas abandona a promessa de "bilíngue" nas mensagens.
- **(b) Parâmetro `lang='pt'|'en'`** (por função ou via config global do pacote,
  ex. `geemap_tools.set_language('en')`) com um dicionário de strings por idioma.
  Mantém o bilinguismo real, mas exige tocar em toda mensagem de erro/aviso/debug.

Sem essa decisão, não faz sentido começar a Fase 2.

## Fase 0 — Higiene de repositório (sem risco, pode ser feita a qualquer momento)

- [ ] Remover do versionamento os arquivos já commitados em `.ipynb_checkpoints/`
      (`git rm -r --cached`), já cobertos pelo `.gitignore` mas commitados antes dele.
- [ ] Remover `setup.py` (mantendo apenas `pyproject.toml`) ou automatizar para que
      `setup.py` não duplique a lista de dependências manualmente.
- [ ] Remover o bloco de código comentado/morto em `analysis.py` (versão antiga de
      `get_TerraClimate`, ~130 linhas).
- [ ] Adicionar `CHANGELOG.md` e começar a versionar de fato (hoje fixo em `0.1.0`
      apesar de múltiplos releases funcionais).

## Fase 1 — Correções antes de tocar em estrutura

- [ ] Corrigir `describe_roi()` em `analysis.py`: usa `display(df)` sem importar —
      funciona só dentro do Jupyter. Trocar por `print(df)`/retorno explícito, ou
      importar `IPython.display.display` com fallback para ambientes não-notebook.
- [ ] Padronizar imports internos: hoje há mistura de absoluto
      (`from geemap_tools.io import roi_to_file`, em `analysis.py`) e relativo
      (`from .clouds import ...`, em `catalog.py`). Definir um padrão (relativo)
      e aplicar em todo o pacote.
- [ ] Revisar `sidra_tools.py`: `urllib3.disable_warnings(InsecureRequestWarning)` e
      `requests.get(..., verify=False)` desligam verificação SSL globalmente.
      Avaliar se é evitável (ex. usando certificado correto) antes de expor a
      função numa API pública mais ampla.

## Fase 2 — Separar `analysis.py` (902 linhas) em módulos coesos

`analysis.py` hoje concentra `index_to_timeseries`, `describe_roi`,
`get_TerraClimate`, `get_CHIRPS` e `extract_mapbiomas`, com blocos de import
repetidos (resultado de arquivos colados sem limpeza). Proposta de divisão:

- [ ] `roi_stats.py` — `describe_roi`
- [ ] `indices.py` — `index_to_timeseries`
- [ ] `terraclimate.py` — `get_TerraClimate`
- [ ] `chirps.py` — `get_CHIRPS`
- [ ] `mapbiomas.py` — `extract_mapbiomas`
- [ ] Atualizar `__init__.py` com os novos caminhos de import (mantendo os mesmos
      nomes públicos para não quebrar quem já usa o pacote).

## Fase 3 — Implementar a estratégia de i18n escolhida

- [ ] Criar módulo `geemap_tools/_messages.py` (ou similar) com as strings de
      erro/aviso/debug em PT e EN, conforme a decisão da Fase 0.
- [ ] Aplicar a opção escolhida em todos os `raise`, `warnings.warn`, `print` e
      `tqdm.write` dos módulos existentes.
- [ ] Traduzir o `class_legend` hardcoded em `extract_mapbiomas` (hoje só em PT).
- [ ] Atualizar `USAGE.md`, `README.md` e `README-en.md` para refletir o
      comportamento real (não só docstring).

## Fase 4 — Testes e CI (pré-requisito para ampliar a API com segurança)

- [ ] Criar `tests/` com testes de smoke para funções sem dependência de rede/GEE
      (`describe_roi` após a correção do `display`, `roi_to_file`/`file_to_roi`
      com geometrias sintéticas).
- [ ] Avaliar mocks para funções que dependem de `ee.*` (TerraClimate, CHIRPS,
      MapBiomas, catalog) ou marcá-las como testes de integração separados.
- [ ] Adicionar `.github/workflows/ci.yml` rodando os testes a cada push/PR.

## Fase 5 — Ampliação da API

- [ ] Revisar a lista de funções já desejadas em `private_dev/TODO.md`
      (`extract_band_values_to_dataframe`, `plot_band_histogram`,
      `plot_band_boxplot`, `convert_featurecollection_to_dataframe`,
      `add_band_statistics`, `compare_bands_across_images`,
      `sample_band_values_to_points`) e decidir quais entram nesta rodada.
- [ ] Adicionar type hints nas novas funções (e, oportunisticamente, nas
      existentes ao tocar nelas) para facilitar geração de docs bilíngues.
- [ ] Só iniciar esta fase depois das Fases 1–4, para não ampliar a API sobre
      uma base sem testes e com dívida de i18n não resolvida.

## Ordem recomendada

`Fase 0 → decisão de i18n → Fase 1 → Fase 2 → Fase 3 → Fase 4 → Fase 5`

Fases 0 e 1 podem ser feitas em paralelo por serem independentes. Fases 2 e 3
têm uma ordem mais flexível — mas separar os módulos (Fase 2) antes de
aplicar i18n (Fase 3) evita re-trabalho.
