# Voxr — Product Requirements Document

> **Versão:** 1.0  
> **Status:** Planejamento  
> **Plataforma:** Zorin OS (Ubuntu-based, X11)  
> **Linguagem:** Python + GTK  

---

## 1. Visão do Produto

Voxr é um aplicativo nativo de ditado por voz para Linux. Ele fica em segundo plano como um serviço do sistema, é acionado por um atalho de teclado global, captura o áudio do usuário, transcreve localmente usando um modelo de IA offline, e insere o texto diretamente no campo ativo — qualquer campo, em qualquer aplicativo.

Não há nuvem. Não há API externa. Não há dependência de conectividade. Tudo roda localmente na máquina do usuário.

---

## 2. Identidade da Marca

**Nome:** Voxr  
**Pronúncia:** "vóxer" (PT-BR) / "voksr" (EN)  
**Raiz:** *Vox* (latim — voz) + sufixo minimalista `-r`

### Tom de Voz

Preciso, discreto, confiante.

Voxr não se anuncia. Ele está lá quando o usuário precisa, some quando não precisa. O tom de comunicação segue essa filosofia: frases curtas, sem floreios, sem jargão técnico. Uma ferramenta profissional que respeita a inteligência de quem usa.

**Exemplos práticos:**
- Erro: *"Microfone não encontrado"* — não *"Ops! Parece que algo deu errado com seu dispositivo de áudio"*
- Menu: *"Configurações / Sair"* — sem elementos decorativos desnecessários
- Setup: *"Voxr detectou seu hardware. Recomendamos o modelo Medium."* — direto, sem elogios vazios

### Idiomas da Interface

A interface nasce bilíngue: **PT-BR e EN**. Selecionável nas configurações. Outros idiomas podem ser adicionados futuramente via contribuição.

---

## 3. Stack Técnico

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Interface | GTK 3 + AppIndicator3 |
| Motor de transcrição | faster-whisper (CTranslate2, int8) |
| Modelo padrão | Whisper Medium |
| Hotkey global | pynput |
| Inserção de texto | xdotool (X11) |
| Detecção de silêncio | faster-whisper VAD integrado |
| Servidor gráfico | X11 (Zorin OS padrão) |
| Distribuição | Pacote .deb |
| Serviço de sistema | systemd user service |

### Sobre o Modelo

O **Whisper Medium** é o modelo padrão. É o melhor equilíbrio entre qualidade e performance para o hardware de referência (i7 8ª gen, 16GB RAM, sem GPU CUDA disponível). O modelo suporta todos os idiomas nativamente — não há download adicional por idioma.

O usuário pode trocar o modelo nas configurações. Modelos disponíveis: Tiny, Base, Small, Medium, Large v3 Turbo.

---

## 4. Distribuição e Instalação

### Pacote .deb

O Voxr é distribuído como pacote `.deb`. A instalação via `dpkg -i` ou gerenciador de pacotes:

- Instala as dependências de sistema (`xdotool`, `portaudio19-dev`, `python3`, `python3-gi`, `libappindicator3-1`, etc.)
- Cria a estrutura de diretórios do app
- Registra o serviço systemd (desabilitado por padrão — o usuário ativa nas configurações)
- Adiciona o app no menu do Zorin

**O modelo Whisper NÃO está incluído no .deb** — é baixado na primeira execução.

### Primeira Execução — Setup GTK

Na primeira vez que o Voxr é aberto, uma janela de setup GTK é exibida. Ela:

1. Detecta o hardware do sistema (RAM disponível, CPU, presença de GPU CUDA)
2. Recomenda o modelo ideal com uma justificativa simples
3. Oferece a opção de escolher outro modelo (com descrição de cada um)
4. Realiza o download do modelo escolhido com barra de progresso
5. Permite configurar o atalho de teclado inicial
6. Pergunta se o usuário deseja iniciar o Voxr automaticamente com o sistema

O setup só é exibido uma vez. Após concluído, o app sobe direto como serviço em background nas próximas inicializações.

---

## 5. Arquitetura de Funcionamento

### 5.1 Serviço em Background

O Voxr roda como um **systemd user service** em background. Ele:

- Escuta o atalho de teclado global via pynput
- Mantém o modelo Whisper carregado em memória (evita o custo de inicialização a cada uso)
- Gerencia o ícone no system tray via AppIndicator3

### 5.2 System Tray

O ícone no system tray é o ponto central de controle do app. Ele possui **três estados visuais**:

| Estado | Ícone |
|---|---|
| Idle (aguardando) | Ícone normal |
| Gravando | Ícone animado / colorido |
| Processando | Ícone com animação de loading |

**Menu do tray (clique direito):**
- Configurações
- *(separador)*
- Sair

---

## 6. Fluxo Principal de Uso

```
[Usuário pressiona o atalho — 1º press]
        ↓
[Widget flutuante aparece perto do cursor]
[Gravação inicia]
        ↓
[Usuário fala]
        ↓
[Usuário pressiona o atalho novamente — 2º press]
    OU
[Usuário clica no widget]
        ↓
[Gravação encerra]
[Widget entra em modo "processando"]
        ↓
[Transcrição concluída]
        ↓
[Texto inserido no campo ativo via xdotool]
[Widget fecha]
```

**Cancelamento:** pressionar `Escape` a qualquer momento cancela a gravação ou o processamento e fecha o widget sem inserir texto.

### 6.1 Widget de Gravação

O widget é uma janela flutuante pequena, sem decorações de janela (sem barra de título, sem bordas), posicionada próxima ao cursor no momento do acionamento.

**Durante a gravação:**
- Exibe ondas sonoras animadas em tempo real, reagindo ao volume do microfone
- Exibe um contador de tempo decorrido

**Nos últimos 10 segundos antes do limite:**
- Exibe uma contagem regressiva visível (10, 9, 8... 0)
- Sutil mudança visual para indicar que o tempo está acabando

**Ao atingir o limite:**
- A gravação encerra automaticamente
- O processamento começa imediatamente

**Durante o processamento:**
- As ondas sonoras são substituídas por uma animação de "processando" (spinner ou pulso suave)

### 6.2 Modos de Acionamento

Configurável nas preferências:

| Modo | Comportamento |
|---|---|
| **Toggle** (padrão) | 1º press inicia, 2º press encerra e transcreve |
| **Push-to-talk** | Segurar inicia, soltar encerra e transcreve |

---

## 7. Pipeline de Transcrição

### 7.1 Modo Padrão (sem pipeline)

Grava todo o áudio → encerra → transcreve tudo de uma vez → insere.

Adequado para gravações curtas (até ~30s). Simples e sem overhead.

### 7.2 Modo Pipeline (configurável em Configurações > Performance)

Estratégia de chunked transcription com processamento paralelo. Reduz drasticamente o tempo de espera em gravações longas.

**Como funciona:**

```
t=0s    Gravação inicia
t=30s   Chunk 1 (30s) → enviado para transcrição
        Chunk 2 começa a gravar simultaneamente
t=45s   Chunk 1 transcrito (~15s de processamento)
t=60s   Chunk 2 (30s) → enviado para transcrição
        Chunk 3 começa a gravar
t=75s   Chunk 2 transcrito
...
[Usuário encerra]
        Último chunk → transcrição → concatenação final → inserção
```

O usuário nunca espera mais que ~15s após encerrar — apenas o tempo do último chunk.

**Overlap entre chunks:**

Para evitar corte no meio de palavras, cada chunk inicia com os últimos **2-3 segundos** do chunk anterior. A deduplicação é feita via timestamps por palavra (disponível nativamente no faster-whisper) — o texto duplicado é removido automaticamente na concatenação.

**Comportamento de inserção no modo pipeline:**

O texto transcrito é **acumulado internamente** e inserido no campo ativo de uma única vez ao final — não em tempo real. Isso evita distração do usuário e garante que a concatenação seja coerente.

**VAD (Voice Activity Detection):**

Ativo por padrão em ambos os modos. Remove silêncios automaticamente antes de enviar para o modelo, prevenindo alucinações em pausas longas.

### 7.3 Resiliência a Falhas

**Retry automático:** se um chunk falhar, o sistema tenta até **2 vezes** antes de considerar falha real.

**Falha parcial:** se após os retries o chunk ainda falhar, o sistema não descarta os chunks já transcritos. O resultado é inserido com um placeholder no trecho que falhou:

```
...texto transcrito normalmente... [trecho não transcrito] ...texto transcrito normalmente...
```

**Notificação:** uma notificação no system tray informa o usuário sobre a falha parcial: *"Transcrição concluída com 1 trecho não transcrito."*

O usuário recebe o resultado parcial e decide se regrava o trecho ausente.

---

## 8. Limites de Gravação

| Configuração | Valor |
|---|---|
| **Limite padrão** | 60 segundos |
| **Mínimo configurável** | 30 segundos |
| **Máximo configurável** | 3 minutos |
| **Aviso de tempo** | Contador regressivo nos últimos 10 segundos |

> **Nota:** ao aumentar o limite acima de 60s, as configurações exibem um aviso informando que o tempo de processamento aumenta proporcionalmente ao tempo gravado (no modo padrão, sem pipeline).

---

## 9. Compatibilidade de Inserção de Texto

A inserção via `xdotool type` no X11 é **universalmente compatível** com qualquer campo de texto ativo no sistema:

- Terminais (bash, zsh, fish)
- Editores de texto nativos (gedit, kate, etc.)
- IDEs (VS Code, etc.)
- Navegadores (Chrome, Firefox) — qualquer campo de texto em páginas web
- Aplicativos nativos GTK/Qt
- Campo de busca do sistema

Não há restrição de contexto. Se o campo tem foco e aceita input de teclado, o Voxr insere.

---

## 10. Tratamento de Microfone Não Detectado

**Comportamento padrão (idle):**
- O ícone no system tray muda de aparência (estado de erro — vermelho ou com indicador visual de problema)
- Uma notificação do sistema é exibida: *"Voxr: nenhum microfone detectado."*
- O atalho de teclado permanece registrado, mas inativo

**Se o usuário acionar o atalho mesmo sem microfone:**
- Um dialog GTK é exibido informando que nenhum microfone foi detectado
- Inclui um botão para abrir as configurações de áudio do sistema

**Reconexão:**
- O Voxr monitora conexão/desconexão de dispositivos de áudio
- Ao detectar um microfone disponível, retorna automaticamente ao estado normal sem necessidade de reiniciar

---

## 11. Configurações

Acessíveis via menu do system tray → "Configurações". Janela GTK organizada em abas.

### Aba: Geral

| Configuração | Tipo | Padrão |
|---|---|---|
| Idioma da interface | Seletor (PT-BR / EN) | PT-BR |
| Iniciar com o sistema | Toggle | Desabilitado |
| Atalho de teclado | Campo de captura de tecla | A definir no setup |
| Modo de acionamento | Seletor (Toggle / Push-to-talk) | Toggle |

### Aba: Transcrição

| Configuração | Tipo | Padrão |
|---|---|---|
| Modelo | Seletor com opção de download | Medium |
| Idioma de transcrição | Seletor + opção "Automático" | Automático |
| Limite de gravação | Slider (30s – 3min) | 60s |

### Aba: Performance

| Configuração | Tipo | Padrão |
|---|---|---|
| Transcrição em pipeline | Toggle | Desabilitado |

> Quando habilitado, exibe uma descrição: *"O áudio é processado em blocos de 30 segundos durante a gravação, reduzindo o tempo de espera ao final."*

---

## 12. Idiomas de Transcrição Suportados

O Whisper Medium suporta **99 idiomas nativamente** — nenhum pacote adicional é necessário. A detecção automática analisa os primeiros segundos do áudio e identifica o idioma.

Os idiomas mais relevantes são expostos no seletor da interface. A opção "Automático" é o padrão.

---

## 13. Fases de Desenvolvimento

### Fase 1 — MVP Funcional
- Serviço em background com systemd
- Hotkey global (toggle)
- Widget flutuante com animação de ondas
- Transcrição com Whisper Medium (modo padrão, sem pipeline)
- Inserção via xdotool
- System tray com menu básico (Configurações / Sair)
- Tratamento de microfone não detectado

### Fase 2 — Configurações e Polimento
- Janela de configurações completa (todas as abas)
- Setup de primeira execução com detecção de hardware
- Download de modelos alternativos
- Contador regressivo e limite de gravação configurável
- Bilinguismo PT-BR / EN

### Fase 3 — Pipeline e Resiliência
- Modo pipeline com chunked transcription
- Overlap e deduplicação por timestamps
- Sistema de retry e falha parcial com placeholder
- VAD refinado

### Fase 4 — Distribuição
- Empacotamento .deb
- Testes em Zorin OS (X11)
- Documentação de instalação

---

## 14. O que Voxr NÃO faz

- Não envia áudio para nenhum servidor externo
- Não requer conexão com a internet após o download do modelo
- Não funciona como transcrição em tempo real (streaming contínuo)
- Não suporta Wayland nativamente nesta versão (X11 apenas)
- Não possui reconhecimento de comandos de voz (não é um assistente)
- Não grava ou armazena o áudio do usuário após a transcrição

---

*Documento gerado como briefing para desenvolvimento. Todas as decisões de arquitetura interna, estrutura de arquivos e escolhas de implementação ficam a critério do desenvolvedor, desde que respeitem os comportamentos e fluxos descritos aqui.*
