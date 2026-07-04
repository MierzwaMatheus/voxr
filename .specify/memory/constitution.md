<!--
SYNC IMPACT REPORT
Version: N/A → 1.0.0 (primeira constituição real — template vazio substituído)
Princípios adicionados: I. Offline e Privacidade Absoluta, II. Integração Nativa Linux,
  III. Latência e Performance Perceptível, IV. Resiliência e Degradação Graciosa,
  V. Entregas Faseadas e Simplicidade Progressiva
Seções adicionadas: Stack Tecnológica Obrigatória, Fases de Entrega
Templates atualizados:
  - .specify/templates/plan-template.md (Constitution Check) ✅
  - .specify/templates/spec-template.md (sem mudanças necessárias) ✅
  - .specify/templates/tasks-template.md (sem mudanças necessárias) ✅
TODOs diferidos: nenhum
-->

# Voxr Constitution

## Core Principles

### I. Offline e Privacidade Absoluta

Voxr DEVE funcionar 100% sem conexão à internet. Nenhum dado de áudio, texto transcrito ou
metadado DEVE ser transmitido a servidores externos em nenhuma circunstância. O modelo Whisper
DEVE ser armazenado localmente no dispositivo do usuário. Qualquer dependência de serviço externo
de inferência ou processamento de voz é proibida.

**Rationale**: privacidade e confiabilidade são requisitos inegociáveis para o público-alvo
(Linux power users que rejeitam telemetria e dependência de nuvem). O valor do produto colapsa
sem essa garantia.

### II. Integração Nativa Linux (X11 / GTK 3 / systemd)

O app DEVE integrar-se ao ambiente Linux padrão via ferramentas do ecossistema:
- UI DEVE usar GTK 3
- Injeção de texto DEVE usar `xdotool type`
- Hotkeys globais DEVEM usar `pynput`
- Autostart DEVE ser implementado via `systemd` user service
- Distribuição DEVE ser exclusivamente via pacote `.deb`
- X11 é o único ambiente de display suportado; Wayland está explicitamente fora de escopo

**Rationale**: a proposta central é "funciona em qualquer campo de texto do Linux sem configuração".
Isso exige integração profunda com X11 e xdotool — não há alternativa portátil equivalente.

### III. Latência e Performance Perceptível

A transcrição DEVE iniciar e completar em menos de 2 segundos após o encerramento da gravação
para gravações de até 30s com o modelo padrão. O modelo padrão DEVE ser Whisper Medium com
quantização int8 via CTranslate2. Modelos maiores (Large, Large-v2) PODEM ser configurados
pelo usuário, mas o comportamento padrão DEVE priorizar velocidade sobre precisão máxima.
VAD (Voice Activity Detection) DEVE estar ativo por padrão para eliminar silêncio desnecessário.

**Rationale**: latência perceptível acima de 2s quebra o fluxo de trabalho e derrota o propósito
de um ditador por voz. O usuário espera feedback tão ágil quanto a digitação manual.

### IV. Resiliência e Degradação Graciosa

Falhas de transcrição (parciais ou totais) NÃO DEVEM travar o app, fechar a janela ou perder
texto já transcrito com sucesso. Regras obrigatórias:
- Chunks com falha após 2 retries DEVEM ser substituídos pelo placeholder `[trecho não transcrito]`
- Falhas parciais DEVEM resultar em entrega do texto disponível + placeholders, nunca em silêncio
- O usuário DEVE ser notificado de falhas parciais via feedback visual não-intrusivo
- Gravações DEVEM ter limite máximo de 3 minutos; countdown visual DEVE iniciar nos últimos 10s

**Rationale**: falhas silenciosas são piores que falhas visíveis — o usuário precisa saber
exatamente o que foi perdido para poder repetir a fala. Robustez é parte do contrato de produto.

### V. Entregas Faseadas e Simplicidade Progressiva (YAGNI)

O desenvolvimento DEVE seguir estritamente as 4 fases definidas no PRD. Nenhuma fase posterior
DEVE ser iniciada antes que a fase atual esteja funcional e testável de ponta a ponta. Código,
abstrações ou configurações sem demanda documentada na fase corrente são proibidos. Complexidade
DEVE ser justificada por necessidade presente, não futura.

**Rationale**: Voxr é um projeto de desenvolvedor solo. Fases protegem contra scope creep e
garantem que cada incremento entregue valor real antes de adicionar complexidade opcional.

---

## Stack Tecnológica Obrigatória

As seguintes dependências são mandatórias e NÃO DEVEM ser substituídas sem emenda à constituição:

| Componente | Tecnologia | Justificativa |
|---|---|---|
| Linguagem | Python 3.11+ | ecossistema ML, GTK bindings |
| UI | GTK 3 | integração nativa Linux |
| Transcrição | faster-whisper (CTranslate2 int8) | performance offline |
| Modelo padrão | Whisper Medium | equilíbrio velocidade/precisão |
| Hotkeys | pynput | captura global X11 |
| Injeção de texto | xdotool | compatibilidade universal X11 |
| Autostart | systemd user service | padrão Linux moderno |
| Distribuição | pacote .deb | instalação sem dependências manuais |
| Display | X11 apenas | Wayland fora de escopo |

**Limites de gravação**: padrão 60s, mínimo 30s, máximo 3 minutos.
**Modos de acionamento**: Toggle (padrão) e Push-to-talk.
**Download do modelo**: realizado na primeira execução via wizard GTK.

---

## Fases de Entrega

As fases abaixo são a referência para o **Constitution Check** em todos os planos de feature:

| Fase | Escopo | Status de Bloqueio |
|---|---|---|
| **Fase 1 — MVP** | Hotkey → gravação → transcrição → injeção via xdotool. Widget flutuante com animação de ondas. Modo Toggle. | Bloqueia todas as demais |
| **Fase 2 — Configurações** | Tela de configurações GTK (Geral, Transcrição, Performance). Seleção de modelo, hotkey, limites. | Requer Fase 1 completa |
| **Fase 3 — Pipeline e Resiliência** | Modo pipeline chunked (chunks 30s + overlap 2-3s). VAD refinado. Retry e placeholders. Modo Push-to-talk. | Requer Fase 2 completa |
| **Fase 4 — Distribuição .deb** | Pacote .deb com systemd user service. Setup wizard na primeira execução. | Requer Fase 3 completa |

Qualquer feature planejada DEVE ser associada a uma fase. Features de fase posterior NÃO DEVEM
ser implementadas enquanto a fase anterior não estiver completa.

---

## Governance

Esta constituição supera todas as outras práticas, convenções ou preferências pessoais durante
o desenvolvimento. Em caso de conflito entre a constituição e qualquer outra diretriz, a
constituição prevalece.

**Procedimento de emenda**:
1. A emenda DEVE ser documentada com motivação explícita e impacto nos princípios existentes
2. `CONSTITUTION_VERSION` DEVE ser incrementada: MAJOR para remoção/redefinição de princípios,
   MINOR para adição de seções ou expansão material, PATCH para refinamentos e clarificações
3. `LAST_AMENDED_DATE` DEVE ser atualizado para a data da emenda (formato ISO 8601: YYYY-MM-DD)
4. Templates dependentes DEVE ser revisados após qualquer emenda (plan, spec, tasks)

**Compliance**: Todo plano de feature DEVE incluir um "Constitution Check" verificando
conformidade com os 5 princípios antes de iniciar a implementação.

**Version**: 1.0.0 | **Ratified**: 2026-07-04 | **Last Amended**: 2026-07-04
