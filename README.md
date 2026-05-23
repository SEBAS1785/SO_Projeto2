```
   main.py         # Ponto de entrada simulação
   aeroporto.py      # Processo Servidor (Aeroporto)
   passageiro.py    # Processo Cliente (Passageiro)
   registo.py       # Registo de operações
   configuracao.py  # Configurações gerais (nº portões, agentes, etc.)
   gui.py           #Interface gráfica + graficos
   README.md
```

# Como Executar

```bash
python main.py
python gui.py
```

Escolher um modo:
**1 — Normal**: passageiros chegam com intervalos aleatórios
**2 — Alta Demanda**: muitos passageiros chegam quase simultaneamente

O log é guardado automaticamente em `airport_log.txt`.

# Arquitetura

# Componentes Principais

| Componente | Tipo | Responsabilidade |

| `airport_server` | `Process` | Gere fila, aloca portões e agentes |
| `passenger_process` | `Process` (×N) | Simula a chegada, a espera e o embarque |
| `_boarding_and_release` | `Process` | Executa o embarque de 1 passageiro |
| `AirportLogger` | Classe | Escreve no log com lock |

# Comunicação entre Processos

```
Passageiro --(escreve)--->  queue_list   <--(lê/remove)--- Servidor
Passageiro --(set)------->  notify_event <---(wait)---Servidor
Servidor   --(escreve)--->  result_dict  <---(lê)--- Passageiro
```

Toda a comunicação é feita através de **memória partilhada** gerida pelo
`multiprocessing.Manager`.

# Sincronização

| Mecanismo | Onde é usado |
|---|---|
| `Lock` (queue_lock) | Acesso exclusivo à fila de embarque |
| `Lock` (log_lock) | Escrita no ficheiro de log |
| `Lock` (stats_lock) | Actualização de estatísticas |
| `Lock` (resource_lock) | Gestão de IDs de portões/agentes |
| `Semaphore` (gate_semaphore) | Limita passageiros por portão |
| `Semaphore` (agent_semaphore) | Limita agentes em uso |
| `Event` (notify_event) | Notifica o servidor de novas chegadas |
| `Event` (stop_event) | Sinaliza ao servidor para encerrar |

# Prioridade de Embarque

A fila é ordenada por:
1. **Prioridade** (alta = 0, média = 1, baixa = 2)
2. **Hora de chegada**

| Classe do Bilhete | Prioridade | Duração embarque |

| Primeira | Alta | 1.0s |
| Executiva | Média | 1.5s |
| Económica | Baixa | 2.0s |

# Desistências

Se um passageiro esperar mais de `MAX_WAIT_TIME` segundos (configurável
em `configuracao.py`), abandona a fila e é registado como "desistido".


# Configurações (configuracao.py)

| Parâmetro | Valor default | Descrição |

| `NUM_GATES` | 3 | Número de portões |
| `NUM_AGENTS` | 4 | Número de agentes |
| `NUM_PASSENGERS` | 20 | Total de passageiros |
| `MAX_WAIT_TIME` | 15s | Timeout para desistência |
| `ARRIVAL_INTERVAL` | 0.5s | Intervalo médio de chegada |


# Exemplo de Log

```
[10:23:01.452] CHEGADA    | Passageiro Ana_1 (PID=1) | Classe: primeira   | Prioridade: alta
[10:23:01.455] FILA       | Passageiro Ana_1 entrou na fila | Posição estimada: 1
[10:23:01.460] EMBARQUE   | Passageiro Ana_1 | Portão 1 | Agente 1 | Espera: 0.3s
[10:23:02.462] CONCLUÍDO  | Passageiro Ana_1 embarcou | Portão 1 | Duração: 1.0s
[10:23:15.800] DESISTÊNCIA| Passageiro Nuno_7 desistiu após 15.0s de espera
```


# Funcionalidades Implementadas

- Prioridade de embarque (alta / média / baixa)
- Portões exclusivos por passageiro (semáforo)
- Agentes de embarque (semáforo)
- Registo completo: chegada, prioridade, espera, duração, hora embarque
- Cenário de alta demanda
- Desistências por timeout
- Tempo de embarque variável por prioridade
- Múltiplos portões com distribuição eficaz
- Simulação modo de alta demanda
- Visualização em consola em tempo real
- Resumo de desistências no log
- Interface gráfica e gráficos para tratar a estatística
